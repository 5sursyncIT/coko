"""
Configuration de l'application shared_models
Inclut le dashboard unifié et les fonctionnalités back-office améliorées
"""

from django.apps import AppConfig


class SharedModelsConfig(AppConfig):
    """Configuration pour shared_models avec fonctionnalités étendues"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shared_models'
    verbose_name = 'Modèles Partagés et Dashboard'
    
    def ready(self):
        """Initialisation de l'application"""
        # Importer les signaux si nécessaire
        try:
            from . import signals
        except ImportError:
            pass
        
        # Enregistrer les tâches Celery si disponible
        try:
            from . import tasks
        except ImportError:
            pass
        
        # Configurer l'analyseur de logs de sécurité
        self.setup_security_analyzer()
    
    def setup_security_analyzer(self):
        """Configure l'analyseur automatique de logs de sécurité"""
        try:
            from django.conf import settings
            
            # Programmer l'analyse automatique si Celery est disponible
            if hasattr(settings, 'CELERY_BROKER_URL'):
                from celery import current_app
                from datetime import timedelta
                
                # Programmer l'analyse toutes les heures
                current_app.conf.beat_schedule.update({
                    'analyze-security-logs': {
                        'task': 'shared_models.tasks.analyze_security_logs',
                        'schedule': timedelta(hours=1),
                    },
                    'cleanup-old-audit-logs': {
                        'task': 'shared_models.tasks.cleanup_old_audit_logs',
                        'schedule': timedelta(days=1),
                    },
                    'generate-financial-reports': {
                        'task': 'shared_models.tasks.generate_daily_financial_report',
                        'schedule': timedelta(hours=6),
                    }
                })
                
        except ImportError:
            # Celery n'est pas disponible, passer
            pass