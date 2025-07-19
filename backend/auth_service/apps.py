from django.apps import AppConfig


class AuthServiceConfig(AppConfig):
    """Configuration de l'application de service d'authentification"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_service'
    verbose_name = "Service d'Authentification"
    
    def ready(self):
        """Méthode appelée quand l'application est prête"""
        # Importer les signaux
        import auth_service.signals