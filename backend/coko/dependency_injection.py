"""
Container d'injection de dépendances pour découpler les services.
Utilise le pattern Dependency Injection pour gérer les dépendances entre services.
"""

import logging
from typing import Dict, Any, Type, TypeVar, Optional, Callable
from django.conf import settings
from django.core.cache import cache

from .interfaces import (
    BookServiceInterface, ReadingServiceInterface, 
    RecommendationServiceInterface, UserServiceInterface,
    EventServiceInterface, ServiceCommunicationInterface, CacheServiceInterface
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceContainer:
    """Container pour l'injection de dépendances des services"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._interfaces: Dict[Type, str] = {}
    
    def register_singleton(self, interface: Type[T], implementation: T, name: str = None) -> None:
        """Enregistrer un service singleton"""
        service_name = name or interface.__name__
        self._singletons[service_name] = implementation
        self._interfaces[interface] = service_name
        logger.info(f"Service singleton enregistré: {service_name}")
    
    def register_transient(self, interface: Type[T], factory: Callable[[], T], name: str = None) -> None:
        """Enregistrer un service transient avec factory"""
        service_name = name or interface.__name__
        self._factories[service_name] = factory
        self._interfaces[interface] = service_name
        logger.info(f"Service transient enregistré: {service_name}")
    
    def register_scoped(self, interface: Type[T], implementation: T, scope: str = 'request', name: str = None) -> None:
        """Enregistrer un service avec scope (request, session, etc.)"""
        service_name = name or interface.__name__
        scoped_key = f"{service_name}_{scope}"
        self._services[scoped_key] = implementation
        self._interfaces[interface] = scoped_key
        logger.info(f"Service avec scope '{scope}' enregistré: {service_name}")
    
    def get_service(self, interface: Type[T], name: str = None) -> T:
        """Récupérer un service par interface"""
        service_name = name or self._interfaces.get(interface)
        
        if not service_name:
            raise ValueError(f"Aucun service enregistré pour l'interface: {interface}")
        
        # Vérifier les singletons d'abord
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Vérifier les factories
        if service_name in self._factories:
            return self._factories[service_name]()
        
        # Vérifier les services avec scope
        for scoped_key in self._services:
            if scoped_key.startswith(service_name):
                return self._services[scoped_key]
        
        raise ValueError(f"Service non trouvé: {service_name}")
    
    def has_service(self, interface: Type[T], name: str = None) -> bool:
        """Vérifier si un service est enregistré"""
        service_name = name or self._interfaces.get(interface)
        return (service_name in self._singletons or 
                service_name in self._factories or
                any(key.startswith(service_name or '') for key in self._services))
    
    def clear_scoped_services(self, scope: str = 'request') -> None:
        """Nettoyer les services avec un scope spécifique"""
        keys_to_remove = [key for key in self._services if key.endswith(f"_{scope}")]
        for key in keys_to_remove:
            del self._services[key]
    
    def get_all_services(self) -> Dict[str, Any]:
        """Obtenir tous les services enregistrés (pour debug)"""
        all_services = {}
        all_services.update(self._singletons)
        all_services.update({name: factory() for name, factory in self._factories.items()})
        all_services.update(self._services)
        return all_services


class ServiceRegistry:
    """Registry pour découvrir et configurer les services automatiquement"""
    
    def __init__(self, container: ServiceContainer):
        self.container = container
        self._service_configs = {}
    
    def load_service_config(self, config_path: str = None) -> None:
        """Charger la configuration des services"""
        # Configuration par défaut
        default_config = {
            'services': {
                'book_service': {
                    'interface': 'BookServiceInterface',
                    'implementation': 'coko.services.BookService',
                    'type': 'singleton'
                },
                'reading_service': {
                    'interface': 'ReadingServiceInterface', 
                    'implementation': 'coko.services.ReadingService',
                    'type': 'singleton'
                },
                'cache_service': {
                    'interface': 'CacheServiceInterface',
                    'implementation': 'coko.services.DjangoCacheService',
                    'type': 'singleton'
                }
            }
        }
        
        # Utiliser la config Django si disponible
        service_config = getattr(settings, 'SERVICE_CONFIGURATION', default_config)
        self._service_configs = service_config.get('services', {})
    
    def auto_register_services(self) -> None:
        """Enregistrer automatiquement les services selon la configuration"""
        for service_name, config in self._service_configs.items():
            try:
                interface_name = config['interface']
                implementation_path = config['implementation']
                service_type = config.get('type', 'singleton')
                
                # Importer l'interface et l'implémentation dynamiquement
                interface = self._import_class(f"coko.interfaces.{interface_name}")
                implementation = self._import_class(implementation_path)
                
                # Créer l'instance
                instance = implementation()
                
                # Enregistrer selon le type
                if service_type == 'singleton':
                    self.container.register_singleton(interface, instance, service_name)
                elif service_type == 'transient':
                    self.container.register_transient(interface, lambda: implementation(), service_name)
                
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement du service {service_name}: {e}")
    
    def _import_class(self, class_path: str) -> Type:
        """Importer une classe dynamiquement"""
        module_path, class_name = class_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)


class ServiceMiddleware:
    """Middleware pour gérer les services avec scope 'request'"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.container = get_service_container()
    
    def __call__(self, request):
        # Configurer les services pour cette requête
        self._setup_request_services(request)
        
        response = self.get_response(request)
        
        # Nettoyer les services avec scope 'request'
        self.container.clear_scoped_services('request')
        
        return response
    
    def _setup_request_services(self, request):
        """Configurer les services spécifiques à la requête"""
        # Exemple: service d'authentification avec le contexte de la requête
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Configuration spéciale pour les utilisateurs authentifiés
            pass


class ServiceProxy:
    """Proxy pour les services avec fonctionnalités avancées (cache, retry, etc.)"""
    
    def __init__(self, service: Any, service_name: str):
        self._service = service
        self._service_name = service_name
        self._call_count = 0
    
    def __getattr__(self, name):
        """Intercepter les appels de méthodes"""
        attr = getattr(self._service, name)
        
        if callable(attr):
            return self._wrap_method(attr, name)
        return attr
    
    def _wrap_method(self, method: Callable, method_name: str) -> Callable:
        """Wrapper pour les méthodes avec logging et métriques"""
        def wrapper(*args, **kwargs):
            self._call_count += 1
            start_time = timezone.now()
            
            try:
                logger.debug(f"Appel {self._service_name}.{method_name} - #{self._call_count}")
                result = method(*args, **kwargs)
                
                # Métriques de performance
                duration = (timezone.now() - start_time).total_seconds()
                if duration > 1.0:  # Log les appels lents
                    logger.warning(f"Appel lent: {self._service_name}.{method_name} - {duration:.2f}s")
                
                return result
                
            except Exception as e:
                logger.error(f"Erreur dans {self._service_name}.{method_name}: {e}")
                raise
        
        return wrapper


# Instance globale du container
_service_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """Obtenir l'instance globale du container"""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
        _initialize_default_services()
    return _service_container


def _initialize_default_services():
    """Initialiser les services par défaut"""
    container = _service_container
    
    try:
        # Importer et enregistrer les services de base
        from .services import BookService, ReadingService
        
        container.register_singleton(BookServiceInterface, BookService())
        container.register_singleton(ReadingServiceInterface, ReadingService())
        
        logger.info("Services par défaut initialisés")
        
    except ImportError as e:
        logger.error(f"Erreur lors de l'initialisation des services: {e}")


def inject_service(interface: Type[T], name: str = None) -> T:
    """Decorator/fonction pour injecter un service"""
    return get_service_container().get_service(interface, name)


def service_required(interface: Type[T], name: str = None):
    """Decorator pour injecter automatiquement un service dans une méthode"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            service = inject_service(interface, name)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator


# Configuration par défaut des services
DEFAULT_SERVICE_CONFIG = {
    'services': {
        'book_service': {
            'interface': 'BookServiceInterface',
            'implementation': 'coko.services.BookService',
            'type': 'singleton',
            'config': {
                'cache_timeout': 3600,
                'enable_search_cache': True
            }
        },
        'reading_service': {
            'interface': 'ReadingServiceInterface',
            'implementation': 'coko.services.ReadingService', 
            'type': 'singleton',
            'config': {
                'track_analytics': True,
                'cache_user_data': True
            }
        }
    },
    'middleware': {
        'enable_service_middleware': True,
        'enable_service_proxy': False,
        'log_service_calls': True
    }
}