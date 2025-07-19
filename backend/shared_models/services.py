"""
Services pour la gestion des références partagées et communication inter-services.
"""

from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import uuid
import logging

from .models import (
    BookReference, AuthorReference, CategoryReference, UserReference,
    ServiceSync, CrossServiceEvent
)

logger = logging.getLogger(__name__)


class ReferenceManagerService:
    """
    Service de gestion des références partagées entre services.
    Centralise la création, mise à jour et synchronisation des références.
    """
    
    def create_book_reference(self, book_data: Dict[str, Any]) -> BookReference:
        """
        Crée ou met à jour une référence de livre.
        
        Args:
            book_data: Données du livre (uuid, title, slug, isbn, etc.)
            
        Returns:
            BookReference: Référence créée ou mise à jour
        """
        try:
            book_ref, created = BookReference.objects.update_or_create(
                book_uuid=book_data['uuid'],
                defaults={
                    'title': book_data.get('title', ''),
                    'slug': book_data.get('slug', ''),
                    'isbn': book_data.get('isbn', ''),
                    'is_active': book_data.get('is_active', True),
                }
            )
            
            action = 'created' if created else 'updated'
            logger.info(f"Book reference {action}: {book_ref.book_uuid}")
            
            return book_ref
            
        except Exception as e:
            logger.error(f"Error creating book reference: {e}")
            raise
    
    def create_author_reference(self, author_data: Dict[str, Any]) -> AuthorReference:
        """
        Crée ou met à jour une référence d'auteur.
        """
        try:
            author_ref, created = AuthorReference.objects.update_or_create(
                author_uuid=author_data['uuid'],
                defaults={
                    'name': author_data.get('name', ''),
                    'slug': author_data.get('slug', ''),
                    'is_active': author_data.get('is_active', True),
                }
            )
            
            action = 'created' if created else 'updated'
            logger.info(f"Author reference {action}: {author_ref.author_uuid}")
            
            return author_ref
            
        except Exception as e:
            logger.error(f"Error creating author reference: {e}")
            raise
    
    def create_category_reference(self, category_data: Dict[str, Any]) -> CategoryReference:
        """
        Crée ou met à jour une référence de catégorie.
        """
        try:
            category_ref, created = CategoryReference.objects.update_or_create(
                category_uuid=category_data['uuid'],
                defaults={
                    'name': category_data.get('name', ''),
                    'slug': category_data.get('slug', ''),
                    'parent_uuid': category_data.get('parent_uuid'),
                    'is_active': category_data.get('is_active', True),
                }
            )
            
            action = 'created' if created else 'updated'
            logger.info(f"Category reference {action}: {category_ref.category_uuid}")
            
            return category_ref
            
        except Exception as e:
            logger.error(f"Error creating category reference: {e}")
            raise
    
    def create_user_reference(self, user_data: Dict[str, Any]) -> UserReference:
        """
        Crée ou met à jour une référence d'utilisateur.
        """
        try:
            user_ref, created = UserReference.objects.update_or_create(
                user_uuid=user_data['uuid'],
                defaults={
                    'username': user_data.get('username', ''),
                    'display_name': user_data.get('display_name', ''),
                    'is_active': user_data.get('is_active', True),
                }
            )
            
            action = 'created' if created else 'updated'
            logger.info(f"User reference {action}: {user_ref.user_uuid}")
            
            return user_ref
            
        except Exception as e:
            logger.error(f"Error creating user reference: {e}")
            raise
    
    def get_book_reference(self, book_uuid: uuid.UUID) -> Optional[BookReference]:
        """
        Récupère une référence de livre par UUID.
        """
        try:
            return BookReference.objects.get(
                book_uuid=book_uuid,
                is_active=True
            )
        except BookReference.DoesNotExist:
            return None
    
    def get_author_reference(self, author_uuid: uuid.UUID) -> Optional[AuthorReference]:
        """
        Récupère une référence d'auteur par UUID.
        """
        try:
            return AuthorReference.objects.get(
                author_uuid=author_uuid,
                is_active=True
            )
        except AuthorReference.DoesNotExist:
            return None
    
    def get_category_reference(self, category_uuid: uuid.UUID) -> Optional[CategoryReference]:
        """
        Récupère une référence de catégorie par UUID.
        """
        try:
            return CategoryReference.objects.get(
                category_uuid=category_uuid,
                is_active=True
            )
        except CategoryReference.DoesNotExist:
            return None
    
    def get_user_reference(self, user_uuid: uuid.UUID) -> Optional[UserReference]:
        """
        Récupère une référence d'utilisateur par UUID.
        """
        try:
            return UserReference.objects.get(
                user_uuid=user_uuid,
                is_active=True
            )
        except UserReference.DoesNotExist:
            return None
    
    def deactivate_reference(self, model_class, object_uuid: uuid.UUID) -> bool:
        """
        Désactive une référence (soft delete).
        """
        try:
            if model_class == BookReference:
                field_name = 'book_uuid'
            elif model_class == AuthorReference:
                field_name = 'author_uuid'
            elif model_class == CategoryReference:
                field_name = 'category_uuid'
            elif model_class == UserReference:
                field_name = 'user_uuid'
            else:
                raise ValueError(f"Unknown model class: {model_class}")
            
            updated = model_class.objects.filter(
                **{field_name: object_uuid}
            ).update(is_active=False)
            
            if updated:
                logger.info(f"Deactivated {model_class.__name__} reference: {object_uuid}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deactivating reference: {e}")
            return False


class ServiceCommunicationService:
    """
    Service de communication entre microservices.
    Gère les événements inter-services et la synchronisation.
    """
    
    def __init__(self):
        self.reference_manager = ReferenceManagerService()
    
    def emit_event(
        self,
        event_type: str,
        source_service: str,
        event_data: Dict[str, Any],
        target_services: Optional[List[str]] = None,
        correlation_id: Optional[uuid.UUID] = None
    ) -> CrossServiceEvent:
        """
        Émet un événement inter-services.
        
        Args:
            event_type: Type d'événement
            source_service: Service émetteur
            event_data: Données de l'événement
            target_services: Services cibles (None = tous)
            correlation_id: ID de corrélation
            
        Returns:
            CrossServiceEvent: Événement créé
        """
        try:
            event = CrossServiceEvent.objects.create(
                event_type=event_type,
                source_service=source_service,
                target_services=target_services or [],
                event_data=event_data,
                correlation_id=correlation_id
            )
            
            logger.info(f"Event emitted: {event_type} from {source_service}")
            
            # Traitement asynchrone de l'événement
            self._process_event_async(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error emitting event: {e}")
            raise
    
    def _process_event_async(self, event: CrossServiceEvent):
        """
        Traite un événement de manière asynchrone.
        Cette méthode devrait idéalement utiliser Celery ou similar.
        """
        try:
            event.status = 'processing'
            event.save(update_fields=['status'])
            
            # Traitement selon le type d'événement
            if event.event_type.startswith('book.'):
                self._handle_book_event(event)
            elif event.event_type.startswith('author.'):
                self._handle_author_event(event)
            elif event.event_type.startswith('category.'):
                self._handle_category_event(event)
            elif event.event_type.startswith('user.'):
                self._handle_user_event(event)
            else:
                logger.warning(f"Unknown event type: {event.event_type}")
            
            event.status = 'processed'
            event.processed_at = timezone.now()
            event.save(update_fields=['status', 'processed_at'])
            
        except Exception as e:
            event.status = 'failed'
            event.error_message = str(e)
            event.retry_count += 1
            
            # Programmer une nouvelle tentative si possible
            if event.can_retry:
                event.next_retry_at = timezone.now() + timezone.timedelta(
                    minutes=2 ** event.retry_count  # Backoff exponentiel
                )
            
            event.save(update_fields=[
                'status', 'error_message', 'retry_count', 'next_retry_at'
            ])
            
            logger.error(f"Error processing event {event.event_id}: {e}")
    
    def _handle_book_event(self, event: CrossServiceEvent):
        """
        Traite les événements liés aux livres.
        """
        event_data = event.event_data
        
        if event.event_type == 'book.created':
            self.reference_manager.create_book_reference(event_data)
            
        elif event.event_type == 'book.updated':
            self.reference_manager.create_book_reference(event_data)
            
        elif event.event_type == 'book.deleted':
            book_uuid = event_data.get('uuid')
            if book_uuid:
                self.reference_manager.deactivate_reference(
                    BookReference, 
                    uuid.UUID(book_uuid)
                )
    
    def _handle_author_event(self, event: CrossServiceEvent):
        """
        Traite les événements liés aux auteurs.
        """
        event_data = event.event_data
        
        if event.event_type == 'author.created':
            self.reference_manager.create_author_reference(event_data)
            
        elif event.event_type == 'author.updated':
            self.reference_manager.create_author_reference(event_data)
    
    def _handle_category_event(self, event: CrossServiceEvent):
        """
        Traite les événements liés aux catégories.
        """
        event_data = event.event_data
        
        if event.event_type == 'category.created':
            self.reference_manager.create_category_reference(event_data)
            
        elif event.event_type == 'category.updated':
            self.reference_manager.create_category_reference(event_data)
    
    def _handle_user_event(self, event: CrossServiceEvent):
        """
        Traite les événements liés aux utilisateurs.
        """
        event_data = event.event_data
        
        if event.event_type == 'user.created':
            self.reference_manager.create_user_reference(event_data)
            
        elif event.event_type == 'user.updated':
            self.reference_manager.create_user_reference(event_data)
    
    def create_sync_task(
        self,
        source_service: str,
        target_service: str,
        sync_type: str,
        object_type: str,
        object_uuid: uuid.UUID,
        sync_data: Dict[str, Any]
    ) -> ServiceSync:
        """
        Crée une tâche de synchronisation entre services.
        """
        try:
            sync_task = ServiceSync.objects.create(
                source_service=source_service,
                target_service=target_service,
                sync_type=sync_type,
                object_type=object_type,
                object_uuid=object_uuid,
                sync_data=sync_data
            )
            
            logger.info(f"Sync task created: {sync_task.sync_id}")
            
            return sync_task
            
        except Exception as e:
            logger.error(f"Error creating sync task: {e}")
            raise
    
    def process_pending_syncs(self, limit: int = 100):
        """
        Traite les synchronisations en attente.
        """
        pending_syncs = ServiceSync.objects.filter(
            status='pending'
        )[:limit]
        
        for sync_task in pending_syncs:
            try:
                self._process_sync_task(sync_task)
            except Exception as e:
                logger.error(f"Error processing sync {sync_task.sync_id}: {e}")
    
    def _process_sync_task(self, sync_task: ServiceSync):
        """
        Traite une tâche de synchronisation.
        """
        try:
            sync_task.status = 'in_progress'
            sync_task.started_at = timezone.now()
            sync_task.save(update_fields=['status', 'started_at'])
            
            # Logique de synchronisation selon le type
            if sync_task.object_type == 'Book':
                self._sync_book(sync_task)
            elif sync_task.object_type == 'Author':
                self._sync_author(sync_task)
            elif sync_task.object_type == 'Category':
                self._sync_category(sync_task)
            elif sync_task.object_type == 'User':
                self._sync_user(sync_task)
            
            sync_task.status = 'completed'
            sync_task.completed_at = timezone.now()
            sync_task.save(update_fields=['status', 'completed_at'])
            
        except Exception as e:
            sync_task.status = 'failed'
            sync_task.error_message = str(e)
            sync_task.save(update_fields=['status', 'error_message'])
            raise
    
    def _sync_book(self, sync_task: ServiceSync):
        """
        Synchronise un livre entre services.
        """
        if sync_task.sync_type == 'create':
            self.reference_manager.create_book_reference(sync_task.sync_data)
        elif sync_task.sync_type == 'update':
            self.reference_manager.create_book_reference(sync_task.sync_data)
        elif sync_task.sync_type == 'delete':
            self.reference_manager.deactivate_reference(
                BookReference, 
                sync_task.object_uuid
            )
    
    def _sync_author(self, sync_task: ServiceSync):
        """
        Synchronise un auteur entre services.
        """
        if sync_task.sync_type in ['create', 'update']:
            self.reference_manager.create_author_reference(sync_task.sync_data)
    
    def _sync_category(self, sync_task: ServiceSync):
        """
        Synchronise une catégorie entre services.
        """
        if sync_task.sync_type in ['create', 'update']:
            self.reference_manager.create_category_reference(sync_task.sync_data)
    
    def _sync_user(self, sync_task: ServiceSync):
        """
        Synchronise un utilisateur entre services.
        """
        if sync_task.sync_type in ['create', 'update']:
            self.reference_manager.create_user_reference(sync_task.sync_data)


class ServiceRegistryService:
    """
    Service de registry pour la découverte de services.
    Maintient un registre des services disponibles et leurs endpoints.
    """
    
    def __init__(self):
        self.services = {
            'auth_service': {
                'base_url': '/api/auth/',
                'endpoints': {
                    'users': 'users/',
                    'profiles': 'profiles/',
                }
            },
            'catalog_service': {
                'base_url': '/api/catalog/',
                'endpoints': {
                    'books': 'books/',
                    'authors': 'authors/',
                    'categories': 'categories/',
                }
            },
            'reading_service': {
                'base_url': '/api/reading/',
                'endpoints': {
                    'sessions': 'sessions/',
                    'bookmarks': 'bookmarks/',
                    'goals': 'goals/',
                }
            },
            'recommendation_service': {
                'base_url': '/api/recommendations/',
                'endpoints': {
                    'recommendations': 'recommendations/',
                    'interactions': 'interactions/',
                    'feedback': 'feedback/',
                }
            }
        }
    
    def get_service_endpoint(self, service_name: str, endpoint: str) -> str:
        """
        Récupère l'URL d'un endpoint de service.
        """
        service_config = self.services.get(service_name)
        if not service_config:
            raise ValueError(f"Unknown service: {service_name}")
        
        endpoint_path = service_config['endpoints'].get(endpoint)
        if not endpoint_path:
            raise ValueError(f"Unknown endpoint {endpoint} for service {service_name}")
        
        return f"{service_config['base_url']}{endpoint_path}"
    
    def get_all_services(self) -> Dict[str, Any]:
        """
        Récupère la configuration de tous les services.
        """
        return self.services


# Instances singleton des services
reference_manager = ReferenceManagerService()
service_communication = ServiceCommunicationService()
service_registry = ServiceRegistryService()