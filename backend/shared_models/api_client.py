"""
Client API pour la communication inter-services.
Fournit une interface unifiée pour communiquer avec les différents services.
"""

import requests
import uuid
from typing import Dict, List, Optional, Any, Union
from django.conf import settings
from django.core.cache import cache
import logging

from .services import service_registry

logger = logging.getLogger(__name__)


class ServiceAPIClient:
    """
    Client API générique pour la communication inter-services.
    """
    
    def __init__(self, service_name: str, base_url: Optional[str] = None):
        self.service_name = service_name
        self.base_url = base_url or service_registry.get_service_endpoint(service_name, '')
        self.session = requests.Session()
        
        # Configuration par défaut
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        
        # Timeout par défaut
        self.timeout = getattr(settings, 'INTER_SERVICE_TIMEOUT', 30)
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """
        Effectue une requête GET vers un service.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling {self.service_name} GET {endpoint}: {e}")
            raise ServiceAPIError(f"Failed to call {self.service_name}: {e}")
    
    def post(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """
        Effectue une requête POST vers un service.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.post(
                url,
                json=data,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling {self.service_name} POST {endpoint}: {e}")
            raise ServiceAPIError(f"Failed to call {self.service_name}: {e}")
    
    def put(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """
        Effectue une requête PUT vers un service.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.put(
                url,
                json=data,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling {self.service_name} PUT {endpoint}: {e}")
            raise ServiceAPIError(f"Failed to call {self.service_name}: {e}")
    
    def delete(self, endpoint: str, **kwargs) -> bool:
        """
        Effectue une requête DELETE vers un service.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.delete(
                url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling {self.service_name} DELETE {endpoint}: {e}")
            raise ServiceAPIError(f"Failed to call {self.service_name}: {e}")


class CatalogServiceClient(ServiceAPIClient):
    """
    Client spécialisé pour le service catalog.
    """
    
    def __init__(self):
        super().__init__('catalog_service')
    
    def get_book(self, book_uuid: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un livre par UUID.
        """
        cache_key = f"book_details_{book_uuid}"
        cached_book = cache.get(cache_key)
        
        if cached_book:
            return cached_book
        
        try:
            book_data = self.get(f"books/{book_uuid}/")
            
            # Cache pendant 1 heure
            cache.set(cache_key, book_data, 3600)
            
            return book_data
            
        except ServiceAPIError as e:
            logger.warning(f"Failed to get book {book_uuid}: {e}")
            return None
    
    def get_books_batch(self, book_uuids: List[Union[str, uuid.UUID]]) -> Dict[str, Dict[str, Any]]:
        """
        Récupère plusieurs livres en une seule requête.
        """
        if not book_uuids:
            return {}
        
        # Vérifier le cache d'abord
        cached_books = {}
        missing_uuids = []
        
        for book_uuid in book_uuids:
            cache_key = f"book_details_{book_uuid}"
            cached_book = cache.get(cache_key)
            if cached_book:
                cached_books[str(book_uuid)] = cached_book
            else:
                missing_uuids.append(str(book_uuid))
        
        # Récupérer les livres manquants
        if missing_uuids:
            try:
                response = self.post("books/batch/", {
                    "book_uuids": missing_uuids
                })
                
                fetched_books = response.get('books', {})
                
                # Mettre en cache les nouveaux livres
                for book_uuid, book_data in fetched_books.items():
                    cache_key = f"book_details_{book_uuid}"
                    cache.set(cache_key, book_data, 3600)
                    cached_books[book_uuid] = book_data
                    
            except ServiceAPIError as e:
                logger.warning(f"Failed to get books batch: {e}")
        
        return cached_books
    
    def get_author(self, author_uuid: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un auteur par UUID.
        """
        cache_key = f"author_details_{author_uuid}"
        cached_author = cache.get(cache_key)
        
        if cached_author:
            return cached_author
        
        try:
            author_data = self.get(f"authors/{author_uuid}/")
            
            # Cache pendant 1 heure
            cache.set(cache_key, author_data, 3600)
            
            return author_data
            
        except ServiceAPIError as e:
            logger.warning(f"Failed to get author {author_uuid}: {e}")
            return None
    
    def get_category(self, category_uuid: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'une catégorie par UUID.
        """
        cache_key = f"category_details_{category_uuid}"
        cached_category = cache.get(cache_key)
        
        if cached_category:
            return cached_category
        
        try:
            category_data = self.get(f"categories/{category_uuid}/")
            
            # Cache pendant 1 heure
            cache.set(cache_key, category_data, 3600)
            
            return category_data
            
        except ServiceAPIError as e:
            logger.warning(f"Failed to get category {category_uuid}: {e}")
            return None
    
    def search_books(self, query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Recherche de livres avec filtres.
        """
        params = {'q': query}
        if filters:
            params.update(filters)
        
        try:
            return self.get("books/search/", params=params)
        except ServiceAPIError as e:
            logger.error(f"Book search failed: {e}")
            return {'results': [], 'count': 0}


class AuthServiceClient(ServiceAPIClient):
    """
    Client spécialisé pour le service auth.
    """
    
    def __init__(self):
        super().__init__('auth_service')
    
    def get_user(self, user_uuid: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un utilisateur par UUID.
        """
        cache_key = f"user_details_{user_uuid}"
        cached_user = cache.get(cache_key)
        
        if cached_user:
            return cached_user
        
        try:
            user_data = self.get(f"users/{user_uuid}/")
            
            # Cache pendant 30 minutes
            cache.set(cache_key, user_data, 1800)
            
            return user_data
            
        except ServiceAPIError as e:
            logger.warning(f"Failed to get user {user_uuid}: {e}")
            return None
    
    def get_user_profile(self, user_uuid: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """
        Récupère le profil d'un utilisateur.
        """
        try:
            return self.get(f"users/{user_uuid}/profile/")
        except ServiceAPIError as e:
            logger.warning(f"Failed to get user profile {user_uuid}: {e}")
            return None


class ReadingServiceClient(ServiceAPIClient):
    """
    Client spécialisé pour le service reading.
    """
    
    def __init__(self):
        super().__init__('reading_service')
    
    def get_user_reading_history(
        self, 
        user_uuid: Union[str, uuid.UUID],
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Récupère l'historique de lecture d'un utilisateur.
        """
        try:
            response = self.get(f"users/{user_uuid}/reading-history/", {
                'limit': limit
            })
            return response.get('results', [])
        except ServiceAPIError as e:
            logger.warning(f"Failed to get reading history for user {user_uuid}: {e}")
            return []
    
    def get_reading_session(self, session_uuid: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """
        Récupère une session de lecture.
        """
        try:
            return self.get(f"sessions/{session_uuid}/")
        except ServiceAPIError as e:
            logger.warning(f"Failed to get reading session {session_uuid}: {e}")
            return None
    
    def create_reading_session(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Crée une nouvelle session de lecture.
        """
        try:
            return self.post("sessions/", session_data)
        except ServiceAPIError as e:
            logger.error(f"Failed to create reading session: {e}")
            return None


class RecommendationServiceClient(ServiceAPIClient):
    """
    Client spécialisé pour le service recommendation.
    """
    
    def __init__(self):
        super().__init__('recommendation_service')
    
    def get_recommendations(
        self, 
        user_uuid: Union[str, uuid.UUID],
        algorithm: str = 'hybrid',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Récupère les recommandations pour un utilisateur.
        """
        try:
            response = self.get(f"users/{user_uuid}/recommendations/", {
                'algorithm': algorithm,
                'limit': limit
            })
            return response.get('recommendations', [])
        except ServiceAPIError as e:
            logger.warning(f"Failed to get recommendations for user {user_uuid}: {e}")
            return []
    
    def record_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """
        Enregistre une interaction utilisateur.
        """
        try:
            self.post("interactions/", interaction_data)
            return True
        except ServiceAPIError as e:
            logger.error(f"Failed to record interaction: {e}")
            return False


class ServiceAPIError(Exception):
    """
    Exception pour les erreurs d'API inter-services.
    """
    pass


# Instances singleton des clients
catalog_client = CatalogServiceClient()
auth_client = AuthServiceClient()
reading_client = ReadingServiceClient()
recommendation_client = RecommendationServiceClient()


class ServiceClientRegistry:
    """
    Registry pour accéder aux clients de services.
    """
    
    def __init__(self):
        self._clients = {
            'catalog': catalog_client,
            'auth': auth_client,
            'reading': reading_client,
            'recommendation': recommendation_client,
        }
    
    def get_client(self, service_name: str) -> ServiceAPIClient:
        """
        Récupère un client de service par nom.
        """
        client = self._clients.get(service_name)
        if not client:
            raise ValueError(f"Unknown service: {service_name}")
        return client
    
    def register_client(self, service_name: str, client: ServiceAPIClient):
        """
        Enregistre un nouveau client de service.
        """
        self._clients[service_name] = client


# Instance singleton du registry
service_clients = ServiceClientRegistry()