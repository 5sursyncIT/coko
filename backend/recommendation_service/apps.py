from django.apps import AppConfig


class RecommendationServiceConfig(AppConfig):
    """Configuration de l'application recommendation_service"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recommendation_service'
    verbose_name = 'Service de Recommandations'
    
    def ready(self):
        """Méthode appelée quand l'application est prête"""
        # Importer les signaux
        try:
            from . import signals
        except ImportError:
            pass