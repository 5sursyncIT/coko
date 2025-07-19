from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver, Signal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging
import json

from catalog_service.models import Book, BookRating
from reading_service.models import ReadingSession, Bookmark
from .models import (
    UserProfile, BookVector, UserInteraction, RecommendationSet,
    Recommendation, SimilarityMatrix, TrendingBook, RecommendationFeedback
)
from .utils import (
    calculate_recommendation_stats, update_recommendation_metrics,
    clean_old_recommendation_data
)

User = get_user_model()
logger = logging.getLogger(__name__)

# Signaux personnalisés
recommendation_generated = Signal()
recommendation_clicked = Signal()
recommendation_converted = Signal()
user_preferences_updated = Signal()
similarity_matrix_updated = Signal()
trending_books_updated = Signal()


@receiver(post_save, sender=User)
def create_user_recommendation_profile(sender, instance, created, **kwargs):
    """Créer un profil de recommandations pour les nouveaux utilisateurs"""
    if created:
        try:
            # Créer le profil avec des valeurs par défaut
            UserProfile.objects.create(
                user=instance,
                preferred_genres=[],
                preferred_authors=[],
                preferred_languages=['fr'],
                reading_level='intermediate',
                reading_frequency='weekly',
                enable_recommendations=True,
                recommendation_frequency='daily'
            )
            
            logger.info(f"Profil de recommandations créé pour l'utilisateur {instance.username}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du profil de recommandations: {str(e)}")


@receiver(post_save, sender=UserProfile)
def invalidate_user_recommendations_cache(sender, instance, **kwargs):
    """Invalider le cache des recommandations quand le profil est mis à jour"""
    try:
        # Invalider tous les caches de recommandations pour cet utilisateur
        cache_patterns = [
            f"user_recommendations_{instance.user.id}_*",
            f"personalized_recommendations_{instance.user.id}_*",
            f"similar_users_{instance.user.id}"
        ]
        
        for pattern in cache_patterns:
            # Django cache ne supporte pas les wildcards, donc on utilise une approche différente
            cache_key = f"user_recommendations_{instance.user.id}"
            cache.delete(cache_key)
        
        # Émettre le signal de mise à jour des préférences
        user_preferences_updated.send(
            sender=UserProfile,
            user=instance.user,
            profile=instance
        )
        
        logger.info(f"Cache de recommandations invalidé pour l'utilisateur {instance.user.username}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'invalidation du cache: {str(e)}")


@receiver(post_save, sender=UserInteraction)
def process_user_interaction(sender, instance, created, **kwargs):
    """Traiter les nouvelles interactions utilisateur"""
    if created:
        try:
            # Invalider le cache des recommandations
            cache_key = f"user_recommendations_{instance.user.id}"
            cache.delete(cache_key)
            
            # Mettre à jour les métriques si l'interaction vient d'une recommandation
            if instance.from_recommendation and instance.recommendation_algorithm:
                update_recommendation_metrics(
                    user=instance.user,
                    book=instance.book,
                    interaction_type=instance.interaction_type,
                    algorithm=instance.recommendation_algorithm
                )
            
            # Mettre à jour le vecteur du livre si nécessaire
            try:
                book_vector, created_vector = BookVector.objects.get_or_create(
                    book=instance.book,
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
                
                if instance.interaction_type == 'view':
                    book_vector.view_count += 1
                elif instance.interaction_type == 'download':
                    book_vector.download_count += 1
                elif instance.interaction_type == 'rating' and instance.interaction_value:
                    # Recalculer la moyenne des notes
                    book_ratings = UserInteraction.objects.filter(
                        book=instance.book,
                        interaction_type='rating',
                        interaction_value__isnull=False
                    )
                    
                    if book_ratings.exists():
                        avg_rating = sum(r.interaction_value for r in book_ratings) / book_ratings.count()
                        book_vector.rating_average = avg_rating
                        book_vector.rating_count = book_ratings.count()
                
                book_vector.last_updated = timezone.now()
                book_vector.save()
                
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du vecteur du livre: {str(e)}")
            
            logger.info(
                f"Interaction {instance.interaction_type} traitée pour "
                f"l'utilisateur {instance.user.username} et le livre {instance.book.title}"
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'interaction: {str(e)}")


@receiver(post_save, sender=RecommendationSet)
def log_recommendation_generation(sender, instance, created, **kwargs):
    """Logger la génération d'ensembles de recommandations"""
    if created:
        try:
            logger.info(
                f"Ensemble de recommandations généré: {instance.algorithm_type} "
                f"pour l'utilisateur {instance.user.username} (contexte: {instance.context})"
            )
            
            # Émettre le signal de génération de recommandations
            recommendation_generated.send(
                sender=RecommendationSet,
                recommendation_set=instance,
                user=instance.user
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du logging de la génération: {str(e)}")


@receiver(post_save, sender=Recommendation)
def track_recommendation_interactions(sender, instance, **kwargs):
    """Suivre les interactions avec les recommandations"""
    try:
        # Vérifier si l'état a changé
        if instance.clicked and not kwargs.get('created', False):
            # La recommandation a été cliquée
            recommendation_clicked.send(
                sender=Recommendation,
                recommendation=instance,
                user=instance.recommendation_set.user
            )
            
            logger.info(
                f"Recommandation cliquée: {instance.book.title} "
                f"par {instance.recommendation_set.user.username}"
            )
        
        if instance.converted and not kwargs.get('created', False):
            # La recommandation a été convertie
            recommendation_converted.send(
                sender=Recommendation,
                recommendation=instance,
                user=instance.recommendation_set.user
            )
            
            logger.info(
                f"Recommandation convertie: {instance.book.title} "
                f"par {instance.recommendation_set.user.username}"
            )
        
    except Exception as e:
        logger.error(f"Erreur lors du suivi des interactions: {str(e)}")


@receiver(post_save, sender=RecommendationFeedback)
def process_recommendation_feedback(sender, instance, created, **kwargs):
    """Traiter les feedbacks de recommandations"""
    if created:
        try:
            logger.info(
                f"Feedback de recommandation reçu: {instance.feedback_type} "
                f"(note: {instance.rating}) de {instance.user.username}"
            )
            
            # Invalider le cache des recommandations pour améliorer les futures recommandations
            cache_key = f"user_recommendations_{instance.user.id}"
            cache.delete(cache_key)
            
            # Envoyer une notification par email si le feedback est très négatif
            if instance.rating and instance.rating <= 2:
                try:
                    send_mail(
                        subject='Feedback négatif sur les recommandations',
                        message=f'L\'utilisateur {instance.user.username} a donné une note de {instance.rating}/5 avec le commentaire: {instance.comment}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else [],
                        fail_silently=True
                    )
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi de l'email de feedback: {str(e)}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du feedback: {str(e)}")


@receiver(post_save, sender=BookRating)
def update_book_vector_on_rating(sender, instance, **kwargs):
    """Mettre à jour le vecteur du livre quand une note est ajoutée"""
    try:
        book_vector, created = BookVector.objects.get_or_create(
            book=instance.book,
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
        
        # Recalculer les métriques de qualité
        ratings = BookRating.objects.filter(book=instance.book)
        if ratings.exists():
            avg_rating = sum(r.rating for r in ratings) / ratings.count()
            book_vector.rating_average = avg_rating
            book_vector.rating_count = ratings.count()
            book_vector.quality_score = min(avg_rating / 5.0, 1.0)
        
        book_vector.last_updated = timezone.now()
        book_vector.save()
        
        logger.info(f"Vecteur du livre {instance.book.title} mis à jour suite à une nouvelle note")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du vecteur: {str(e)}")


@receiver(post_save, sender=ReadingSession)
def update_recommendations_on_reading(sender, instance, **kwargs):
    """Mettre à jour les recommandations basées sur les sessions de lecture"""
    try:
        # Créer une interaction utilisateur pour la session de lecture
        if instance.status == 'completed':
            UserInteraction.objects.get_or_create(
                user=instance.user,
                book=instance.book,
                interaction_type='read',
                defaults={
                    'interaction_value': 100,  # 100% lu
                    'session_id': str(instance.id),
                    'device_type': instance.device_info.get('type', 'unknown') if instance.device_info else 'unknown'
                }
            )
            
            # Invalider le cache des recommandations
            cache_key = f"user_recommendations_{instance.user.id}"
            cache.delete(cache_key)
            
            logger.info(
                f"Recommandations mises à jour suite à la lecture complète de "
                f"{instance.book.title} par {instance.user.username}"
            )
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des recommandations: {str(e)}")


@receiver(post_save, sender=Bookmark)
def update_recommendations_on_bookmark(sender, instance, created, **kwargs):
    """Mettre à jour les recommandations basées sur les marque-pages"""
    if created:
        try:
            # Créer une interaction utilisateur pour le marque-page
            UserInteraction.objects.get_or_create(
                user=instance.user,
                book=instance.book,
                interaction_type='bookmark',
                defaults={
                    'interaction_value': 1,
                    'interaction_metadata': {
                        'bookmark_type': instance.bookmark_type,
                        'content': instance.content[:100] if instance.content else None
                    }
                }
            )
            
            # Invalider le cache des recommandations
            cache_key = f"user_recommendations_{instance.user.id}"
            cache.delete(cache_key)
            
            logger.info(
                f"Recommandations mises à jour suite à l'ajout d'un marque-page "
                f"sur {instance.book.title} par {instance.user.username}"
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des recommandations: {str(e)}")


@receiver(post_delete, sender=RecommendationSet)
def log_recommendation_deletion(sender, instance, **kwargs):
    """Logger la suppression d'ensembles de recommandations"""
    try:
        logger.info(
            f"Ensemble de recommandations supprimé: {instance.algorithm_type} "
            f"de l'utilisateur {instance.user.username}"
        )
    except Exception as e:
        logger.error(f"Erreur lors du logging de la suppression: {str(e)}")


@receiver(similarity_matrix_updated)
def invalidate_similarity_cache(sender, **kwargs):
    """Invalider le cache de similarité quand la matrice est mise à jour"""
    try:
        # Invalider tous les caches liés à la similarité
        cache_patterns = [
            'similar_books_*',
            'content_based_recommendations_*',
            'collaborative_recommendations_*'
        ]
        
        # Note: Django cache ne supporte pas les wildcards nativement
        # Dans un environnement de production, vous pourriez utiliser Redis avec des patterns
        
        logger.info("Cache de similarité invalidé")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'invalidation du cache de similarité: {str(e)}")


@receiver(trending_books_updated)
def update_trending_recommendations(sender, **kwargs):
    """Mettre à jour les recommandations basées sur les tendances"""
    try:
        # Invalider le cache des recommandations de popularité
        cache.delete('popularity_recommendations')
        cache.delete('trending_books')
        
        logger.info("Recommandations de tendances mises à jour")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des tendances: {str(e)}")


# Signaux pour les tâches de maintenance
@receiver(user_preferences_updated)
def schedule_preference_analysis(sender, user, profile, **kwargs):
    """Programmer une analyse des préférences utilisateur"""
    try:
        # Dans un environnement de production, vous pourriez utiliser Celery
        # pour programmer des tâches asynchrones
        
        logger.info(f"Analyse des préférences programmée pour {user.username}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la programmation de l'analyse: {str(e)}")


@receiver(recommendation_generated)
def track_recommendation_metrics(sender, recommendation_set, user, **kwargs):
    """Suivre les métriques de génération de recommandations"""
    try:
        # Incrémenter les compteurs de métriques
        cache_key = f"recommendation_metrics_{timezone.now().date()}"
        current_metrics = cache.get(cache_key, {'generated': 0, 'users': set()})
        
        current_metrics['generated'] += 1
        current_metrics['users'].add(user.id)
        
        cache.set(cache_key, current_metrics, 86400)  # 24 heures
        
        logger.info(f"Métriques de recommandations mises à jour")
        
    except Exception as e:
        logger.error(f"Erreur lors du suivi des métriques: {str(e)}")


def cleanup_old_recommendation_data():
    """Fonction utilitaire pour nettoyer les anciennes données"""
    try:
        result = clean_old_recommendation_data(days_to_keep=90)
        logger.info(f"Nettoyage terminé: {result}")
        return result
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {str(e)}")
        return None


def update_trending_books_data():
    """Fonction utilitaire pour mettre à jour les données de tendances"""
    try:
        from .utils import get_trending_books
        
        # Mettre à jour les livres en tendance pour différentes périodes
        periods = ['day', 'week', 'month']
        trend_types = ['overall', 'genre', 'new_releases']
        
        for period in periods:
            for trend_type in trend_types:
                trending_books = get_trending_books(
                    period=period,
                    trend_type=trend_type,
                    limit=50
                )
                
                # Mettre à jour ou créer les entrées TrendingBook
                # (Logique à implémenter selon vos besoins)
        
        # Émettre le signal de mise à jour
        trending_books_updated.send(sender=None)
        
        logger.info("Données de tendances mises à jour")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des tendances: {str(e)}")


def recalculate_similarity_matrix():
    """Fonction utilitaire pour recalculer la matrice de similarité"""
    try:
        # Cette fonction serait appelée périodiquement (par exemple, via une tâche cron)
        # pour recalculer les similarités entre les livres
        
        logger.info("Recalcul de la matrice de similarité démarré")
        
        # Logique de recalcul à implémenter
        # ...
        
        # Émettre le signal de mise à jour
        similarity_matrix_updated.send(sender=None)
        
        logger.info("Matrice de similarité recalculée")
        
    except Exception as e:
        logger.error(f"Erreur lors du recalcul de la matrice: {str(e)}")