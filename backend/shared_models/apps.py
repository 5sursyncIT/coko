from django.apps import AppConfig


class SharedModelsConfig(AppConfig):
    """Configuration pour l'application shared_models"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shared_models'
    verbose_name = 'Modèles Partagés'
    
    def ready(self):
        """Initialisation de l'application"""
        pass