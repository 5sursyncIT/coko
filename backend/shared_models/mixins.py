"""
Mixins pour faciliter l'intégration des références UUID dans les modèles.
"""

from typing import Dict, Optional, Any, List
from django.db import models
import uuid

from .api_client import service_clients
from .services import reference_manager


class BookReferenceMixin:
    """
    Mixin pour les modèles qui référencent des livres.
    Fournit des méthodes pour récupérer les détails du livre.
    """
    
    def get_book_details(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails du livre via l'API catalog_service.
        """
        if not hasattr(self, 'book_uuid') or not self.book_uuid:
            return None
        
        catalog_client = service_clients.get_client('catalog')
        return catalog_client.get_book(self.book_uuid)
    
    def update_book_cache(self, book_data: Dict[str, Any]):
        """
        Met à jour les informations mises en cache du livre.
        """
        if hasattr(self, 'book_title') and 'title' in book_data:
            self.book_title = book_data['title']
            self.save(update_fields=['book_title'])
    
    @property
    def book_details_cached(self) -> Dict[str, Any]:
        """
        Propriété qui retourne les détails du livre avec cache intelligent.
        """
        # Utiliser les données mises en cache si disponibles
        cached_data = {
            'uuid': str(self.book_uuid),
            'title': getattr(self, 'book_title', ''),
        }
        
        # Si on a besoin de plus de détails, faire un appel API
        if not cached_data['title']:
            full_details = self.get_book_details()
            if full_details:
                cached_data.update(full_details)
                self.update_book_cache(full_details)
        
        return cached_data


class AuthorReferenceMixin:
    """
    Mixin pour les modèles qui référencent des auteurs.
    """
    
    def get_author_details(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails de l'auteur via l'API catalog_service.
        """
        if not hasattr(self, 'author_uuid') or not self.author_uuid:
            return None
        
        catalog_client = service_clients.get_client('catalog')
        return catalog_client.get_author(self.author_uuid)
    
    @property
    def author_details_cached(self) -> Dict[str, Any]:
        """
        Propriété qui retourne les détails de l'auteur avec cache.
        """
        cached_data = {
            'uuid': str(self.author_uuid) if self.author_uuid else None,
        }
        
        if self.author_uuid:
            full_details = self.get_author_details()
            if full_details:
                cached_data.update(full_details)
        
        return cached_data


class CategoryReferenceMixin:
    """
    Mixin pour les modèles qui référencent des catégories.
    """
    
    def get_category_details(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails de la catégorie via l'API catalog_service.
        """
        if not hasattr(self, 'category_uuid') or not self.category_uuid:
            return None
        
        catalog_client = service_clients.get_client('catalog')
        return catalog_client.get_category(self.category_uuid)
    
    @property
    def category_details_cached(self) -> Dict[str, Any]:
        """
        Propriété qui retourne les détails de la catégorie avec cache.
        """
        cached_data = {
            'uuid': str(self.category_uuid) if self.category_uuid else None,
        }
        
        if self.category_uuid:
            full_details = self.get_category_details()
            if full_details:
                cached_data.update(full_details)
        
        return cached_data


class UserReferenceMixin:
    """
    Mixin pour les modèles qui référencent des utilisateurs.
    """
    
    def get_user_details(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails de l'utilisateur via l'API auth_service.
        """
        if not hasattr(self, 'user_uuid') or not self.user_uuid:
            return None
        
        auth_client = service_clients.get_client('auth')
        return auth_client.get_user(self.user_uuid)
    
    @property
    def user_details_cached(self) -> Dict[str, Any]:
        """
        Propriété qui retourne les détails de l'utilisateur avec cache.
        """
        cached_data = {
            'uuid': str(self.user_uuid) if self.user_uuid else None,
        }
        
        if self.user_uuid:
            full_details = self.get_user_details()
            if full_details:
                cached_data.update(full_details)
        
        return cached_data


class BatchReferenceMixin:
    """
    Mixin pour optimiser les requêtes batch vers les services.
    """
    
    @classmethod
    def get_books_batch(cls, queryset) -> Dict[str, Dict[str, Any]]:
        """
        Récupère les détails de plusieurs livres en une seule requête.
        """
        # Extraire tous les UUIDs de livres uniques
        book_uuids = set()
        for obj in queryset:
            if hasattr(obj, 'book_uuid') and obj.book_uuid:
                book_uuids.add(obj.book_uuid)
        
        if not book_uuids:
            return {}
        
        catalog_client = service_clients.get_client('catalog')
        return catalog_client.get_books_batch(list(book_uuids))
    
    @classmethod
    def prefetch_book_details(cls, queryset):
        """
        Précharge les détails des livres pour un queryset.
        Utilise cette méthode pour optimiser les performances.
        """
        books_data = cls.get_books_batch(queryset)
        
        # Attacher les données aux objets
        for obj in queryset:
            if hasattr(obj, 'book_uuid') and obj.book_uuid:
                book_data = books_data.get(str(obj.book_uuid))
                if book_data:
                    obj._cached_book_details = book_data
        
        return queryset


class EventEmitterMixin:
    """
    Mixin pour émettre des événements inter-services lors des modifications de modèles.
    """
    
    def emit_created_event(self):
        """
        Émet un événement de création.
        """
        from .services import service_communication
        
        model_name = self.__class__.__name__.lower()
        event_type = f"{model_name}.created"
        
        event_data = self.to_event_data()
        
        service_communication.emit_event(
            event_type=event_type,
            source_service=self.get_source_service(),
            event_data=event_data
        )
    
    def emit_updated_event(self):
        """
        Émet un événement de mise à jour.
        """
        from .services import service_communication
        
        model_name = self.__class__.__name__.lower()
        event_type = f"{model_name}.updated"
        
        event_data = self.to_event_data()
        
        service_communication.emit_event(
            event_type=event_type,
            source_service=self.get_source_service(),
            event_data=event_data
        )
    
    def emit_deleted_event(self):
        """
        Émet un événement de suppression.
        """
        from .services import service_communication
        
        model_name = self.__class__.__name__.lower()
        event_type = f"{model_name}.deleted"
        
        event_data = self.to_event_data()
        
        service_communication.emit_event(
            event_type=event_type,
            source_service=self.get_source_service(),
            event_data=event_data
        )
    
    def to_event_data(self) -> Dict[str, Any]:
        """
        Convertit l'objet en données d'événement.
        À surcharger dans les classes dérivées.
        """
        return {
            'uuid': str(getattr(self, 'id', '')) or str(getattr(self, 'uuid', '')),
            'model': self.__class__.__name__,
        }
    
    def get_source_service(self) -> str:
        """
        Retourne le nom du service source.
        À surcharger dans les classes dérivées.
        """
        app_label = self._meta.app_label
        return f"{app_label}"


class SyncStatusMixin:
    """
    Mixin pour tracker le statut de synchronisation des objets.
    """
    
    def mark_for_sync(self, target_services: List[str]):
        """
        Marque l'objet pour synchronisation avec les services cibles.
        """
        from .services import service_communication
        
        for target_service in target_services:
            service_communication.create_sync_task(
                source_service=self.get_source_service(),
                target_service=target_service,
                sync_type='update',
                object_type=self.__class__.__name__,
                object_uuid=getattr(self, 'id', None) or getattr(self, 'uuid', None),
                sync_data=self.to_sync_data()
            )
    
    def to_sync_data(self) -> Dict[str, Any]:
        """
        Convertit l'objet en données de synchronisation.
        À surcharger dans les classes dérivées.
        """
        return self.to_event_data()
    
    @property
    def sync_status(self) -> str:
        """
        Retourne le statut de synchronisation de l'objet.
        """
        from .models import ServiceSync
        
        object_uuid = getattr(self, 'id', None) or getattr(self, 'uuid', None)
        if not object_uuid:
            return 'unknown'
        
        latest_sync = ServiceSync.objects.filter(
            object_type=self.__class__.__name__,
            object_uuid=object_uuid
        ).order_by('-created_at').first()
        
        return latest_sync.status if latest_sync else 'not_synced'


class CacheOptimizedMixin:
    """
    Mixin pour optimiser la mise en cache des références.
    """
    
    def invalidate_reference_cache(self):
        """
        Invalide le cache des références pour cet objet.
        """
        from django.core.cache import cache
        
        # Invalider les caches liés aux livres
        if hasattr(self, 'book_uuid') and self.book_uuid:
            cache_key = f"book_details_{self.book_uuid}"
            cache.delete(cache_key)
        
        # Invalider les caches liés aux auteurs
        if hasattr(self, 'author_uuid') and self.author_uuid:
            cache_key = f"author_details_{self.author_uuid}"
            cache.delete(cache_key)
        
        # Invalider les caches liés aux catégories
        if hasattr(self, 'category_uuid') and self.category_uuid:
            cache_key = f"category_details_{self.category_uuid}"
            cache.delete(cache_key)
    
    def refresh_cached_data(self):
        """
        Actualise les données mises en cache depuis les services.
        """
        # Actualiser les données du livre
        if hasattr(self, 'book_uuid') and self.book_uuid:
            book_details = self.get_book_details()
            if book_details and hasattr(self, 'book_title'):
                self.book_title = book_details.get('title', self.book_title)
        
        # Sauvegarder les changements
        if hasattr(self, 'save'):
            self.save()


class ServiceIntegrationMixin(
    BookReferenceMixin,
    AuthorReferenceMixin,
    CategoryReferenceMixin,
    UserReferenceMixin,
    BatchReferenceMixin,
    EventEmitterMixin,
    SyncStatusMixin,
    CacheOptimizedMixin
):
    """
    Mixin combiné qui fournit toutes les fonctionnalités d'intégration inter-services.
    """
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """
        Override de save pour gérer les événements et la synchronisation.
        """
        is_new = self.pk is None
        
        # Sauvegarder l'objet
        super().save(*args, **kwargs)
        
        # Émettre les événements appropriés
        if is_new:
            self.emit_created_event()
        else:
            self.emit_updated_event()
    
    def delete(self, *args, **kwargs):
        """
        Override de delete pour gérer les événements.
        """
        # Émettre l'événement de suppression avant la suppression
        self.emit_deleted_event()
        
        # Invalider les caches
        self.invalidate_reference_cache()
        
        # Supprimer l'objet
        super().delete(*args, **kwargs)