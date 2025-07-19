from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission personnalisée pour permettre seulement aux propriétaires d'un objet de le modifier."""
    
    def has_object_permission(self, request, view, obj):
        # Permissions de lecture pour toutes les requêtes
        # Donc on autorise toujours les requêtes GET, HEAD ou OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissions d'écriture seulement pour le propriétaire de l'objet
        return obj.created_by == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permission personnalisée pour permettre seulement aux admins de modifier."""
    
    def has_permission(self, request, view):
        # Permissions de lecture pour toutes les requêtes
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissions d'écriture seulement pour les admins
        return request.user and request.user.is_staff


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Permission pour les auteurs de livres."""
    
    def has_object_permission(self, request, view, obj):
        # Permissions de lecture pour toutes les requêtes
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissions d'écriture pour les auteurs du livre ou les admins
        if request.user.is_staff:
            return True
        
        # Vérifier si l'utilisateur est un des auteurs du livre
        if hasattr(obj, 'authors'):
            return obj.authors.filter(user=request.user).exists()
        
        return False


class CanManageBooks(permissions.BasePermission):
    """Permission pour gérer les livres (auteurs, éditeurs, admins)."""
    
    def has_permission(self, request, view):
        # Permissions de lecture pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permissions d'écriture pour les utilisateurs authentifiés avec rôle approprié
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins peuvent tout faire
        if request.user.is_staff:
            return True
        
        # Vérifier les rôles utilisateur
        user_roles = request.user.user_roles.values_list('role__name', flat=True)
        allowed_roles = ['author', 'publisher', 'editor']
        
        return any(role in allowed_roles for role in user_roles)


class CanRateBooks(permissions.BasePermission):
    """Permission pour évaluer les livres."""
    
    def has_permission(self, request, view):
        # Seuls les utilisateurs authentifiés peuvent évaluer
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # L'utilisateur peut modifier/supprimer seulement ses propres évaluations
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.user == request.user


class CanManageCollections(permissions.BasePermission):
    """Permission pour gérer les collections."""
    
    def has_permission(self, request, view):
        # Lecture libre pour les collections publiques
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Création/modification pour les utilisateurs authentifiés
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Lecture libre pour les collections publiques
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.created_by == request.user
        
        # Modification seulement par le créateur ou les admins
        return obj.created_by == request.user or request.user.is_staff


class IsPremiumUser(permissions.BasePermission):
    """Permission pour les utilisateurs premium."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Vérifier si l'utilisateur a un abonnement premium
        return request.user.subscription_type in ['premium', 'premium_plus']
    
    def has_object_permission(self, request, view, obj):
        # Pour les livres premium uniquement
        if hasattr(obj, 'is_premium_only') and obj.is_premium_only:
            return self.has_permission(request, view)
        
        return True


class CanDownloadBooks(permissions.BasePermission):
    """Permission pour télécharger les livres."""
    
    def has_object_permission(self, request, view, obj):
        # Livres gratuits : accessible à tous
        if obj.is_free:
            return True
        
        # Utilisateur non authentifié : seulement les livres gratuits
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Livres premium : seulement pour les utilisateurs premium
        if obj.is_premium_only:
            return request.user.subscription_type in ['premium', 'premium_plus']
        
        # Autres livres : utilisateurs authentifiés
        return True


class CanAccessAdminFeatures(permissions.BasePermission):
    """Permission pour accéder aux fonctionnalités d'administration."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)
        )