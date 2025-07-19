from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'auth_service'

urlpatterns = [
    # Authentification de base
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Gestion du profil utilisateur
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('preferences/', views.UserPreferencesView.as_view(), name='preferences'),
    
    # Gestion des mots de passe
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/<str:uid>/<str:token>/', 
         views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/change/', views.ChangePasswordView.as_view(), name='password_change'),
    
    # Vérification d'email
    path('email/verify/<str:uid>/<str:token>/', 
         views.EmailVerificationView.as_view(), name='email_verify'),
    path('email/resend-verification/', 
         views.ResendVerificationView.as_view(), name='resend_verification'),
    
    # Gestion des sessions
    path('sessions/', views.UserSessionsView.as_view(), name='user_sessions'),
    path('sessions/<uuid:session_id>/revoke/', 
         views.RevokeSessionView.as_view(), name='revoke_session'),
    
    # Rôles utilisateur
    path('roles/', views.UserRolesView.as_view(), name='user_roles'),
    
    # Statistiques et informations
    path('stats/', views.user_stats, name='user_stats'),
    
    # Gestion du compte
    path('deactivate/', views.deactivate_account, name='deactivate_account'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
]