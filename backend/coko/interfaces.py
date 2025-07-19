"""
Interfaces abstraites pour découpler les services
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from django.contrib.auth import get_user_model

User = get_user_model()


class BookServiceInterface(ABC):
    """Interface pour les opérations sur les livres"""
    
    @abstractmethod
    def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un livre par son ID"""
        pass
    
    @abstractmethod
    def get_books_by_category(self, category_names: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer des livres par catégorie"""
        pass
    
    @abstractmethod
    def get_books_by_author(self, author_names: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer des livres par auteur"""
        pass
    
    @abstractmethod
    def get_popular_books(self, limit: int = 10, exclude_ids: List[int] = None) -> List[Dict[str, Any]]:
        """Récupérer les livres populaires"""
        pass
    
    @abstractmethod
    def search_books(self, query: str, filters: Dict[str, Any] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Rechercher des livres"""
        pass
    
    @abstractmethod
    def get_book_categories(self, book_id: int) -> List[str]:
        """Récupérer les catégories d'un livre"""
        pass
    
    @abstractmethod
    def get_book_authors(self, book_id: int) -> List[str]:
        """Récupérer les auteurs d'un livre"""
        pass


class ReadingServiceInterface(ABC):
    """Interface pour les opérations de lecture"""
    
    @abstractmethod
    def get_user_reading_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupérer l'historique de lecture d'un utilisateur"""
        pass
    
    @abstractmethod
    def get_user_current_books(self, user_id: int) -> List[Dict[str, Any]]:
        """Récupérer les livres en cours de lecture"""
        pass
    
    @abstractmethod
    def get_user_completed_books(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupérer les livres terminés par l'utilisateur"""
        pass
    
    @abstractmethod
    def get_user_bookmarks(self, user_id: int, book_id: int = None) -> List[Dict[str, Any]]:
        """Récupérer les signets d'un utilisateur"""
        pass
    
    @abstractmethod
    def get_reading_statistics(self, user_id: int, period: str = 'monthly') -> Dict[str, Any]:
        """Récupérer les statistiques de lecture"""
        pass
    
    @abstractmethod
    def has_user_read_book(self, user_id: int, book_id: int) -> bool:
        """Vérifier si un utilisateur a lu un livre"""
        pass


class RecommendationServiceInterface(ABC):
    """Interface pour les opérations de recommandation"""
    
    @abstractmethod
    def get_personalized_recommendations(self, user_id: int, algorithm: str = 'hybrid', 
                                       count: int = 10, context: str = 'general') -> Dict[str, Any]:
        """Obtenir des recommandations personnalisées"""
        pass
    
    @abstractmethod
    def get_similar_books(self, book_id: int, count: int = 10) -> List[Dict[str, Any]]:
        """Obtenir des livres similaires"""
        pass
    
    @abstractmethod
    def record_user_interaction(self, user_id: int, book_id: int, 
                              interaction_type: str, metadata: Dict[str, Any] = None) -> None:
        """Enregistrer une interaction utilisateur"""
        pass
    
    @abstractmethod
    def get_trending_books(self, period: str = 'week', trend_type: str = 'overall', 
                         limit: int = 20) -> List[Dict[str, Any]]:
        """Obtenir les livres en tendance"""
        pass


class UserServiceInterface(ABC):
    """Interface pour les opérations utilisateur"""
    
    @abstractmethod
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Récupérer les préférences utilisateur"""
        pass
    
    @abstractmethod
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Mettre à jour les préférences utilisateur"""
        pass
    
    @abstractmethod
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Récupérer le profil utilisateur"""
        pass


class EventServiceInterface(ABC):
    """Interface pour le système d'événements"""
    
    @abstractmethod
    def publish_event(self, event_type: str, data: Dict[str, Any], user_id: int = None) -> None:
        """Publier un événement"""
        pass
    
    @abstractmethod
    def subscribe_to_event(self, event_type: str, handler_function: callable) -> None:
        """S'abonner à un type d'événement"""
        pass


class ServiceCommunicationInterface(ABC):
    """Interface pour la communication inter-services"""
    
    @abstractmethod
    def call_service(self, service_name: str, endpoint: str, method: str = 'GET', 
                    data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Appeler un autre service"""
        pass
    
    @abstractmethod
    def register_service_endpoint(self, service_name: str, endpoint: str, url: str) -> None:
        """Enregistrer un endpoint de service"""
        pass
    
    @abstractmethod
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Obtenir l'état de santé d'un service"""
        pass


class CacheServiceInterface(ABC):
    """Interface pour le service de cache"""
    
    @abstractmethod
    def get(self, key: str) -> Any:
        """Récupérer une valeur du cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: int = None) -> bool:
        """Stocker une valeur dans le cache"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Supprimer une clé du cache"""
        pass
    
    @abstractmethod
    def clear_pattern(self, pattern: str) -> int:
        """Supprimer toutes les clés correspondant à un pattern"""
        pass