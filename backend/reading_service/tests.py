from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from decimal import Decimal

from catalog_service.models import Book, Author, Publisher, Category
from .models import (
    ReadingSession, ReadingProgress, Bookmark, 
    ReadingGoal, ReadingStatistics
)
from .utils import (
    calculate_reading_statistics, calculate_reading_consistency,
    get_reading_recommendations, update_reading_goals,
    generate_reading_insights, calculate_reading_streak
)

User = get_user_model()


class ReadingSessionModelTest(TestCase):
    """Tests pour le modèle ReadingSession"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer un livre de test
        self.category = Category.objects.create(name='Fiction', slug='fiction')
        self.author = Author.objects.create(
            first_name='Test',
            last_name='Author',
            slug='test-author'
        )
        self.publisher = Publisher.objects.create(
            name='Test Publisher',
            slug='test-publisher'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            slug='test-book',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            page_count=300,
            language='fr',
            status='published',
            category=self.category,
            publisher=self.publisher
        )
        self.book.authors.add(self.author)
    
    def test_reading_session_creation(self):
        """Test de création d'une session de lecture"""
        session = ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            device_type='mobile',
            device_info='iPhone 12'
        )
        
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.book, self.book)
        self.assertEqual(session.status, 'active')
        self.assertEqual(session.current_page, 1)
        self.assertEqual(session.total_pages_read, 0)
        self.assertIsNotNone(session.start_time)
        self.assertIsNone(session.end_time)
    
    def test_reading_session_completion(self):
        """Test de completion d'une session de lecture"""
        session = ReadingSession.objects.create(
            user=self.user,
            book=self.book
        )
        
        # Marquer comme complétée
        session.status = 'completed'
        session.end_time = timezone.now()
        session.current_page = self.book.page_count
        session.save()
        
        self.assertEqual(session.status, 'completed')
        self.assertIsNotNone(session.end_time)
        self.assertEqual(session.current_page, self.book.page_count)
    
    def test_reading_session_progress_percentage(self):
        """Test du calcul du pourcentage de progression"""
        session = ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            current_page=150
        )
        
        expected_progress = (150 / 300) * 100
        self.assertEqual(session.progress_percentage, expected_progress)
    
    def test_reading_session_str(self):
        """Test de la représentation string"""
        session = ReadingSession.objects.create(
            user=self.user,
            book=self.book
        )
        
        expected_str = f"{self.user.username} - {self.book.title}"
        self.assertEqual(str(session), expected_str)


class ReadingProgressModelTest(TestCase):
    """Tests pour le modèle ReadingProgress"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer un livre et une session
        self.category = Category.objects.create(name='Fiction', slug='fiction')
        self.author = Author.objects.create(
            first_name='Test',
            last_name='Author',
            slug='test-author'
        )
        self.publisher = Publisher.objects.create(
            name='Test Publisher',
            slug='test-publisher'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            slug='test-book',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            page_count=300,
            language='fr',
            status='published',
            category=self.category,
            publisher=self.publisher
        )
        self.book.authors.add(self.author)
        
        self.session = ReadingSession.objects.create(
            user=self.user,
            book=self.book
        )
    
    def test_reading_progress_creation(self):
        """Test de création d'un progrès de lecture"""
        progress = ReadingProgress.objects.create(
            session=self.session,
            page_number=50,
            time_spent=timedelta(minutes=30),
            reading_speed=250
        )
        
        self.assertEqual(progress.session, self.session)
        self.assertEqual(progress.page_number, 50)
        self.assertEqual(progress.time_spent, timedelta(minutes=30))
        self.assertEqual(progress.reading_speed, 250)
        self.assertIsNotNone(progress.timestamp)
    
    def test_reading_progress_str(self):
        """Test de la représentation string"""
        progress = ReadingProgress.objects.create(
            session=self.session,
            page_number=50
        )
        
        expected_str = f"{self.session} - Page 50"
        self.assertEqual(str(progress), expected_str)


class BookmarkModelTest(TestCase):
    """Tests pour le modèle Bookmark"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer un livre
        self.category = Category.objects.create(name='Fiction', slug='fiction')
        self.author = Author.objects.create(
            first_name='Test',
            last_name='Author',
            slug='test-author'
        )
        self.publisher = Publisher.objects.create(
            name='Test Publisher',
            slug='test-publisher'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            slug='test-book',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            page_count=300,
            language='fr',
            status='published',
            category=self.category,
            publisher=self.publisher
        )
        self.book.authors.add(self.author)
    
    def test_bookmark_creation(self):
        """Test de création d'un signet"""
        bookmark = Bookmark.objects.create(
            user=self.user,
            book=self.book,
            page_number=100,
            bookmark_type='bookmark',
            title='Chapitre important',
            content='Passage intéressant à retenir'
        )
        
        self.assertEqual(bookmark.user, self.user)
        self.assertEqual(bookmark.book, self.book)
        self.assertEqual(bookmark.page_number, 100)
        self.assertEqual(bookmark.bookmark_type, 'bookmark')
        self.assertEqual(bookmark.title, 'Chapitre important')
        self.assertFalse(bookmark.is_public)
        self.assertFalse(bookmark.is_favorite)
    
    def test_bookmark_str(self):
        """Test de la représentation string"""
        bookmark = Bookmark.objects.create(
            user=self.user,
            book=self.book,
            page_number=100,
            title='Test Bookmark'
        )
        
        expected_str = f"{self.user.username} - {self.book.title} - Page 100"
        self.assertEqual(str(bookmark), expected_str)


class ReadingGoalModelTest(TestCase):
    """Tests pour le modèle ReadingGoal"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_reading_goal_creation(self):
        """Test de création d'un objectif de lecture"""
        goal = ReadingGoal.objects.create(
            user=self.user,
            title='Lire 12 livres cette année',
            goal_type='books_per_year',
            target_value=12,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365)
        )
        
        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.title, 'Lire 12 livres cette année')
        self.assertEqual(goal.goal_type, 'books_per_year')
        self.assertEqual(goal.target_value, 12)
        self.assertEqual(goal.current_value, 0)
        self.assertEqual(goal.status, 'active')
        self.assertFalse(goal.is_completed)
    
    def test_reading_goal_progress_percentage(self):
        """Test du calcul du pourcentage de progression"""
        goal = ReadingGoal.objects.create(
            user=self.user,
            title='Test Goal',
            goal_type='books_per_year',
            target_value=10,
            current_value=3,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365)
        )
        
        self.assertEqual(goal.progress_percentage, 30.0)
    
    def test_reading_goal_completion(self):
        """Test de la completion d'un objectif"""
        goal = ReadingGoal.objects.create(
            user=self.user,
            title='Test Goal',
            goal_type='books_per_year',
            target_value=5,
            current_value=5,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365)
        )
        
        self.assertTrue(goal.is_completed)
        self.assertEqual(goal.progress_percentage, 100.0)


class ReadingStatisticsModelTest(TestCase):
    """Tests pour le modèle ReadingStatistics"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_reading_statistics_creation(self):
        """Test de création de statistiques de lecture"""
        stats = ReadingStatistics.objects.create(
            user=self.user,
            period_type='monthly',
            period_start=timezone.now().date().replace(day=1),
            period_end=timezone.now().date(),
            books_started=5,
            books_completed=3,
            pages_read=450,
            total_reading_time=timedelta(hours=15),
            reading_sessions_count=20
        )
        
        self.assertEqual(stats.user, self.user)
        self.assertEqual(stats.period_type, 'monthly')
        self.assertEqual(stats.books_started, 5)
        self.assertEqual(stats.books_completed, 3)
        self.assertEqual(stats.pages_read, 450)
        self.assertEqual(stats.reading_sessions_count, 20)
    
    def test_reading_statistics_str(self):
        """Test de la représentation string"""
        stats = ReadingStatistics.objects.create(
            user=self.user,
            period_type='monthly',
            period_start=timezone.now().date().replace(day=1),
            period_end=timezone.now().date()
        )
        
        expected_str = f"{self.user.username} - monthly - {stats.period_start}"
        self.assertEqual(str(stats), expected_str)


class ReadingUtilsTest(TestCase):
    """Tests pour les fonctions utilitaires"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer des données de test
        self.category = Category.objects.create(name='Fiction', slug='fiction')
        self.author = Author.objects.create(
            first_name='Test',
            last_name='Author',
            slug='test-author'
        )
        self.publisher = Publisher.objects.create(
            name='Test Publisher',
            slug='test-publisher'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            slug='test-book',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            page_count=300,
            language='fr',
            status='published',
            category=self.category,
            publisher=self.publisher
        )
        self.book.authors.add(self.author)
        
        # Créer une session de lecture
        self.session = ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            status='completed',
            current_page=300,
            total_pages_read=300,
            total_reading_time=timedelta(hours=5),
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now()
        )
    
    def test_calculate_reading_statistics(self):
        """Test du calcul des statistiques de lecture"""
        stats = calculate_reading_statistics(self.user, 'daily')
        
        self.assertIn('session_stats', stats)
        self.assertIn('bookmark_stats', stats)
        self.assertIn('progress_stats', stats)
        
        session_stats = stats['session_stats']
        self.assertGreaterEqual(session_stats['total_sessions'], 1)
        self.assertGreaterEqual(session_stats['books_completed'], 1)
    
    def test_calculate_reading_consistency(self):
        """Test du calcul de la consistance de lecture"""
        consistency = calculate_reading_consistency(self.user, 'weekly')
        
        self.assertIsInstance(consistency, float)
        self.assertGreaterEqual(consistency, 0)
        self.assertLessEqual(consistency, 100)
    
    def test_get_reading_recommendations(self):
        """Test des recommandations de lecture"""
        recommendations = get_reading_recommendations(self.user, limit=5)
        
        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 5)
    
    def test_update_reading_goals(self):
        """Test de la mise à jour des objectifs de lecture"""
        # Créer un objectif
        goal = ReadingGoal.objects.create(
            user=self.user,
            title='Test Goal',
            goal_type='books_per_year',
            target_value=10,
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=timezone.now().date() + timedelta(days=335)
        )
        
        # Mettre à jour les objectifs
        update_reading_goals(self.user)
        
        # Recharger l'objectif
        goal.refresh_from_db()
        
        # Vérifier que la valeur actuelle a été mise à jour
        self.assertGreaterEqual(goal.current_value, 1)
    
    def test_calculate_reading_streak(self):
        """Test du calcul de la série de lecture"""
        streak = calculate_reading_streak(self.user)
        
        self.assertIsInstance(streak, int)
        self.assertGreaterEqual(streak, 0)
    
    def test_generate_reading_insights(self):
        """Test de la génération d'insights de lecture"""
        insights = generate_reading_insights(self.user)
        
        self.assertIsInstance(insights, dict)
        self.assertIn('reading_speed', insights)
        self.assertIn('consistency', insights)
        self.assertIn('preferred_times', insights)


class ReadingAPITest(APITestCase):
    """Tests pour l'API de lecture"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer un livre de test
        self.category = Category.objects.create(name='Fiction', slug='fiction')
        self.author = Author.objects.create(
            first_name='Test',
            last_name='Author',
            slug='test-author'
        )
        self.publisher = Publisher.objects.create(
            name='Test Publisher',
            slug='test-publisher'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            slug='test-book',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            page_count=300,
            language='fr',
            status='published',
            category=self.category,
            publisher=self.publisher
        )
        self.book.authors.add(self.author)
    
    def test_reading_sessions_list_authenticated(self):
        """Test de la liste des sessions de lecture (authentifié)"""
        self.client.force_authenticate(user=self.user)
        
        # Créer une session
        ReadingSession.objects.create(
            user=self.user,
            book=self.book
        )
        
        url = reverse('reading_service:reading-sessions-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_reading_sessions_list_unauthenticated(self):
        """Test de la liste des sessions de lecture (non authentifié)"""
        url = reverse('reading_service:reading-sessions-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_reading_session(self):
        """Test de création d'une session de lecture"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('reading_service:reading-sessions-list')
        data = {
            'book': self.book.id,
            'device_type': 'mobile',
            'device_info': 'iPhone 12'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReadingSession.objects.count(), 1)
        
        session = ReadingSession.objects.first()
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.book, self.book)
    
    def test_bookmarks_list(self):
        """Test de la liste des signets"""
        self.client.force_authenticate(user=self.user)
        
        # Créer un signet
        Bookmark.objects.create(
            user=self.user,
            book=self.book,
            page_number=100,
            title='Test Bookmark'
        )
        
        url = reverse('reading_service:bookmarks-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_bookmark(self):
        """Test de création d'un signet"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('reading_service:bookmarks-list')
        data = {
            'book': self.book.id,
            'page_number': 150,
            'bookmark_type': 'highlight',
            'title': 'Passage important',
            'content': 'Texte surligné'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bookmark.objects.count(), 1)
        
        bookmark = Bookmark.objects.first()
        self.assertEqual(bookmark.user, self.user)
        self.assertEqual(bookmark.book, self.book)
        self.assertEqual(bookmark.page_number, 150)
    
    def test_reading_goals_list(self):
        """Test de la liste des objectifs de lecture"""
        self.client.force_authenticate(user=self.user)
        
        # Créer un objectif
        ReadingGoal.objects.create(
            user=self.user,
            title='Test Goal',
            goal_type='books_per_year',
            target_value=12,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365)
        )
        
        url = reverse('reading_service:reading-goals-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_reading_goal(self):
        """Test de création d'un objectif de lecture"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('reading_service:reading-goals-list')
        data = {
            'title': 'Lire 24 livres cette année',
            'goal_type': 'books_per_year',
            'target_value': 24,
            'start_date': timezone.now().date().isoformat(),
            'end_date': (timezone.now().date() + timedelta(days=365)).isoformat()
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReadingGoal.objects.count(), 1)
        
        goal = ReadingGoal.objects.first()
        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.title, 'Lire 24 livres cette année')
        self.assertEqual(goal.target_value, 24)
    
    def test_reading_dashboard(self):
        """Test du tableau de bord de lecture"""
        self.client.force_authenticate(user=self.user)
        
        # Créer des données de test
        session = ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            status='completed',
            total_pages_read=100,
            total_reading_time=timedelta(hours=2)
        )
        
        Bookmark.objects.create(
            user=self.user,
            book=self.book,
            page_number=50
        )
        
        ReadingGoal.objects.create(
            user=self.user,
            title='Test Goal',
            goal_type='books_per_year',
            target_value=12,
            current_value=1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365)
        )
        
        url = reverse('reading_service:reading-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('current_sessions', data)
        self.assertIn('recent_bookmarks', data)
        self.assertIn('active_goals', data)
        self.assertIn('reading_stats', data)
    
    def test_reading_statistics(self):
        """Test des statistiques de lecture"""
        self.client.force_authenticate(user=self.user)
        
        # Créer des données de test
        ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            status='completed',
            total_pages_read=200,
            total_reading_time=timedelta(hours=3)
        )
        
        url = reverse('reading_service:reading-statistics')
        response = self.client.get(url, {'period': 'monthly'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('session_stats', data)
        self.assertIn('bookmark_stats', data)
        self.assertIn('progress_stats', data)
    
    def test_health_check(self):
        """Test du health check"""
        url = reverse('reading_service:health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['service'], 'reading_service')


class ReadingPermissionsTest(APITestCase):
    """Tests pour les permissions de lecture"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Créer un livre de test
        self.category = Category.objects.create(name='Fiction', slug='fiction')
        self.author = Author.objects.create(
            first_name='Test',
            last_name='Author',
            slug='test-author'
        )
        self.publisher = Publisher.objects.create(
            name='Test Publisher',
            slug='test-publisher'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            slug='test-book',
            isbn='1234567890123',
            publication_date=timezone.now().date(),
            page_count=300,
            language='fr',
            status='published',
            category=self.category,
            publisher=self.publisher
        )
        self.book.authors.add(self.author)
        
        # Créer une session pour user1
        self.session = ReadingSession.objects.create(
            user=self.user1,
            book=self.book
        )
    
    def test_user_can_only_access_own_sessions(self):
        """Test que l'utilisateur ne peut accéder qu'à ses propres sessions"""
        # User1 peut voir sa session
        self.client.force_authenticate(user=self.user1)
        url = reverse('reading_service:reading-sessions-detail', kwargs={'pk': self.session.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User2 ne peut pas voir la session de user1
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_can_only_modify_own_sessions(self):
        """Test que l'utilisateur ne peut modifier que ses propres sessions"""
        # User1 peut modifier sa session
        self.client.force_authenticate(user=self.user1)
        url = reverse('reading_service:reading-sessions-detail', kwargs={'pk': self.session.pk})
        data = {'current_page': 50}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User2 ne peut pas modifier la session de user1
        self.client.force_authenticate(user=self.user2)
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_public_bookmark_visibility(self):
        """Test de la visibilité des signets publics"""
        # Créer un signet public
        bookmark = Bookmark.objects.create(
            user=self.user1,
            book=self.book,
            page_number=100,
            title='Public Bookmark',
            is_public=True
        )
        
        # User2 peut voir le signet public de user1
        self.client.force_authenticate(user=self.user2)
        url = reverse('reading_service:bookmarks-detail', kwargs={'pk': bookmark.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Mais ne peut pas le modifier
        data = {'title': 'Modified Title'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)