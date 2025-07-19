from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from datetime import timedelta
import json

from .models import User, UserPreferences, UserSession, Role, UserRole
from .utils import generate_verification_token, validate_password_strength

User = get_user_model()


class UserModelTest(TestCase):
    """Tests pour le modèle User"""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'country': 'FR',
            'language': 'fr'
        }
    
    def test_create_user(self):
        """Test de création d'un utilisateur"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('TestPassword123!'))
        self.assertFalse(user.is_verified)
        self.assertEqual(user.subscription_type, 'free')
        self.assertFalse(user.is_premium)
    
    def test_create_superuser(self):
        """Test de création d'un superutilisateur"""
        admin_data = self.user_data.copy()
        admin_data['username'] = 'admin'
        admin_data['email'] = 'admin@example.com'
        
        admin = User.objects.create_superuser(**admin_data)
        
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
    
    def test_user_full_name(self):
        """Test de la propriété full_name"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, 'Test User')
        
        # Test avec nom vide
        user.first_name = ''
        user.last_name = ''
        self.assertEqual(user.full_name, '')
    
    def test_user_is_premium(self):
        """Test de la propriété is_premium"""
        user = User.objects.create_user(**self.user_data)
        
        # Utilisateur gratuit
        self.assertFalse(user.is_premium)
        
        # Utilisateur premium
        user.subscription_type = 'premium'
        user.subscription_expires_at = timezone.now() + timedelta(days=30)
        self.assertTrue(user.is_premium)
        
        # Abonnement expiré
        user.subscription_expires_at = timezone.now() - timedelta(days=1)
        self.assertFalse(user.is_premium)
    
    def test_user_preferences_creation(self):
        """Test de création automatique des préférences"""
        user = User.objects.create_user(**self.user_data)
        
        # Les préférences doivent être créées automatiquement via le signal
        self.assertTrue(hasattr(user, 'preferences'))
        preferences = UserPreferences.objects.get(user=user)
        self.assertEqual(preferences.language, 'fr')
        self.assertEqual(preferences.theme, 'light')


class AuthenticationAPITest(APITestCase):
    """Tests pour les API d'authentification"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth_service:register')
        self.login_url = reverse('auth_service:login')
        self.logout_url = reverse('auth_service:logout')
        
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'country': 'FR',
            'language': 'fr',
            'terms_accepted': True
        }
    
    def test_user_registration(self):
        """Test d'inscription d'un utilisateur"""
        response = self.client.post(self.register_url, self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        
        # Vérifier que l'utilisateur a été créé
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertFalse(user.is_verified)
        
        # Vérifier qu'un email de vérification a été envoyé
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Vérifiez votre adresse email', mail.outbox[0].subject)
    
    def test_registration_validation(self):
        """Test de validation lors de l'inscription"""
        # Email déjà utilisé
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='password123'
        )
        
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        
        # Mots de passe différents
        data = self.user_data.copy()
        data['email'] = 'new@example.com'
        data['password_confirm'] = 'DifferentPassword'
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Conditions non acceptées
        data = self.user_data.copy()
        data['email'] = 'new2@example.com'
        data['terms_accepted'] = False
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login(self):
        """Test de connexion d'un utilisateur"""
        # Créer un utilisateur
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_login_invalid_credentials(self):
        """Test de connexion avec des identifiants invalides"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_logout(self):
        """Test de déconnexion"""
        # Créer et connecter un utilisateur
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        logout_data = {'refresh': str(refresh)}
        response = self.client.post(self.logout_url, logout_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)


class PasswordManagementTest(APITestCase):
    """Tests pour la gestion des mots de passe"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPassword123!'
        )
        
        self.reset_request_url = reverse('auth_service:password_reset')
        self.change_password_url = reverse('auth_service:password_change')
    
    def test_password_reset_request(self):
        """Test de demande de réinitialisation de mot de passe"""
        data = {'email': 'test@example.com'}
        response = self.client.post(self.reset_request_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Vérifier qu'un email a été envoyé
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Réinitialisation', mail.outbox[0].subject)
        
        # Vérifier que le token a été sauvegardé
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_token)
        self.assertIsNotNone(self.user.password_reset_requested_at)
    
    def test_password_reset_nonexistent_email(self):
        """Test de demande de réinitialisation avec email inexistant"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.reset_request_url, data)
        
        # Doit retourner le même message pour des raisons de sécurité
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_change_password(self):
        """Test de changement de mot de passe"""
        # Authentifier l'utilisateur
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        data = {
            'current_password': 'OldPassword123!',
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        response = self.client.post(self.change_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que le mot de passe a changé
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))
        self.assertFalse(self.user.check_password('OldPassword123!'))
    
    def test_change_password_wrong_current(self):
        """Test de changement avec mauvais mot de passe actuel"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        data = {
            'current_password': 'WrongPassword',
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!'
        }
        
        response = self.client.post(self.change_password_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileTest(APITestCase):
    """Tests pour la gestion du profil utilisateur"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        
        self.profile_url = reverse('auth_service:profile')
        self.preferences_url = reverse('auth_service:preferences')
        
        # Authentifier l'utilisateur
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_profile(self):
        """Test de récupération du profil"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('preferences', response.data)
    
    def test_update_profile(self):
        """Test de mise à jour du profil"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+33123456789',
            'country': 'US'
        }
        
        response = self.client.patch(self.profile_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.phone, '+33123456789')
        self.assertEqual(self.user.country, 'US')
    
    def test_update_preferences(self):
        """Test de mise à jour des préférences"""
        data = {
            'theme': 'dark',
            'language': 'en',
            'email_notifications': False,
            'reading_mode': 'night'
        }
        
        response = self.client.patch(self.preferences_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        preferences = UserPreferences.objects.get(user=self.user)
        self.assertEqual(preferences.theme, 'dark')
        self.assertEqual(preferences.language, 'en')
        self.assertFalse(preferences.email_notifications)
        self.assertEqual(preferences.reading_mode, 'night')


class UtilsTest(TestCase):
    """Tests pour les fonctions utilitaires"""
    
    def test_password_strength_validation(self):
        """Test de validation de la force des mots de passe"""
        # Mot de passe faible
        result = validate_password_strength('123')
        self.assertFalse(result['is_valid'])
        self.assertEqual(result['strength'], 'Faible')
        self.assertTrue(len(result['errors']) > 0)
        
        # Mot de passe moyen
        result = validate_password_strength('Password123')
        self.assertFalse(result['is_valid'])  # Manque caractère spécial
        
        # Mot de passe fort
        result = validate_password_strength('StrongPassword123!')
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['strength'], 'Fort')
        self.assertEqual(len(result['errors']), 0)
    
    def test_generate_verification_token(self):
        """Test de génération de token de vérification"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        token = generate_verification_token(user)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)


class SessionManagementTest(APITestCase):
    """Tests pour la gestion des sessions"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        self.sessions_url = reverse('auth_service:user_sessions')
        
        # Authentifier l'utilisateur
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_user_sessions(self):
        """Test de listage des sessions utilisateur"""
        # Créer quelques sessions
        UserSession.objects.create(
            user=self.user,
            session_key='session1',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        UserSession.objects.create(
            user=self.user,
            session_key='session2',
            ip_address='192.168.1.2',
            user_agent='Chrome/90.0',
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        response = self.client.get(self.sessions_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Vérifier les champs retournés
        session_data = response.data[0]
        self.assertIn('id', session_data)
        self.assertIn('ip_address', session_data)
        self.assertIn('user_agent', session_data)
        self.assertIn('created_at', session_data)
        self.assertIn('is_current', session_data)
    
    def test_revoke_session(self):
        """Test de révocation d'une session"""
        session = UserSession.objects.create(
            user=self.user,
            session_key='session_to_revoke',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        revoke_url = reverse('auth_service:revoke_session', kwargs={'session_id': session.id})
        response = self.client.delete(revoke_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que la session a été supprimée
        self.assertFalse(UserSession.objects.filter(id=session.id).exists())


class RoleManagementTest(TestCase):
    """Tests pour la gestion des rôles"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        self.role = Role.objects.create(
            name='Editor',
            description='Can edit content',
            permissions=['edit_books', 'publish_books']
        )
    
    def test_assign_role_to_user(self):
        """Test d'assignation d'un rôle à un utilisateur"""
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role
        )
        
        self.assertEqual(user_role.user, self.user)
        self.assertEqual(user_role.role, self.role)
        self.assertIsNotNone(user_role.assigned_at)
    
    def test_role_permissions(self):
        """Test des permissions de rôle"""
        self.assertEqual(self.role.permissions, ['edit_books', 'publish_books'])
        self.assertIn('edit_books', self.role.permissions)
        self.assertNotIn('delete_books', self.role.permissions)