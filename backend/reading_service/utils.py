from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, Max, F
from django.core.cache import cache
from datetime import datetime, timedelta
import logging
import random
from typing import List, Dict, Any

User = get_user_model()
logger = logging.getLogger(__name__)


def calculate_reading_statistics(user, period='monthly'):
    """Calcule les statistiques de lecture pour une période donnée"""
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
        }
    }


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


def get_reading_recommendations(user, limit=10):
    """Génère des recommandations de lecture personnalisées"""
    from .models import ReadingSession
    
    try:
        # Importer les modèles du service de catalogue
        from catalog_service.models import Book, Category, Author
        
        recommendations = []
        
        # 1. Livres de la même catégorie que les livres récemment lus
        recent_sessions = ReadingSession.objects.filter(
            user=user,
            status__in=['completed', 'active']
        ).select_related('book').order_by('-last_activity')[:5]
        
        if recent_sessions:
            # Récupérer les catégories des livres récents
            recent_categories = set()
            for session in recent_sessions:
                recent_categories.update(session.book.categories.all())
            
            # Livres de ces catégories non encore lus
            read_books = ReadingSession.objects.filter(user=user).values_list('book_id', flat=True)
            
            category_books = Book.objects.filter(
                categories__in=recent_categories,
                status='published'
            ).exclude(
                id__in=read_books
            ).distinct()[:limit//2]
            
            for book in category_books:
                recommendations.append({
                    'book_id': book.id,
                    'title': book.title,
                    'authors': [author.full_name for author in book.authors.all()],
                    'cover_image': book.cover_image.url if book.cover_image else None,
                    'rating': book.average_rating,
                    'category': book.categories.first().name if book.categories.exists() else '',
                    'reason': 'Basé sur vos lectures récentes',
                    'confidence_score': 0.8
                })
        
        # 2. Livres populaires non lus
        if len(recommendations) < limit:
            read_books = ReadingSession.objects.filter(user=user).values_list('book_id', flat=True)
            
            popular_books = Book.objects.filter(
                status='published'
            ).exclude(
                id__in=read_books
            ).annotate(
                popularity_score=Count('reading_sessions') + Count('ratings')
            ).order_by('-popularity_score')[:limit - len(recommendations)]
            
            for book in popular_books:
                recommendations.append({
                    'book_id': book.id,
                    'title': book.title,
                    'authors': [author.full_name for author in book.authors.all()],
                    'cover_image': book.cover_image.url if book.cover_image else None,
                    'rating': book.average_rating,
                    'category': book.categories.first().name if book.categories.exists() else '',
                    'reason': 'Populaire auprès des lecteurs',
                    'confidence_score': 0.6
                })
        
        # 3. Compléter avec des livres aléatoires si nécessaire
        if len(recommendations) < limit:
            read_books = ReadingSession.objects.filter(user=user).values_list('book_id', flat=True)
            
            random_books = Book.objects.filter(
                status='published'
            ).exclude(
                id__in=read_books
            ).order_by('?')[:limit - len(recommendations)]
            
            for book in random_books:
                recommendations.append({
                    'book_id': book.id,
                    'title': book.title,
                    'authors': [author.full_name for author in book.authors.all()],
                    'cover_image': book.cover_image.url if book.cover_image else None,
                    'rating': book.average_rating,
                    'category': book.categories.first().name if book.categories.exists() else '',
                    'reason': 'Découverte',
                    'confidence_score': 0.4
                })
        
        return recommendations[:limit]
        
    except ImportError:
        logger.warning("Impossible d'importer les modèles du service de catalogue")
        return []
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {e}")
        return []


def update_reading_goals(user):
    """Met à jour la progression des objectifs de lecture de l'utilisateur"""
    from .models import ReadingGoal
    
    try:
        active_goals = ReadingGoal.objects.filter(
            user=user,
            status='active'
        )
        
        for goal in active_goals:
            goal.update_progress()
            
            # Vérifier si l'objectif est atteint
            if goal.is_completed and goal.status == 'active':
                goal.status = 'completed'
                goal.save()
                
                # Envoyer une notification (à implémenter)
                logger.info(f"Objectif de lecture atteint pour l'utilisateur {user.username}: {goal.title}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des objectifs de lecture: {e}")


def generate_reading_insights(user):
    """Génère des insights personnalisés sur les habitudes de lecture"""
    from .models import ReadingSession, ReadingProgress
    
    insights = []
    
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
                    'trend': 'stable'  # À calculer avec les données historiques
                })
        
        # Insight 2: Moment préféré de lecture
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
                'trend': 'stable'
            })
        
        # Insight 3: Consistance de lecture
        today = timezone.now().date()
        month_start = today.replace(day=1)
        consistency = calculate_reading_consistency(user, month_start, today)
        
        if consistency > 0:
            consistency_level = 'faible'
            if consistency >= 70:
                consistency_level = 'excellente'
            elif consistency >= 50:
                consistency_level = 'bonne'
            elif consistency >= 30:
                consistency_level = 'moyenne'
            
            insights.append({
                'type': 'consistency',
                'title': 'Régularité de lecture',
                'description': f'Votre régularité ce mois est {consistency_level} ({consistency:.1f}% des jours).',
                'value': consistency,
                'trend': 'stable'
            })
        
        # Insight 4: Progression des livres
        active_sessions = ReadingSession.objects.filter(
            user=user,
            status='active'
        )
        
        if active_sessions:
            avg_progress = active_sessions.aggregate(
                avg=Avg('current_position')
            )['avg']
            
            insights.append({
                'type': 'progress',
                'title': 'Progression des lectures',
                'description': f'Vous avez {active_sessions.count()} livre(s) en cours avec une progression moyenne de {avg_progress:.1f}%.',
                'value': avg_progress,
                'trend': 'stable'
            })
        
        return insights
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des insights: {e}")
        return []


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


def export_reading_data(user, format='json'):
    """Exporte les données de lecture de l'utilisateur"""
    from .models import ReadingSession, Bookmark, ReadingGoal
    
    try:
        # Récupérer toutes les données
        sessions = ReadingSession.objects.filter(user=user).select_related('book')
        bookmarks = Bookmark.objects.filter(user=user).select_related('book')
        goals = ReadingGoal.objects.filter(user=user)
        
        data = {
            'user': {
                'username': user.username,
                'email': user.email,
                'export_date': timezone.now().isoformat()
            },
            'reading_sessions': [],
            'bookmarks': [],
            'reading_goals': [],
            'statistics': calculate_reading_statistics(user, 'yearly')
        }
        
        # Sessions de lecture
        for session in sessions:
            data['reading_sessions'].append({
                'id': str(session.id),
                'book_title': session.book.title,
                'status': session.status,
                'device_type': session.device_type,
                'current_page': session.current_page,
                'progress_percentage': session.progress_percentage,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'total_reading_time': str(session.total_reading_time),
                'created_at': session.created_at.isoformat()
            })
        
        # Signets
        for bookmark in bookmarks:
            data['bookmarks'].append({
                'id': str(bookmark.id),
                'book_title': bookmark.book.title,
                'type': bookmark.type,
                'title': bookmark.title,
                'content': bookmark.content,
                'note': bookmark.note,
                'page_number': bookmark.page_number,
                'is_favorite': bookmark.is_favorite,
                'created_at': bookmark.created_at.isoformat()
            })
        
        # Objectifs de lecture
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
        logger.error(f"Erreur lors de l'export des données: {e}")
        return None


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