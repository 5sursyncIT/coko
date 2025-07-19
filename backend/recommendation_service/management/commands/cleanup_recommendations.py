from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
import logging
from datetime import timedelta

from recommendation_service.models import (
    RecommendationSet, Recommendation, UserInteraction, 
    RecommendationFeedback, SimilarityMatrix, TrendingBook
)
from recommendation_service.utils import clean_old_recommendation_data

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Nettoyer les anciennes données de recommandations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Nombre de jours de données à conserver (défaut: 90)'
        )
        
        parser.add_argument(
            '--recommendations',
            action='store_true',
            help='Nettoyer les anciens ensembles de recommandations'
        )
        
        parser.add_argument(
            '--interactions',
            action='store_true',
            help='Nettoyer les anciennes interactions utilisateur'
        )
        
        parser.add_argument(
            '--feedback',
            action='store_true',
            help='Nettoyer les anciens feedbacks'
        )
        
        parser.add_argument(
            '--similarity',
            action='store_true',
            help='Nettoyer les anciennes données de similarité'
        )
        
        parser.add_argument(
            '--trending',
            action='store_true',
            help='Nettoyer les anciennes données de tendances'
        )
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Nettoyer tous les types de données'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Taille des lots pour la suppression (défaut: 1000)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans réellement supprimer les données'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé des opérations'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la suppression sans confirmation'
        )
        
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Vider le cache après le nettoyage'
        )
    
    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        self.dry_run = options.get('dry_run', False)
        self.batch_size = options['batch_size']
        
        try:
            # Calculer la date seuil
            cutoff_date = timezone.now() - timedelta(days=options['days'])
            self._log(f"Nettoyage des données antérieures au {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if self.dry_run:
                self._log("[MODE SIMULATION] Aucune donnée ne sera réellement supprimée")
            
            # Demander confirmation si pas en mode force
            if not options['force'] and not self.dry_run:
                confirm = input("Êtes-vous sûr de vouloir supprimer ces données ? (oui/non): ")
                if confirm.lower() not in ['oui', 'yes', 'y', 'o']:
                    self._log("Opération annulée")
                    return
            
            total_deleted = 0
            
            # Déterminer quoi nettoyer
            if options['all']:
                cleanup_options = {
                    'recommendations': True,
                    'interactions': True,
                    'feedback': True,
                    'similarity': True,
                    'trending': True
                }
            else:
                cleanup_options = {
                    'recommendations': options['recommendations'],
                    'interactions': options['interactions'],
                    'feedback': options['feedback'],
                    'similarity': options['similarity'],
                    'trending': options['trending']
                }
            
            # Effectuer le nettoyage
            if cleanup_options['recommendations']:
                deleted = self._cleanup_recommendations(cutoff_date)
                total_deleted += deleted
            
            if cleanup_options['interactions']:
                deleted = self._cleanup_interactions(cutoff_date)
                total_deleted += deleted
            
            if cleanup_options['feedback']:
                deleted = self._cleanup_feedback(cutoff_date)
                total_deleted += deleted
            
            if cleanup_options['similarity']:
                deleted = self._cleanup_similarity(cutoff_date)
                total_deleted += deleted
            
            if cleanup_options['trending']:
                deleted = self._cleanup_trending(cutoff_date)
                total_deleted += deleted
            
            # Vider le cache si demandé
            if options['clear_cache']:
                self._clear_cache()
            
            if self.dry_run:
                self._log_success(f"[SIMULATION] {total_deleted} enregistrements seraient supprimés")
            else:
                self._log_success(f"Nettoyage terminé: {total_deleted} enregistrements supprimés")
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {str(e)}")
            raise CommandError(f"Erreur: {str(e)}")
    
    def _cleanup_recommendations(self, cutoff_date) -> int:
        """Nettoyer les anciens ensembles de recommandations"""
        self._log("Nettoyage des ensembles de recommandations...")
        
        # Compter d'abord
        old_sets = RecommendationSet.objects.filter(created_at__lt=cutoff_date)
        count = old_sets.count()
        
        if count == 0:
            self._log("  Aucun ensemble de recommandations à supprimer")
            return 0
        
        self._log(f"  {count} ensembles de recommandations à supprimer")
        
        if self.dry_run:
            return count
        
        # Supprimer par lots
        deleted_total = 0
        while True:
            with transaction.atomic():
                batch_ids = list(
                    RecommendationSet.objects.filter(
                        created_at__lt=cutoff_date
                    ).values_list('id', flat=True)[:self.batch_size]
                )
                
                if not batch_ids:
                    break
                
                # Supprimer d'abord les recommandations individuelles
                Recommendation.objects.filter(
                    recommendation_set_id__in=batch_ids
                ).delete()
                
                # Puis les ensembles
                deleted_count = RecommendationSet.objects.filter(
                    id__in=batch_ids
                ).delete()[0]
                
                deleted_total += deleted_count
                
                if self.verbose:
                    self._log(f"    {deleted_total}/{count} ensembles supprimés...")
        
        self._log(f"  ✓ {deleted_total} ensembles de recommandations supprimés")
        return deleted_total
    
    def _cleanup_interactions(self, cutoff_date) -> int:
        """Nettoyer les anciennes interactions utilisateur"""
        self._log("Nettoyage des interactions utilisateur...")
        
        # Garder les interactions importantes (ratings, bookmarks) plus longtemps
        important_types = ['rating', 'bookmark', 'purchase']
        
        # Interactions normales (plus anciennes que cutoff_date)
        normal_interactions = UserInteraction.objects.filter(
            created_at__lt=cutoff_date
        ).exclude(interaction_type__in=important_types)
        
        # Interactions importantes (plus anciennes que cutoff_date * 2)
        important_cutoff = cutoff_date - timedelta(days=90)  # Garder 90 jours de plus
        important_interactions = UserInteraction.objects.filter(
            created_at__lt=important_cutoff,
            interaction_type__in=important_types
        )
        
        normal_count = normal_interactions.count()
        important_count = important_interactions.count()
        total_count = normal_count + important_count
        
        if total_count == 0:
            self._log("  Aucune interaction à supprimer")
            return 0
        
        self._log(f"  {normal_count} interactions normales + {important_count} interactions importantes à supprimer")
        
        if self.dry_run:
            return total_count
        
        deleted_total = 0
        
        # Supprimer les interactions normales
        deleted_total += self._delete_in_batches(
            normal_interactions, "interactions normales"
        )
        
        # Supprimer les interactions importantes anciennes
        deleted_total += self._delete_in_batches(
            important_interactions, "interactions importantes"
        )
        
        self._log(f"  ✓ {deleted_total} interactions supprimées")
        return deleted_total
    
    def _cleanup_feedback(self, cutoff_date) -> int:
        """Nettoyer les anciens feedbacks"""
        self._log("Nettoyage des feedbacks...")
        
        old_feedback = RecommendationFeedback.objects.filter(created_at__lt=cutoff_date)
        count = old_feedback.count()
        
        if count == 0:
            self._log("  Aucun feedback à supprimer")
            return 0
        
        self._log(f"  {count} feedbacks à supprimer")
        
        if self.dry_run:
            return count
        
        deleted_total = self._delete_in_batches(old_feedback, "feedbacks")
        
        self._log(f"  ✓ {deleted_total} feedbacks supprimés")
        return deleted_total
    
    def _cleanup_similarity(self, cutoff_date) -> int:
        """Nettoyer les anciennes données de similarité"""
        self._log("Nettoyage des données de similarité...")
        
        old_similarities = SimilarityMatrix.objects.filter(
            last_calculated__lt=cutoff_date
        )
        count = old_similarities.count()
        
        if count == 0:
            self._log("  Aucune donnée de similarité à supprimer")
            return 0
        
        self._log(f"  {count} données de similarité à supprimer")
        
        if self.dry_run:
            return count
        
        deleted_total = self._delete_in_batches(old_similarities, "données de similarité")
        
        self._log(f"  ✓ {deleted_total} données de similarité supprimées")
        return deleted_total
    
    def _cleanup_trending(self, cutoff_date) -> int:
        """Nettoyer les anciennes données de tendances"""
        self._log("Nettoyage des données de tendances...")
        
        # Supprimer les tendances inactives et anciennes
        old_trending = TrendingBook.objects.filter(
            models.Q(last_updated__lt=cutoff_date) |
            models.Q(is_active=False, last_updated__lt=timezone.now() - timedelta(days=30))
        )
        count = old_trending.count()
        
        if count == 0:
            self._log("  Aucune donnée de tendance à supprimer")
            return 0
        
        self._log(f"  {count} données de tendance à supprimer")
        
        if self.dry_run:
            return count
        
        deleted_total = self._delete_in_batches(old_trending, "données de tendance")
        
        self._log(f"  ✓ {deleted_total} données de tendance supprimées")
        return deleted_total
    
    def _delete_in_batches(self, queryset, description: str) -> int:
        """Supprimer un queryset par lots"""
        total_count = queryset.count()
        deleted_total = 0
        
        while True:
            with transaction.atomic():
                batch_ids = list(
                    queryset.values_list('id', flat=True)[:self.batch_size]
                )
                
                if not batch_ids:
                    break
                
                deleted_count = queryset.filter(id__in=batch_ids).delete()[0]
                deleted_total += deleted_count
                
                if self.verbose:
                    self._log(f"    {deleted_total}/{total_count} {description} supprimées...")
        
        return deleted_total
    
    def _clear_cache(self):
        """Vider le cache"""
        self._log("Vidage du cache...")
        
        if self.dry_run:
            self._log("  [SIMULATION] Cache vidé")
            return
        
        try:
            cache.clear()
            self._log("  ✓ Cache vidé")
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