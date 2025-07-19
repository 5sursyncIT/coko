from celery import Celery
from celery.schedules import crontab
from django.conf import settings
import os

# Configuration Celery pour le service de recommandations

# Tâches périodiques pour les recommandations
CELERY_BEAT_SCHEDULE = {
    # Tâches quotidiennes
    'daily-maintenance': {
        'task': 'recommendation_service.tasks.daily_maintenance',
        'schedule': crontab(hour=2, minute=0),  # 2h00 du matin
        'options': {'queue': 'recommendations'}
    },
    
    'update-book-vectors-daily': {
        'task': 'recommendation_service.tasks.update_book_vectors',
        'schedule': crontab(hour=3, minute=0),  # 3h00 du matin
        'options': {'queue': 'recommendations'}
    },
    
    'update-trending-books-daily': {
        'task': 'recommendation_service.tasks.update_trending_books',
        'schedule': crontab(hour=4, minute=0),  # 4h00 du matin
        'options': {'queue': 'recommendations'}
    },
    
    'generate-analytics-report-daily': {
        'task': 'recommendation_service.tasks.generate_recommendation_analytics_report',
        'schedule': crontab(hour=5, minute=0),  # 5h00 du matin
        'options': {'queue': 'analytics'}
    },
    
    'send-recommendation-notifications': {
        'task': 'recommendation_service.tasks.send_recommendation_notifications',
        'schedule': crontab(hour=9, minute=0),  # 9h00 du matin
        'options': {'queue': 'notifications'}
    },
    
    # Tâches hebdomadaires
    'weekly-maintenance': {
        'task': 'recommendation_service.tasks.weekly_maintenance',
        'schedule': crontab(hour=1, minute=0, day_of_week=1),  # Lundi 1h00
        'options': {'queue': 'recommendations'}
    },
    
    'calculate-similarity-matrix-weekly': {
        'task': 'recommendation_service.tasks.calculate_similarity_matrix',
        'schedule': crontab(hour=0, minute=0, day_of_week=0),  # Dimanche minuit
        'options': {'queue': 'heavy_computation'}
    },
    
    'cleanup-old-data-weekly': {
        'task': 'recommendation_service.tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Dimanche 2h00
        'options': {'queue': 'maintenance'}
    },
    
    'optimize-recommendation-algorithms': {
        'task': 'recommendation_service.tasks.optimize_recommendation_algorithms',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Dimanche 3h00
        'options': {'queue': 'analytics'}
    },
    
    # Tâches de génération de recommandations par lots
    'batch-generate-recommendations-morning': {
        'task': 'recommendation_service.tasks.batch_generate_recommendations',
        'schedule': crontab(hour=6, minute=0),  # 6h00 du matin
        'kwargs': {'user_limit': 1000, 'algorithm': 'hybrid'},
        'options': {'queue': 'recommendations'}
    },
    
    'batch-generate-recommendations-evening': {
        'task': 'recommendation_service.tasks.batch_generate_recommendations',
        'schedule': crontab(hour=18, minute=0),  # 18h00
        'kwargs': {'user_limit': 500, 'algorithm': 'content_based'},
        'options': {'queue': 'recommendations'}
    },
    
    # Tâches de monitoring
    'monitor-recommendation-performance': {
        'task': 'recommendation_service.tasks.monitor_recommendation_performance',
        'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes
        'options': {'queue': 'monitoring'}
    },
}

# Configuration des queues Celery
CELERY_TASK_ROUTES = {
    # Tâches de recommandations
    'recommendation_service.tasks.generate_user_recommendations': {'queue': 'recommendations'},
    'recommendation_service.tasks.batch_generate_recommendations': {'queue': 'recommendations'},
    'recommendation_service.tasks.update_book_vectors': {'queue': 'recommendations'},
    'recommendation_service.tasks.update_trending_books': {'queue': 'recommendations'},
    'recommendation_service.tasks.daily_maintenance': {'queue': 'recommendations'},
    'recommendation_service.tasks.weekly_maintenance': {'queue': 'recommendations'},
    
    # Tâches de calcul intensif
    'recommendation_service.tasks.calculate_similarity_matrix': {'queue': 'heavy_computation'},
    'recommendation_service.tasks.calculate_cosine_similarity_vectors': {'queue': 'heavy_computation'},
    
    # Tâches d'analytics
    'recommendation_service.tasks.generate_recommendation_analytics_report': {'queue': 'analytics'},
    'recommendation_service.tasks.optimize_recommendation_algorithms': {'queue': 'analytics'},
    
    # Tâches de maintenance
    'recommendation_service.tasks.cleanup_old_data': {'queue': 'maintenance'},
    
    # Tâches de notifications
    'recommendation_service.tasks.send_recommendation_notifications': {'queue': 'notifications'},
    
    # Tâches de monitoring
    'recommendation_service.tasks.monitor_recommendation_performance': {'queue': 'monitoring'},
}

# Configuration des priorités des tâches
CELERY_TASK_ANNOTATIONS = {
    # Priorité haute pour les recommandations en temps réel
    'recommendation_service.tasks.generate_user_recommendations': {
        'rate_limit': '100/m',
        'priority': 9,
        'time_limit': 300,  # 5 minutes
        'soft_time_limit': 240,  # 4 minutes
    },
    
    # Priorité moyenne pour les tâches par lots
    'recommendation_service.tasks.batch_generate_recommendations': {
        'rate_limit': '10/m',
        'priority': 5,
        'time_limit': 3600,  # 1 heure
        'soft_time_limit': 3300,  # 55 minutes
    },
    
    # Priorité basse pour les tâches de calcul intensif
    'recommendation_service.tasks.calculate_similarity_matrix': {
        'rate_limit': '1/h',
        'priority': 1,
        'time_limit': 7200,  # 2 heures
        'soft_time_limit': 6900,  # 1h55
    },
    
    # Configuration pour les autres tâches
    'recommendation_service.tasks.update_book_vectors': {
        'rate_limit': '5/m',
        'priority': 6,
        'time_limit': 1800,  # 30 minutes
    },
    
    'recommendation_service.tasks.update_trending_books': {
        'rate_limit': '10/m',
        'priority': 6,
        'time_limit': 900,  # 15 minutes
    },
    
    'recommendation_service.tasks.cleanup_old_data': {
        'rate_limit': '1/h',
        'priority': 2,
        'time_limit': 3600,  # 1 heure
    },
    
    'recommendation_service.tasks.send_recommendation_notifications': {
        'rate_limit': '20/m',
        'priority': 7,
        'time_limit': 1800,  # 30 minutes
    },
    
    'recommendation_service.tasks.generate_recommendation_analytics_report': {
        'rate_limit': '2/h',
        'priority': 4,
        'time_limit': 2400,  # 40 minutes
    },
}

# Configuration des retry policies
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minute
CELERY_TASK_MAX_RETRIES = 3

# Configuration spécifique pour les recommandations
RECOMMENDATION_TASK_CONFIG = {
    'default_algorithm': 'hybrid',
    'default_recommendation_count': 10,
    'cache_timeout': 3600,  # 1 heure
    'batch_size': 100,
    'similarity_threshold': 0.1,
    'trending_update_frequency': 'daily',
    'analytics_retention_days': 90,
    'notification_frequency': 'daily',
}

# Configuration des workers
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_DISABLE_RATE_LIMITS = False

# Configuration du monitoring
CELERY_SEND_TASK_EVENTS = True
CELERY_SEND_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True

# Configuration de la sérialisation
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Configuration du backend de résultats
CELERY_RESULT_BACKEND = getattr(settings, 'CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_RESULT_EXPIRES = 3600  # 1 heure

# Configuration du broker
CELERY_BROKER_URL = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Configuration de la timezone
CELERY_TIMEZONE = getattr(settings, 'TIME_ZONE', 'UTC')
CELERY_ENABLE_UTC = True

# Configuration des logs
CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Configuration pour le développement
if settings.DEBUG:
    CELERY_TASK_ALWAYS_EAGER = False
    CELERY_TASK_EAGER_PROPAGATES = True
    
    # Réduire les fréquences en développement
    CELERY_BEAT_SCHEDULE.update({
        'daily-maintenance': {
            'task': 'recommendation_service.tasks.daily_maintenance',
            'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes en dev
            'options': {'queue': 'recommendations'}
        },
        'update-trending-books-daily': {
            'task': 'recommendation_service.tasks.update_trending_books',
            'schedule': crontab(minute='*/15'),  # Toutes les 15 minutes en dev
            'options': {'queue': 'recommendations'}
        },
    })

# Fonction pour initialiser Celery avec cette configuration
def configure_celery(app):
    """Configurer Celery avec les paramètres du service de recommandations"""
    app.conf.update(
        beat_schedule=CELERY_BEAT_SCHEDULE,
        task_routes=CELERY_TASK_ROUTES,
        task_annotations=CELERY_TASK_ANNOTATIONS,
        worker_prefetch_multiplier=CELERY_WORKER_PREFETCH_MULTIPLIER,
        worker_max_tasks_per_child=CELERY_WORKER_MAX_TASKS_PER_CHILD,
        worker_disable_rate_limits=CELERY_WORKER_DISABLE_RATE_LIMITS,
        send_task_events=CELERY_SEND_TASK_EVENTS,
        send_events=CELERY_SEND_EVENTS,
        task_send_sent_event=CELERY_TASK_SEND_SENT_EVENT,
        task_serializer=CELERY_TASK_SERIALIZER,
        result_serializer=CELERY_RESULT_SERIALIZER,
        accept_content=CELERY_ACCEPT_CONTENT,
        result_backend=CELERY_RESULT_BACKEND,
        result_expires=CELERY_RESULT_EXPIRES,
        broker_url=CELERY_BROKER_URL,
        broker_connection_retry_on_startup=CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP,
        timezone=CELERY_TIMEZONE,
        enable_utc=CELERY_ENABLE_UTC,
        worker_log_format=CELERY_WORKER_LOG_FORMAT,
        worker_task_log_format=CELERY_WORKER_TASK_LOG_FORMAT,
        task_default_retry_delay=CELERY_TASK_DEFAULT_RETRY_DELAY,
        task_max_retries=CELERY_TASK_MAX_RETRIES,
    )
    
    if settings.DEBUG:
        app.conf.update(
            task_always_eager=CELERY_TASK_ALWAYS_EAGER,
            task_eager_propagates=CELERY_TASK_EAGER_PROPAGATES,
        )
    
    return app

# Configuration des queues pour différents environnements
QUEUE_CONFIGURATIONS = {
    'development': {
        'recommendations': {
            'exchange': 'recommendations',
            'exchange_type': 'direct',
            'routing_key': 'recommendations',
        },
        'heavy_computation': {
            'exchange': 'computation',
            'exchange_type': 'direct',
            'routing_key': 'heavy',
        },
    },
    'production': {
        'recommendations': {
            'exchange': 'recommendations',
            'exchange_type': 'direct',
            'routing_key': 'recommendations',
            'queue_arguments': {
                'x-max-priority': 10,
                'x-message-ttl': 3600000,  # 1 heure
            }
        },
        'heavy_computation': {
            'exchange': 'computation',
            'exchange_type': 'direct',
            'routing_key': 'heavy',
            'queue_arguments': {
                'x-max-priority': 5,
                'x-message-ttl': 7200000,  # 2 heures
            }
        },
        'analytics': {
            'exchange': 'analytics',
            'exchange_type': 'direct',
            'routing_key': 'analytics',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'exchange_type': 'direct',
            'routing_key': 'maintenance',
        },
        'notifications': {
            'exchange': 'notifications',
            'exchange_type': 'direct',
            'routing_key': 'notifications',
        },
        'monitoring': {
            'exchange': 'monitoring',
            'exchange_type': 'direct',
            'routing_key': 'monitoring',
        },
    }
}

# Fonction pour obtenir la configuration des queues selon l'environnement
def get_queue_config(environment='development'):
    """Obtenir la configuration des queues pour un environnement donné"""
    return QUEUE_CONFIGURATIONS.get(environment, QUEUE_CONFIGURATIONS['development'])