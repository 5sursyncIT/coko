from django.apps import AppConfig


class ReadingServiceConfig(AppConfig):
    """Configuration de l'application service de lecture"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reading_service'
    verbose_name = 'Service de Lecture'
    
    def ready(self):
        """Méthode appelée quand l'application est prête"""
        import reading_service.signals