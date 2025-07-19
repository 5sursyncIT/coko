"""
Adaptateurs pour découpler les services et faciliter la communication inter-services.
Ces adaptateurs fournissent une couche d'abstraction entre les services.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .interfaces import (
    BookServiceInterface, ReadingServiceInterface, 
    RecommendationServiceInterface, UserServiceInterface
)
from .events import publish_event, EventType

User = get_user_model()
logger = logging.getLogger(__name__)


class ServiceAdapterMixin:
    """Mixin pour les adaptateurs de service avec fonctionnalités communes"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 heure par défaut
    
    def get_cached_result(self, cache_key: str, fetch_func: callable, timeout: int = None) -> Any:
        """Utiliser le cache pour optimiser les appels de service"""
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        result = fetch_func()
        cache.set(cache_key, result, timeout or self.cache_timeout)
        return result
    
    def invalidate_cache_pattern(self, pattern: str):
        """Invalider les clés de cache correspondant à un pattern"""
        # Cette méthode devrait être implémentée selon le backend de cache utilisé
        try:
            cache.delete_many([key for key in cache._cache.keys() if pattern in key])
        except AttributeError:
            # Fallback pour les backends qui ne supportent pas _cache.keys()
            logger.warning(f"Impossible d'invalider le cache pour le pattern: {pattern}")


class BookServiceAdapter(ServiceAdapterMixin):
    """Adaptateur pour le service de livres avec cache et optimisations"""
    
    def __init__(self, book_service: BookServiceInterface):
        super().__init__()
        self.book_service = book_service
    
    def get_book_with_cache(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un livre avec mise en cache"""
        cache_key = f"book_data_{book_id}"
        return self.get_cached_result(
            cache_key,
            lambda: self.book_service.get_book_by_id(book_id)
        )
    
    def search_books_with_filters(
        self, 
        query: str, 
        filters: Dict[str, Any] = None, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Recherche de livres avec filtres et cache"""
        cache_key = f"book_search_{hash(str(query) + str(filters) + str(limit))}"
        return self.get_cached_result(
            cache_key,
            lambda: self.book_service.search_books(query, filters, limit),
            timeout=1800  # 30 minutes pour les recherches
        )
    
    def get_popular_books_by_context(
        self, 
        context: str = 'general', 
        limit: int = 10,
        exclude_ids: List[int] = None
    ) -> List[Dict[str, Any]]:
        """Obtenir des livres populaires selon le contexte"""
        cache_key = f"popular_books_{context}_{limit}"
        
        def fetch_popular():
            books = self.book_service.get_popular_books(limit, exclude_ids or [])
            # Ajouter le contexte aux données
            for book in books:
                book['recommendation_context'] = context
            return books
        
        return self.get_cached_result(cache_key, fetch_popular)
    
    def get_books_by_multiple_criteria(
        self, 
        categories: List[str] = None,
        authors: List[str] = None,
        limit: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Obtenir des livres selon plusieurs critères"""
        results = {
            'by_category': [],
            'by_author': [],
            'combined': []
        }
        
        if categories:
            results['by_category'] = self.book_service.get_books_by_category(
                categories, limit//2
            )
        
        if authors:
            results['by_author'] = self.book_service.get_books_by_author(
                authors, limit//2
            )
        
        # Combiner les résultats en évitant les doublons
        combined_books = {}
        for book in results['by_category'] + results['by_author']:
            if book['id'] not in combined_books:
                combined_books[book['id']] = book
        
        results['combined'] = list(combined_books.values())[:limit]
        return results


class ReadingServiceAdapter(ServiceAdapterMixin):
    """Adaptateur pour le service de lecture avec analytics"""
    
    def __init__(self, reading_service: ReadingServiceInterface):
        super().__init__()
        self.reading_service = reading_service
    
    def get_user_reading_profile(self, user_id: int) -> Dict[str, Any]:
        """Obtenir un profil de lecture complet de l'utilisateur"""
        cache_key = f"reading_profile_{user_id}"
        
        def fetch_profile():
            profile = {
                'current_books': self.reading_service.get_user_current_books(user_id),
                'completed_books': self.reading_service.get_user_completed_books(user_id, 20),
                'reading_history': self.reading_service.get_user_reading_history(user_id, 50),
                'bookmarks': self.reading_service.get_user_bookmarks(user_id),
                'statistics': self.reading_service.get_reading_statistics(user_id, 'monthly')
            }
            
            # Enrichir avec des métriques calculées
            profile['metrics'] = self._calculate_reading_metrics(profile)
            return profile
        
        return self.get_cached_result(cache_key, fetch_profile, timeout=1800)
    
    def get_reading_patterns(self, user_id: int) -> Dict[str, Any]:
        """Analyser les patterns de lecture de l'utilisateur"""
        reading_history = self.reading_service.get_user_reading_history(user_id, 100)
        
        patterns = {
            'preferred_reading_times': [],
            'average_session_duration': 0,
            'reading_frequency': 'unknown',
            'completion_rate': 0,
            'favorite_genres': [],
            'reading_speed': 'average'
        }
        
        if reading_history:
            # Analyser les patterns (implémentation simplifiée)
            total_sessions = len(reading_history)
            completed_sessions = len([s for s in reading_history if s['status'] == 'completed'])
            patterns['completion_rate'] = completed_sessions / total_sessions if total_sessions > 0 else 0
        
        return patterns
    
    def track_reading_interaction(
        self, 
        user_id: int, 
        book_id: int, 
        interaction_type: str,
        metadata: Dict[str, Any] = None
    ):
        """Suivre une interaction de lecture et publier l'événement"""
        
        # Vérifier si l'utilisateur a déjà lu ce livre
        has_read = self.reading_service.has_user_read_book(user_id, book_id)
        
        interaction_data = {
            'user_id': user_id,
            'book_id': book_id,
            'interaction_type': interaction_type,
            'has_read_before': has_read,
            'timestamp': timezone.now().isoformat()
        }
        
        if metadata:
            interaction_data.update(metadata)
        
        # Publier l'événement pour les autres services
        publish_event(
            EventType.USER_INTERACTION_RECORDED,
            interaction_data,
            user_id=user_id,
            source_service='reading_service_adapter'
        )
        
        # Invalider le cache du profil utilisateur
        self.invalidate_cache_pattern(f"reading_profile_{user_id}")
    
    def _calculate_reading_metrics(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculer des métriques de lecture avancées"""
        metrics = {
            'total_books_read': len(profile.get('completed_books', [])),
            'books_in_progress': len(profile.get('current_books', [])),
            'total_bookmarks': len(profile.get('bookmarks', [])),
            'reading_consistency': 0.0,
            'genre_diversity': 0.0
        }
        
        # Calculer d'autres métriques selon les besoins
        return metrics


class UserServiceAdapter(ServiceAdapterMixin):
    """Adaptateur pour le service utilisateur avec gestion des préférences"""
    
    def __init__(self, user_service: UserServiceInterface):
        super().__init__()
        self.user_service = user_service
    
    def get_enhanced_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Obtenir un profil utilisateur enrichi"""
        cache_key = f"enhanced_user_profile_{user_id}"
        
        def fetch_enhanced_profile():
            base_profile = self.user_service.get_user_profile(user_id)
            preferences = self.user_service.get_user_preferences(user_id)
            
            return {
                **base_profile,
                'preferences': preferences,
                'profile_completeness': self._calculate_profile_completeness(preferences),
                'recommendation_settings': preferences.get('recommendations', {}),
                'privacy_settings': preferences.get('privacy', {})
            }
        
        return self.get_cached_result(cache_key, fetch_enhanced_profile)
    
    def update_user_preferences_with_validation(
        self, 
        user_id: int, 
        preferences: Dict[str, Any]
    ) -> bool:
        """Mettre à jour les préférences avec validation"""
        
        # Valider les préférences
        validated_preferences = self._validate_preferences(preferences)
        
        if not validated_preferences:
            return False
        
        # Mettre à jour via le service
        success = self.user_service.update_user_preferences(user_id, validated_preferences)
        
        if success:
            # Invalider le cache
            self.invalidate_cache_pattern(f"enhanced_user_profile_{user_id}")
            
            # Publier l'événement
            publish_event(
                EventType.USER_PREFERENCES_UPDATED,
                {'updated_preferences': validated_preferences},
                user_id=user_id,
                source_service='user_service_adapter'
            )
        
        return success
    
    def _calculate_profile_completeness(self, preferences: Dict[str, Any]) -> float:
        """Calculer le pourcentage de complétude du profil"""
        required_fields = [
            'preferred_genres', 'preferred_authors', 'reading_frequency',
            'notification_preferences', 'privacy_level'
        ]
        
        completed_fields = sum(1 for field in required_fields if preferences.get(field))
        return completed_fields / len(required_fields)
    
    def _validate_preferences(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Valider les préférences utilisateur"""
        
        validated = {}
        
        # Valider les genres préférés
        if 'preferred_genres' in preferences:
            genres = preferences['preferred_genres']
            if isinstance(genres, list) and all(isinstance(g, str) for g in genres):
                validated['preferred_genres'] = genres[:10]  # Limiter à 10 genres
        
        # Valider les auteurs préférés
        if 'preferred_authors' in preferences:
            authors = preferences['preferred_authors']
            if isinstance(authors, list) and all(isinstance(a, str) for a in authors):
                validated['preferred_authors'] = authors[:20]  # Limiter à 20 auteurs
        
        # Valider la fréquence de lecture
        valid_frequencies = ['daily', 'weekly', 'monthly', 'occasionally']
        if preferences.get('reading_frequency') in valid_frequencies:
            validated['reading_frequency'] = preferences['reading_frequency']
        
        return validated if validated else None


class RecommendationServiceAdapter(ServiceAdapterMixin):
    """Adaptateur pour le service de recommandations avec optimisations"""
    
    def __init__(self, recommendation_service: RecommendationServiceInterface):
        super().__init__()
        self.recommendation_service = recommendation_service
    
    def get_personalized_recommendations_with_context(
        self,
        user_id: int,
        algorithm: str = 'hybrid',
        count: int = 10,
        context: str = 'general',
        refresh_cache: bool = False
    ) -> Dict[str, Any]:
        """Obtenir des recommandations personnalisées avec contexte"""
        
        cache_key = f"recommendations_{user_id}_{algorithm}_{count}_{context}"
        
        if refresh_cache:
            cache.delete(cache_key)
        
        def fetch_recommendations():
            return self.recommendation_service.get_personalized_recommendations(
                user_id, algorithm, count, context
            )
        
        return self.get_cached_result(
            cache_key, 
            fetch_recommendations, 
            timeout=3600  # 1 heure pour les recommandations
        )
    
    def get_similar_books_with_explanation(
        self, 
        book_id: int, 
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtenir des livres similaires avec explications détaillées"""
        
        similar_books = self.recommendation_service.get_similar_books(book_id, count)
        
        # Enrichir avec des explications
        for book in similar_books:
            book['similarity_explanation'] = self._generate_similarity_explanation(
                book_id, book
            )
        
        return similar_books
    
    def record_recommendation_interaction(
        self,
        user_id: int,
        book_id: int,
        interaction_type: str,
        recommendation_context: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Enregistrer une interaction avec les recommandations"""
        
        interaction_metadata = {
            'recommendation_context': recommendation_context,
            'timestamp': timezone.now().isoformat()
        }
        
        if metadata:
            interaction_metadata.update(metadata)
        
        # Enregistrer via le service
        self.recommendation_service.record_user_interaction(
            user_id, book_id, interaction_type, interaction_metadata
        )
        
        # Invalider le cache des recommandations
        self.invalidate_cache_pattern(f"recommendations_{user_id}")
    
    def _generate_similarity_explanation(
        self, 
        source_book_id: int, 
        similar_book: Dict[str, Any]
    ) -> str:
        """Générer une explication de similarité"""
        
        reasons = similar_book.get('similarity_reasons', [])
        score = similar_book.get('similarity_score', 0)
        
        if score > 0.8:
            strength = "très similaire"
        elif score > 0.6:
            strength = "similaire"
        else:
            strength = "quelque peu similaire"
        
        explanation = f"Ce livre est {strength} car : {', '.join(reasons)}"
        return explanation


# Factory pour créer les adaptateurs avec les services appropriés
class ServiceAdapterFactory:
    """Factory pour créer les adaptateurs de service"""
    
    @staticmethod
    def create_book_adapter(book_service: BookServiceInterface) -> BookServiceAdapter:
        return BookServiceAdapter(book_service)
    
    @staticmethod
    def create_reading_adapter(reading_service: ReadingServiceInterface) -> ReadingServiceAdapter:
        return ReadingServiceAdapter(reading_service)
    
    @staticmethod
    def create_user_adapter(user_service: UserServiceInterface) -> UserServiceAdapter:
        return UserServiceAdapter(user_service)
    
    @staticmethod
    def create_recommendation_adapter(
        recommendation_service: RecommendationServiceInterface
    ) -> RecommendationServiceAdapter:
        return RecommendationServiceAdapter(recommendation_service)