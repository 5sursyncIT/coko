"""
Implémentations concrètes des interfaces de service
"""
import logging
from typing import Dict, List, Any, Optional
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q, Count, Avg, F

from .interfaces import (
    BookServiceInterface, ReadingServiceInterface, 
    RecommendationServiceInterface, UserServiceInterface
)
from .events import publish_event, EventType

User = get_user_model()
logger = logging.getLogger(__name__)


class BookService(BookServiceInterface):
    """Service pour les opérations sur les livres"""
    
    def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer un livre par son ID"""
        try:
            from catalog_service.models import Book
            
            cache_key = f"book_{book_id}"
            cached_book = cache.get(cache_key)
            if cached_book:
                return cached_book
            
            book = Book.objects.select_related().prefetch_related(
                'authors', 'categories'
            ).get(id=book_id, is_active=True)
            
            book_data = {
                'id': book.id,
                'title': book.title,
                'slug': book.slug,
                'description': book.description,
                'authors': [{'id': author.id, 'name': author.name} for author in book.authors.all()],
                'categories': [{'id': cat.id, 'name': cat.name} for cat in book.categories.all()],
                'cover_image': book.cover_image.url if book.cover_image else None,
                'average_rating': book.average_rating,
                'publication_date': book.publication_date,
                'language': book.language,
                'is_active': book.is_active
            }
            
            cache.set(cache_key, book_data, 3600)  # Cache 1 heure
            return book_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du livre {book_id}: {str(e)}")
            return None
    
    def get_books_by_category(self, category_names: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer des livres par catégorie"""
        try:
            from catalog_service.models import Book
            
            books = Book.objects.filter(
                categories__name__in=category_names,
                is_active=True
            ).select_related().prefetch_related(
                'authors', 'categories'
            ).distinct()[:limit]
            
            return [self._serialize_book(book) for book in books]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des livres par catégorie: {str(e)}")
            return []
    
    def get_books_by_author(self, author_names: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer des livres par auteur"""
        try:
            from catalog_service.models import Book
            
            books = Book.objects.filter(
                authors__name__in=author_names,
                is_active=True
            ).select_related().prefetch_related(
                'authors', 'categories'
            ).distinct()[:limit]
            
            return [self._serialize_book(book) for book in books]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des livres par auteur: {str(e)}")
            return []
    
    def get_popular_books(self, limit: int = 10, exclude_ids: List[int] = None) -> List[Dict[str, Any]]:
        """Récupérer les livres populaires"""
        try:
            from catalog_service.models import Book
            
            queryset = Book.objects.filter(is_active=True)
            
            if exclude_ids:
                queryset = queryset.exclude(id__in=exclude_ids)
            
            books = queryset.annotate(
                popularity_score=(
                    F('view_count') * 0.3 +
                    F('download_count') * 0.4 +
                    F('average_rating') * F('rating_count') * 0.3
                )
            ).order_by('-popularity_score')[:limit]
            
            return [self._serialize_book(book) for book in books]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des livres populaires: {str(e)}")
            return []
    
    def search_books(self, query: str, filters: Dict[str, Any] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Rechercher des livres"""
        try:
            from catalog_service.models import Book
            
            queryset = Book.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(authors__name__icontains=query),
                is_active=True
            ).distinct()
            
            if filters:
                if 'categories' in filters:
                    queryset = queryset.filter(categories__name__in=filters['categories'])
                if 'language' in filters:
                    queryset = queryset.filter(language=filters['language'])
                if 'min_rating' in filters:
                    queryset = queryset.filter(average_rating__gte=filters['min_rating'])
            
            books = queryset.select_related().prefetch_related(
                'authors', 'categories'
            )[:limit]
            
            return [self._serialize_book(book) for book in books]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de livres: {str(e)}")
            return []
    
    def get_book_categories(self, book_id: int) -> List[str]:
        """Récupérer les catégories d'un livre"""
        book_data = self.get_book_by_id(book_id)
        if book_data:
            return [cat['name'] for cat in book_data.get('categories', [])]
        return []
    
    def get_book_authors(self, book_id: int) -> List[str]:
        """Récupérer les auteurs d'un livre"""
        book_data = self.get_book_by_id(book_id)
        if book_data:
            return [author['name'] for author in book_data.get('authors', [])]
        return []
    
    def _serialize_book(self, book) -> Dict[str, Any]:
        """Sérialiser un objet Book"""
        return {
            'id': book.id,
            'title': book.title,
            'slug': book.slug,
            'authors': [author.name for author in book.authors.all()],
            'categories': [cat.name for cat in book.categories.all()],
            'cover_image': book.cover_image.url if book.cover_image else None,
            'average_rating': book.average_rating,
            'publication_date': book.publication_date,
            'language': book.language
        }


class ReadingService(ReadingServiceInterface):
    """Service pour les opérations de lecture"""
    
    def get_user_reading_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupérer l'historique de lecture d'un utilisateur"""
        try:
            from reading_service.models import ReadingSession
            
            sessions = ReadingSession.objects.filter(
                user_id=user_id
            ).select_related('book').order_by('-last_activity')[:limit]
            
            return [self._serialize_reading_session(session) for session in sessions]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}")
            return []
    
    def get_user_current_books(self, user_id: int) -> List[Dict[str, Any]]:
        """Récupérer les livres en cours de lecture"""
        try:
            from reading_service.models import ReadingSession
            
            sessions = ReadingSession.objects.filter(
                user_id=user_id,
                status='active'
            ).select_related('book')
            
            return [self._serialize_reading_session(session) for session in sessions]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des livres en cours: {str(e)}")
            return []
    
    def get_user_completed_books(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupérer les livres terminés par l'utilisateur"""
        try:
            from reading_service.models import ReadingSession
            
            sessions = ReadingSession.objects.filter(
                user_id=user_id,
                status='completed'
            ).select_related('book').order_by('-end_time')[:limit]
            
            return [self._serialize_reading_session(session) for session in sessions]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des livres terminés: {str(e)}")
            return []
    
    def get_user_bookmarks(self, user_id: int, book_id: int = None) -> List[Dict[str, Any]]:
        """Récupérer les signets d'un utilisateur"""
        try:
            from reading_service.models import Bookmark
            
            queryset = Bookmark.objects.filter(user_id=user_id)
            
            if book_id:
                queryset = queryset.filter(book_id=book_id)
            
            bookmarks = queryset.select_related('book').order_by('-created_at')
            
            return [self._serialize_bookmark(bookmark) for bookmark in bookmarks]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des signets: {str(e)}")
            return []
    
    def get_reading_statistics(self, user_id: int, period: str = 'monthly') -> Dict[str, Any]:
        """Récupérer les statistiques de lecture"""
        try:
            from reading_service.utils import calculate_reading_statistics
            
            user = User.objects.get(id=user_id)
            return calculate_reading_statistics(user, period)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {}
    
    def has_user_read_book(self, user_id: int, book_id: int) -> bool:
        """Vérifier si un utilisateur a lu un livre"""
        try:
            from reading_service.models import ReadingSession
            
            return ReadingSession.objects.filter(
                user_id=user_id,
                book_id=book_id,
                status__in=['completed', 'active']
            ).exists()
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de lecture: {str(e)}")
            return False
    
    def _serialize_reading_session(self, session) -> Dict[str, Any]:
        """Sérialiser une session de lecture"""
        return {
            'id': session.id,
            'book_id': session.book.id,
            'book_title': session.book.title,
            'status': session.status,
            'progress_percentage': session.progress_percentage,
            'current_page': session.current_page,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'last_activity': session.last_activity,
            'total_reading_time': str(session.total_reading_time),
            'device_type': session.device_type
        }
    
    def _serialize_bookmark(self, bookmark) -> Dict[str, Any]:
        """Sérialiser un signet"""
        return {
            'id': bookmark.id,
            'book_id': bookmark.book.id,
            'book_title': bookmark.book.title,
            'type': bookmark.type,
            'title': bookmark.title,
            'content': bookmark.content,
            'note': bookmark.note,
            'page_number': bookmark.page_number,
            'is_favorite': bookmark.is_favorite,
            'created_at': bookmark.created_at
        }


# Instance globale des services
book_service = BookService()
reading_service = ReadingService()


def get_book_service() -> BookServiceInterface:
    """Obtenir l'instance du service de livres"""
    return book_service


def get_reading_service() -> ReadingServiceInterface:
    """Obtenir l'instance du service de lecture"""
    return reading_service