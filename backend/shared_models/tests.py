"""
Tests pour le système de références partagées et communication inter-services.
"""

from django.test import TestCase, override_settings
from django.utils import timezone
from unittest.mock import patch, MagicMock
import uuid

from .models import (
    BookReference, AuthorReference, CategoryReference, UserReference,
    ServiceSync, CrossServiceEvent
)
from .services import ReferenceManagerService, ServiceCommunicationService
from .api_client import ServiceAPIError, CatalogServiceClient


class BookReferenceTestCase(TestCase):
    """Tests pour le modèle BookReference"""
    
    def setUp(self):
        self.book_uuid = uuid.uuid4()
        self.book_data = {
            'book_uuid': self.book_uuid,
            'title': 'Test Book',
            'slug': 'test-book',
            'isbn': '1234567890',
        }
    
    def test_create_book_reference(self):
        """Test de création d'une référence de livre"""
        book_ref = BookReference.objects.create(**self.book_data)
        
        self.assertEqual(book_ref.book_uuid, self.book_uuid)
        self.assertEqual(book_ref.title, 'Test Book')
        self.assertEqual(book_ref.slug, 'test-book')
        self.assertEqual(book_ref.isbn, '1234567890')
        self.assertTrue(book_ref.is_active)
        self.assertEqual(book_ref.service_source, 'catalog_service')
    
    def test_book_reference_str(self):
        """Test de la représentation string"""
        book_ref = BookReference.objects.create(**self.book_data)
        self.assertEqual(str(book_ref), 'BookRef: Test Book')
    
    def test_unique_book_uuid(self):
        """Test de l'unicité de book_uuid"""
        BookReference.objects.create(**self.book_data)
        
        with self.assertRaises(Exception):
            BookReference.objects.create(**self.book_data)


class AuthorReferenceTestCase(TestCase):
    """Tests pour le modèle AuthorReference"""
    
    def setUp(self):
        self.author_uuid = uuid.uuid4()
        self.author_data = {
            'author_uuid': self.author_uuid,
            'name': 'Test Author',
            'slug': 'test-author',
        }
    
    def test_create_author_reference(self):
        """Test de création d'une référence d'auteur"""
        author_ref = AuthorReference.objects.create(**self.author_data)
        
        self.assertEqual(author_ref.author_uuid, self.author_uuid)
        self.assertEqual(author_ref.name, 'Test Author')
        self.assertEqual(author_ref.slug, 'test-author')
        self.assertTrue(author_ref.is_active)


class ReferenceManagerServiceTestCase(TestCase):
    """Tests pour ReferenceManagerService"""
    
    def setUp(self):
        self.service = ReferenceManagerService()
        self.book_uuid = uuid.uuid4()
    
    def test_create_book_reference(self):
        """Test de création de référence de livre via le service"""
        book_data = {
            'uuid': self.book_uuid,
            'title': 'Service Test Book',
            'slug': 'service-test-book',
            'isbn': '0987654321',
        }
        
        book_ref = self.service.create_book_reference(book_data)
        
        self.assertIsInstance(book_ref, BookReference)
        self.assertEqual(book_ref.book_uuid, self.book_uuid)
        self.assertEqual(book_ref.title, 'Service Test Book')
    
    def test_update_existing_book_reference(self):
        """Test de mise à jour d'une référence existante"""
        # Créer une référence initiale
        initial_data = {
            'uuid': self.book_uuid,
            'title': 'Initial Title',
            'slug': 'initial-title',
        }
        self.service.create_book_reference(initial_data)
        
        # Mettre à jour avec de nouvelles données
        updated_data = {
            'uuid': self.book_uuid,
            'title': 'Updated Title',
            'slug': 'updated-title',
            'isbn': '1111111111',
        }
        
        book_ref = self.service.create_book_reference(updated_data)
        
        self.assertEqual(book_ref.title, 'Updated Title')
        self.assertEqual(book_ref.isbn, '1111111111')
        
        # Vérifier qu'il n'y a qu'une seule référence
        self.assertEqual(BookReference.objects.filter(book_uuid=self.book_uuid).count(), 1)
    
    def test_get_book_reference(self):
        """Test de récupération d'une référence de livre"""
        book_data = {
            'uuid': self.book_uuid,
            'title': 'Get Test Book',
            'slug': 'get-test-book',
        }
        
        # Créer la référence
        self.service.create_book_reference(book_data)
        
        # La récupérer
        book_ref = self.service.get_book_reference(self.book_uuid)
        
        self.assertIsNotNone(book_ref)
        self.assertEqual(book_ref.book_uuid, self.book_uuid)
        self.assertEqual(book_ref.title, 'Get Test Book')
    
    def test_get_nonexistent_book_reference(self):
        """Test de récupération d'une référence inexistante"""
        nonexistent_uuid = uuid.uuid4()
        book_ref = self.service.get_book_reference(nonexistent_uuid)
        self.assertIsNone(book_ref)
    
    def test_deactivate_reference(self):
        """Test de désactivation d'une référence"""
        book_data = {
            'uuid': self.book_uuid,
            'title': 'Deactivate Test Book',
            'slug': 'deactivate-test-book',
        }
        
        # Créer la référence
        self.service.create_book_reference(book_data)
        
        # Vérifier qu'elle est active
        book_ref = self.service.get_book_reference(self.book_uuid)
        self.assertIsNotNone(book_ref)
        
        # La désactiver
        result = self.service.deactivate_reference(BookReference, self.book_uuid)
        self.assertTrue(result)
        
        # Vérifier qu'elle n'est plus récupérable (car is_active=False)
        book_ref = self.service.get_book_reference(self.book_uuid)
        self.assertIsNone(book_ref)


class ServiceCommunicationServiceTestCase(TestCase):
    """Tests pour ServiceCommunicationService"""
    
    def setUp(self):
        self.service = ServiceCommunicationService()
    
    def test_emit_event(self):
        """Test d'émission d'événement"""
        event_data = {
            'uuid': str(uuid.uuid4()),
            'title': 'Test Event Book',
        }
        
        with patch.object(self.service, '_process_event_async') as mock_process:
            event = self.service.emit_event(
                event_type='book.created',
                source_service='catalog_service',
                event_data=event_data
            )
            
            self.assertIsInstance(event, CrossServiceEvent)
            self.assertEqual(event.event_type, 'book.created')
            self.assertEqual(event.source_service, 'catalog_service')
            self.assertEqual(event.event_data, event_data)
            self.assertEqual(event.status, 'pending')
            
            mock_process.assert_called_once_with(event)
    
    def test_create_sync_task(self):
        """Test de création d'une tâche de synchronisation"""
        object_uuid = uuid.uuid4()
        sync_data = {'title': 'Sync Test'}
        
        sync_task = self.service.create_sync_task(
            source_service='catalog_service',
            target_service='recommendation_service',
            sync_type='create',
            object_type='Book',
            object_uuid=object_uuid,
            sync_data=sync_data
        )
        
        self.assertIsInstance(sync_task, ServiceSync)
        self.assertEqual(sync_task.source_service, 'catalog_service')
        self.assertEqual(sync_task.target_service, 'recommendation_service')
        self.assertEqual(sync_task.sync_type, 'create')
        self.assertEqual(sync_task.object_type, 'Book')
        self.assertEqual(sync_task.object_uuid, object_uuid)
        self.assertEqual(sync_task.sync_data, sync_data)
        self.assertEqual(sync_task.status, 'pending')


class CrossServiceEventTestCase(TestCase):
    """Tests pour le modèle CrossServiceEvent"""
    
    def test_create_event(self):
        """Test de création d'un événement inter-services"""
        event_data = {'test': 'data'}
        
        event = CrossServiceEvent.objects.create(
            event_type='book.created',
            source_service='catalog_service',
            event_data=event_data
        )
        
        self.assertEqual(event.event_type, 'book.created')
        self.assertEqual(event.source_service, 'catalog_service')
        self.assertEqual(event.event_data, event_data)
        self.assertEqual(event.status, 'pending')
        self.assertEqual(event.retry_count, 0)
        self.assertEqual(event.max_retries, 3)
    
    def test_can_retry_property(self):
        """Test de la propriété can_retry"""
        event = CrossServiceEvent.objects.create(
            event_type='book.created',
            source_service='catalog_service',
            event_data={},
            status='failed',
            retry_count=2
        )
        
        self.assertTrue(event.can_retry)
        
        # Dépasser le nombre maximum de tentatives
        event.retry_count = 3
        event.save()
        
        self.assertFalse(event.can_retry)


class ServiceSyncTestCase(TestCase):
    """Tests pour le modèle ServiceSync"""
    
    def test_create_sync_task(self):
        """Test de création d'une tâche de synchronisation"""
        object_uuid = uuid.uuid4()
        sync_data = {'title': 'Test Sync'}
        
        sync_task = ServiceSync.objects.create(
            source_service='catalog_service',
            target_service='recommendation_service',
            sync_type='create',
            object_type='Book',
            object_uuid=object_uuid,
            sync_data=sync_data
        )
        
        self.assertEqual(sync_task.source_service, 'catalog_service')
        self.assertEqual(sync_task.target_service, 'recommendation_service')
        self.assertEqual(sync_task.sync_type, 'create')
        self.assertEqual(sync_task.object_type, 'Book')
        self.assertEqual(sync_task.object_uuid, object_uuid)
        self.assertEqual(sync_task.sync_data, sync_data)
        self.assertEqual(sync_task.status, 'pending')


class CatalogServiceClientTestCase(TestCase):
    """Tests pour CatalogServiceClient"""
    
    def setUp(self):
        self.client = CatalogServiceClient()
        self.book_uuid = uuid.uuid4()
    
    @patch('shared_models.api_client.requests.Session.get')
    def test_get_book_success(self, mock_get):
        """Test de récupération réussie d'un livre"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': str(self.book_uuid),
            'title': 'Test Book',
            'slug': 'test-book'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        book_data = self.client.get_book(self.book_uuid)
        
        self.assertIsNotNone(book_data)
        self.assertEqual(book_data['title'], 'Test Book')
        mock_get.assert_called_once()
    
    @patch('shared_models.api_client.requests.Session.get')
    def test_get_book_error(self, mock_get):
        """Test de gestion d'erreur lors de la récupération d'un livre"""
        mock_get.side_effect = Exception('Network error')
        
        book_data = self.client.get_book(self.book_uuid)
        
        self.assertIsNone(book_data)
    
    @patch('shared_models.api_client.requests.Session.post')
    def test_get_books_batch(self, mock_post):
        """Test de récupération en lot de livres"""
        book_uuids = [uuid.uuid4(), uuid.uuid4()]
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'books': {
                str(book_uuids[0]): {'title': 'Book 1'},
                str(book_uuids[1]): {'title': 'Book 2'},
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        books_data = self.client.get_books_batch(book_uuids)
        
        self.assertEqual(len(books_data), 2)
        self.assertEqual(books_data[str(book_uuids[0])]['title'], 'Book 1')
        self.assertEqual(books_data[str(book_uuids[1])]['title'], 'Book 2')


class IntegrationTestCase(TestCase):
    """Tests d'intégration pour le système complet"""
    
    def test_full_workflow(self):
        """Test du workflow complet de création et synchronisation"""
        # 1. Créer une référence de livre
        reference_service = ReferenceManagerService()
        book_uuid = uuid.uuid4()
        
        book_data = {
            'uuid': book_uuid,
            'title': 'Integration Test Book',
            'slug': 'integration-test-book',
        }
        
        book_ref = reference_service.create_book_reference(book_data)
        self.assertIsNotNone(book_ref)
        
        # 2. Émettre un événement
        communication_service = ServiceCommunicationService()
        
        event = communication_service.emit_event(
            event_type='book.created',
            source_service='catalog_service',
            event_data=book_data
        )
        
        self.assertEqual(event.event_type, 'book.created')
        self.assertEqual(event.source_service, 'catalog_service')
        
        # 3. Vérifier que l'événement a été créé
        self.assertTrue(
            CrossServiceEvent.objects.filter(
                event_type='book.created',
                source_service='catalog_service'
            ).exists()
        )
        
        # 4. Récupérer la référence
        retrieved_ref = reference_service.get_book_reference(book_uuid)
        self.assertEqual(retrieved_ref.book_uuid, book_uuid)
        self.assertEqual(retrieved_ref.title, 'Integration Test Book')


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
})
class CacheTestCase(TestCase):
    """Tests pour la gestion du cache"""
    
    def setUp(self):
        self.client = CatalogServiceClient()
        self.book_uuid = uuid.uuid4()
    
    @patch('shared_models.api_client.requests.Session.get')
    def test_cache_behavior(self, mock_get):
        """Test du comportement du cache"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': str(self.book_uuid),
            'title': 'Cached Book'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Premier appel - doit faire une requête réseau
        book_data1 = self.client.get_book(self.book_uuid)
        self.assertEqual(mock_get.call_count, 1)
        
        # Deuxième appel - doit utiliser le cache
        book_data2 = self.client.get_book(self.book_uuid)
        self.assertEqual(mock_get.call_count, 1)  # Pas d'appel supplémentaire
        
        # Vérifier que les données sont identiques
        self.assertEqual(book_data1, book_data2)