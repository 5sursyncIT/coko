from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import User, Role, UserRole, UserSession, UserPreferences


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administration des utilisateurs"""
    
    list_display = (
        'username', 'email', 'full_name', 'subscription_type', 
        'is_verified', 'is_premium', 'country', 'date_joined', 'last_login'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'is_verified', 
        'subscription_type', 'country', 'language', 'date_joined'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Informations personnelles', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone', 
                'avatar', 'country', 'language'
            )
        }),
        ('Abonnement', {
            'fields': ('subscription_type', 'subscription_expires_at')
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 
                'is_verified', 'groups', 'user_permissions'
            )
        }),
        ('Dates importantes', {
            'fields': (
                'last_login', 'date_joined', 'last_login_ip'
            )
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'first_name', 'last_name', 'country', 'language'
            ),
        }),
    )
    
    readonly_fields = (
        'date_joined', 'last_login', 'last_login_ip'
    )
    
    def full_name(self, obj):
        return obj.get_full_name() or '-'
    full_name.short_description = 'Nom complet'
    
    def is_premium(self, obj):
        if obj.subscription_type in ['premium', 'premium_plus']:
            return format_html(
                '<span style="color: gold;">✓ Premium</span>'
            )
        return format_html(
            '<span style="color: gray;">✗ Gratuit</span>'
        )
    is_premium.short_description = 'Premium'
    
    actions = ['verify_users', 'unverify_users', 'deactivate_users']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(
            is_verified=True
        )
        self.message_user(
            request, 
            f'{updated} utilisateur(s) vérifié(s) avec succès.'
        )
    verify_users.short_description = "Vérifier les utilisateurs sélectionnés"
    
    def unverify_users(self, request, queryset):
        updated = queryset.update(
            is_verified=False
        )
        self.message_user(
            request, 
            f'{updated} utilisateur(s) non-vérifié(s) avec succès.'
        )
    unverify_users.short_description = "Annuler la vérification des utilisateurs sélectionnés"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} utilisateur(s) désactivé(s) avec succès.'
        )
    deactivate_users.short_description = "Désactiver les utilisateurs sélectionnés"


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Administration des rôles"""
    
    list_display = ('name', 'description', 'permissions_count', 'users_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'permissions')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def permissions_count(self, obj):
        return len(obj.permissions)
    permissions_count.short_description = 'Nb permissions'
    
    def users_count(self, obj):
        count = obj.userrole_set.count()
        if count > 0:
            url = reverse('admin:auth_service_userrole_changelist')
            return format_html(
                '<a href="{}?role__id__exact={}">{} utilisateur(s)</a>',
                url, obj.id, count
            )
        return '0 utilisateur'
    users_count.short_description = 'Utilisateurs'


class UserRoleInline(admin.TabularInline):
    """Inline pour les rôles utilisateur"""
    model = UserRole
    extra = 0
    readonly_fields = ('assigned_at',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Administration des rôles utilisateur"""
    
    list_display = ('user', 'role', 'assigned_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__username', 'user__email', 'role__name')
    ordering = ('-assigned_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'role')
        }),
        ('Métadonnées', {
            'fields': ('assigned_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('assigned_at',)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Administration des sessions utilisateur"""
    
    list_display = (
        'user', 'session_key_short', 'ip_address', 
        'is_active', 'created_at', 'last_activity', 'expires_at'
    )
    list_filter = ('created_at', 'last_activity', 'expires_at')
    search_fields = ('user__username', 'user__email', 'ip_address', 'session_key')
    ordering = ('-last_activity',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'session_key', 'ip_address', 'user_agent')
        }),
        ('Dates', {
            'fields': ('created_at', 'last_activity', 'expires_at')
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def session_key_short(self, obj):
        return f"{obj.session_key[:8]}..." if obj.session_key else '-'
    session_key_short.short_description = 'Session'
    
    def is_active(self, obj):
        if obj.expires_at > timezone.now():
            return format_html(
                '<span style="color: green;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Expirée</span>'
        )
    is_active.short_description = 'Statut'
    
    actions = ['revoke_sessions']
    
    def revoke_sessions(self, request, queryset):
        updated = queryset.update(expires_at=timezone.now())
        self.message_user(
            request, 
            f'{updated} session(s) révoquée(s) avec succès.'
        )
    revoke_sessions.short_description = "Révoquer les sessions sélectionnées"


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """Administration des préférences utilisateur"""
    
    list_display = (
        'user', 'theme', 'language_interface', 'font_size', 
        'notifications_email', 'notifications_push', 'updated_at'
    )
    list_filter = (
        'theme', 'language_interface', 'font_size', 
        'notifications_email', 'notifications_push', 'updated_at'
    )
    search_fields = ('user__username', 'user__email')
    ordering = ('-updated_at',)
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Interface', {
            'fields': ('theme', 'language_interface', 'font_size')
        }),
        ('Notifications', {
            'fields': (
                'notifications_email', 'notifications_push', 
                'notifications_sms', 'marketing_emails'
            )
        }),
        ('Lecture', {
            'fields': (
                'reading_mode', 'auto_download'
            )
        }),
        ('Confidentialité', {
            'fields': (
                'privacy_profile',
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


# Configuration de l'interface d'administration
admin.site.site_header = "Administration COKO - Service d'Authentification"
admin.site.site_title = "COKO Auth Admin"
admin.site.index_title = "Gestion du Service d'Authentification"