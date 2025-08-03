from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class User(AbstractUser):
    """Modèle utilisateur personnalisé pour la plateforme Coko"""
    
    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
    ]
    
    COUNTRY_CHOICES = [
        ('SN', 'Sénégal'),
        ('CI', 'Côte d\'Ivoire'),
        ('ML', 'Mali'),
        ('BF', 'Burkina Faso'),
        ('MA', 'Maroc'),
        ('TN', 'Tunisie'),
        ('DZ', 'Algérie'),
        ('CM', 'Cameroun'),
        ('CD', 'République Démocratique du Congo'),
        ('FR', 'France'),
        ('CA', 'Canada'),
        ('OTHER', 'Autre'),
    ]
    
    SUBSCRIPTION_CHOICES = [
        ('free', 'Gratuit'),
        ('premium', 'Premium'),
        ('creator', 'Créateur'),
        ('institutional', 'Institutionnel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    country = models.CharField(max_length=10, choices=COUNTRY_CHOICES, default='SN')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='fr')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_CHOICES, default='free')
    subscription_expires_at = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    reset_password_token = models.CharField(max_length=100, blank=True, null=True)
    reset_password_expires = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_users'
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_premium(self):
        """Vérifie si l'utilisateur a un abonnement premium actif"""
        if self.subscription_type == 'free':
            return False
        if self.subscription_expires_at:
            from django.utils import timezone
            return self.subscription_expires_at > timezone.now()
        return True
    
    @property
    def full_name(self):
        return self.get_full_name() or self.username


class Role(models.Model):
    """Rôles et permissions pour les utilisateurs"""
    
    ROLE_TYPES = [
        ('admin', 'Administrateur'),
        ('moderator', 'Modérateur'),
        ('author', 'Auteur'),
        ('publisher', 'Éditeur'),
        ('reader', 'Lecteur'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=ROLE_TYPES, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, help_text="Liste des permissions accordées")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_roles'
        verbose_name = _('Rôle')
        verbose_name_plural = _('Rôles')
    
    def __str__(self):
        return self.get_name_display()


class UserRole(models.Model):
    """Association entre utilisateurs et rôles"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_roles')
    
    class Meta:
        db_table = 'auth_user_roles'
        unique_together = ['user', 'role']
        verbose_name = _('Rôle utilisateur')
        verbose_name_plural = _('Rôles utilisateurs')
    
    def __str__(self):
        return f"{self.user.full_name} - {self.role.name}"


class UserSession(models.Model):
    """Sessions utilisateur pour le suivi des connexions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=20, blank=True)  # mobile, desktop, tablet
    location = models.CharField(max_length=100, blank=True)  # Pays/Ville
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'auth_user_sessions'
        verbose_name = _('Session utilisateur')
        verbose_name_plural = _('Sessions utilisateurs')
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.device_type} ({self.ip_address})"


class UserPreferences(models.Model):
    """Préférences utilisateur pour l'interface et les notifications"""
    
    THEME_CHOICES = [
        ('light', 'Clair'),
        ('dark', 'Sombre'),
        ('auto', 'Automatique'),
    ]
    
    FONT_SIZE_CHOICES = [
        ('small', 'Petit'),
        ('medium', 'Moyen'),
        ('large', 'Grand'),
        ('xlarge', 'Très grand'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='auto')
    font_size = models.CharField(max_length=10, choices=FONT_SIZE_CHOICES, default='medium')
    notifications_email = models.BooleanField(default=True)
    notifications_push = models.BooleanField(default=True)
    notifications_sms = models.BooleanField(default=False)
    auto_download = models.BooleanField(default=False)
    reading_mode = models.CharField(max_length=20, default='paginated')  # paginated, continuous
    language_interface = models.CharField(max_length=5, choices=User.LANGUAGE_CHOICES, default='fr')
    privacy_profile = models.CharField(max_length=20, default='public')  # public, friends, private
    marketing_emails = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user_preferences'
        verbose_name = _('Préférences utilisateur')
        verbose_name_plural = _('Préférences utilisateurs')
    
    def __str__(self):
        return f"Préférences de {self.user.full_name}"


class SecurityLog(models.Model):
    """Journal des événements de sécurité"""
    
    EVENT_TYPES = [
        ('LOGIN_SUCCESS', 'Connexion réussie'),
        ('LOGIN_FAILED', 'Échec de connexion'),
        ('LOGOUT', 'Déconnexion'),
        ('PASSWORD_CHANGED', 'Mot de passe modifié'),
        ('EMAIL_VERIFIED', 'Email vérifié'),
        ('ACCOUNT_CREATED', 'Compte créé'),
        ('SESSION_CREATED', 'Session créée'),
        ('SESSION_DELETED', 'Session supprimée'),
        ('SUSPICIOUS_LOGIN', 'Connexion suspecte'),
        ('MULTIPLE_FAILED_LOGINS', 'Multiples échecs de connexion'),
        ('PASSWORD_BREACH_ATTEMPT', 'Tentative de violation de mot de passe'),
        ('ACCOUNT_LOCKOUT', 'Verrouillage de compte'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_logs', null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_security_logs'
        verbose_name = _('Journal de sécurité')
        verbose_name_plural = _('Journaux de sécurité')
        ordering = ['-created_at']
    
    def __str__(self):
        user_info = self.user.username if self.user else 'Anonyme'
        return f"{self.get_event_type_display()} - {user_info} ({self.created_at})"