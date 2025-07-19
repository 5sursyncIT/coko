"""
Adaptateurs pour utiliser les services dans le service de recommandations
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from coko.services import get_book_service, get_reading_service
from coko.events import publish_event, EventType, event_bus, Event
from .models import UserProfile, UserInteraction, RecommendationSet, Recommendation

User = get_user_model()
logger = logging.getLogger(__name__)


class RecommendationServiceAdapter:
    """Adaptateur pour le service de recommandations utilisant les interfaces"""
    
    def __init__(self):
        self.book_service = get_book_service()
        self.reading_service = get_reading_service()
        
        # S'abonner aux événements
        event_bus.subscribe(EventType.BOOK_COMPLETED, self._handle_book_completed)
        event_bus.subscribe(EventType.USER_INTERACTION_RECORDED, self._handle_user_interaction)
        event_bus.subscribe(EventType.USER_PREFERENCES_UPDATED, self._handle_preferences_updated)
    
    def generate_content_based_recommendations(
        self, 
        user: User, 
        user_profile: UserProfile, 
        read_book_ids: set, 
        count: int, 
        context: str
    ) -> List[Tuple[Dict[str, Any], float, List[str]]]:
        """Générer des recommandations basées sur le contenu via les services"""
        
        recommendations = []
        
        # Obtenir les préférences utilisateur
        preferred_genres = user_profile.preferred_genres or []
        preferred_authors = user_profile.preferred_authors or []
        
        # Si pas de préférences, utiliser l'historique via le service
        if not preferred_genres and not preferred_authors:
            history = self.reading_service.get_user_reading_history(user.id, limit=10)
            
            for session in history:
                book_data = self.book_service.get_book_by_id(session['book_id'])
                if book_data:
                    preferred_genres.extend([cat['name'] for cat in book_data.get('categories', [])])
                    preferred_authors.extend([author['name'] for author in book_data.get('authors', [])])
        
        # Obtenir des livres par auteurs préférés
        if preferred_authors:
            author_books = self.book_service.get_books_by_author(
                preferred_authors, 
                limit=count//2
            )
            for book in author_books:
                if book['id'] not in read_book_ids:
                    recommendations.append((book, 0.9, ['Auteur préféré']))
        
        # Obtenir des livres par genres préférés
        if preferred_genres and len(recommendations) < count:
            genre_books = self.book_service.get_books_by_category(
                preferred_genres, 
                limit=count - len(recommendations)
            )
            for book in genre_books:
                if book['id'] not in read_book_ids:
                    # Vérifier qu'on n'a pas déjà ce livre
                    if not any(rec[0]['id'] == book['id'] for rec in recommendations):
                        recommendations.append((book, 0.7, ['Genre préféré']))
        
        # Compléter avec des livres populaires
        if len(recommendations) < count:
            exclude_ids = list(read_book_ids) + [rec[0]['id'] for rec in recommendations]
            popular_books = self.book_service.get_popular_books(
                limit=count - len(recommendations),
                exclude_ids=exclude_ids
            )
            for book in popular_books:
                recommendations.append((book, 0.5, ['Livre populaire']))
        
        return recommendations[:count]
    
    def generate_collaborative_recommendations(
        self, 
        user: User, 
        user_profile: UserProfile, 
        read_book_ids: set, 
        count: int, 
        context: str
    ) -> List[Tuple[Dict[str, Any], float, List[str]]]:
        """Générer des recommandations collaboratives via les services"""
        
        recommendations = []
        
        # Trouver des utilisateurs similaires basés sur l'historique
        similar_users = self._find_similar_users_via_service(user.id)
        
        if not similar_users:
            # Fallback vers recommandations basées sur le contenu
            return self.generate_content_based_recommendations(
                user, user_profile, read_book_ids, count, context
            )
        
        # Analyser les livres des utilisateurs similaires
        book_scores = {}
        
        for similar_user_id, similarity_score in similar_users:
            similar_user_books = self.reading_service.get_user_completed_books(similar_user_id)
            
            for session in similar_user_books:
                book_id = session['book_id']
                if book_id not in read_book_ids:
                    if book_id not in book_scores:
                        book_scores[book_id] = []
                    book_scores[book_id].append(similarity_score)
        
        # Calculer les scores finaux et récupérer les données des livres
        for book_id, scores in book_scores.items():
            avg_score = sum(scores) / len(scores)
            book_data = self.book_service.get_book_by_id(book_id)
            
            if book_data:
                reasons = [f'Recommandé par {len(scores)} utilisateurs similaires']
                recommendations.append((book_data, avg_score, reasons))
        
        # Trier par score et retourner les meilleurs
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:count]
    
    def get_similar_books_via_service(self, book_id: int, count: int = 10) -> List[Dict[str, Any]]:
        """Obtenir des livres similaires via les services"""
        
        # Obtenir les informations du livre source
        source_book = self.book_service.get_book_by_id(book_id)
        if not source_book:
            return []
        
        similar_books = []
        
        # 1. Livres de la même catégorie
        categories = [cat['name'] for cat in source_book.get('categories', [])]
        if categories:
            category_books = self.book_service.get_books_by_category(
                categories, 
                limit=count//2
            )
            for book in category_books:
                if book['id'] != book_id:
                    similar_books.append({
                        **book,
                        'similarity_score': 0.7,
                        'similarity_reason': 'Même catégorie'
                    })
        
        # 2. Livres du même auteur
        authors = [author['name'] for author in source_book.get('authors', [])]
        if authors and len(similar_books) < count:
            author_books = self.book_service.get_books_by_author(
                authors, 
                limit=count - len(similar_books)
            )
            for book in author_books:
                if book['id'] != book_id:
                    # Vérifier qu'on n'a pas déjà ce livre
                    if not any(sb['id'] == book['id'] for sb in similar_books):
                        similar_books.append({
                            **book,
                            'similarity_score': 0.8,
                            'similarity_reason': 'Même auteur'
                        })
        
        # 3. Compléter avec des livres populaires si nécessaire
        if len(similar_books) < count:
            exclude_ids = [book_id] + [sb['id'] for sb in similar_books]
            popular_books = self.book_service.get_popular_books(
                limit=count - len(similar_books),
                exclude_ids=exclude_ids
            )
            for book in popular_books:
                similar_books.append({
                    **book,
                    'similarity_score': 0.5,
                    'similarity_reason': 'Livre populaire'
                })
        
        return similar_books[:count]
    
    def record_interaction_via_service(
        self, 
        user_id: int, 
        book_id: int, 
        interaction_type: str, 
        metadata: Dict[str, Any] = None
    ) -> None:
        """Enregistrer une interaction utilisateur et publier l'événement"""
        
        try:
            # Vérifier que le livre existe
            book_data = self.book_service.get_book_by_id(book_id)
            if not book_data:
                logger.warning(f"Tentative d'interaction avec un livre inexistant: {book_id}")
                return
            
            # Créer l'interaction (en gardant le modèle local pour les données spécifiques)
            interaction_data = {
                'user_id': user_id,
                'book_id': book_id,
                'interaction_type': interaction_type,
                'timestamp': timezone.now()
            }
            
            if metadata:
                interaction_data.update(metadata)
            
            # Publier l'événement
            publish_event(
                EventType.USER_INTERACTION_RECORDED,
                interaction_data,
                user_id=user_id,
                source_service='recommendation_service'
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'interaction: {str(e)}")
    
    def _find_similar_users_via_service(self, user_id: int, limit: int = 20) -> List[Tuple[int, float]]:
        """Trouver des utilisateurs similaires via les services"""
        
        # Obtenir l'historique de l'utilisateur
        user_history = self.reading_service.get_user_completed_books(user_id)
        if not user_history:
            return []
        
        user_books = set(session['book_id'] for session in user_history)
        
        # Analyser les autres utilisateurs (simulation - dans un vrai système,
        # cela serait plus optimisé avec des requêtes spécialisées)
        similar_users = []
        
        # Pour l'exemple, on simule avec quelques utilisateurs
        # Dans un vrai système, on utiliserait des techniques plus sophistiquées
        other_users = User.objects.exclude(id=user_id).filter(is_active=True)[:50]
        
        for other_user in other_users:
            other_history = self.reading_service.get_user_completed_books(other_user.id)
            other_books = set(session['book_id'] for session in other_history)
            
            # Calculer la similarité Jaccard simple
            intersection = len(user_books & other_books)
            union = len(user_books | other_books)
            
            if union > 0 and intersection >= 2:  # Au moins 2 livres en commun
                similarity = intersection / union
                if similarity > 0.1:  # Seuil minimum
                    similar_users.append((other_user.id, similarity))
        
        # Trier par similarité décroissante
        similar_users.sort(key=lambda x: x[1], reverse=True)
        return similar_users[:limit]
    
    def _handle_book_completed(self, event: Event):
        """Gérer l'événement de livre terminé"""
        try:
            book_id = event.data.get('book_id')
            user_id = event.user_id
            
            if book_id and user_id:
                # Mettre à jour le profil utilisateur ou déclencher des recommandations
                self._update_user_preferences_from_book(user_id, book_id)
                
                logger.info(f"Livre {book_id} terminé par l'utilisateur {user_id} - "
                           "profil mis à jour")
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de livre terminé: {str(e)}")
    
    def _handle_user_interaction(self, event: Event):
        """Gérer les événements d'interaction utilisateur"""
        try:
            # Enregistrer l'interaction dans le modèle local si nécessaire
            UserInteraction.objects.create(
                user_id=event.user_id,
                book_id=event.data.get('book_id'),
                interaction_type=event.data.get('interaction_type'),
                timestamp=event.data.get('timestamp', timezone.now()),
                metadata=event.data.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'interaction: {str(e)}")
    
    def _handle_preferences_updated(self, event: Event):
        """Gérer les mises à jour de préférences utilisateur"""
        try:
            user_id = event.user_id
            if user_id:
                # Invalider le cache des recommandations pour cet utilisateur
                cache.delete_many([
                    f"user_recommendations_{user_id}*",
                    f"personalized_recommendations_{user_id}*"
                ])
                
                logger.info(f"Cache de recommandations invalidé pour l'utilisateur {user_id}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des préférences: {str(e)}")
    
    def _update_user_preferences_from_book(self, user_id: int, book_id: int):
        """Mettre à jour les préférences utilisateur basées sur un livre lu"""
        try:
            book_data = self.book_service.get_book_by_id(book_id)
            if not book_data:
                return
            
            user_profile, created = UserProfile.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'preferred_genres': [],
                    'preferred_authors': [],
                    'preferred_languages': ['fr']
                }
            )
            
            # Ajouter les genres du livre aux préférences
            book_categories = [cat['name'] for cat in book_data.get('categories', [])]
            if book_categories:
                current_genres = set(user_profile.preferred_genres or [])
                current_genres.update(book_categories)
                user_profile.preferred_genres = list(current_genres)
            
            # Ajouter les auteurs du livre aux préférences
            book_authors = [author['name'] for author in book_data.get('authors', [])]
            if book_authors:
                current_authors = set(user_profile.preferred_authors or [])
                current_authors.update(book_authors)
                user_profile.preferred_authors = list(current_authors)
            
            user_profile.save()
            
            # Publier un événement de mise à jour des préférences
            publish_event(
                EventType.USER_PREFERENCES_UPDATED,
                {
                    'updated_fields': ['preferred_genres', 'preferred_authors'],
                    'trigger': 'book_completed'
                },
                user_id=user_id,
                source_service='recommendation_service'
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des préférences: {str(e)}")


# Instance globale de l'adaptateur
recommendation_adapter = RecommendationServiceAdapter()