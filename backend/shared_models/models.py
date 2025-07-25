"""
Modèles partagés pour les références inter-services dans l'architecture microservices.
Ces modèles contiennent uniquement les données essentielles pour les références
sans créer de dépendances directes entre services.
"""

from django.db import models
import uuid

# Import des modèles de facturation
from .billing import (
    Invoice, InvoiceItem, AuthorRoyalty, RecurringBilling, 
    BillingConfiguration
)
from .financial_reports import PaymentTransaction


class BookReference(models.Model):
    """
    Référence partagée pour les livres.
    Contient uniquement les informations essentielles nécessaires
    pour les références inter-services.
    """
    
    # UUID du livre dans le service catalog
    book_uuid = models.UUIDField(
        unique=True,
        help_text="UUID du livre dans catalog_service"
    )
    
    # Métadonnées essentielles
    title = models.CharField(
        max_length=500,
        help_text="Titre du livre"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="Slug pour les URLs"
    )
    
    # Informations de base pour les relations
    isbn = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="ISBN du livre"
    )
    
    # Métadonnées de synchronisation
    service_source = models.CharField(
        max_length=50,
        default='catalog_service',
        help_text="Service source de cette référence"
    )
    last_sync = models.DateTimeField(
        auto_now=True,
        help_text="Dernière synchronisation avec le service source"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Indique si le livre est toujours actif"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shared_book_references'
        verbose_name = 'Référence de livre'
        verbose_name_plural = 'Références de livres'
        indexes = [
            models.Index(fields=['book_uuid']),
            models.Index(fields=['slug']),
            models.Index(fields=['isbn']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"BookRef: {self.title}"


class AuthorReference(models.Model):
    """
    Référence partagée pour les auteurs.
    """
    
    # UUID de l'auteur dans le service catalog
    author_uuid = models.UUIDField(
        unique=True,
        help_text="UUID de l'auteur dans catalog_service"
    )
    
    # Métadonnées essentielles
    name = models.CharField(
        max_length=200,
        help_text="Nom de l'auteur"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="Slug pour les URLs"
    )
    
    # Métadonnées de synchronisation
    service_source = models.CharField(
        max_length=50,
        default='catalog_service'
    )
    last_sync = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shared_author_references'
        verbose_name = 'Référence d\'auteur'
        verbose_name_plural = 'Références d\'auteurs'
        indexes = [
            models.Index(fields=['author_uuid']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"AuthorRef: {self.name}"


class CategoryReference(models.Model):
    """
    Référence partagée pour les catégories.
    """
    
    # UUID de la catégorie dans le service catalog
    category_uuid = models.UUIDField(
        unique=True,
        help_text="UUID de la catégorie dans catalog_service"
    )
    
    # Métadonnées essentielles
    name = models.CharField(
        max_length=200,
        help_text="Nom de la catégorie"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="Slug pour les URLs"
    )
    
    # Hiérarchie simple
    parent_uuid = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID de la catégorie parente"
    )
    
    # Métadonnées de synchronisation
    service_source = models.CharField(
        max_length=50,
        default='catalog_service'
    )
    last_sync = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shared_category_references'
        verbose_name = 'Référence de catégorie'
        verbose_name_plural = 'Références de catégories'
        indexes = [
            models.Index(fields=['category_uuid']),
            models.Index(fields=['slug']),
            models.Index(fields=['parent_uuid']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"CategoryRef: {self.name}"


class UserReference(models.Model):
    """
    Référence partagée pour les utilisateurs.
    Contient uniquement les informations publiques nécessaires
    pour les références inter-services.
    """
    
    # UUID de l'utilisateur dans le service auth
    user_uuid = models.UUIDField(
        unique=True,
        help_text="UUID de l'utilisateur dans auth_service"
    )
    
    # Métadonnées publiques essentielles
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Nom d'utilisateur"
    )
    
    # Informations de profil public
    display_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nom d'affichage public"
    )
    
    # Métadonnées de synchronisation
    service_source = models.CharField(
        max_length=50,
        default='auth_service'
    )
    last_sync = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shared_user_references'
        verbose_name = 'Référence d\'utilisateur'
        verbose_name_plural = 'Références d\'utilisateurs'
        indexes = [
            models.Index(fields=['user_uuid']),
            models.Index(fields=['username']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"UserRef: {self.username}"


class ServiceSync(models.Model):
    """
    Modèle pour gérer la synchronisation entre services.
    Permet de tracker les synchronisations et gérer les conflits.
    """
    
    SYNC_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('conflict', 'Conflit'),
    ]
    
    SYNC_TYPE_CHOICES = [
        ('create', 'Création'),
        ('update', 'Mise à jour'),
        ('delete', 'Suppression'),
        ('full_sync', 'Synchronisation complète'),
    ]
    
    # Identification
    sync_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Services concernés
    source_service = models.CharField(
        max_length=50,
        help_text="Service source de la synchronisation"
    )
    target_service = models.CharField(
        max_length=50,
        help_text="Service cible de la synchronisation"
    )
    
    # Type de synchronisation
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPE_CHOICES
    )
    
    # Objet concerné
    object_type = models.CharField(
        max_length=50,
        help_text="Type d'objet synchronisé (Book, Author, etc.)"
    )
    object_uuid = models.UUIDField(
        help_text="UUID de l'objet synchronisé"
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='pending'
    )
    
    # Métadonnées
    sync_data = models.JSONField(
        default=dict,
        help_text="Données de synchronisation"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Message d'erreur en cas d'échec"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'shared_service_sync'
        verbose_name = 'Synchronisation de service'
        verbose_name_plural = 'Synchronisations de services'
        indexes = [
            models.Index(fields=['source_service', 'target_service']),
            models.Index(fields=['object_type', 'object_uuid']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Sync: {self.source_service} -> {self.target_service} ({self.object_type})"


class CrossServiceEvent(models.Model):
    """
    Modèle pour les événements inter-services.
    Permet la communication asynchrone entre services.
    """
    
    EVENT_TYPES = [
        ('book.created', 'Livre créé'),
        ('book.updated', 'Livre mis à jour'),
        ('book.deleted', 'Livre supprimé'),
        ('author.created', 'Auteur créé'),
        ('author.updated', 'Auteur mis à jour'),
        ('category.created', 'Catégorie créée'),
        ('user.created', 'Utilisateur créé'),
        ('user.updated', 'Utilisateur mis à jour'),
        ('reading.started', 'Lecture commencée'),
        ('reading.completed', 'Lecture terminée'),
        ('recommendation.generated', 'Recommandation générée'),
        ('recommendation.clicked', 'Recommandation cliquée'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En traitement'),
        ('processed', 'Traité'),
        ('failed', 'Échoué'),
        ('ignored', 'Ignoré'),
    ]
    
    # Identification
    event_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Événement
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES
    )
    event_version = models.CharField(
        max_length=10,
        default='1.0',
        help_text="Version du schéma d'événement"
    )
    
    # Services
    source_service = models.CharField(
        max_length=50,
        help_text="Service émetteur de l'événement"
    )
    target_services = models.JSONField(
        default=list,
        help_text="Liste des services cibles"
    )
    
    # Données
    event_data = models.JSONField(
        default=dict,
        help_text="Données de l'événement"
    )
    
    # Métadonnées
    correlation_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID de corrélation pour tracer les événements liés"
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Traitement
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Messages d'erreur
    error_message = models.TextField(blank=True)
    processing_log = models.JSONField(
        default=list,
        help_text="Log des tentatives de traitement"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'shared_cross_service_events'
        verbose_name = 'Événement inter-services'
        verbose_name_plural = 'Événements inter-services'
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['source_service']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['next_retry_at']),
            models.Index(fields=['correlation_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Event: {self.event_type} from {self.source_service}"
    
    @property
    def can_retry(self):
        """Vérifie si l'événement peut être retenté"""
        return (
            self.status == 'failed' and 
            self.retry_count < self.max_retries
        )