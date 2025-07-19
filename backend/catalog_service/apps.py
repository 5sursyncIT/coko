from django.apps import AppConfig


class CatalogServiceConfig(AppConfig):
    """Configuration de l'application catalog_service"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog_service'
    verbose_name = 'Service de Catalogue'
    
    def ready(self):
        """Méthode appelée quand l'application est prête"""
        import catalog_service.signals