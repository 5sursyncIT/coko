from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from datetime import date
import tempfile
import os

from .models import (
    Book, Author, Publisher, Category, Series, BookFile, 
    BookRating, BookTag, BookTagAssignment, BookCollection
)

User = get_user_model()


class CategoryModelTest(TestCase):
    """Tests pour le modèle Category"""
    
    def setUp(self):
        self.parent_category = Category.objects.create(
            name="Fiction",
            description="Livres de fiction"
        )
        
        self.child_category = Category.objects.create(
            name="Science-Fiction",
            description="Livres de science-fiction",
            parent=self.parent_category
        )
    
    def test_category_creation(self):
        """Test de création d'une catégorie"""
        self.assertEqual(self.parent_category.name, "Fiction")
        self.assertTrue(self.parent_category.is_active)
        self.assertIsNotNone(self.parent_category.slug)
    
    def test_category_hierarchy(self):
        """Test de la hiérarchie des catégories"""
        self.assertEqual(self.child_category.parent, self.parent_category)
        self.assertIn(self.child_category, self.parent_category.subcategories.all())
    
    def test_full_path(self):
        """Test du chemin complet de la catégorie"""
        expected_path = f"{self.parent_category.name} > {self.child_category.name}"
        self.assertEqual(self.child_category.full_path, expected_path)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        self.assertEqual(str(self.parent_category), "Fiction")


class AuthorModelTest(TestCase):
    """Tests pour le modèle Author"""
    
    def setUp(self):
        self.author = Author.objects.create(
            first_name="Isaac",
            last_name="Asimov",
            biography="Auteur de science-fiction",
            birth_date=date(1920, 1, 2),
            nationality="Américain"
        )
    
    def test_author_creation(self):
        """Test de création d'un auteur"""
        self.assertEqual(self.author.first_name, "Isaac")
        self.assertEqual(self.author.last_name, "Asimov")
        self.assertIsNotNone(self.author.slug)
    
    def test_full_name(self):
        """Test du nom complet"""
        self.assertEqual(self.author.full_name, "Isaac Asimov")
    
    def test_age_calculation(self):
        """Test du calcul de l'âge"""
        # L'auteur est décédé, donc on teste avec une date de décès
        self.author.death_date = date(1992, 4, 6)
        self.author.save()
        self.assertEqual(self.author.age, 72)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        self.assertEqual(str(self.author), "Isaac Asimov")


class PublisherModelTest(TestCase):
    """Tests pour le modèle Publisher"""
    
    def setUp(self):
        self.publisher = Publisher.objects.create(
            name="Gallimard",
            description="Maison d'édition française",
            founded_year=1911,
            country="France"
        )
    
    def test_publisher_creation(self):
        """Test de création d'un éditeur"""
        self.assertEqual(self.publisher.name, "Gallimard")
        self.assertEqual(self.publisher.founded_year, 1911)
        self.assertIsNotNone(self.publisher.slug)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        self.assertEqual(str(self.publisher), "Gallimard")


class SeriesModelTest(TestCase):
    """Tests pour le modèle Series"""
    
    def setUp(self):
        self.series = Series.objects.create(
            title="Foundation",
            description="Série de science-fiction",
            total_books=7,
            is_completed=True
        )
    
    def test_series_creation(self):
        """Test de création d'une série"""
        self.assertEqual(self.series.title, "Foundation")
        self.assertEqual(self.series.total_books, 7)
        self.assertTrue(self.series.is_completed)
        self.assertIsNotNone(self.series.slug)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        self.assertEqual(str(self.series), "Foundation")


class BookModelTest(TestCase):
    """Tests pour le modèle Book"""
    
    def setUp(self):
        self.author = Author.objects.create(
            first_name="Isaac",
            last_name="Asimov"
        )
        
        self.publisher = Publisher.objects.create(
            name="Gallimard"
        )
        
        self.category = Category.objects.create(
            name="Science-Fiction"
        )
        
        self.series = Series.objects.create(
            title="Foundation"
        )
        
        self.book = Book.objects.create(
            title="Foundation",
            description="Premier livre de la série Foundation",
            publisher=self.publisher,
            series=self.series,
            isbn="978-2-07-029552-3",
            language="fr",
            page_count=250,
            publication_date=date(1951, 5, 1),
            status="published"
        )
        
        self.book.authors.add(self.author)
        self.book.categories.add(self.category)
    
    def test_book_creation(self):
        """Test de création d'un livre"""
        self.assertEqual(self.book.title, "Foundation")
        self.assertEqual(self.book.status, "published")
        self.assertIsNotNone(self.book.slug)
    
    def test_full_title(self):
        """Test du titre complet"""
        self.book.subtitle = "L'avenir de l'humanité"
        expected_title = "Foundation - L'avenir de l'humanité"
        self.assertEqual(self.book.full_title, expected_title)
    
    def test_authors_list(self):
        """Test de la liste des auteurs"""
        self.assertEqual(self.book.authors_list, "Isaac Asimov")
    
    def test_is_available(self):
        """Test de la disponibilité"""
        self.assertTrue(self.book.is_available)
        
        # Livre en brouillon
        self.book.status = "draft"
        self.assertFalse(self.book.is_available)
    
    def test_str_representation(self):
        """Test de la représentation string"""
        self.assertEqual(str(self.book), "Foundation")


class BookRatingModelTest(TestCase):
    """Tests pour le modèle BookRating"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.book = Book.objects.create(
            title="Test Book",
            status="published"
        )
        
        self.rating = BookRating.objects.create(
            book=self.book,
            user=self.user,
            score=5,
            review="Excellent livre!"
        )
    
    def test_rating_creation(self):
        """Test de création d'une évaluation"""
        self.assertEqual(self.rating.score, 5)
        self.assertEqual(self.rating.review, "Excellent livre!")
        self.assertEqual(self.rating.book, self.book)
        self.assertEqual(self.rating.user, self.user)
    
    def test_unique_constraint(self):
        """Test de la contrainte d'unicité"""
        with self.assertRaises(Exception):
            BookRating.objects.create(
                book=self.book,
                user=self.user,
                score=3
            )
    
    def test_str_representation(self):
        """Test de la représentation string"""
        expected_str = f"{self.book.title} - {self.user.username} (5/5)"
        self.assertEqual(str(self.rating), expected_str)


class BookAPITest(APITestCase):
    """Tests pour l'API des livres"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_staff=True
        )
        
        self.author = Author.objects.create(
            first_name="Test",
            last_name="Author"
        )
        
        self.publisher = Publisher.objects.create(
            name="Test Publisher"
        )
        
        self.category = Category.objects.create(
            name="Test Category"
        )
        
        self.book = Book.objects.create(
            title="Test Book",
            description="Description du livre de test",
            publisher=self.publisher,
            status="published"
        )
        
        self.book.authors.add(self.author)
        self.book.categories.add(self.category)
    
    def test_book_list_api(self):
        """Test de l'API de liste des livres"""
        url = reverse('catalog:book-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Test Book")
    
    def test_book_detail_api(self):
        """Test de l'API de détail d'un livre"""
        url = reverse('catalog:book-detail', kwargs={'slug': self.book.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test Book")
    
    def test_book_search_api(self):
        """Test de l'API de recherche de livres"""
        url = reverse('catalog:book-search')
        response = self.client.get(url, {'q': 'Test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_book_creation_requires_auth(self):
        """Test que la création de livre nécessite une authentification"""
        url = reverse('catalog:book-list')
        data = {
            'title': 'Nouveau Livre',
            'author_ids': [str(self.author.id)],
            'category_ids': [str(self.category.id)],
            'publisher': str(self.publisher.id)
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_book_creation_with_auth(self):
        """Test de création de livre avec authentification"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('catalog:book-list')
        data = {
            'title': 'Nouveau Livre',
            'description': 'Description du nouveau livre',
            'author_ids': [str(self.author.id)],
            'category_ids': [str(self.category.id)],
            'publisher': str(self.publisher.id),
            'language': 'fr',
            'status': 'draft'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)


class BookRatingAPITest(APITestCase):
    """Tests pour l'API des évaluations de livres"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.book = Book.objects.create(
            title="Test Book",
            status="published"
        )
    
    def test_rating_creation_requires_auth(self):
        """Test que la création d'évaluation nécessite une authentification"""
        url = reverse('catalog:book-rating-list', kwargs={'book_slug': self.book.slug})
        data = {
            'score': 5,
            'review': 'Excellent livre!'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_rating_creation_with_auth(self):
        """Test de création d'évaluation avec authentification"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('catalog:book-rating-list', kwargs={'book_slug': self.book.slug})
        data = {
            'score': 5,
            'review': 'Excellent livre!'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BookRating.objects.count(), 1)
    
    def test_rating_list(self):
        """Test de la liste des évaluations"""
        BookRating.objects.create(
            book=self.book,
            user=self.user,
            score=4,
            review="Bon livre"
        )
        
        url = reverse('catalog:book-rating-list', kwargs={'book_slug': self.book.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class BookCollectionAPITest(APITestCase):
    """Tests pour l'API des collections de livres"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.book = Book.objects.create(
            title="Test Book",
            status="published"
        )
        
        self.collection = BookCollection.objects.create(
            title="Ma Collection",
            description="Collection de test",
            created_by=self.user,
            is_public=True
        )
    
    def test_collection_list(self):
        """Test de la liste des collections"""
        url = reverse('catalog:collection-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_collection_creation_requires_auth(self):
        """Test que la création de collection nécessite une authentification"""
        url = reverse('catalog:collection-list')
        data = {
            'title': 'Nouvelle Collection',
            'description': 'Description de la nouvelle collection'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_collection_creation_with_auth(self):
        """Test de création de collection avec authentification"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('catalog:collection-list')
        data = {
            'title': 'Nouvelle Collection',
            'description': 'Description de la nouvelle collection',
            'is_public': True
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BookCollection.objects.count(), 2)
    
    def test_add_book_to_collection(self):
        """Test d'ajout d'un livre à une collection"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('catalog:collection-add-book', kwargs={
            'collection_slug': self.collection.slug,
            'book_slug': self.book.slug
        })
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.book, self.collection.books.all())
    
    def test_remove_book_from_collection(self):
        """Test de suppression d'un livre d'une collection"""
        self.client.force_authenticate(user=self.user)
        
        # Ajouter d'abord le livre
        self.collection.books.add(self.book)
        
        url = reverse('catalog:collection-remove-book', kwargs={
            'collection_slug': self.collection.slug,
            'book_slug': self.book.slug
        })
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.book, self.collection.books.all())


class BookStatsAPITest(APITestCase):
    """Tests pour l'API des statistiques de livres"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Créer quelques livres pour les statistiques
        for i in range(5):
            Book.objects.create(
                title=f"Book {i}",
                status="published",
                is_featured=(i < 2),
                is_free=(i < 3)
            )
    
    def test_book_stats(self):
        """Test des statistiques de livres"""
        url = reverse('catalog:book-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_books'], 5)
        self.assertEqual(response.data['published_books'], 5)
        self.assertEqual(response.data['featured_books'], 2)
        self.assertEqual(response.data['free_books'], 3)


class HealthCheckAPITest(APITestCase):
    """Tests pour l'API de vérification de santé"""
    
    def test_health_check(self):
        """Test de vérification de santé"""
        url = reverse('catalog:health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['service'], 'catalog_service')
        self.assertIn('books_count', response.data)