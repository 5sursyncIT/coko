from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import uuid

from .models import User, UserSession, UserPreferences, UserRole, Role
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, 
    CustomTokenObtainPairSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, ChangePasswordSerializer,
    EmailVerificationSerializer, UserProfileUpdateSerializer,
    UserPreferencesSerializer, RoleSerializer, UserRoleSerializer
)
from .utils import generate_verification_token, send_verification_email


class RegisterView(generics.CreateAPIView):
    """Vue pour l'inscription d'un nouvel utilisateur"""
    
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
            # Générer et envoyer le token de vérification
            verification_token = generate_verification_token(user)
            send_verification_email(user, verification_token)
            
            # Créer une session utilisateur
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key or str(uuid.uuid4()),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                expires_at=timezone.now() + timedelta(days=30)
            )
        
        return Response({
            'message': 'Compte créé avec succès. Veuillez vérifier votre email.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vue personnalisée pour l'obtention de tokens JWT"""
    
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        remember_me = serializer.validated_data.get('remember_me', False)
        
        # Générer les tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        # Configurer la durée de vie des tokens
        if remember_me:
            refresh.set_exp(lifetime=timedelta(days=30))
            access.set_exp(lifetime=timedelta(hours=24))
        
        # Mettre à jour les informations de connexion
        user.last_login = timezone.now()
        user.last_login_ip = request.META.get('REMOTE_ADDR')
        user.save(update_fields=['last_login', 'last_login_ip'])
        
        # Créer ou mettre à jour la session
        session, created = UserSession.objects.get_or_create(
            user=user,
            session_key=request.session.session_key or str(uuid.uuid4()),
            defaults={
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'expires_at': timezone.now() + timedelta(days=30 if remember_me else 1)
            }
        )
        
        if not created:
            session.last_activity = timezone.now()
            session.expires_at = timezone.now() + timedelta(days=30 if remember_me else 1)
            session.save()
        
        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    """Vue pour la déconnexion"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Invalider le refresh token
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Supprimer la session utilisateur
            UserSession.objects.filter(
                user=request.user,
                session_key=request.session.session_key
            ).delete()
            
            logout(request)
            
            return Response({
                'message': 'Déconnexion réussie'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'error': 'Erreur lors de la déconnexion'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour consulter et modifier le profil utilisateur"""
    
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserProfileUpdateSerializer


class PasswordResetRequestView(APIView):
    """Vue pour demander une réinitialisation de mot de passe"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Générer le token de réinitialisation
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Envoyer l'email de réinitialisation
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            send_mail(
                subject='Réinitialisation de votre mot de passe - COKO',
                message=f'Cliquez sur ce lien pour réinitialiser votre mot de passe: {reset_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            # Enregistrer la demande de réinitialisation
            user.password_reset_token = token
            user.password_reset_requested_at = timezone.now()
            user.save(update_fields=['password_reset_token', 'password_reset_requested_at'])
            
        except User.DoesNotExist:
            # Pour des raisons de sécurité, on ne révèle pas si l'email existe
            pass
        
        return Response({
            'message': 'Si cet email existe, vous recevrez un lien de réinitialisation.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Vue pour confirmer la réinitialisation de mot de passe"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, uid, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if not default_token_generator.check_token(user, token):
                return Response({
                    'error': 'Token invalide ou expiré'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier que le token correspond à celui stocké
            if user.password_reset_token != token:
                return Response({
                    'error': 'Token invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier l'expiration (24h)
            if user.password_reset_requested_at and \
               timezone.now() - user.password_reset_requested_at > timedelta(hours=24):
                return Response({
                    'error': 'Token expiré'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = PasswordResetConfirmSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Changer le mot de passe
            user.set_password(serializer.validated_data['password'])
            user.password_reset_token = None
            user.password_reset_requested_at = None
            user.save()
            
            # Invalider toutes les sessions existantes
            UserSession.objects.filter(user=user).delete()
            
            return Response({
                'message': 'Mot de passe réinitialisé avec succès'
            }, status=status.HTTP_200_OK)
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Token invalide'
            }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Vue pour changer le mot de passe"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Invalider toutes les autres sessions
        UserSession.objects.filter(user=user).exclude(
            session_key=request.session.session_key
        ).delete()
        
        return Response({
            'message': 'Mot de passe modifié avec succès'
        }, status=status.HTTP_200_OK)


class EmailVerificationView(APIView):
    """Vue pour vérifier l'email"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, uid, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
            
            if user.is_verified:
                return Response({
                    'message': 'Email déjà vérifié'
                }, status=status.HTTP_200_OK)
            
            if default_token_generator.check_token(user, token):
                user.is_verified = True
                user.email_verified_at = timezone.now()
                user.save(update_fields=['is_verified', 'email_verified_at'])
                
                return Response({
                    'message': 'Email vérifié avec succès'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Token de vérification invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Token de vérification invalide'
            }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    """Vue pour renvoyer l'email de vérification"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if user.is_verified:
            return Response({
                'message': 'Email déjà vérifié'
            }, status=status.HTTP_200_OK)
        
        # Générer et envoyer un nouveau token
        verification_token = generate_verification_token(user)
        send_verification_email(user, verification_token)
        
        return Response({
            'message': 'Email de vérification renvoyé'
        }, status=status.HTTP_200_OK)


class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """Vue pour gérer les préférences utilisateur"""
    
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        preferences, created = UserPreferences.objects.get_or_create(
            user=self.request.user
        )
        return preferences


class UserSessionsView(generics.ListAPIView):
    """Vue pour lister les sessions actives de l'utilisateur"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        sessions = UserSession.objects.filter(
            user=request.user,
            expires_at__gt=timezone.now()
        ).order_by('-last_activity')
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': session.id,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'is_current': session.session_key == request.session.session_key
            })
        
        return Response(sessions_data)


class RevokeSessionView(APIView):
    """Vue pour révoquer une session"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, session_id):
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=request.user
            )
            session.delete()
            
            return Response({
                'message': 'Session révoquée avec succès'
            }, status=status.HTTP_200_OK)
            
        except UserSession.DoesNotExist:
            return Response({
                'error': 'Session non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)


class UserRolesView(generics.ListAPIView):
    """Vue pour lister les rôles de l'utilisateur"""
    
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserRole.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Vue pour obtenir les statistiques de l'utilisateur"""
    user = request.user
    
    stats = {
        'total_sessions': UserSession.objects.filter(user=user).count(),
        'active_sessions': UserSession.objects.filter(
            user=user,
            expires_at__gt=timezone.now()
        ).count(),
        'account_age_days': (timezone.now() - user.date_joined).days,
        'is_premium': user.is_premium,
        'subscription_type': user.subscription_type,
        'last_login': user.last_login,
        'is_verified': user.is_verified
    }
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def deactivate_account(request):
    """Vue pour désactiver le compte utilisateur"""
    user = request.user
    password = request.data.get('password')
    
    if not password or not user.check_password(password):
        return Response({
            'error': 'Mot de passe incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Désactiver le compte
    user.is_active = False
    user.save()
    
    # Supprimer toutes les sessions
    UserSession.objects.filter(user=user).delete()
    
    return Response({
        'message': 'Compte désactivé avec succès'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """Vue pour vérifier l'état du service d'authentification"""
    return Response({
        'status': 'healthy',
        'service': 'auth_service',
        'timestamp': timezone.now()
    })