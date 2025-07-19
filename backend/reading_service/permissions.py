from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission pour permettre seulement au propriétaire de modifier ses données"""
    
    def has_object_permission(self, request, view, obj):
        # Permissions de lecture pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissions d'écriture seulement pour le propriétaire
        return obj.user == request.user


class CanAccessReadingData(permissions.BasePermission):
    """Permission pour accéder aux données de lecture"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        if not request.user.is_authenticated:
            return False
        
        # Les administrateurs ont accès à tout
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Les utilisateurs normaux peuvent accéder à leurs propres données
        return True
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont accès à tout
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Vérifier si l'objet appartient à l'utilisateur
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class CanManageReadingSessions(permissions.BasePermission):
    """Permission pour gérer les sessions de lecture"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire peut gérer ses sessions
        return obj.user == request.user


class CanManageBookmarks(permissions.BasePermission):
    """Permission pour gérer les signets"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée si le signet n'est pas privé ou si c'est le propriétaire
        if request.method in permissions.SAFE_METHODS:
            return not obj.is_private or obj.user == request.user
        
        # Modification/suppression seulement par le propriétaire
        return obj.user == request.user


class CanManageReadingGoals(permissions.BasePermission):
    """Permission pour gérer les objectifs de lecture"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée si l'objectif est public ou si c'est le propriétaire
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user
        
        # Modification/suppression seulement par le propriétaire
        return obj.user == request.user


class CanViewReadingStatistics(permissions.BasePermission):
    """Permission pour voir les statistiques de lecture"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        if not request.user.is_authenticated:
            return False
        
        # Les administrateurs peuvent voir toutes les statistiques
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Les utilisateurs peuvent voir leurs propres statistiques
        return True
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont accès à tout
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Vérifier si les statistiques appartiennent à l'utilisateur
        return obj.user == request.user


class IsPremiumUserOrReadOnly(permissions.BasePermission):
    """Permission pour les fonctionnalités premium"""
    
    def has_permission(self, request, view):
        # Lecture autorisée pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Écriture seulement pour les utilisateurs premium
        return (
            request.user.is_authenticated and 
            (request.user.is_premium or request.user.is_staff or request.user.is_superuser)
        )


class CanAccessAdvancedAnalytics(permissions.BasePermission):
    """Permission pour accéder aux analyses avancées"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        if not request.user.is_authenticated:
            return False
        
        # Les administrateurs ont toujours accès
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Les utilisateurs premium ont accès aux analyses avancées
        return request.user.is_premium


class CanExportReadingData(permissions.BasePermission):
    """Permission pour exporter les données de lecture"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        if not request.user.is_authenticated:
            return False
        
        # Les administrateurs peuvent exporter toutes les données
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Les utilisateurs peuvent exporter leurs propres données
        return True


class CanManageReadingPreferences(permissions.BasePermission):
    """Permission pour gérer les préférences de lecture"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire peut modifier ses préférences
        return obj.user == request.user


class CanAccessReadingRecommendations(permissions.BasePermission):
    """Permission pour accéder aux recommandations de lecture"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        return request.user.is_authenticated


class CanShareReadingData(permissions.BasePermission):
    """Permission pour partager les données de lecture"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur peut partager ses données
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsAdminOrOwner(permissions.BasePermission):
    """Permission pour les administrateurs ou propriétaires"""
    
    def has_permission(self, request, view):
        # L'utilisateur doit être authentifié
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont accès à tout
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Le propriétaire a accès à ses propres données
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class CanModerateReadingContent(permissions.BasePermission):
    """Permission pour modérer le contenu de lecture"""
    
    def has_permission(self, request, view):
        # Seuls les modérateurs et administrateurs
        return (
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser or 
             request.user.groups.filter(name='moderators').exists())
        )


class CanAccessBulkOperations(permissions.BasePermission):
    """Permission pour les opérations en lot"""
    
    def has_permission(self, request, view):
        # Seuls les administrateurs et utilisateurs premium
        return (
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser or request.user.is_premium)
        )