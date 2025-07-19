from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver, Signal
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging

from .models import (
    ReadingSession, ReadingProgress, Bookmark, 
    ReadingGoal, ReadingStatistics
)
from .utils import update_reading_goals, calculate_reading_statistics

User = get_user_model()
logger = logging.getLogger(__name__)

# Signal personnalisé pour les événements de lecture
reading_milestone_reached = Signal()
goal_completed = Signal()
reading_streak_updated = Signal()


@receiver(post_save, sender=ReadingSession)
def handle_reading_session_save(sender, instance, created, **kwargs):
    """Gère la sauvegarde des sessions de lecture"""
    
    if created:
        logger.info(f"Nouvelle session de lecture créée: {instance.user.username} - {instance.book.title}")
        
        # Invalider le cache des statistiques
        cache_key = f"reading_stats_{instance.user.id}"
        cache.delete(cache_key)
        
        # Mettre à jour les objectifs de lecture
        update_reading_goals(instance.user)
        
    else:
        # Session mise à jour
        if instance.status == 'completed' and instance.end_time:
            logger.info(f"Lecture terminée: {instance.user.username} - {instance.book.title}")
            
            # Envoyer le signal de milestone
            reading_milestone_reached.send(
                sender=ReadingSession,
                user=instance.user,
                session=instance,
                milestone_type='book_completed'
            )
            
            # Mettre à jour les objectifs
            update_reading_goals(instance.user)
            
            # Invalider le cache
            cache_key = f"reading_stats_{instance.user.id}"
            cache.delete(cache_key)


@receiver(post_delete, sender=ReadingSession)
def handle_reading_session_delete(sender, instance, **kwargs):
    """Gère la suppression des sessions de lecture"""
    
    logger.info(f"Session de lecture supprimée: {instance.user.username} - {instance.book.title}")
    
    # Invalider le cache des statistiques
    cache_key = f"reading_stats_{instance.user.id}"
    cache.delete(cache_key)
    
    # Mettre à jour les objectifs
    update_reading_goals(instance.user)


@receiver(post_save, sender=ReadingProgress)
def handle_reading_progress_save(sender, instance, created, **kwargs):
    """Gère la sauvegarde de la progression de lecture"""
    
    if created:
        # Mettre à jour la session associée
        session = instance.session
        session.last_activity = timezone.now()
        
        # Incrémenter le nombre total de pages lues
        if instance.page_number > session.current_page:
            pages_read = instance.page_number - session.current_page
            session.total_pages_read += pages_read
            session.current_page = instance.page_number
        
        # Ajouter le temps de lecture
        if instance.time_spent:
            session.total_reading_time += instance.time_spent
        
        session.save()
        
        # Vérifier les milestones de pages
        total_pages = session.total_pages_read
        milestones = [50, 100, 250, 500, 1000]
        
        for milestone in milestones:
            if total_pages >= milestone and (total_pages - pages_read) < milestone:
                reading_milestone_reached.send(
                    sender=ReadingProgress,
                    user=session.user,
                    session=session,
                    milestone_type='pages_read',
                    milestone_value=milestone
                )
                break


@receiver(post_save, sender=Bookmark)
def handle_bookmark_save(sender, instance, created, **kwargs):
    """Gère la sauvegarde des signets"""
    
    if created:
        logger.info(
            f"Nouveau signet créé: {instance.user.username} - "
            f"{instance.book.title} - Page {instance.page_number}"
        )
        
        # Vérifier les milestones de signets
        bookmark_count = Bookmark.objects.filter(user=instance.user).count()
        milestones = [10, 50, 100, 500]
        
        for milestone in milestones:
            if bookmark_count == milestone:
                reading_milestone_reached.send(
                    sender=Bookmark,
                    user=instance.user,
                    bookmark=instance,
                    milestone_type='bookmarks_created',
                    milestone_value=milestone
                )
                break


@receiver(post_save, sender=ReadingGoal)
def handle_reading_goal_save(sender, instance, created, **kwargs):
    """Gère la sauvegarde des objectifs de lecture"""
    
    if created:
        logger.info(f"Nouvel objectif de lecture créé: {instance.user.username} - {instance.title}")
    
    # Vérifier si l'objectif vient d'être complété
    if instance.status == 'completed' and instance.is_completed:
        logger.info(f"Objectif de lecture atteint: {instance.user.username} - {instance.title}")
        
        # Envoyer le signal de completion
        goal_completed.send(
            sender=ReadingGoal,
            user=instance.user,
            goal=instance
        )
        
        # Envoyer une notification par email
        if instance.send_reminders:
            try:
                send_mail(
                    subject=f'Objectif de lecture atteint: {instance.title}',
                    message=f'Félicitations ! Vous avez atteint votre objectif "{instance.title}".\n\n'
                           f'Progression: {instance.current_value}/{instance.target_value}\n'
                           f'Pourcentage: {instance.progress_percentage:.1f}%',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.user.email],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email d'objectif atteint: {e}")


@receiver(post_delete, sender=ReadingGoal)
def handle_reading_goal_delete(sender, instance, **kwargs):
    """Gère la suppression des objectifs de lecture"""
    
    logger.info(f"Objectif de lecture supprimé: {instance.user.username} - {instance.title}")


@receiver(post_save, sender=ReadingStatistics)
def handle_reading_statistics_save(sender, instance, created, **kwargs):
    """Gère la sauvegarde des statistiques de lecture"""
    
    if created:
        logger.info(
            f"Nouvelles statistiques générées: {instance.user.username} - "
            f"{instance.period_type} - {instance.period_start}"
        )


@receiver(reading_milestone_reached)
def handle_reading_milestone(sender, user, milestone_type, milestone_value=None, **kwargs):
    """Gère les milestones de lecture atteints"""
    
    logger.info(
        f"Milestone atteint: {user.username} - {milestone_type} - {milestone_value}"
    )
    
    # Envoyer une notification selon le type de milestone
    if milestone_type == 'book_completed':
        session = kwargs.get('session')
        if session:
            try:
                send_mail(
                    subject='Livre terminé !',
                    message=f'Félicitations ! Vous avez terminé la lecture de "{session.book.title}".\n\n'
                           f'Temps de lecture: {session.total_reading_time}\n'
                           f'Pages lues: {session.total_pages_read}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email de livre terminé: {e}")
    
    elif milestone_type == 'pages_read':
        try:
            send_mail(
                subject=f'Milestone de lecture: {milestone_value} pages !',
                message=f'Félicitations ! Vous avez lu {milestone_value} pages.\n\n'
                       'Continuez votre excellente progression !',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de milestone: {e}")
    
    elif milestone_type == 'bookmarks_created':
        try:
            send_mail(
                subject=f'Milestone de signets: {milestone_value} signets !',
                message=f'Félicitations ! Vous avez créé {milestone_value} signets.\n\n'
                       'Vos annotations enrichissent votre expérience de lecture !',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de milestone signets: {e}")


@receiver(goal_completed)
def handle_goal_completed(sender, user, goal, **kwargs):
    """Gère la completion d'un objectif de lecture"""
    
    logger.info(f"Objectif complété: {user.username} - {goal.title}")
    
    # Créer automatiquement un nouvel objectif similaire si c'est un objectif récurrent
    if goal.goal_type in ['books_per_month', 'pages_per_day', 'minutes_per_day']:
        try:
            # Calculer les nouvelles dates
            if goal.goal_type == 'books_per_month':
                new_start = goal.end_date + timedelta(days=1)
                new_end = (new_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            elif goal.goal_type in ['pages_per_day', 'minutes_per_day']:
                new_start = goal.end_date + timedelta(days=1)
                new_end = new_start + timedelta(days=30)  # Objectif mensuel
            
            # Créer le nouvel objectif
            new_goal = ReadingGoal.objects.create(
                user=user,
                title=f"{goal.title} (Auto-renouvelé)",
                description=goal.description,
                goal_type=goal.goal_type,
                target_value=goal.target_value,
                start_date=new_start,
                end_date=new_end,
                category=goal.category,
                author=goal.author,
                is_public=goal.is_public,
                send_reminders=goal.send_reminders
            )
            
            logger.info(f"Nouvel objectif auto-créé: {new_goal.title}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création automatique d'objectif: {e}")


@receiver(reading_streak_updated)
def handle_reading_streak_updated(sender, user, streak_days, **kwargs):
    """Gère la mise à jour des séries de lecture"""
    
    logger.info(f"Série de lecture mise à jour: {user.username} - {streak_days} jours")
    
    # Envoyer une notification pour les séries importantes
    milestone_streaks = [7, 30, 100, 365]
    
    if streak_days in milestone_streaks:
        try:
            if streak_days == 7:
                message = "Félicitations ! Vous avez lu pendant 7 jours consécutifs !"
            elif streak_days == 30:
                message = "Incroyable ! Un mois de lecture quotidienne !"
            elif streak_days == 100:
                message = "Extraordinaire ! 100 jours de lecture consécutive !"
            elif streak_days == 365:
                message = "Légendaire ! Une année complète de lecture quotidienne !"
            
            send_mail(
                subject=f'Série de lecture: {streak_days} jours !',
                message=f'{message}\n\n'
                       'Continuez sur cette excellente lancée !',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de série: {e}")


# Signal pour nettoyer les données anciennes
@receiver(post_save, sender=User)
def schedule_data_cleanup(sender, instance, created, **kwargs):
    """Programme le nettoyage des données anciennes pour les nouveaux utilisateurs"""
    
    if created:
        # Programmer une tâche de nettoyage (à implémenter avec Celery)
        logger.info(f"Nouvel utilisateur créé, programmation du nettoyage: {instance.username}")


# Fonction utilitaire pour calculer et mettre à jour les séries de lecture
def update_reading_streak(user):
    """Met à jour la série de lecture d'un utilisateur"""
    from .utils import calculate_reading_streak
    
    try:
        streak = calculate_reading_streak(user)
        
        # Envoyer le signal de mise à jour de série
        reading_streak_updated.send(
            sender=User,
            user=user,
            streak_days=streak
        )
        
        return streak
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul de la série de lecture: {e}")
        return 0


# Fonction pour générer les statistiques périodiques
def generate_periodic_statistics(user, period_type='daily'):
    """Génère les statistiques périodiques pour un utilisateur"""
    
    try:
        today = timezone.now().date()
        
        if period_type == 'daily':
            start_date = end_date = today
        elif period_type == 'weekly':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period_type == 'monthly':
            start_date = today.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            return
        
        # Vérifier si les statistiques existent déjà
        existing_stats = ReadingStatistics.objects.filter(
            user=user,
            period_type=period_type,
            period_start=start_date
        ).first()
        
        if existing_stats:
            return existing_stats
        
        # Calculer les statistiques
        stats_data = calculate_reading_statistics(user, period_type)
        
        # Créer l'objet statistiques
        stats = ReadingStatistics.objects.create(
            user=user,
            period_type=period_type,
            period_start=start_date,
            period_end=end_date,
            books_started=stats_data['session_stats']['total_sessions'],
            books_completed=stats_data['session_stats']['books_completed'],
            pages_read=stats_data['session_stats']['total_pages_read'],
            total_reading_time=stats_data['session_stats']['total_reading_time'],
            average_session_duration=stats_data['session_stats']['average_session_duration'],
            reading_sessions_count=stats_data['session_stats']['total_sessions'],
            preferred_device=stats_data['session_stats']['favorite_device']
        )
        
        logger.info(f"Statistiques {period_type} générées pour {user.username}")
        return stats
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des statistiques: {e}")
        return None