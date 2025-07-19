"""
Système d'événements pour découpler les services
"""
import logging
from typing import Dict, Any, List, Callable
from django.dispatch import Signal, receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from dataclasses import dataclass
from enum import Enum

User = get_user_model()
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types d'événements du système"""
    # Événements de lecture
    READING_SESSION_STARTED = "reading_session_started"
    READING_SESSION_ENDED = "reading_session_ended"
    BOOK_COMPLETED = "book_completed"
    BOOKMARK_CREATED = "bookmark_created"
    
    # Événements de recommandation
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RECOMMENDATION_CLICKED = "recommendation_clicked"
    RECOMMENDATION_CONVERTED = "recommendation_converted"
    USER_INTERACTION_RECORDED = "user_interaction_recorded"
    
    # Événements de catalogue
    BOOK_RATED = "book_rated"
    BOOK_FAVORITED = "book_favorited"
    BOOK_DOWNLOADED = "book_downloaded"
    
    # Événements utilisateur
    USER_PREFERENCES_UPDATED = "user_preferences_updated"
    USER_PROFILE_UPDATED = "user_profile_updated"


@dataclass
class Event:
    """Structure d'un événement"""
    type: EventType
    data: Dict[str, Any]
    user_id: int = None
    timestamp: timezone.datetime = None
    source_service: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = timezone.now()


# Signaux Django pour les événements
reading_session_started = Signal()
reading_session_ended = Signal()
book_completed = Signal()
bookmark_created = Signal()

recommendation_generated = Signal()
recommendation_clicked = Signal()
recommendation_converted = Signal()
user_interaction_recorded = Signal()

book_rated = Signal()
book_favorited = Signal()
book_downloaded = Signal()

user_preferences_updated = Signal()
user_profile_updated = Signal()


class EventBus:
    """Bus d'événements centralisé"""
    
    _instance = None
    _handlers: Dict[EventType, List[Callable]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = {}
        return cls._instance
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """S'abonner à un type d'événement"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Handler enregistré pour l'événement {event_type.value}")
    
    def publish(self, event: Event):
        """Publier un événement"""
        try:
            # Enregistrer l'événement (optionnel pour audit/debug)
            logger.info(f"Événement publié: {event.type.value} par {event.source_service}")
            
            # Traiter avec les handlers enregistrés
            if event.type in self._handlers:
                for handler in self._handlers[event.type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Erreur dans le handler d'événement {event.type.value}: {str(e)}")
            
            # Publier via Django signals pour compatibilité
            self._publish_django_signal(event)
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication de l'événement: {str(e)}")
    
    def _publish_django_signal(self, event: Event):
        """Publier l'événement via Django signals"""
        signal_mapping = {
            EventType.READING_SESSION_STARTED: reading_session_started,
            EventType.READING_SESSION_ENDED: reading_session_ended,
            EventType.BOOK_COMPLETED: book_completed,
            EventType.BOOKMARK_CREATED: bookmark_created,
            EventType.RECOMMENDATION_GENERATED: recommendation_generated,
            EventType.RECOMMENDATION_CLICKED: recommendation_clicked,
            EventType.RECOMMENDATION_CONVERTED: recommendation_converted,
            EventType.USER_INTERACTION_RECORDED: user_interaction_recorded,
            EventType.BOOK_RATED: book_rated,
            EventType.BOOK_FAVORITED: book_favorited,
            EventType.BOOK_DOWNLOADED: book_downloaded,
            EventType.USER_PREFERENCES_UPDATED: user_preferences_updated,
            EventType.USER_PROFILE_UPDATED: user_profile_updated,
        }
        
        signal = signal_mapping.get(event.type)
        if signal:
            signal.send(
                sender=self.__class__,
                event_type=event.type,
                data=event.data,
                user_id=event.user_id,
                timestamp=event.timestamp,
                source_service=event.source_service
            )


# Instance globale du bus d'événements
event_bus = EventBus()


def publish_event(event_type: EventType, data: Dict[str, Any], 
                 user_id: int = None, source_service: str = None):
    """Fonction utilitaire pour publier un événement"""
    event = Event(
        type=event_type,
        data=data,
        user_id=user_id,
        source_service=source_service
    )
    event_bus.publish(event)


# Handlers d'événements par défaut

def handle_book_completed(event: Event):
    """Gérer l'événement de livre terminé"""
    logger.info(f"Livre terminé par l'utilisateur {event.user_id}: {event.data.get('book_id')}")
    
    # Publier un événement pour les recommandations
    publish_event(
        EventType.USER_INTERACTION_RECORDED,
        {
            'book_id': event.data.get('book_id'),
            'interaction_type': 'completed',
            'timestamp': event.timestamp
        },
        user_id=event.user_id,
        source_service='reading_service'
    )


def handle_user_interaction(event: Event):
    """Gérer les interactions utilisateur pour les recommandations"""
    logger.info(f"Interaction enregistrée: {event.data.get('interaction_type')} "
               f"pour le livre {event.data.get('book_id')}")


def handle_recommendation_clicked(event: Event):
    """Gérer les clics sur les recommandations"""
    logger.info(f"Recommandation cliquée: {event.data.get('recommendation_id')} "
               f"par l'utilisateur {event.user_id}")


# Enregistrement des handlers par défaut
event_bus.subscribe(EventType.BOOK_COMPLETED, handle_book_completed)
event_bus.subscribe(EventType.USER_INTERACTION_RECORDED, handle_user_interaction)
event_bus.subscribe(EventType.RECOMMENDATION_CLICKED, handle_recommendation_clicked)


# Décorateur pour automatiser la publication d'événements
def event_publisher(event_type: EventType, source_service: str = None):
    """Décorateur pour publier automatiquement des événements"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Extraire les données pour l'événement
            event_data = {}
            if hasattr(result, 'id'):
                event_data['id'] = result.id
            if 'user' in kwargs:
                user_id = kwargs['user'].id if hasattr(kwargs['user'], 'id') else kwargs['user']
            elif len(args) > 0 and hasattr(args[0], 'user'):
                user_id = args[0].user.id
            else:
                user_id = None
            
            publish_event(event_type, event_data, user_id, source_service)
            return result
        return wrapper
    return decorator