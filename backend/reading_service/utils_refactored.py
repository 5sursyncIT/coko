"""
Utils de lecture refactorisés pour utiliser les services découplés
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, Max, F
from django.core.cache import cache
from datetime import datetime, timedelta
import logging
import random
from typing import List, Dict, Any

from coko.services import get_book_service
from coko.events import publish_event, EventType

User = get_user_model()
logger = logging.getLogger(__name__)


def calculate_reading_statistics(user, period='monthly'):
    """Calcule les statistiques de lecture pour une période donnée (version découplée)"""
    from .models import ReadingSession, ReadingProgress, Bookmark, ReadingGoal
    
    today = timezone.now().date()
    
    # Définir les dates selon la période
    if period == 'daily':
        start_date = today
        end_date = today
    elif period == 'weekly':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'monthly':
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    elif period == 'yearly':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Statistiques des sessions
    sessions = ReadingSession.objects.filter(
        user=user,
        last_activity__date__gte=start_date,
        last_activity__date__lte=end_date
    )
    
    session_stats = sessions.aggregate(
        total_sessions=Count('id'),
        active_sessions=Count('id', filter=Q(status='active')),
        completed_sessions=Count('id', filter=Q(status='completed')),
        total_reading_time=Sum('total_reading_time'),
        total_pages_read=Sum('total_pages_read'),
        avg_session_duration=Avg('total_reading_time')
    )
    
    # Statistiques des signets
    bookmark_stats = Bookmark.objects.filter(
        user=user,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).aggregate(
        total_bookmarks=Count('id'),
        bookmarks_by_type=Count('id'),
        favorite_bookmarks=Count('id', filter=Q(is_favorite=True))
    )
    
    # Appareil le plus utilisé
    favorite_device = sessions.values('device_type').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    # Heure de lecture préférée
    favorite_time = sessions.aggregate(
        avg_hour=Avg('last_activity__hour')
    )['avg_hour']
    
    return {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'session_stats': {
            'total_sessions': session_stats['total_sessions'] or 0,
            'active_sessions': session_stats['active_sessions'] or 0,
            'completed_sessions': session_stats['completed_sessions'] or 0,
            'total_reading_time': session_stats['total_reading_time'] or timedelta(),
            'average_session_duration': session_stats['avg_session_duration'] or timedelta(),
            'total_pages_read': session_stats['total_pages_read'] or 0,
            'books_completed': session_stats['completed_sessions'] or 0,
            'favorite_device': favorite_device['device_type'] if favorite_device else None,
            'favorite_reading_time': f"{int(favorite_time):02d}:00" if favorite_time else None
        },
        'bookmark_stats': {
            'total_bookmarks': bookmark_stats['total_bookmarks'] or 0,
            'favorite_bookmarks': bookmark_stats['favorite_bookmarks'] or 0
        },
        'progress_stats': {
            'books_in_progress': sessions.filter(status='active').count(),
            'average_progress': sessions.filter(status='active').aggregate(
                avg=Avg('current_position')
            )['avg'] or 0,
            'reading_consistency': calculate_reading_consistency(user, start_date, end_date)
        },
        'via_services': True  # Indicateur que les stats utilisent les services découplés
    }


def get_reading_recommendations_via_service(user, limit=10):
    """Génère des recommandations de lecture via les services découplés"""
    from .models import ReadingSession
    
    try:
        book_service = get_book_service()
        recommendations = []
        
        # 1. Livres de la même catégorie que les livres récemment lus
        recent_sessions = ReadingSession.objects.filter(
            user=user,
            status__in=['completed', 'active']
        ).order_by('-last_activity')[:5]
        
        if recent_sessions:
            # Récupérer les catégories des livres récents via le service
            recent_categories = set()
            recent_book_ids = []
            
            for session in recent_sessions:
                recent_book_ids.append(session.book_id)
                book_categories = book_service.get_book_categories(session.book_id)
                recent_categories.update(book_categories)
            
            # Obtenir les livres lus pour les exclure
            read_sessions = ReadingSession.objects.filter(user=user)
            read_book_ids = list(read_sessions.values_list('book_id', flat=True))
            
            # Livres de ces catégories non encore lus
            if recent_categories:
                category_books = book_service.get_books_by_category(
                    list(recent_categories), 
                    limit=limit//2
                )
                
                for book_data in category_books:
                    if book_data['id'] not in read_book_ids:
                        recommendations.append({
                            'book_id': book_data['id'],
                            'title': book_data['title'],
                            'authors': book_data.get('authors', []),
                            'cover_image': book_data.get('cover_image'),
                            'rating': book_data.get('average_rating', 0),
                            'category': book_data.get('categories', [''])[0] if book_data.get('categories') else '',
                            'reason': 'Basé sur vos lectures récentes',
                            'confidence_score': 0.8,
                            'via_service': True
                        })
        
        # 2. Livres populaires non lus
        if len(recommendations) < limit:
            read_sessions = ReadingSession.objects.filter(user=user)
            read_book_ids = list(read_sessions.values_list('book_id', flat=True))
            
            popular_books = book_service.get_popular_books(
                limit=limit - len(recommendations),
                exclude_ids=read_book_ids
            )
            
            for book_data in popular_books:
                recommendations.append({
                    'book_id': book_data['id'],
                    'title': book_data['title'],
                    'authors': book_data.get('authors', []),
                    'cover_image': book_data.get('cover_image'),
                    'rating': book_data.get('average_rating', 0),
                    'category': book_data.get('categories', [''])[0] if book_data.get('categories') else '',
                    'reason': 'Populaire auprès des lecteurs',
                    'confidence_score': 0.6,
                    'via_service': True
                })
        
        # 3. Compléter avec une recherche générale si nécessaire
        if len(recommendations) < limit:
            read_sessions = ReadingSession.objects.filter(user=user)
            read_book_ids = list(read_sessions.values_list('book_id', flat=True))
            recommended_ids = [rec['book_id'] for rec in recommendations]
            
            # Recherche générale de livres
            additional_books = book_service.search_books(
                "",  # Recherche vide pour obtenir des livres généraux
                filters={'min_rating': 3.0},
                limit=limit - len(recommendations)
            )
            
            for book_data in additional_books:
                if book_data['id'] not in read_book_ids and book_data['id'] not in recommended_ids:
                    recommendations.append({
                        'book_id': book_data['id'],
                        'title': book_data['title'],
                        'authors': book_data.get('authors', []),
                        'cover_image': book_data.get('cover_image'),
                        'rating': book_data.get('average_rating', 0),
                        'category': book_data.get('categories', [''])[0] if book_data.get('categories') else '',
                        'reason': 'Découverte',
                        'confidence_score': 0.4,
                        'via_service': True
                    })
        
        return recommendations[:limit]
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations via service: {e}")
        return []


def update_reading_goals_with_events(user):
    """Met à jour la progression des objectifs de lecture avec publication d'événements"""
    from .models import ReadingGoal
    
    try:
        active_goals = ReadingGoal.objects.filter(
            user=user,
            status='active'
        )
        
        for goal in active_goals:
            old_progress = goal.progress_percentage
            goal.update_progress()
            new_progress = goal.progress_percentage
            
            # Publier un événement si le progrès a changé significativement
            if new_progress - old_progress >= 10:  # Au moins 10% de progrès
                publish_event(
                    EventType.USER_INTERACTION_RECORDED,
                    {
                        'goal_id': goal.id,
                        'goal_type': goal.goal_type,
                        'progress_change': new_progress - old_progress,
                        'current_progress': new_progress
                    },
                    user_id=user.id,
                    source_service='reading_service'
                )
            
            # Vérifier si l'objectif est atteint
            if goal.is_completed and goal.status == 'active':
                goal.status = 'completed'
                goal.save()
                
                # Publier un événement de completion
                publish_event(
                    EventType.USER_INTERACTION_RECORDED,
                    {
                        'goal_id': goal.id,
                        'goal_type': goal.goal_type,
                        'goal_completed': True,
                        'title': goal.title
                    },
                    user_id=user.id,
                    source_service='reading_service'
                )
                
                logger.info(f"Objectif de lecture atteint pour l'utilisateur {user.username}: {goal.title}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des objectifs de lecture: {e}")


def generate_reading_insights_via_service(user):
    """Génère des insights personnalisés via les services découplés"""
    from .models import ReadingSession, ReadingProgress
    
    insights = []
    book_service = get_book_service()
    
    try:
        # Insight 1: Vitesse de lecture
        recent_sessions = ReadingSession.objects.filter(
            user=user,
            status='completed',
            total_reading_time__gt=timedelta(minutes=10)
        ).order_by('-end_time')[:10]
        
        if recent_sessions:
            avg_speed = sum(
                session.reading_speed_pages_per_hour 
                for session in recent_sessions
            ) / len(recent_sessions)
            
            if avg_speed > 0:
                insights.append({
                    'type': 'reading_speed',
                    'title': 'Vitesse de lecture',
                    'description': f'Votre vitesse moyenne est de {avg_speed:.1f} pages par heure.',
                    'value': avg_speed,
                    'trend': 'stable',
                    'via_service': True
                })
        
        # Insight 2: Genres préférés basés sur l'historique via le service
        genre_counts = {}
        reading_history = ReadingSession.objects.filter(user=user, status='completed')
        
        for session in reading_history:
            book_categories = book_service.get_book_categories(session.book_id)
            for category in book_categories:
                genre_counts[category] = genre_counts.get(category, 0) + 1
        
        if genre_counts:
            favorite_genre = max(genre_counts, key=genre_counts.get)
            genre_count = genre_counts[favorite_genre]
            
            insights.append({
                'type': 'favorite_genre',
                'title': 'Genre préféré',
                'description': f'Vous avez lu {genre_count} livre(s) de {favorite_genre}.',
                'value': favorite_genre,
                'trend': 'stable',
                'via_service': True
            })
        
        # Insight 3: Moment préféré de lecture (inchangé)
        session_hours = ReadingSession.objects.filter(
            user=user
        ).values_list('last_activity__hour', flat=True)
        
        if session_hours:
            hour_counts = {}
            for hour in session_hours:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            favorite_hour = max(hour_counts, key=hour_counts.get)
            
            time_periods = {
                range(6, 12): 'matinée',
                range(12, 18): 'après-midi',
                range(18, 22): 'soirée',
                range(22, 24): 'nuit',
                range(0, 6): 'nuit'
            }
            
            period = 'journée'
            for time_range, period_name in time_periods.items():
                if favorite_hour in time_range:
                    period = period_name
                    break
            
            insights.append({
                'type': 'reading_time',
                'title': 'Moment de lecture préféré',
                'description': f'Vous lisez principalement en {period} (vers {favorite_hour}h).',
                'value': favorite_hour,
                'trend': 'stable',
                'via_service': True
            })
        
        # Insight 4: Recommandations basées sur l'analyse
        recommendations_data = get_reading_recommendations_via_service(user, limit=3)
        if recommendations_data:
            insights.append({
                'type': 'recommendations',
                'title': 'Livres recommandés',
                'description': f'Nous avons {len(recommendations_data)} nouvelles recommandations pour vous.',
                'value': len(recommendations_data),
                'trend': 'stable',
                'recommendations': recommendations_data,
                'via_service': True
            })
        
        return insights
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des insights via service: {e}")
        return []


def export_reading_data_with_services(user, format='json'):
    """Exporte les données de lecture en utilisant les services pour enrichir les données"""
    from .models import ReadingSession, Bookmark, ReadingGoal
    
    try:
        book_service = get_book_service()
        
        # Récupérer toutes les données locales
        sessions = ReadingSession.objects.filter(user=user)
        bookmarks = Bookmark.objects.filter(user=user)
        goals = ReadingGoal.objects.filter(user=user)
        
        data = {
            'user': {
                'username': user.username,
                'email': user.email,
                'export_date': timezone.now().isoformat(),
                'export_method': 'services_enhanced'
            },
            'reading_sessions': [],
            'bookmarks': [],
            'reading_goals': [],
            'statistics': calculate_reading_statistics(user, 'yearly'),
            'book_details': {}  # Cache des détails de livres via le service
        }
        
        # Sessions de lecture avec détails des livres
        for session in sessions:
            book_details = book_service.get_book_by_id(session.book_id)
            if book_details:
                data['book_details'][session.book_id] = book_details
            
            data['reading_sessions'].append({
                'id': str(session.id),
                'book_id': session.book_id,
                'book_title': book_details.get('title', 'Titre inconnu') if book_details else 'Titre inconnu',
                'book_authors': book_details.get('authors', []) if book_details else [],
                'book_categories': book_details.get('categories', []) if book_details else [],
                'status': session.status,
                'device_type': session.device_type,
                'current_page': session.current_page,
                'progress_percentage': session.progress_percentage,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'total_reading_time': str(session.total_reading_time),
                'created_at': session.created_at.isoformat(),
                'enhanced_via_service': True
            })
        
        # Signets avec détails des livres
        for bookmark in bookmarks:
            book_details = data['book_details'].get(bookmark.book_id)
            if not book_details:
                book_details = book_service.get_book_by_id(bookmark.book_id)
                if book_details:
                    data['book_details'][bookmark.book_id] = book_details
            
            data['bookmarks'].append({
                'id': str(bookmark.id),
                'book_id': bookmark.book_id,
                'book_title': book_details.get('title', 'Titre inconnu') if book_details else 'Titre inconnu',
                'type': bookmark.type,
                'title': bookmark.title,
                'content': bookmark.content,
                'note': bookmark.note,
                'page_number': bookmark.page_number,
                'is_favorite': bookmark.is_favorite,
                'created_at': bookmark.created_at.isoformat(),
                'enhanced_via_service': True
            })
        
        # Objectifs de lecture (inchangés)
        for goal in goals:
            data['reading_goals'].append({
                'id': str(goal.id),
                'title': goal.title,
                'description': goal.description,
                'goal_type': goal.goal_type,
                'target_value': goal.target_value,
                'current_value': goal.current_value,
                'progress_percentage': goal.progress_percentage,
                'status': goal.status,
                'start_date': goal.start_date.isoformat(),
                'end_date': goal.end_date.isoformat(),
                'created_at': goal.created_at.isoformat()
            })
        
        return data
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export des données via services: {e}")
        return None


# Fonctions utilitaires inchangées (pas de dépendances inter-services)

def calculate_reading_consistency(user, start_date, end_date):
    """Calcule la consistance de lecture (pourcentage de jours avec lecture)"""
    from .models import ReadingSession
    
    total_days = (end_date - start_date).days + 1
    
    reading_days = ReadingSession.objects.filter(
        user=user,
        last_activity__date__gte=start_date,
        last_activity__date__lte=end_date
    ).values('last_activity__date').distinct().count()
    
    return (reading_days / total_days) * 100 if total_days > 0 else 0


def calculate_reading_streak(user):
    """Calcule la série de jours consécutifs avec lecture"""
    from .models import ReadingSession
    
    today = timezone.now().date()
    streak = 0
    current_date = today
    
    while True:
        has_reading = ReadingSession.objects.filter(
            user=user,
            last_activity__date=current_date
        ).exists()
        
        if has_reading:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
        
        # Limite pour éviter les boucles infinies
        if streak > 365:
            break
    
    return streak


def get_reading_heatmap_data(user, year=None):
    """Génère les données pour une heatmap de lecture annuelle"""
    from .models import ReadingSession
    
    if year is None:
        year = timezone.now().year
    
    start_date = datetime(year, 1, 1).date()
    end_date = datetime(year, 12, 31).date()
    
    # Récupérer les sessions de lecture pour l'année
    sessions = ReadingSession.objects.filter(
        user=user,
        last_activity__date__gte=start_date,
        last_activity__date__lte=end_date
    ).values('last_activity__date').annotate(
        session_count=Count('id'),
        total_time=Sum('total_reading_time'),
        pages_read=Sum('total_pages_read')
    )
    
    # Créer un dictionnaire avec toutes les dates de l'année
    heatmap_data = {}
    current_date = start_date
    
    while current_date <= end_date:
        heatmap_data[current_date.isoformat()] = {
            'date': current_date.isoformat(),
            'session_count': 0,
            'total_time_minutes': 0,
            'pages_read': 0,
            'intensity': 0
        }
        current_date += timedelta(days=1)
    
    # Remplir avec les données réelles
    for session in sessions:
        date_str = session['last_activity__date'].isoformat()
        if date_str in heatmap_data:
            total_minutes = session['total_time'].total_seconds() / 60 if session['total_time'] else 0
            
            heatmap_data[date_str].update({
                'session_count': session['session_count'],
                'total_time_minutes': total_minutes,
                'pages_read': session['pages_read'] or 0,
                'intensity': min(session['session_count'] / 3, 1)  # Normaliser entre 0 et 1
            })
    
    return list(heatmap_data.values())


def clean_old_reading_data(days_to_keep=365):
    """Nettoie les anciennes données de lecture"""
    from .models import ReadingProgress, ReadingStatistics
    
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    try:
        # Supprimer les anciennes entrées de progression
        old_progress = ReadingProgress.objects.filter(
            timestamp__lt=cutoff_date
        )
        progress_count = old_progress.count()
        old_progress.delete()
        
        # Supprimer les anciennes statistiques quotidiennes
        old_stats = ReadingStatistics.objects.filter(
            period_type='daily',
            period_start__lt=cutoff_date.date()
        )
        stats_count = old_stats.count()
        old_stats.delete()
        
        logger.info(
            f"Nettoyage terminé: {progress_count} entrées de progression et "
            f"{stats_count} statistiques supprimées"
        )
        
        return {
            'progress_entries_deleted': progress_count,
            'statistics_deleted': stats_count
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des données: {e}")
        return None