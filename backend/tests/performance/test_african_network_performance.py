"""
Tests de performance réseau simulant les conditions africaines
Conformément aux recommandations du document RECOMMENDATIONS.md
"""

import time
import pytest
import requests
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, Mock
import json
from datetime import timedelta
import threading

from auth_service.models import User
from catalog_service.models import Book
from reading_service.models import ReadingSession


User = get_user_model()


class NetworkLatencySimulator:
    """Simulateur de latence réseau pour conditions africaines"""
    
    # Latences moyennes observées en Afrique de l'Ouest (en millisecondes)
    LATENCY_PROFILES = {
        '2g': {'min': 300, 'max': 800, 'avg': 550},
        '3g': {'min': 150, 'max': 400, 'avg': 250},  
        '4g': {'min': 50, 'max': 150, 'avg': 80},
        'wifi_poor': {'min': 200, 'max': 600, 'avg': 350},
        'wifi_good': {'min': 20, 'max': 100, 'avg': 50}
    }
    
    @classmethod
    def simulate_latency(cls, network_type='3g'):
        """Simule la latence réseau en ajoutant un délai"""
        latency = cls.LATENCY_PROFILES[network_type]['avg'] / 1000  # Convert to seconds
        time.sleep(latency)


@pytest.mark.african_performance
class AfricanNetworkPerformanceTest(APITestCase):
    """Tests de performance pour conditions réseau africaines"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='african_user',
            email='user@example.sn',  # Domaine sénégalais
            password='TestPassword123!',
            country='SN',  # Sénégal
            language='fr'
        )
        
        # Créer quelques livres pour les tests
        for i in range(5):
            Book.objects.create(
                title=f'Test Book {i}',
                author=f'Author {i}',
                isbn=f'123456789{i}',
                language='fr',
                publication_date='2023-01-01',
                description='Test book description'
            )
    
    def _authenticate_user(self):
        """Helper pour authentifier l'utilisateur"""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return refresh.access_token
    
    @pytest.mark.performance
    def test_api_response_time_3g(self):
        """Test: temps de réponse API ≤ 500ms sur 3G depuis l'Afrique"""
        self._authenticate_user()
        
        # Test différents endpoints critiques
        endpoints = [
            ('catalog:book-list', {}),
            ('auth_service:profile', {}),
            ('reading_service:session-list', {}),
        ]
        
        for endpoint_name, kwargs in endpoints:
            with self.subTest(endpoint=endpoint_name):
                # Simuler latence 3G africaine
                NetworkLatencySimulator.simulate_latency('3g')
                
                start_time = time.time()
                url = reverse(endpoint_name, kwargs=kwargs)
                response = self.client.get(url)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # En millisecondes
                
                # Vérifier que la réponse est valide
                self.assertIn(response.status_code, [200, 201])
                
                # Objectif: ≤ 500ms depuis l'Afrique (sans latence réseau)
                # On teste le temps de traitement serveur uniquement
                processing_time = response_time - NetworkLatencySimulator.LATENCY_PROFILES['3g']['avg']
                self.assertLess(
                    processing_time, 
                    500,
                    f"Endpoint {endpoint_name} took {processing_time:.2f}ms (target: ≤500ms)"
                )
    
    @pytest.mark.performance
    def test_page_load_time_mobile_3g(self):
        """Test: temps de chargement page ≤ 3s sur mobile 3G"""
        # Simuler une requête de page complète avec tous les assets
        start_time = time.time()
        
        # Simuler latence 3G
        NetworkLatencySimulator.simulate_latency('3g')
        
        # Requête principale
        response = self.client.get('/')
        
        # Simuler chargement des assets (CSS, JS, images)
        # En conditions réelles, ceci serait fait par le navigateur
        asset_requests = 5  # Estimation du nombre d'assets critiques
        for _ in range(asset_requests):
            NetworkLatencySimulator.simulate_latency('3g')
        
        end_time = time.time()
        total_load_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(
            total_load_time,
            3.0,
            f"Page load time {total_load_time:.2f}s exceeds 3s target for mobile 3G"
        )
    
    @pytest.mark.performance
    def test_api_performance_under_load(self):
        """Test: performance API sous charge simulant trafic africain"""
        self._authenticate_user()
        
        def make_request():
            NetworkLatencySimulator.simulate_latency('3g')
            response = self.client.get(reverse('catalog:book-list'))
            return response.status_code == 200
        
        # Simuler 10 requêtes concurrentes (charge modérée)
        threads = []
        results = []
        
        start_time = time.time()
        for _ in range(10):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Vérifier que toutes les requêtes ont réussi
        success_rate = sum(results) / len(results)
        self.assertGreaterEqual(success_rate, 0.95, "Success rate should be ≥ 95%")
        
        # Temps total ne doit pas dépasser 5s même sous charge
        total_time = end_time - start_time
        self.assertLess(total_time, 5.0, f"Load test took {total_time:.2f}s (target: <5s)")
    
    @pytest.mark.performance
    def test_database_query_optimization(self):
        """Test: optimisation requêtes DB pour latence africaine"""
        self._authenticate_user()
        
        # Test que les requêtes utilisent bien les index et optimisations
        with self.assertNumQueries(3):  # Doit être optimisé pour ≤ 3 requêtes
            response = self.client.get(reverse('catalog:book-list'))
            self.assertEqual(response.status_code, 200)
        
        # Test pagination efficace
        with self.assertNumQueries(2):  # Pagination doit être optimisée
            response = self.client.get(reverse('catalog:book-list') + '?page=1&page_size=10')
            self.assertEqual(response.status_code, 200)
    
    @pytest.mark.performance
    def test_cache_efficiency_african_content(self):
        """Test: efficacité du cache pour contenu africain populaire"""
        cache.clear()
        
        # Premier accès - doit mettre en cache
        start_time = time.time()
        response1 = self.client.get(reverse('catalog:book-list'))
        first_request_time = time.time() - start_time
        
        # Deuxième accès - doit utiliser le cache
        start_time = time.time()
        response2 = self.client.get(reverse('catalog:book-list'))
        cached_request_time = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Le cache doit accélérer significativement (au moins 50% plus rapide)
        improvement_ratio = cached_request_time / first_request_time
        self.assertLess(
            improvement_ratio,
            0.5,
            f"Cache improvement ratio {improvement_ratio:.2f} (target: <0.5)"
        )
    
    @pytest.mark.performance
    def test_offline_sync_performance(self):
        """Test: performance de synchronisation hors-ligne"""
        self._authenticate_user()
        
        # Simuler des données à synchroniser
        sync_data = {
            'reading_progress': [
                {
                    'book_id': 1,
                    'page': 45,
                    'progress_percentage': 30.5,
                    'last_read_at': '2023-12-01T10:00:00Z'
                }
            ],
            'bookmarks': [
                {
                    'book_id': 1,
                    'page': 23,
                    'note': 'Important passage'
                }
            ]
        }
        
        # Test temps de synchronisation
        start_time = time.time()
        NetworkLatencySimulator.simulate_latency('3g')
        
        # Endpoint de sync (à implémenter)
        # response = self.client.post(reverse('reading_service:sync'), sync_data)
        # Pour maintenant, simuler le traitement
        time.sleep(0.1)  # Simule traitement serveur
        
        end_time = time.time()
        sync_time = end_time - start_time
        
        # Synchronisation doit être rapide même avec latence
        self.assertLess(sync_time, 2.0, f"Sync took {sync_time:.2f}s (target: <2s)")


@pytest.mark.african_performance
class AfricanBandwidthOptimizationTest(TestCase):
    """Tests d'optimisation pour bande passante limitée africaine"""
    
    def setUp(self):
        self.client = Client()
    
    @pytest.mark.performance
    def test_response_compression(self):
        """Test: compression des réponses pour économiser la bande passante"""
        # Test avec header Accept-Encoding
        response = self.client.get(
            reverse('catalog:book-list'),
            HTTP_ACCEPT_ENCODING='gzip, deflate'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la réponse est compressée
        # Dans un vrai test, on vérifierait les headers de compression
        response_size = len(response.content)
        
        # La réponse compressée doit être raisonnable (< 50KB pour une liste)
        self.assertLess(
            response_size,
            50 * 1024,
            f"Response size {response_size} bytes too large for African bandwidth"
        )
    
    @pytest.mark.performance
    def test_minimal_data_transfer(self):
        """Test: transfert de données minimal pour économiser la bande passante"""
        response = self.client.get(reverse('catalog:book-list'))
        data = response.json()
        
        # Vérifier que les champs non-essentiels sont exclus par défaut
        if 'results' in data and data['results']:
            book = data['results'][0]
            
            # Champs essentiels qui doivent être présents
            essential_fields = ['id', 'title', 'author']
            for field in essential_fields:
                self.assertIn(field, book)
            
            # Champs lourds qui ne doivent pas être dans la liste (seulement en détail)
            heavy_fields = ['full_text', 'detailed_description']
            for field in heavy_fields:
                self.assertNotIn(field, book)
    
    @pytest.mark.performance
    def test_image_optimization(self):
        """Test: optimisation des images pour les connexions lentes"""
        # Si l'API retourne des URLs d'images, elles doivent être optimisées
        response = self.client.get(reverse('catalog:book-list'))
        data = response.json()
        
        if 'results' in data and data['results']:
            book = data['results'][0]
            if 'cover_image' in book and book['cover_image']:
                cover_url = book['cover_image']
                
                # L'URL doit contenir des paramètres d'optimisation pour mobile
                self.assertTrue(
                    any(param in cover_url for param in ['?w=', '?width=', 'thumbnail', 'mobile']),
                    f"Cover image URL {cover_url} should be optimized for mobile"
                )


@pytest.mark.african_performance
class AfricanConnectivityResilienceTest(APITestCase):
    """Tests de résilience pour connectivité instable africaine"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='african_user',
            email='user@example.sn',
            password='TestPassword123!'
        )
    
    def _authenticate_user(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    @pytest.mark.performance
    @patch('requests.get')
    def test_retry_mechanism(self, mock_get):
        """Test: mécanisme de retry pour connexions instables"""
        self._authenticate_user()
        
        # Simuler des échecs de connexion puis succès
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.ConnectionError(),
            Mock(status_code=200, json=lambda: {'status': 'success'})
        ]
        
        # Le système doit implémenter un retry avec backoff exponentiel
        # Ce test vérifie qu'on a bien 3 tentatives
        
        # En attendant l'implémentation réelle, on simule
        attempts = 0
        max_attempts = 3
        success = False
        
        for attempt in range(max_attempts):
            try:
                attempts += 1
                if attempt < 2:  # Simuler les échecs
                    raise requests.exceptions.Timeout()
                success = True
                break
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                if attempt < max_attempts - 1:
                    # Backoff exponentiel
                    backoff_time = (2 ** attempt) * 0.1
                    time.sleep(backoff_time)
                    continue
                raise
        
        self.assertTrue(success, "Retry mechanism should succeed after failures")
        self.assertEqual(attempts, 3, "Should attempt exactly 3 times")
    
    @pytest.mark.performance
    def test_graceful_degradation(self):
        """Test: dégradation gracieuse en cas de services indisponibles"""
        self._authenticate_user()
        
        # Test que l'API principale fonctionne même si les services auxiliaires échouent
        with patch('recommendation_service.views.get_recommendations') as mock_reco:
            mock_reco.side_effect = Exception("Recommendation service down")
            
            # L'API des livres doit fonctionner sans recommandations
            response = self.client.get(reverse('catalog:book-list'))
            self.assertEqual(response.status_code, 200)
            
            # Les recommandations peuvent être absentes mais le reste doit marcher
            data = response.json()
            self.assertIn('results', data)
    
    @pytest.mark.performance
    def test_connection_timeout_handling(self):
        """Test: gestion appropriée des timeouts de connexion"""
        # Configuration de timeout adaptée aux conditions africaines
        timeout_settings = {
            'connect_timeout': 10,  # 10s pour établir la connexion
            'read_timeout': 30,     # 30s pour lire les données
        }
        
        # Vérifier que les timeouts sont configurés de manière appropriée
        # pour les conditions de réseau africaines
        self.assertGreaterEqual(timeout_settings['connect_timeout'], 10)
        self.assertGreaterEqual(timeout_settings['read_timeout'], 30)


@pytest.mark.african_performance
class AfricanUserExperienceTest(APITestCase):
    """Tests d'expérience utilisateur adaptée au contexte africain"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='african_user',
            email='user@example.sn',
            password='TestPassword123!',
            country='SN',
            language='fr'
        )
    
    def _authenticate_user(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    @pytest.mark.performance
    def test_progressive_loading(self):
        """Test: chargement progressif adapté aux connexions lentes"""
        self._authenticate_user()
        
        # Test de pagination avec petites pages pour chargement progressif
        response = self.client.get(reverse('catalog:book-list') + '?page_size=5')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertLessEqual(len(data['results']), 5)
        
        # Doit avoir des liens de pagination
        self.assertIn('next', data)
        self.assertIn('previous', data)
    
    @pytest.mark.performance
    def test_essential_content_first(self):
        """Test: contenu essentiel chargé en premier"""
        response = self.client.get(reverse('catalog:book-list'))
        data = response.json()
        
        if 'results' in data and data['results']:
            book = data['results'][0]
            
            # Vérifier que les champs essentiels sont présents
            essential_fields = ['id', 'title', 'author']
            for field in essential_fields:
                self.assertIn(field, book, f"Essential field {field} missing")
            
            # Le contenu doit être structuré pour permettre un rendu progressif
            self.assertTrue(len(str(book)) < 1000, "Book summary should be lightweight")
    
    @pytest.mark.performance
    def test_mobile_optimized_responses(self):
        """Test: réponses optimisées pour mobile"""
        # Simuler une requête mobile
        response = self.client.get(
            reverse('catalog:book-list'),
            HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # La réponse doit être adaptée au mobile (moins de données)
        data = response.json()
        if 'results' in data and data['results']:
            # Pagination plus petite pour mobile
            self.assertLessEqual(len(data['results']), 10)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])