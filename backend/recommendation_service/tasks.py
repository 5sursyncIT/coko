from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta, datetime
import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional

from catalog_service.models import Book, BookRating
from .models import (
    UserProfile, BookVector, UserInteraction, RecommendationSet,
    Recommendation, SimilarityMatrix, TrendingBook, RecommendationFeedback
)
from .utils import (
    generate_personalized_recommendations, calculate_recommendation_stats,
    get_trending_books, clean_old_recommendation_data, get_recommendation_analytics
)
from .signals import (
    similarity_matrix_updated, trending_books_updated, recommendation_generated
)

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_user_recommendations(self, user_id: int, algorithm: str = 'hybrid', 
                                count: int = 10, context: str = 'general'):
    """
    Générer des recommandations personnalisées pour un utilisateur
    """
    try:
        user = User.objects.get(id=user_id)
        
        logger.info(f"Génération de recommandations pour l'utilisateur {user.username}")
        
        # Générer les recommandations
        recommendations = generate_personalized_recommendations(
            user=user,
            algorithm=algorithm,
            count=count,
            context=context
        )
        
        if recommendations:
            logger.info(
                f"Recommandations générées avec succès pour {user.username}: "
                f"{len(recommendations)} livres"
            )
            return {
                'success': True,
                'user_id': user_id,
                'count': len(recommendations),
                'algorithm': algorithm
            }
        else:
            logger.warning(f"Aucune recommandation générée pour {user.username}")
            return {
                'success': False,
                'user_id': user_id,
                'error': 'No recommendations generated'
            }
            
    except User.DoesNotExist:
        logger.error(f"Utilisateur {user_id} non trouvé")
        return {'success': False, 'error': 'User not found'}
        
    except Exception as exc:
        logger.error(f"Erreur lors de la génération de recommandations: {str(exc)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Tentative {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(exc)}


@shared_task
def batch_generate_recommendations(user_ids: List[int], algorithm: str = 'hybrid'):
    """
    Générer des recommandations pour plusieurs utilisateurs en lot
    """
    results = []
    
    for user_id in user_ids:
        try:
            result = generate_user_recommendations.delay(user_id, algorithm)
            results.append({
                'user_id': user_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            logger.error(f"Erreur lors de la mise en file d'attente pour l'utilisateur {user_id}: {str(e)}")
            results.append({
                'user_id': user_id,
                'status': 'error',
                'error': str(e)
            })
    
    logger.info(f"Génération en lot lancée pour {len(user_ids)} utilisateurs")
    return results


@shared_task(bind=True, max_retries=2)
def update_book_vectors(self, book_ids: Optional[List[int]] = None):
    """
    Mettre à jour les vecteurs des livres
    """
    try:
        if book_ids:
            books = Book.objects.filter(id__in=book_ids)
        else:
            # Mettre à jour tous les livres modifiés dans les dernières 24h
            yesterday = timezone.now() - timedelta(days=1)
            books = Book.objects.filter(updated_at__gte=yesterday)
        
        updated_count = 0
        
        for book in books:
            try:
                # Obtenir ou créer le vecteur du livre
                book_vector, created = BookVector.objects.get_or_create(
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
                
                # Calculer les scores de popularité
                interactions = UserInteraction.objects.filter(book=book)
                view_count = interactions.filter(interaction_type='view').count()
                download_count = interactions.filter(interaction_type='download').count()
                
                # Calculer le score de qualité basé sur les notes
                ratings = BookRating.objects.filter(book=book)
                if ratings.exists():
                    avg_rating = sum(r.rating for r in ratings) / ratings.count()
                    book_vector.rating_average = avg_rating
                    book_vector.rating_count = ratings.count()
                    book_vector.quality_score = min(avg_rating / 5.0, 1.0)
                
                # Calculer le score de récence
                days_since_publication = (timezone.now().date() - book.publication_date).days
                book_vector.recency_score = max(0, 1 - (days_since_publication / 365))
                
                # Calculer le score de popularité
                max_views = max(BookVector.objects.aggregate(
                    max_views=models.Max('view_count')
                )['max_views'] or 1, 1)
                book_vector.popularity_score = min(view_count / max_views, 1.0)
                
                # Mettre à jour les compteurs
                book_vector.view_count = view_count
                book_vector.download_count = download_count
                book_vector.last_updated = timezone.now()
                
                # Générer les vecteurs de contenu (simplifié)
                # Dans un vrai système, vous utiliseriez des embeddings plus sophistiqués
                book_vector.genre_vector = [1.0 if genre in book.genres else 0.0 
                                          for genre in ['fiction', 'non-fiction', 'science', 'history', 'romance']]
                book_vector.author_vector = [hash(book.author) % 100 / 100.0]  # Simplifié
                
                book_vector.save()
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du vecteur pour le livre {book.id}: {str(e)}")
                continue
        
        logger.info(f"Vecteurs mis à jour pour {updated_count} livres")
        return {'success': True, 'updated_count': updated_count}
        
    except Exception as exc:
        logger.error(f"Erreur lors de la mise à jour des vecteurs: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300)  # Retry après 5 minutes
        
        return {'success': False, 'error': str(exc)}


@shared_task(bind=True, max_retries=2)
def calculate_similarity_matrix(self, batch_size: int = 100):
    """
    Calculer la matrice de similarité entre les livres
    """
    try:
        logger.info("Début du calcul de la matrice de similarité")
        
        # Obtenir tous les vecteurs de livres
        book_vectors = BookVector.objects.select_related('book').all()
        
        if book_vectors.count() < 2:
            logger.warning("Pas assez de vecteurs de livres pour calculer la similarité")
            return {'success': False, 'error': 'Not enough book vectors'}
        
        # Traiter par lots pour éviter les problèmes de mémoire
        total_pairs = 0
        
        for i, vector1 in enumerate(book_vectors):
            if i % batch_size == 0:
                logger.info(f"Traitement du lot {i // batch_size + 1}")
            
            for j, vector2 in enumerate(book_vectors[i+1:], i+1):
                try:
                    # Calculer la similarité cosinus
                    similarity_score = calculate_cosine_similarity_vectors(
                        vector1, vector2
                    )
                    
                    if similarity_score > 0.1:  # Seuil minimum de similarité
                        # Sauvegarder la similarité
                        SimilarityMatrix.objects.update_or_create(
                            book1=vector1.book,
                            book2=vector2.book,
                            defaults={
                                'similarity_score': similarity_score,
                                'algorithm_type': 'cosine',
                                'last_calculated': timezone.now()
                            }
                        )
                        
                        # Sauvegarder aussi la relation inverse
                        SimilarityMatrix.objects.update_or_create(
                            book1=vector2.book,
                            book2=vector1.book,
                            defaults={
                                'similarity_score': similarity_score,
                                'algorithm_type': 'cosine',
                                'last_calculated': timezone.now()
                            }
                        )
                        
                        total_pairs += 1
                
                except Exception as e:
                    logger.error(f"Erreur lors du calcul de similarité entre {vector1.book.id} et {vector2.book.id}: {str(e)}")
                    continue
        
        # Nettoyer les anciennes similarités
        old_threshold = timezone.now() - timedelta(days=7)
        deleted_count = SimilarityMatrix.objects.filter(
            last_calculated__lt=old_threshold
        ).delete()[0]
        
        logger.info(f"Matrice de similarité calculée: {total_pairs} paires, {deleted_count} anciennes supprimées")
        
        # Émettre le signal de mise à jour
        similarity_matrix_updated.send(sender=None)
        
        return {
            'success': True,
            'total_pairs': total_pairs,
            'deleted_old': deleted_count
        }
        
    except Exception as exc:
        logger.error(f"Erreur lors du calcul de la matrice de similarité: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=600)  # Retry après 10 minutes
        
        return {'success': False, 'error': str(exc)}


def calculate_cosine_similarity_vectors(vector1: BookVector, vector2: BookVector) -> float:
    """
    Calculer la similarité cosinus entre deux vecteurs de livres
    """
    try:
        # Combiner tous les vecteurs
        v1 = (
            vector1.content_vector + 
            vector1.genre_vector + 
            vector1.author_vector + 
            [vector1.popularity_score, vector1.quality_score, vector1.recency_score]
        )
        
        v2 = (
            vector2.content_vector + 
            vector2.genre_vector + 
            vector2.author_vector + 
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


@shared_task
def update_trending_books():
    """
    Mettre à jour les livres en tendance
    """
    try:
        logger.info("Mise à jour des livres en tendance")
        
        periods = ['day', 'week', 'month']
        trend_types = ['overall', 'genre', 'new_releases']
        
        for period in periods:
            for trend_type in trend_types:
                try:
                    trending_books = get_trending_books(
                        period=period,
                        trend_type=trend_type,
                        limit=50
                    )
                    
                    # Marquer tous les anciens comme inactifs pour cette catégorie
                    TrendingBook.objects.filter(
                        period=period,
                        trend_type=trend_type
                    ).update(is_active=False)
                    
                    # Créer ou mettre à jour les nouveaux
                    for rank, book_data in enumerate(trending_books, 1):
                        TrendingBook.objects.update_or_create(
                            book_id=book_data['book_id'],
                            period=period,
                            trend_type=trend_type,
                            defaults={
                                'rank': rank,
                                'score': book_data.get('score', 0.0),
                                'is_active': True,
                                'last_updated': timezone.now()
                            }
                        )
                    
                    logger.info(f"Tendances mises à jour: {period}/{trend_type} - {len(trending_books)} livres")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la mise à jour des tendances {period}/{trend_type}: {str(e)}")
                    continue
        
        # Nettoyer les anciennes entrées
        old_threshold = timezone.now() - timedelta(days=30)
        deleted_count = TrendingBook.objects.filter(
            last_updated__lt=old_threshold,
            is_active=False
        ).delete()[0]
        
        logger.info(f"Livres en tendance mis à jour, {deleted_count} anciennes entrées supprimées")
        
        # Émettre le signal de mise à jour
        trending_books_updated.send(sender=None)
        
        return {'success': True, 'deleted_old': deleted_count}
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des tendances: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_data():
    """
    Nettoyer les anciennes données de recommandations
    """
    try:
        logger.info("Début du nettoyage des anciennes données")
        
        result = clean_old_recommendation_data(days_to_keep=90)
        
        logger.info(f"Nettoyage terminé: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def generate_recommendation_analytics_report():
    """
    Générer un rapport d'analytics des recommandations
    """
    try:
        logger.info("Génération du rapport d'analytics")
        
        # Obtenir les analytics globales
        analytics = get_recommendation_analytics()
        
        # Calculer des métriques supplémentaires
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Recommandations générées cette semaine
        weekly_recommendations = RecommendationSet.objects.filter(
            created_at__date__gte=week_ago
        ).count()
        
        # Utilisateurs actifs cette semaine
        weekly_active_users = UserInteraction.objects.filter(
            created_at__date__gte=week_ago
        ).values('user').distinct().count()
        
        # Taux de conversion moyen
        total_recommendations = Recommendation.objects.count()
        converted_recommendations = Recommendation.objects.filter(converted=True).count()
        conversion_rate = (converted_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0
        
        report = {
            'date': today.isoformat(),
            'global_analytics': analytics,
            'weekly_metrics': {
                'recommendations_generated': weekly_recommendations,
                'active_users': weekly_active_users,
                'conversion_rate': round(conversion_rate, 2)
            }
        }
        
        # Sauvegarder le rapport dans le cache
        cache.set('recommendation_analytics_report', report, 86400)  # 24 heures
        
        # Envoyer par email aux administrateurs si configuré
        if hasattr(settings, 'ADMIN_EMAIL') and settings.ADMIN_EMAIL:
            try:
                send_mail(
                    subject=f'Rapport Analytics Recommandations - {today}',
                    message=f'Rapport d\'analytics généré:\n\n{json.dumps(report, indent=2)}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du rapport par email: {str(e)}")
        
        logger.info("Rapport d'analytics généré avec succès")
        return report
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def send_recommendation_notifications():
    """
    Envoyer des notifications de recommandations aux utilisateurs
    """
    try:
        logger.info("Envoi des notifications de recommandations")
        
        # Obtenir les utilisateurs qui ont activé les notifications
        users_to_notify = UserProfile.objects.filter(
            enable_recommendations=True,
            recommendation_frequency__in=['daily', 'weekly']
        ).select_related('user')
        
        notifications_sent = 0
        
        for profile in users_to_notify:
            try:
                # Vérifier si l'utilisateur doit recevoir une notification aujourd'hui
                should_notify = False
                
                if profile.recommendation_frequency == 'daily':
                    should_notify = True
                elif profile.recommendation_frequency == 'weekly':
                    # Envoyer le lundi
                    should_notify = timezone.now().weekday() == 0
                
                if should_notify:
                    # Générer des recommandations fraîches
                    recommendations = generate_personalized_recommendations(
                        user=profile.user,
                        algorithm='hybrid',
                        count=5,
                        context='notification'
                    )
                    
                    if recommendations:
                        # Envoyer la notification (email, push, etc.)
                        # Ici vous pourriez intégrer avec votre système de notifications
                        
                        logger.info(f"Notification envoyée à {profile.user.username}")
                        notifications_sent += 1
                
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de notification à {profile.user.username}: {str(e)}")
                continue
        
        logger.info(f"Notifications envoyées: {notifications_sent}")
        return {'success': True, 'notifications_sent': notifications_sent}
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des notifications: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def optimize_recommendation_algorithms():
    """
    Optimiser les algorithmes de recommandation basés sur les performances
    """
    try:
        logger.info("Optimisation des algorithmes de recommandation")
        
        # Analyser les performances des différents algorithmes
        algorithms = ['content_based', 'collaborative', 'popularity', 'hybrid']
        performance_data = {}
        
        for algorithm in algorithms:
            # Calculer les métriques de performance
            recommendations = Recommendation.objects.filter(
                recommendation_set__algorithm_type=algorithm,
                recommendation_set__created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            total_count = recommendations.count()
            clicked_count = recommendations.filter(clicked=True).count()
            converted_count = recommendations.filter(converted=True).count()
            
            click_rate = (clicked_count / total_count * 100) if total_count > 0 else 0
            conversion_rate = (converted_count / total_count * 100) if total_count > 0 else 0
            
            performance_data[algorithm] = {
                'total_recommendations': total_count,
                'click_rate': round(click_rate, 2),
                'conversion_rate': round(conversion_rate, 2),
                'score': round((click_rate + conversion_rate * 2) / 3, 2)  # Score pondéré
            }
        
        # Identifier le meilleur algorithme
        best_algorithm = max(performance_data.keys(), 
                           key=lambda x: performance_data[x]['score'])
        
        # Sauvegarder les résultats
        cache.set('algorithm_performance', performance_data, 86400)
        cache.set('best_algorithm', best_algorithm, 86400)
        
        logger.info(f"Optimisation terminée. Meilleur algorithme: {best_algorithm}")
        return {
            'success': True,
            'performance_data': performance_data,
            'best_algorithm': best_algorithm
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation: {str(e)}")
        return {'success': False, 'error': str(e)}


# Tâches périodiques (à configurer dans Celery Beat)
@shared_task
def daily_maintenance():
    """
    Tâche de maintenance quotidienne
    """
    logger.info("Début de la maintenance quotidienne")
    
    tasks = [
        update_book_vectors.delay(),
        update_trending_books.delay(),
        generate_recommendation_analytics_report.delay(),
        send_recommendation_notifications.delay()
    ]
    
    return {'tasks_launched': len(tasks)}


@shared_task
def weekly_maintenance():
    """
    Tâche de maintenance hebdomadaire
    """
    logger.info("Début de la maintenance hebdomadaire")
    
    tasks = [
        calculate_similarity_matrix.delay(),
        cleanup_old_data.delay(),
        optimize_recommendation_algorithms.delay()
    ]
    
    return {'tasks_launched': len(tasks)}