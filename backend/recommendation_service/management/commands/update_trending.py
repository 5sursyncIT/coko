from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Avg, Q, F
from django.core.cache import cache
import logging
from datetime import timedelta
from typing import List, Dict, Any

from recommendation_service.models import (
    TrendingBook, BookVector, UserInteraction
)
from books.models import Book
from recommendation_service.tasks import update_trending_books

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Mettre à jour les livres tendances'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'all'],
            default='all',
            help='Période pour calculer les tendances (défaut: all)'
        )
        
        parser.add_argument(
            '--trend-type',
            type=str,
            choices=['views', 'downloads', 'ratings', 'interactions', 'all'],
            default='all',
            help='Type de tendance à calculer (défaut: all)'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Nombre maximum de livres tendances par catégorie (défaut: 100)'
        )
        
        parser.add_argument(
            '--min-interactions',
            type=int,
            default=5,
            help='Nombre minimum d\'interactions pour être considéré comme tendance (défaut: 5)'
        )
        
        parser.add_argument(
            '--async',
            action='store_true',
            help='Utiliser les tâches asynchrones (Celery)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la mise à jour même si récente'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans réellement mettre à jour'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé des opérations'
        )
        
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Vider le cache après la mise à jour'
        )
    
    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        self.dry_run = options.get('dry_run', False)
        
        try:
            if options['async']:
                self._handle_async(options)
            else:
                self._handle_sync(options)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des tendances: {str(e)}")
            raise CommandError(f"Erreur: {str(e)}")
    
    def _handle_async(self, options):
        """Traitement asynchrone avec Celery"""
        self._log("Lancement de la mise à jour asynchrone des tendances...")
        
        if self.dry_run:
            self._log("[MODE SIMULATION] Tâche asynchrone non lancée")
            return
        
        try:
            task = update_trending_books.delay()
            self._log_success(f"Tâche asynchrone lancée: {task.id}")
            self._log("Utilisez 'celery -A coko worker' pour traiter la tâche")
            
        except Exception as e:
            logger.error(f"Erreur lors du lancement de la tâche asynchrone: {str(e)}")
            raise CommandError(f"Erreur asynchrone: {str(e)}")
    
    def _handle_sync(self, options):
        """Traitement synchrone"""
        self._log("Mise à jour synchrone des tendances...")
        
        periods = [options['period']] if options['period'] != 'all' else ['daily', 'weekly', 'monthly']
        trend_types = [options['trend_type']] if options['trend_type'] != 'all' else ['views', 'downloads', 'ratings', 'interactions']
        
        total_updated = 0
        
        for period in periods:
            for trend_type in trend_types:
                updated = self._update_trending_for_period_and_type(
                    period, trend_type, options
                )
                total_updated += updated
        
        # Nettoyer les anciennes entrées
        if not self.dry_run:
            self._cleanup_old_trending()
        
        # Vider le cache si demandé
        if options['clear_cache']:
            self._clear_cache()
        
        if self.dry_run:
            self._log_success(f"[SIMULATION] {total_updated} livres tendances seraient mis à jour")
        else:
            self._log_success(f"Mise à jour terminée: {total_updated} livres tendances mis à jour")
    
    def _update_trending_for_period_and_type(self, period: str, trend_type: str, options: Dict[str, Any]) -> int:
        """Mettre à jour les tendances pour une période et un type donnés"""
        self._log(f"Calcul des tendances {trend_type} pour la période {period}...")
        
        # Calculer la date de début selon la période
        now = timezone.now()
        if period == 'daily':
            start_date = now - timedelta(days=1)
        elif period == 'weekly':
            start_date = now - timedelta(weeks=1)
        elif period == 'monthly':
            start_date = now - timedelta(days=30)
        else:
            raise CommandError(f"Période inconnue: {period}")
        
        # Vérifier si une mise à jour récente existe
        if not options['force'] and not self.dry_run:
            recent_update = TrendingBook.objects.filter(
                period=period,
                trend_type=trend_type,
                last_updated__gte=now - timedelta(hours=1)
            ).exists()
            
            if recent_update:
                self._log(f"  Mise à jour récente trouvée pour {period}/{trend_type}, ignoré")
                return 0
        
        # Calculer les tendances selon le type
        trending_books = self._calculate_trending_books(
            start_date, trend_type, options['limit'], options['min_interactions']
        )
        
        if not trending_books:
            self._log(f"  Aucun livre tendance trouvé pour {period}/{trend_type}")
            return 0
        
        self._log(f"  {len(trending_books)} livres tendances trouvés")
        
        if self.dry_run:
            if self.verbose:
                for i, book_data in enumerate(trending_books[:10], 1):
                    self._log(f"    {i}. {book_data['title']} (score: {book_data['score']:.2f})")
            return len(trending_books)
        
        # Sauvegarder les tendances
        updated_count = self._save_trending_books(trending_books, period, trend_type)
        
        self._log(f"  ✓ {updated_count} livres tendances mis à jour pour {period}/{trend_type}")
        return updated_count
    
    def _calculate_trending_books(self, start_date, trend_type: str, limit: int, min_interactions: int) -> List[Dict[str, Any]]:
        """Calculer les livres tendances selon le type"""
        base_query = UserInteraction.objects.filter(
            created_at__gte=start_date
        )
        
        if trend_type == 'views':
            interactions = base_query.filter(interaction_type='view')
        elif trend_type == 'downloads':
            interactions = base_query.filter(interaction_type='download')
        elif trend_type == 'ratings':
            interactions = base_query.filter(interaction_type='rating')
        elif trend_type == 'interactions':
            interactions = base_query
        else:
            raise CommandError(f"Type de tendance inconnu: {trend_type}")
        
        # Grouper par livre et calculer les métriques
        if trend_type == 'ratings':
            book_stats = interactions.values('book_id').annotate(
                interaction_count=Count('id'),
                avg_rating=Avg('rating'),
                score=F('avg_rating') * Count('id')
            ).filter(
                interaction_count__gte=min_interactions
            ).order_by('-score')[:limit]
        else:
            book_stats = interactions.values('book_id').annotate(
                interaction_count=Count('id'),
                score=Count('id')
            ).filter(
                interaction_count__gte=min_interactions
            ).order_by('-score')[:limit]
        
        # Enrichir avec les informations du livre
        trending_books = []
        book_ids = [stat['book_id'] for stat in book_stats]
        books = {book.id: book for book in Book.objects.filter(id__in=book_ids)}
        
        for stat in book_stats:
            book = books.get(stat['book_id'])
            if book:
                trending_books.append({
                    'book_id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'score': float(stat['score']),
                    'interaction_count': stat['interaction_count'],
                    'avg_rating': stat.get('avg_rating', 0.0) or 0.0
                })
        
        return trending_books
    
    def _save_trending_books(self, trending_books: List[Dict[str, Any]], period: str, trend_type: str) -> int:
        """Sauvegarder les livres tendances"""
        updated_count = 0
        
        with transaction.atomic():
            # Marquer les anciennes entrées comme inactives
            TrendingBook.objects.filter(
                period=period,
                trend_type=trend_type,
                is_active=True
            ).update(is_active=False)
            
            # Créer ou mettre à jour les nouvelles entrées
            for rank, book_data in enumerate(trending_books, 1):
                try:
                    book = Book.objects.get(id=book_data['book_id'])
                    
                    trending_book, created = TrendingBook.objects.update_or_create(
                        book=book,
                        period=period,
                        trend_type=trend_type,
                        defaults={
                            'rank': rank,
                            'score': book_data['score'],
                            'interaction_count': book_data['interaction_count'],
                            'avg_rating': book_data['avg_rating'],
                            'is_active': True,
                            'last_updated': timezone.now()
                        }
                    )
                    
                    updated_count += 1
                    
                    if self.verbose:
                        action = "Créé" if created else "Mis à jour"
                        self._log(f"    {action}: {book.title} (rang {rank}, score {book_data['score']:.2f})")
                        
                except Book.DoesNotExist:
                    logger.warning(f"Livre introuvable: {book_data['book_id']}")
                    continue
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde du livre {book_data['book_id']}: {str(e)}")
                    continue
        
        return updated_count
    
    def _cleanup_old_trending(self):
        """Nettoyer les anciennes entrées de tendances"""
        self._log("Nettoyage des anciennes tendances...")
        
        # Supprimer les entrées inactives de plus de 7 jours
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count = TrendingBook.objects.filter(
            is_active=False,
            last_updated__lt=cutoff_date
        ).delete()[0]
        
        if deleted_count > 0:
            self._log(f"  ✓ {deleted_count} anciennes tendances supprimées")
        else:
            self._log("  Aucune ancienne tendance à supprimer")
    
    def _clear_cache(self):
        """Vider le cache"""
        self._log("Vidage du cache des tendances...")
        
        if self.dry_run:
            self._log("  [SIMULATION] Cache vidé")
            return
        
        try:
            # Vider les clés de cache spécifiques aux tendances
            cache_keys = [
                'trending_books_daily_views',
                'trending_books_daily_downloads',
                'trending_books_daily_ratings',
                'trending_books_daily_interactions',
                'trending_books_weekly_views',
                'trending_books_weekly_downloads',
                'trending_books_weekly_ratings',
                'trending_books_weekly_interactions',
                'trending_books_monthly_views',
                'trending_books_monthly_downloads',
                'trending_books_monthly_ratings',
                'trending_books_monthly_interactions',
            ]
            
            for key in cache_keys:
                cache.delete(key)
            
            self._log("  ✓ Cache des tendances vidé")
            
        except Exception as e:
            logger.error(f"Erreur lors du vidage du cache: {str(e)}")
            self._log_error(f"  ✗ Erreur lors du vidage du cache: {str(e)}")
    
    def _log(self, message: str):
        """Logger un message selon le niveau de verbosité"""
        if self.verbosity >= 1:
            self.stdout.write(message)
        
        logger.info(message)
    
    def _log_success(self, message: str):
        """Logger un message de succès"""
        if self.verbosity >= 1:
            self.stdout.write(self.style.SUCCESS(message))
        
        logger.info(message)
    
    def _log_warning(self, message: str):
        """Logger un message d'avertissement"""
        if self.verbosity >= 1:
            self.stdout.write(self.style.WARNING(message))
        
        logger.warning(message)
    
    def _log_error(self, message: str):
        """Logger un message d'erreur"""
        if self.verbosity >= 1:
            self.stdout.write(self.style.ERROR(message))
        
        logger.error(message)