from rest_framework import permissions
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission pour permettre seulement aux propriétaires de modifier leurs objets"""
    
    def has_object_permission(self, request, view, obj):
        # Permissions de lecture pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Permissions d'écriture seulement pour le propriétaire
        return obj.user == request.user


class CanAccessRecommendations(permissions.BasePermission):
    """Permission pour accéder aux recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les utilisateurs actifs peuvent accéder aux recommandations
        if request.user.is_active:
            return True
        
        # Les admins ont toujours accès
        return request.user.is_staff or request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        # Vérifier que l'utilisateur peut accéder à cet objet
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        
        return True


class CanManageRecommendations(permissions.BasePermission):
    """Permission pour gérer les recommandations (créer, modifier, supprimer)"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Seuls les utilisateurs actifs peuvent gérer les recommandations
        if not request.user.is_active:
            return False
        
        # Les méthodes de lecture sont autorisées
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Les méthodes d'écriture nécessitent des permissions spéciales
        return (
            request.user.is_staff or 
            request.user.is_superuser or
            request.user.has_perm('recommendation_service.add_recommendationset')
        )
    
    def has_object_permission(self, request, view, obj):
        # Les méthodes de lecture sont autorisées pour le propriétaire
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'user'):
                return obj.user == request.user or request.user.is_staff
            return True
        
        # Les méthodes d'écriture sont autorisées pour le propriétaire ou les admins
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        
        return request.user.is_staff


class CanViewRecommendationAnalytics(permissions.BasePermission):
    """Permission pour voir les analytics de recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les utilisateurs peuvent voir leurs propres analytics
        user_id = request.query_params.get('user_id')
        if not user_id or user_id == str(request.user.id):
            return True
        
        # Seuls les admins peuvent voir les analytics d'autres utilisateurs
        return request.user.is_staff or request.user.is_superuser


class CanManageUserProfiles(permissions.BasePermission):
    """Permission pour gérer les profils utilisateur de recommandations"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire peut modifier son profil
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user or request.user.is_staff
        
        return obj.user == request.user


class CanAccessAdvancedRecommendations(permissions.BasePermission):
    """Permission pour accéder aux recommandations avancées (utilisateurs premium)"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les admins ont toujours accès
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Vérifier si l'utilisateur a un abonnement premium
        # (Cette logique dépendra de votre système d'abonnement)
        if hasattr(request.user, 'subscription'):
            return request.user.subscription.is_premium
        
        # Par défaut, autoriser l'accès (à ajuster selon vos besoins)
        return True


class CanProvideFeedback(permissions.BasePermission):
    """Permission pour donner des feedbacks sur les recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les utilisateurs actifs peuvent donner des feedbacks
        return request.user.is_active
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire peut modifier son feedback
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user or request.user.is_staff
        
        return obj.user == request.user


class CanAccessSimilarityData(permissions.BasePermission):
    """Permission pour accéder aux données de similarité"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les méthodes de lecture sont autorisées pour tous les utilisateurs
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Seuls les admins peuvent modifier les données de similarité
        return request.user.is_staff or request.user.is_superuser


class CanManageTrendingBooks(permissions.BasePermission):
    """Permission pour gérer les livres en tendance"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les méthodes de lecture sont autorisées pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Seuls les admins peuvent modifier les tendances
        return request.user.is_staff or request.user.is_superuser


class CanExportRecommendationData(permissions.BasePermission):
    """Permission pour exporter les données de recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les utilisateurs peuvent exporter leurs propres données
        user_id = request.query_params.get('user_id')
        if not user_id or user_id == str(request.user.id):
            return True
        
        # Seuls les admins peuvent exporter les données d'autres utilisateurs
        return request.user.is_staff or request.user.is_superuser


class IsAdminOrOwner(permissions.BasePermission):
    """Permission pour les admins ou propriétaires"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Les admins ont accès à tout
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Les propriétaires ont accès à leurs objets
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class CanModerateRecommendations(permissions.BasePermission):
    """Permission pour modérer les recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Seuls les modérateurs et admins peuvent modérer
        return (
            request.user.is_staff or 
            request.user.is_superuser or
            request.user.groups.filter(name='moderators').exists()
        )


class CanAccessBulkOperations(permissions.BasePermission):
    """Permission pour les opérations en lot"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Seuls les admins et utilisateurs premium peuvent faire des opérations en lot
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Vérifier si l'utilisateur a un abonnement premium
        if hasattr(request.user, 'subscription'):
            return request.user.subscription.is_premium
        
        return False


class CanConfigureRecommendationEngine(permissions.BasePermission):
    """Permission pour configurer le moteur de recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Seuls les super admins peuvent configurer le moteur
        return request.user.is_superuser


class RateLimitedPermission(permissions.BasePermission):
    """Permission avec limitation de taux pour les recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les admins ne sont pas limités
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Vérifier la limite de taux (exemple: 100 requêtes par heure)
        from django.core.cache import cache
        
        cache_key = f"rate_limit_recommendations_{request.user.id}"
        current_requests = cache.get(cache_key, 0)
        
        # Limite pour les utilisateurs normaux
        max_requests = 100
        
        # Limite plus élevée pour les utilisateurs premium
        if hasattr(request.user, 'subscription') and request.user.subscription.is_premium:
            max_requests = 500
        
        if current_requests >= max_requests:
            return False
        
        # Incrémenter le compteur
        cache.set(cache_key, current_requests + 1, 3600)  # 1 heure
        
        return True


class CanShareRecommendations(permissions.BasePermission):
    """Permission pour partager des recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les utilisateurs actifs peuvent partager leurs recommandations
        return request.user.is_active
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire peut partager ses recommandations
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        
        return True


class CanAccessRecommendationHistory(permissions.BasePermission):
    """Permission pour accéder à l'historique des recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return request.user.is_active
    
    def has_object_permission(self, request, view, obj):
        # Les utilisateurs peuvent voir leur propre historique
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        
        return True


class CanManageRecommendationSettings(permissions.BasePermission):
    """Permission pour gérer les paramètres de recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les utilisateurs peuvent gérer leurs propres paramètres
        return request.user.is_active
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire peut modifier ses paramètres
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class CanAccessRecommendationInsights(permissions.BasePermission):
    """Permission pour accéder aux insights de recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Les utilisateurs peuvent voir leurs propres insights
        user_id = request.query_params.get('user_id')
        if not user_id or user_id == str(request.user.id):
            return True
        
        # Seuls les admins peuvent voir les insights d'autres utilisateurs
        return request.user.is_staff or request.user.is_superuser


class CanTestRecommendationAlgorithms(permissions.BasePermission):
    """Permission pour tester les algorithmes de recommandations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Seuls les développeurs et admins peuvent tester les algorithmes
        return (
            request.user.is_staff or 
            request.user.is_superuser or
            request.user.groups.filter(name__in=['developers', 'data_scientists']).exists()
        )