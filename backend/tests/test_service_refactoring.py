"""
Tests pour valider la refactorisation des dépendances inter-services
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import Mock, patch
from datetime import timedelta

from coko.interfaces import BookServiceInterface, ReadingServiceInterface
from coko.services import BookService, ReadingService, get_book_service, get_reading_service
from coko.events import EventBus, Event, EventType, publish_event
from recommendation_service.service_adapters import RecommendationServiceAdapter
from recommendation_service.utils_refactored import (
    generate_personalized_recommendations,
    generate_popularity_based_recommendations_via_service
)

User = get_user_model()


class TestServiceInterfaces(TestCase):
    """Tests pour valider les interfaces de service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.book_service = BookService()
        self.reading_service = ReadingService()
    
    def test_book_service_interface(self):
        """Tester que BookService implémente correctement l'interface"""
        self.assertIsInstance(self.book_service, BookServiceInterface)
        
        # Vérifier que toutes les méthodes de l'interface sont présentes
        interface_methods = [
            'get_book_by_id',
            'get_books_by_category',
            'get_books_by_author',
            'get_popular_books',
            'search_books',
            'get_book_categories',
            'get_book_authors'
        ]
        
        for method_name in interface_methods:
            self.assertTrue(hasattr(self.book_service, method_name))
            self.assertTrue(callable(getattr(self.book_service, method_name)))
    
    def test_reading_service_interface(self):
        """Tester que ReadingService implémente correctement l'interface"""
        self.assertIsInstance(self.reading_service, ReadingServiceInterface)
        
        # Vérifier que toutes les méthodes de l'interface sont présentes
        interface_methods = [
            'get_user_reading_history',
            'get_user_current_books',
            'get_user_completed_books',
            'get_user_bookmarks',
            'get_reading_statistics',
            'has_user_read_book'
        ]
        
        for method_name in interface_methods:
            self.assertTrue(hasattr(self.reading_service, method_name))
            self.assertTrue(callable(getattr(self.reading_service, method_name)))
    
    def test_service_factory_functions(self):
        """Tester les fonctions factory des services"""
        book_service = get_book_service()
        reading_service = get_reading_service()
        
        self.assertIsInstance(book_service, BookServiceInterface)
        self.assertIsInstance(reading_service, ReadingServiceInterface)
        
        # Vérifier que les instances sont les mêmes (singleton)
        self.assertIs(book_service, get_book_service())
        self.assertIs(reading_service, get_reading_service())


class TestEventSystem(TestCase):
    """Tests pour valider le système d'événements"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.event_bus = EventBus()
        self.received_events = []
    
    def event_handler(self, event: Event):
        """Handler de test pour capturer les événements"""
        self.received_events.append(event)
    
    def test_event_subscription_and_publishing(self):
        """Tester l'abonnement et la publication d'événements"""
        # S'abonner à un événement
        self.event_bus.subscribe(EventType.BOOK_COMPLETED, self.event_handler)
        
        # Publier un événement
        event_data = {'book_id': 123, 'completion_time': timezone.now()}
        publish_event(
            EventType.BOOK_COMPLETED,
            event_data,
            user_id=self.user.id,
            source_service='test_service'
        )
        
        # Vérifier que l'événement a été reçu
        self.assertEqual(len(self.received_events), 1)
        received_event = self.received_events[0]
        self.assertEqual(received_event.type, EventType.BOOK_COMPLETED)
        self.assertEqual(received_event.data, event_data)
        self.assertEqual(received_event.user_id, self.user.id)
        self.assertEqual(received_event.source_service, 'test_service')
    
    def test_multiple_handlers(self):
        """Tester plusieurs handlers pour le même événement"""
        received_events_2 = []
        
        def second_handler(event: Event):
            received_events_2.append(event)
        
        # S'abonner avec deux handlers
        self.event_bus.subscribe(EventType.USER_INTERACTION_RECORDED, self.event_handler)
        self.event_bus.subscribe(EventType.USER_INTERACTION_RECORDED, second_handler)
        
        # Publier un événement
        event_data = {'interaction_type': 'click', 'book_id': 456}
        publish_event(
            EventType.USER_INTERACTION_RECORDED,
            event_data,
            user_id=self.user.id,
            source_service='test_service'
        )
        
        # Vérifier que les deux handlers ont reçu l'événement
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(len(received_events_2), 1)


class TestRecommendationServiceAdapter(TestCase):
    """Tests pour l'adaptateur du service de recommandations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.adapter = RecommendationServiceAdapter()
    
    @patch('coko.services.BookService.get_book_by_id')
    @patch('coko.services.BookService.get_books_by_category')
    def test_content_based_recommendations_via_service(self, mock_get_books_by_category, mock_get_book_by_id):
        """Tester les recommandations basées sur le contenu via les services"""
        # Mock des données de livre
        mock_book_data = {
            'id': 1,
            'title': 'Test Book',
            'authors': ['Test Author'],
            'categories': ['Fiction'],
            'average_rating': 4.5
        }
        
        mock_get_book_by_id.return_value = mock_book_data
        mock_get_books_by_category.return_value = [mock_book_data]
        
        # Créer un profil utilisateur avec des préférences
        from recommendation_service.models import UserProfile
        user_profile = UserProfile.objects.create(
            user=self.user,
            preferred_genres=['Fiction'],
            preferred_authors=['Test Author']
        )
        
        # Générer des recommandations
        recommendations = self.adapter.generate_content_based_recommendations(
            self.user, user_profile, set(), 5, 'general'
        )
        
        # Vérifications
        self.assertIsInstance(recommendations, list)
        self.assertTrue(len(recommendations) <= 5)
        
        if recommendations:
            book_data, score, reasons = recommendations[0]
            self.assertIsInstance(book_data, dict)
            self.assertIsInstance(score, float)
            self.assertIsInstance(reasons, list)
            self.assertTrue(0 <= score <= 1)
    
    @patch('coko.services.BookService.get_book_by_id')
    def test_record_interaction_via_service(self, mock_get_book_by_id):
        """Tester l'enregistrement d'interactions via les services"""
        # Mock des données de livre
        mock_book_data = {
            'id': 1,
            'title': 'Test Book',
            'authors': ['Test Author']
        }
        mock_get_book_by_id.return_value = mock_book_data
        
        # Enregistrer une interaction
        self.adapter.record_interaction_via_service(
            self.user.id,
            1,
            'click',
            {'source': 'recommendation'}
        )
        
        # Vérifier que le service a été appelé
        mock_get_book_by_id.assert_called_once_with(1)


class TestDecoupledRecommendations(TestCase):
    """Tests pour les recommandations découplées"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('coko.services.get_book_service')
    @patch('coko.services.get_reading_service')
    def test_generate_personalized_recommendations_via_services(self, mock_reading_service, mock_book_service):
        """Tester la génération de recommandations personnalisées via les services"""
        # Mock des services
        mock_book_service.return_value.get_popular_books.return_value = [
            {
                'id': 1,
                'title': 'Popular Book',
                'authors': ['Popular Author'],
                'categories': ['Fiction'],
                'average_rating': 4.5
            }
        ]
        
        mock_reading_service.return_value.get_user_reading_history.return_value = []
        
        # Générer des recommandations
        result = generate_personalized_recommendations(
            self.user,
            algorithm='popularity',
            count=5,
            context='general'
        )
        
        # Vérifications
        self.assertIsInstance(result, dict)
        self.assertIn('books', result)
        self.assertIn('algorithm_used', result)
        self.assertIn('confidence_score', result)
        self.assertEqual(result['algorithm_used'], 'popularity')
    
    @patch('coko.services.get_book_service')
    def test_popularity_based_recommendations_via_service(self, mock_book_service):
        """Tester les recommandations basées sur la popularité via les services"""
        # Mock du service de livres
        mock_books = [
            {
                'id': 1,
                'title': 'Popular Book 1',
                'average_rating': 4.8
            },
            {
                'id': 2,
                'title': 'Popular Book 2',
                'average_rating': 4.5
            }
        ]
        mock_book_service.return_value.get_popular_books.return_value = mock_books
        
        # Créer un profil utilisateur
        from recommendation_service.models import UserProfile
        user_profile = UserProfile.objects.create(user=self.user)
        
        # Générer des recommandations
        recommendations = generate_popularity_based_recommendations_via_service(
            self.user, user_profile, set(), 5, 'general'
        )
        
        # Vérifications
        self.assertIsInstance(recommendations, list)
        self.assertEqual(len(recommendations), 2)
        
        book_data, score, reasons = recommendations[0]
        self.assertEqual(book_data['id'], 1)
        self.assertGreater(score, 0)
        self.assertIn('Livre populaire', reasons)


class TestServiceDecoupling(TestCase):
    """Tests pour valider le découplage des services"""
    
    def test_no_direct_model_imports_in_recommendation_utils(self):
        """Vérifier qu'il n'y a plus d'imports directs de modèles dans les utils refactorisés"""
        import recommendation_service.utils_refactored as refactored_utils
        import inspect
        
        # Obtenir le code source du module
        source_code = inspect.getsource(refactored_utils)
        
        # Vérifier qu'il n'y a plus d'imports directs problématiques
        forbidden_imports = [
            'from catalog_service.models import',
            'from reading_service.models import'
        ]
        
        for forbidden_import in forbidden_imports:
            self.assertNotIn(forbidden_import, source_code, 
                           f"Import direct trouvé: {forbidden_import}")
    
    def test_service_interfaces_used_in_adapters(self):
        """Vérifier que les adaptateurs utilisent les interfaces de service"""
        from recommendation_service.service_adapters import RecommendationServiceAdapter
        
        adapter = RecommendationServiceAdapter()
        
        # Vérifier que l'adaptateur utilise les interfaces
        self.assertIsInstance(adapter.book_service, BookServiceInterface)
        self.assertIsInstance(adapter.reading_service, ReadingServiceInterface)
    
    def test_event_system_integration(self):
        """Tester l'intégration du système d'événements"""
        events_received = []
        
        def test_handler(event):
            events_received.append(event.type)
        
        # S'abonner aux événements
        from coko.events import event_bus
        event_bus.subscribe(EventType.BOOK_COMPLETED, test_handler)
        
        # Publier un événement
        publish_event(
            EventType.BOOK_COMPLETED,
            {'book_id': 123},
            user_id=self.user.id if hasattr(self, 'user') else 1,
            source_service='test'
        )
        
        # Vérifier que l'événement a été traité
        self.assertIn(EventType.BOOK_COMPLETED, events_received)


# Test de performance pour valider que le découplage n'impacte pas les performances
class TestServicePerformance(TestCase):
    """Tests de performance pour la refactorisation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='testpass123'
        )
    
    @patch('coko.services.BookService.get_popular_books')
    def test_recommendation_generation_performance(self, mock_get_popular_books):
        """Tester que la génération de recommandations reste performante"""
        import time
        
        # Mock avec de nombreux livres
        mock_books = [
            {
                'id': i,
                'title': f'Book {i}',
                'authors': [f'Author {i}'],
                'categories': ['Fiction'],
                'average_rating': 4.0
            }
            for i in range(100)
        ]
        mock_get_popular_books.return_value = mock_books
        
        # Mesurer le temps de génération
        start_time = time.time()
        
        result = generate_personalized_recommendations(
            self.user,
            algorithm='popularity',
            count=10,
            context='general'
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Vérifier que le temps d'exécution est raisonnable (< 1 seconde)
        self.assertLess(execution_time, 1.0)
        self.assertIsInstance(result, dict)
        self.assertIn('books', result)


if __name__ == '__main__':
    pytest.main([__file__])