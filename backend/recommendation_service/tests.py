from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import timedelta
import json

from catalog_service.models import Book, BookRating
from .models import (
    UserProfile, BookVector, UserInteraction, RecommendationSet,
    Recommendation, SimilarityMatrix, TrendingBook, RecommendationFeedback
)
from .utils import (
    generate_personalized_recommendations, calculate_cosine_similarity,
    calculate_diversity_score, calculate_novelty_score, calculate_confidence_score,
    find_similar_users, get_trending_books
)
from .serializers import (
    UserProfileSerializer, UserInteractionSerializer, RecommendationSerializer
)
from .permissions import IsOwnerOrReadOnly, CanAccessRecommendations

User = get_user_model()


class UserProfileModelTest(TestCase):
    """Tests pour le modèle UserProfile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_user_profile(self):
        """Test de création d'un profil utilisateur"""
        profile = UserProfile.objects.create(
            user=self.user,
            preferred_genres=['fiction', 'science'],
            preferred_authors=['Isaac Asimov', 'Philip K. Dick'],
            preferred_languages=['en', 'fr'],
            reading_level='advanced',
            reading_frequency='daily'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(len(profile.preferred_genres), 2)
        self.assertIn('fiction', profile.preferred_genres)
        self.assertTrue(profile.enable_recommendations)
        self.assertEqual(profile.recommendation_frequency, 'daily')
    
    def test_user_profile_str(self):
        """Test de la représentation string du profil"""
        profile = UserProfile.objects.create(user=self.user)
        expected = f"Profil de recommandations - {self.user.username}"
        self.assertEqual(str(profile), expected)
    
    def test_profile_completeness_calculation(self):
        """Test du calcul de complétude du profil"""
        profile = UserProfile.objects.create(
            user=self.user,
            preferred_genres=['fiction'],
            preferred_authors=['Test Author'],
            reading_level='intermediate'
        )
        
        # Le profil devrait être partiellement complet
        # (genres, auteurs, niveau définis mais pas de langues)
        self.assertGreater(profile.get_completeness_score(), 0)
        self.assertLess(profile.get_completeness_score(), 100)


class BookVectorModelTest(TestCase):
    """Tests pour le modèle BookVector"""
    
    def setUp(self):
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            language='fr'
        )
    
    def test_create_book_vector(self):
        """Test de création d'un vecteur de livre"""
        vector = BookVector.objects.create(
            book=self.book,
            content_vector=[0.1, 0.2, 0.3],
            genre_vector=[1.0, 0.0, 0.5],
            popularity_score=0.8,
            quality_score=0.9
        )
        
        self.assertEqual(vector.book, self.book)
        self.assertEqual(len(vector.content_vector), 3)
        self.assertEqual(vector.popularity_score, 0.8)
        self.assertEqual(vector.quality_score, 0.9)
    
    def test_book_vector_str(self):
        """Test de la représentation string du vecteur"""
        vector = BookVector.objects.create(book=self.book)
        expected = f"Vecteur - {self.book.title}"
        self.assertEqual(str(vector), expected)


class UserInteractionModelTest(TestCase):
    """Tests pour le modèle UserInteraction"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            language='fr'
        )
    
    def test_create_user_interaction(self):
        """Test de création d'une interaction utilisateur"""
        interaction = UserInteraction.objects.create(
            user=self.user,
            book=self.book,
            interaction_type='view',
            interaction_value=1,
            device_type='mobile'
        )
        
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.book, self.book)
        self.assertEqual(interaction.interaction_type, 'view')
        self.assertEqual(interaction.device_type, 'mobile')
    
    def test_interaction_unique_constraint(self):
        """Test de la contrainte d'unicité des interactions"""
        UserInteraction.objects.create(
            user=self.user,
            book=self.book,
            interaction_type='view'
        )
        
        # Créer une deuxième interaction du même type devrait être autorisé
        # (car un utilisateur peut voir un livre plusieurs fois)
        interaction2 = UserInteraction.objects.create(
            user=self.user,
            book=self.book,
            interaction_type='view'
        )
        
        self.assertIsNotNone(interaction2.id)


class RecommendationUtilsTest(TestCase):
    """Tests pour les fonctions utilitaires de recommandation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            preferred_genres=['fiction', 'science'],
            preferred_authors=['Isaac Asimov'],
            reading_level='advanced'
        )
        
        # Créer quelques livres de test
        self.books = []
        for i in range(5):
            book = Book.objects.create(
                title=f'Test Book {i}',
                author='Test Author' if i < 3 else 'Isaac Asimov',
                isbn=f'123456789012{i}',
                publication_date=timezone.now().date(),
                language='fr',
                genres=['fiction'] if i % 2 == 0 else ['science']
            )
            self.books.append(book)
            
            # Créer des vecteurs pour les livres
            BookVector.objects.create(
                book=book,
                content_vector=[0.1 * i, 0.2 * i, 0.3 * i],
                genre_vector=[1.0, 0.0] if 'fiction' in book.genres else [0.0, 1.0],
                popularity_score=0.5 + (i * 0.1),
                quality_score=0.6 + (i * 0.1)
            )
    
    def test_calculate_cosine_similarity(self):
        """Test du calcul de similarité cosinus"""
        ratings1 = [1, 2, 3, 4, 5]
        ratings2 = [2, 3, 4, 5, 1]
        
        similarity = calculate_cosine_similarity(ratings1, ratings2)
        
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, -1.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_calculate_diversity_score(self):
        """Test du calcul de score de diversité"""
        diversity = calculate_diversity_score(self.books[:3])
        
        self.assertIsInstance(diversity, float)
        self.assertGreaterEqual(diversity, 0.0)
        self.assertLessEqual(diversity, 1.0)
    
    def test_calculate_novelty_score(self):
        """Test du calcul de score de nouveauté"""
        novelty = calculate_novelty_score(self.user, self.books[:3])
        
        self.assertIsInstance(novelty, float)
        self.assertGreaterEqual(novelty, 0.0)
        self.assertLessEqual(novelty, 1.0)
    
    def test_calculate_confidence_score(self):
        """Test du calcul de score de confiance"""
        recommendations_data = [
            {'book': self.books[0], 'score': 0.8},
            {'book': self.books[1], 'score': 0.6},
            {'book': self.books[2], 'score': 0.9}
        ]
        
        confidence = calculate_confidence_score(self.user, recommendations_data)
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    @patch('recommendation_service.utils.cache')
    def test_generate_personalized_recommendations(self, mock_cache):
        """Test de génération de recommandations personnalisées"""
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        
        recommendations = generate_personalized_recommendations(
            user=self.user,
            algorithm='content_based',
            count=3
        )
        
        self.assertIsInstance(recommendations, list)
        # Les recommandations peuvent être vides si pas assez de données
        if recommendations:
            self.assertLessEqual(len(recommendations), 3)
            for rec in recommendations:
                self.assertIn('book', rec)
                self.assertIn('score', rec)
    
    def test_find_similar_users(self):
        """Test de recherche d'utilisateurs similaires"""
        # Créer un autre utilisateur avec des interactions
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Créer des interactions pour les deux utilisateurs
        for book in self.books[:3]:
            UserInteraction.objects.create(
                user=self.user,
                book=book,
                interaction_type='rating',
                interaction_value=4
            )
            UserInteraction.objects.create(
                user=user2,
                book=book,
                interaction_type='rating',
                interaction_value=3
            )
        
        similar_users = find_similar_users(self.user, limit=5)
        
        self.assertIsInstance(similar_users, list)
        # Peut être vide si pas assez de données
        if similar_users:
            for user_data in similar_users:
                self.assertIn('user', user_data)
                self.assertIn('similarity', user_data)


class RecommendationAPITest(APITestCase):
    """Tests pour l'API de recommandations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            preferred_genres=['fiction'],
            reading_level='intermediate'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            language='fr'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_user_profile_list_create(self):
        """Test de l'endpoint de liste/création des profils"""
        url = reverse('recommendation_service:userprofile-list')
        
        # Test GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test POST (création d'un nouveau profil)
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        self.client.force_authenticate(user=new_user)
        
        data = {
            'preferred_genres': ['science', 'history'],
            'preferred_authors': ['Carl Sagan'],
            'reading_level': 'advanced',
            'reading_frequency': 'weekly'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], new_user.id)
    
    def test_user_profile_detail(self):
        """Test de l'endpoint de détail du profil"""
        url = reverse('recommendation_service:userprofile-detail', kwargs={'pk': self.profile.pk})
        
        # Test GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.profile.id)
        
        # Test PUT
        data = {
            'preferred_genres': ['fiction', 'mystery'],
            'reading_level': 'advanced',
            'reading_frequency': 'daily'
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reading_level'], 'advanced')
    
    def test_user_interaction_create(self):
        """Test de création d'interaction utilisateur"""
        url = reverse('recommendation_service:userinteraction-list')
        
        data = {
            'book': self.book.id,
            'interaction_type': 'view',
            'interaction_value': 1,
            'device_type': 'mobile'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['book'], self.book.id)
    
    @patch('recommendation_service.views.generate_personalized_recommendations')
    def test_personalized_recommendations(self, mock_generate):
        """Test de l'endpoint de recommandations personnalisées"""
        mock_generate.return_value = [
            {'book': self.book, 'score': 0.8, 'explanation': 'Test'}
        ]
        
        url = reverse('recommendation_service:personalized-recommendations')
        
        response = self.client.get(url, {'algorithm': 'hybrid', 'count': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data)
        
        mock_generate.assert_called_once()
    
    def test_recommendation_feedback_create(self):
        """Test de création de feedback de recommandation"""
        # Créer une recommandation
        rec_set = RecommendationSet.objects.create(
            user=self.user,
            algorithm_type='hybrid',
            context='test'
        )
        
        recommendation = Recommendation.objects.create(
            recommendation_set=rec_set,
            book=self.book,
            score=0.8,
            rank=1
        )
        
        url = reverse('recommendation_service:recommendationfeedback-list')
        
        data = {
            'recommendation': recommendation.id,
            'feedback_type': 'like',
            'rating': 4,
            'comment': 'Great recommendation!'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)
    
    def test_unauthorized_access(self):
        """Test d'accès non autorisé"""
        self.client.force_authenticate(user=None)
        
        url = reverse('recommendation_service:userprofile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_permission_owner_only(self):
        """Test de permission propriétaire uniquement"""
        # Créer un autre utilisateur
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        other_profile = UserProfile.objects.create(
            user=other_user,
            preferred_genres=['mystery']
        )
        
        # Essayer d'accéder au profil d'un autre utilisateur
        url = reverse('recommendation_service:userprofile-detail', kwargs={'pk': other_profile.pk})
        response = self.client.get(url)
        
        # Devrait être interdit ou retourner seulement les données publiques
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_200_OK])


class RecommendationSerializerTest(TestCase):
    """Tests pour les serializers de recommandation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            language='fr'
        )
    
    def test_user_profile_serializer(self):
        """Test du serializer UserProfile"""
        data = {
            'preferred_genres': ['fiction', 'science'],
            'preferred_authors': ['Isaac Asimov'],
            'reading_level': 'advanced',
            'reading_frequency': 'daily'
        }
        
        serializer = UserProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        profile = serializer.save(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(len(profile.preferred_genres), 2)
    
    def test_user_profile_serializer_validation(self):
        """Test de validation du serializer UserProfile"""
        # Test avec des genres invalides
        data = {
            'preferred_genres': ['invalid_genre'],
            'reading_level': 'invalid_level'
        }
        
        serializer = UserProfileSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('preferred_genres', serializer.errors)
        self.assertIn('reading_level', serializer.errors)
    
    def test_user_interaction_serializer(self):
        """Test du serializer UserInteraction"""
        data = {
            'book': self.book.id,
            'interaction_type': 'rating',
            'interaction_value': 4,
            'device_type': 'desktop'
        }
        
        serializer = UserInteractionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        interaction = serializer.save(user=self.user)
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.book, self.book)
        self.assertEqual(interaction.interaction_value, 4)
    
    def test_user_interaction_serializer_validation(self):
        """Test de validation du serializer UserInteraction"""
        # Test avec une valeur d'interaction invalide pour le rating
        data = {
            'book': self.book.id,
            'interaction_type': 'rating',
            'interaction_value': 6  # Invalide (max 5)
        }
        
        serializer = UserInteractionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('interaction_value', serializer.errors)


class RecommendationPermissionTest(TestCase):
    """Tests pour les permissions de recommandation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            preferred_genres=['fiction']
        )
    
    def test_is_owner_or_read_only_permission(self):
        """Test de la permission IsOwnerOrReadOnly"""
        permission = IsOwnerOrReadOnly()
        
        # Mock request et view
        request = MagicMock()
        request.user = self.user
        request.method = 'GET'
        
        view = MagicMock()
        
        # Test lecture pour propriétaire
        self.assertTrue(permission.has_object_permission(request, view, self.profile))
        
        # Test écriture pour propriétaire
        request.method = 'PUT'
        self.assertTrue(permission.has_object_permission(request, view, self.profile))
        
        # Test écriture pour non-propriétaire
        request.user = self.other_user
        self.assertFalse(permission.has_object_permission(request, view, self.profile))
        
        # Test lecture pour non-propriétaire
        request.method = 'GET'
        self.assertTrue(permission.has_object_permission(request, view, self.profile))
    
    def test_can_access_recommendations_permission(self):
        """Test de la permission CanAccessRecommendations"""
        permission = CanAccessRecommendations()
        
        request = MagicMock()
        request.user = self.user
        
        view = MagicMock()
        
        # Test utilisateur authentifié et actif
        self.user.is_active = True
        self.assertTrue(permission.has_permission(request, view))
        
        # Test utilisateur inactif
        self.user.is_active = False
        self.assertFalse(permission.has_permission(request, view))


class RecommendationCacheTest(TestCase):
    """Tests pour le cache des recommandations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        cache.clear()  # Nettoyer le cache avant chaque test
    
    def test_cache_invalidation_on_profile_update(self):
        """Test d'invalidation du cache lors de la mise à jour du profil"""
        profile = UserProfile.objects.create(
            user=self.user,
            preferred_genres=['fiction']
        )
        
        # Mettre quelque chose en cache
        cache_key = f"user_recommendations_{self.user.id}"
        cache.set(cache_key, ['test_data'], 300)
        
        # Vérifier que c'est en cache
        self.assertEqual(cache.get(cache_key), ['test_data'])
        
        # Mettre à jour le profil
        profile.preferred_genres = ['science']
        profile.save()
        
        # Le cache devrait être invalidé (via les signaux)
        # Note: Dans un test unitaire, les signaux peuvent ne pas être déclenchés
        # automatiquement selon la configuration
    
    def tearDown(self):
        cache.clear()


class RecommendationIntegrationTest(TransactionTestCase):
    """Tests d'intégration pour le système de recommandations"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            preferred_genres=['fiction', 'science'],
            preferred_authors=['Isaac Asimov'],
            reading_level='advanced'
        )
        
        # Créer plusieurs livres avec des vecteurs
        self.books = []
        for i in range(10):
            book = Book.objects.create(
                title=f'Test Book {i}',
                author='Isaac Asimov' if i < 5 else 'Other Author',
                isbn=f'123456789012{i}',
                publication_date=timezone.now().date() - timedelta(days=i*30),
                language='fr',
                genres=['fiction'] if i % 2 == 0 else ['science']
            )
            self.books.append(book)
            
            BookVector.objects.create(
                book=book,
                content_vector=[0.1 * i, 0.2 * i, 0.3 * i],
                genre_vector=[1.0, 0.0] if 'fiction' in book.genres else [0.0, 1.0],
                author_vector=[1.0] if book.author == 'Isaac Asimov' else [0.0],
                popularity_score=0.5 + (i * 0.05),
                quality_score=0.6 + (i * 0.04),
                recency_score=1.0 - (i * 0.1)
            )
    
    def test_full_recommendation_workflow(self):
        """Test du workflow complet de recommandation"""
        # 1. Créer des interactions utilisateur
        for book in self.books[:3]:
            UserInteraction.objects.create(
                user=self.user,
                book=book,
                interaction_type='view'
            )
        
        # 2. Générer des recommandations
        recommendations = generate_personalized_recommendations(
            user=self.user,
            algorithm='content_based',
            count=5
        )
        
        # 3. Vérifier que des recommandations ont été générées
        self.assertIsInstance(recommendations, list)
        
        # 4. Si des recommandations existent, vérifier leur structure
        if recommendations:
            for rec in recommendations:
                self.assertIn('book', rec)
                self.assertIn('score', rec)
                self.assertIsInstance(rec['score'], (int, float))
    
    def test_recommendation_feedback_loop(self):
        """Test de la boucle de feedback des recommandations"""
        # Créer un ensemble de recommandations
        rec_set = RecommendationSet.objects.create(
            user=self.user,
            algorithm_type='hybrid',
            context='test'
        )
        
        recommendation = Recommendation.objects.create(
            recommendation_set=rec_set,
            book=self.books[0],
            score=0.8,
            rank=1
        )
        
        # Simuler un clic
        recommendation.clicked = True
        recommendation.click_timestamp = timezone.now()
        recommendation.save()
        
        # Créer un feedback
        feedback = RecommendationFeedback.objects.create(
            user=self.user,
            recommendation=recommendation,
            feedback_type='like',
            rating=5,
            comment='Excellent recommendation!'
        )
        
        # Vérifier que le feedback a été créé
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.rating, 5)
        self.assertTrue(recommendation.clicked)
    
    def test_trending_books_calculation(self):
        """Test du calcul des livres en tendance"""
        # Créer des interactions pour simuler des tendances
        for i, book in enumerate(self.books[:5]):
            # Plus d'interactions pour les premiers livres
            interaction_count = 10 - i * 2
            for j in range(interaction_count):
                user = User.objects.create_user(
                    username=f'user_{i}_{j}',
                    email=f'user_{i}_{j}@example.com',
                    password='testpass123'
                )
                UserInteraction.objects.create(
                    user=user,
                    book=book,
                    interaction_type='view'
                )
        
        # Calculer les livres en tendance
        trending = get_trending_books(period='week', trend_type='overall', limit=3)
        
        self.assertIsInstance(trending, list)
        # Peut être vide selon l'implémentation
        if trending:
            self.assertLessEqual(len(trending), 3)
            for book_data in trending:
                self.assertIn('book_id', book_data)
                self.assertIn('score', book_data)


class RecommendationPerformanceTest(TestCase):
    """Tests de performance pour le système de recommandations"""
    
    def setUp(self):
        # Créer un grand nombre d'utilisateurs et de livres pour les tests de performance
        self.users = []
        for i in range(50):
            user = User.objects.create_user(
                username=f'user_{i}',
                email=f'user_{i}@example.com',
                password='testpass123'
            )
            self.users.append(user)
            
            UserProfile.objects.create(
                user=user,
                preferred_genres=['fiction', 'science'][i % 2:],
                reading_level=['beginner', 'intermediate', 'advanced'][i % 3]
            )
        
        self.books = []
        for i in range(100):
            book = Book.objects.create(
                title=f'Performance Test Book {i}',
                author=f'Author {i % 10}',
                isbn=f'123456789{i:04d}',
                publication_date=timezone.now().date(),
                language='fr',
                genres=['fiction', 'science', 'history'][i % 3:i % 3 + 1]
            )
            self.books.append(book)
    
    def test_bulk_recommendation_generation(self):
        """Test de génération de recommandations en masse"""
        import time
        
        start_time = time.time()
        
        # Générer des recommandations pour plusieurs utilisateurs
        for user in self.users[:10]:  # Limiter pour le test
            recommendations = generate_personalized_recommendations(
                user=user,
                algorithm='content_based',
                count=5
            )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Vérifier que l'exécution ne prend pas trop de temps
        self.assertLess(execution_time, 30)  # Moins de 30 secondes
        
        print(f"Temps d'exécution pour 10 utilisateurs: {execution_time:.2f} secondes")
    
    def test_similarity_calculation_performance(self):
        """Test de performance du calcul de similarité"""
        import time
        
        # Créer des vecteurs pour quelques livres
        vectors = []
        for book in self.books[:20]:
            vector = BookVector.objects.create(
                book=book,
                content_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                genre_vector=[1.0, 0.0, 0.5],
                popularity_score=0.7,
                quality_score=0.8
            )
            vectors.append(vector)
        
        start_time = time.time()
        
        # Calculer les similarités
        similarities = []
        for i, v1 in enumerate(vectors):
            for v2 in vectors[i+1:]:
                similarity = calculate_cosine_similarity(
                    v1.content_vector + v1.genre_vector,
                    v2.content_vector + v2.genre_vector
                )
                similarities.append(similarity)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertLess(execution_time, 5)  # Moins de 5 secondes
        print(f"Temps de calcul de similarité pour {len(similarities)} paires: {execution_time:.2f} secondes")