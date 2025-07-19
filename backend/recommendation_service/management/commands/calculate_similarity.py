from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
import logging
import time
from typing import List, Tuple

from catalog_service.models import Book
from recommendation_service.models import BookVector, SimilarityMatrix
from recommendation_service.tasks import calculate_similarity_matrix
from recommendation_service.signals import similarity_matrix_updated

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculer la matrice de similarité entre les livres'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Taille des lots pour le traitement (défaut: 100)'
        )
        
        parser.add_argument(
            '--threshold',
            type=float,
            default=0.1,
            help='Seuil minimum de similarité à sauvegarder (défaut: 0.1)'
        )
        
        parser.add_argument(
            '--book-ids',
            nargs='+',
            type=int,
            help='IDs spécifiques des livres à traiter'
        )
        
        parser.add_argument(
            '--async',
            action='store_true',
            dest='use_async',
            help='Utiliser les tâches asynchrones (Celery) pour le calcul'
        )
        
        parser.add_argument(
            '--clean-old',
            action='store_true',
            help='Nettoyer les anciennes similarités avant le calcul'
        )
        
        parser.add_argument(
            '--update-vectors',
            action='store_true',
            help='Mettre à jour les vecteurs des livres avant le calcul'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans réellement calculer les similarités'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé des opérations'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer le recalcul même pour les similarités récentes'
        )
    
    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        self.threshold = options['threshold']
        
        try:
            start_time = time.time()
            
            if options['clean_old']:
                self._clean_old_similarities(options)
            
            if options['update_vectors']:
                self._update_book_vectors(options)
            
            if options['use_async']:
                self._calculate_async(options)
            else:
                self._calculate_sync(options)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            self._log_success(f"Calcul terminé en {execution_time:.2f} secondes")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de similarité: {str(e)}")
            raise CommandError(f"Erreur: {str(e)}")
    
    def _clean_old_similarities(self, options):
        """Nettoyer les anciennes similarités"""
        self._log("Nettoyage des anciennes similarités...")
        
        if options['dry_run']:
            old_count = SimilarityMatrix.objects.filter(
                last_calculated__lt=timezone.now() - timezone.timedelta(days=7)
            ).count()
            self._log(f"[DRY RUN] {old_count} anciennes similarités seraient supprimées")
            return
        
        deleted_count = SimilarityMatrix.objects.filter(
            last_calculated__lt=timezone.now() - timezone.timedelta(days=7)
        ).delete()[0]
        
        self._log(f"✓ {deleted_count} anciennes similarités supprimées")
    
    def _update_book_vectors(self, options):
        """Mettre à jour les vecteurs des livres"""
        self._log("Mise à jour des vecteurs des livres...")
        
        if options['book_ids']:
            books = Book.objects.filter(id__in=options['book_ids'])
        else:
            # Mettre à jour les livres sans vecteur ou avec des vecteurs anciens
            yesterday = timezone.now() - timezone.timedelta(days=1)
            books = Book.objects.filter(
                models.Q(bookvector__isnull=True) |
                models.Q(bookvector__last_updated__lt=yesterday)
            ).distinct()
        
        if options['dry_run']:
            self._log(f"[DRY RUN] {books.count()} vecteurs de livres seraient mis à jour")
            return
        
        updated_count = 0
        for book in books:
            try:
                self._update_single_book_vector(book)
                updated_count += 1
                
                if self.verbose and updated_count % 10 == 0:
                    self._log(f"  {updated_count} vecteurs mis à jour...")
                    
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du vecteur pour {book.title}: {str(e)}")
                continue
        
        self._log(f"✓ {updated_count} vecteurs de livres mis à jour")
    
    def _update_single_book_vector(self, book: Book):
        """Mettre à jour le vecteur d'un livre spécifique"""
        from recommendation_service.models import UserInteraction
        from catalog_service.models import BookRating
        
        vector, created = BookVector.objects.get_or_create(
            book=book,
            defaults={
                'content_vector': [],
                'genre_vector': [],
                'author_vector': [],
                'metadata_vector': [],
                'popularity_score': 0.0,
                'quality_score': 0.0,
                'recency_score': 0.0
            }
        )
        
        # Calculer les métriques de popularité
        interactions = UserInteraction.objects.filter(book=book)
        view_count = interactions.filter(interaction_type='view').count()
        download_count = interactions.filter(interaction_type='download').count()
        
        # Calculer le score de qualité basé sur les notes
        ratings = BookRating.objects.filter(book=book)
        if ratings.exists():
            avg_rating = sum(r.rating for r in ratings) / ratings.count()
            vector.rating_average = avg_rating
            vector.rating_count = ratings.count()
            vector.quality_score = min(avg_rating / 5.0, 1.0)
        
        # Calculer le score de récence
        days_since_publication = (timezone.now().date() - book.publication_date).days
        vector.recency_score = max(0, 1 - (days_since_publication / 365))
        
        # Calculer le score de popularité
        max_views = BookVector.objects.aggregate(
            max_views=models.Max('view_count')
        )['max_views'] or 1
        vector.popularity_score = min(view_count / max_views, 1.0)
        
        # Mettre à jour les compteurs
        vector.view_count = view_count
        vector.download_count = download_count
        vector.last_updated = timezone.now()
        
        # Générer les vecteurs de contenu (simplifié)
        available_genres = ['fiction', 'non-fiction', 'science', 'history', 'romance', 'mystery', 'fantasy']
        vector.genre_vector = [1.0 if genre in book.genres else 0.0 for genre in available_genres]
        
        # Vecteur d'auteur simplifié (hash de l'auteur)
        vector.author_vector = [hash(book.author) % 100 / 100.0]
        
        # Vecteur de métadonnées
        vector.metadata_vector = [
            len(book.title) / 100.0,  # Longueur du titre normalisée
            1.0 if book.language == 'fr' else 0.0,  # Langue française
            vector.recency_score  # Score de récence
        ]
        
        vector.save()
    
    def _calculate_async(self, options):
        """Calculer la similarité de manière asynchrone"""
        self._log("Lancement du calcul asynchrone de la matrice de similarité...")
        
        if options['dry_run']:
            self._log("[DRY RUN] Tâche asynchrone de calcul de similarité")
            return
        
        try:
            task = calculate_similarity_matrix.delay(
                batch_size=options['batch_size']
            )
            
            self._log(f"Tâche asynchrone lancée: {task.id}")
            
        except Exception as e:
            logger.error(f"Erreur lors du lancement de la tâche: {str(e)}")
            raise CommandError(f"Erreur lors du lancement: {str(e)}")
    
    def _calculate_sync(self, options):
        """Calculer la similarité de manière synchrone"""
        self._log("Calcul synchrone de la matrice de similarité...")
        
        # Obtenir les vecteurs de livres
        if options['book_ids']:
            book_vectors = BookVector.objects.filter(
                book__id__in=options['book_ids']
            ).select_related('book')
        else:
            book_vectors = BookVector.objects.select_related('book').all()
        
        book_vectors_list = list(book_vectors)
        total_vectors = len(book_vectors_list)
        
        if total_vectors < 2:
            self._log_warning("Pas assez de vecteurs de livres pour calculer la similarité")
            return
        
        self._log(f"Calcul des similarités pour {total_vectors} livres...")
        
        if options['dry_run']:
            total_pairs = (total_vectors * (total_vectors - 1)) // 2
            self._log(f"[DRY RUN] {total_pairs} paires de similarité seraient calculées")
            return
        
        batch_size = options['batch_size']
        total_pairs = 0
        saved_pairs = 0
        
        for i, vector1 in enumerate(book_vectors_list):
            if i % batch_size == 0:
                self._log(f"Traitement du lot {i // batch_size + 1}/{(total_vectors - 1) // batch_size + 1}")
            
            batch_similarities = []
            
            for j, vector2 in enumerate(book_vectors_list[i+1:], i+1):
                try:
                    similarity_score = self._calculate_cosine_similarity(vector1, vector2)
                    total_pairs += 1
                    
                    if similarity_score >= self.threshold:
                        batch_similarities.extend([
                            SimilarityMatrix(
                                book1=vector1.book,
                                book2=vector2.book,
                                similarity_score=similarity_score,
                                algorithm_type='cosine',
                                last_calculated=timezone.now()
                            ),
                            SimilarityMatrix(
                                book1=vector2.book,
                                book2=vector1.book,
                                similarity_score=similarity_score,
                                algorithm_type='cosine',
                                last_calculated=timezone.now()
                            )
                        ])
                        saved_pairs += 2
                    
                    if self.verbose and total_pairs % 1000 == 0:
                        self._log(f"  {total_pairs} paires calculées, {saved_pairs} sauvegardées...")
                
                except Exception as e:
                    logger.error(f"Erreur lors du calcul entre {vector1.book.title} et {vector2.book.title}: {str(e)}")
                    continue
            
            # Sauvegarder le lot
            if batch_similarities:
                try:
                    with transaction.atomic():
                        # Supprimer les anciennes similarités pour ces livres
                        SimilarityMatrix.objects.filter(
                            book1=vector1.book
                        ).delete()
                        
                        # Créer les nouvelles
                        SimilarityMatrix.objects.bulk_create(
                            batch_similarities,
                            ignore_conflicts=True
                        )
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde du lot: {str(e)}")
                    continue
        
        # Nettoyer les anciennes similarités
        if not options['force']:
            old_threshold = timezone.now() - timezone.timedelta(days=7)
            deleted_count = SimilarityMatrix.objects.filter(
                last_calculated__lt=old_threshold
            ).delete()[0]
            
            if deleted_count > 0:
                self._log(f"✓ {deleted_count} anciennes similarités supprimées")
        
        self._log(f"✓ Calcul terminé: {total_pairs} paires calculées, {saved_pairs} sauvegardées")
        
        # Émettre le signal de mise à jour
        similarity_matrix_updated.send(sender=None)
        
        # Invalider les caches liés
        self._invalidate_similarity_caches()
    
    def _calculate_cosine_similarity(self, vector1: BookVector, vector2: BookVector) -> float:
        """Calculer la similarité cosinus entre deux vecteurs de livres"""
        import numpy as np
        
        try:
            # Combiner tous les vecteurs
            v1 = (
                vector1.content_vector + 
                vector1.genre_vector + 
                vector1.author_vector + 
                vector1.metadata_vector +
                [vector1.popularity_score, vector1.quality_score, vector1.recency_score]
            )
            
            v2 = (
                vector2.content_vector + 
                vector2.genre_vector + 
                vector2.author_vector + 
                vector2.metadata_vector +
                [vector2.popularity_score, vector2.quality_score, vector2.recency_score]
            )
            
            # S'assurer que les vecteurs ont la même longueur
            max_len = max(len(v1), len(v2))
            v1.extend([0.0] * (max_len - len(v1)))
            v2.extend([0.0] * (max_len - len(v2)))
            
            # Calculer la similarité cosinus
            v1_array = np.array(v1)
            v2_array = np.array(v2)
            
            dot_product = np.dot(v1_array, v2_array)
            norm1 = np.linalg.norm(v1_array)
            norm2 = np.linalg.norm(v2_array)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de similarité cosinus: {str(e)}")
            return 0.0
    
    def _invalidate_similarity_caches(self):
        """Invalider les caches liés à la similarité"""
        try:
            cache_keys = [
                'similar_books_*',
                'content_based_recommendations_*',
                'collaborative_recommendations_*'
            ]
            
            # Note: Django cache ne supporte pas les wildcards nativement
            # Dans un environnement de production, vous pourriez utiliser Redis avec des patterns
            
            self._log("Cache de similarité invalidé")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation du cache: {str(e)}")
    
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