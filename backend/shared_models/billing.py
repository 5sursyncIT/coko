"""
Système de facturation complète et automatisée pour Coko
Gestion des factures clients, royalties auteurs, et facturation récurrente
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Any, Optional


class Invoice(models.Model):
    """Modèle principal pour les factures"""
    
    INVOICE_TYPES = [
        ('subscription', 'Abonnement'),
        ('book_purchase', 'Achat de livre'),
        ('premium_upgrade', 'Mise à niveau premium'),
        ('author_royalty', 'Royalties auteur'),
        ('refund', 'Remboursement'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente'),
        ('sent', 'Envoyée'),
        ('paid', 'Payée'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annulée'),
        ('refunded', 'Remboursée'),
    ]
    
    CURRENCY_CHOICES = [
        ('XOF', 'Franc CFA (XOF)'),
        ('NGN', 'Naira nigérian'),
        ('GHS', 'Cedi ghanéen'),
        ('EUR', 'Euro'),
        ('USD', 'Dollar américain'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True)
    
    # Relations
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    payment_transaction = models.OneToOneField(
        'shared_models.PaymentTransaction', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='invoice'
    )
    
    # Détails de facturation
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='XOF')
    
    # Montants
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Informations client
    billing_name = models.CharField(max_length=255)
    billing_email = models.EmailField()
    billing_address = models.TextField(blank=True)
    billing_country = models.CharField(max_length=10, blank=True)
    billing_phone = models.CharField(max_length=20, blank=True)
    
    # Dates importantes
    issue_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    paid_date = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['invoice_type', 'status']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self):
        return f"Facture {self.invoice_number} - {self.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Calculer le total
        self.calculate_totals()
        
        # Définir la date d'échéance si non définie
        if not self.due_date:
            self.due_date = self.issue_date + timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self) -> str:
        """Génère un numéro de facture unique"""
        year = timezone.now().year
        month = timezone.now().month
        
        # Compter les factures du mois
        count = Invoice.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).count() + 1
        
        return f"COKO-{year}{month:02d}-{count:04d}"
    
    def calculate_totals(self):
        """Calcule les totaux de la facture"""
        # Calculer le sous-total à partir des lignes de facture
        self.subtotal = sum(
            item.total_amount for item in self.items.all()
        ) or Decimal('0.00')
        
        # Calculer la TVA
        self.tax_amount = self.subtotal * self.tax_rate
        
        # Calculer le total
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
    
    def mark_as_paid(self, payment_date: datetime = None):
        """Marque la facture comme payée"""
        self.status = 'paid'
        self.paid_date = payment_date or timezone.now()
        self.save()
    
    def is_overdue(self) -> bool:
        """Vérifie si la facture est en retard"""
        return (
            self.status in ['pending', 'sent'] and 
            self.due_date < timezone.now()
        )
    
    @property
    def days_overdue(self) -> int:
        """Nombre de jours de retard"""
        if self.is_overdue():
            return (timezone.now() - self.due_date).days
        return 0


class InvoiceItem(models.Model):
    """Lignes de facture"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    
    # Détails de l'article
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Références optionnelles
    book_uuid = models.UUIDField(null=True, blank=True)
    book_title = models.CharField(max_length=500, blank=True)
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'billing_invoice_items'
        ordering = ['created_at']
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Recalculer les totaux de la facture
        self.invoice.calculate_totals()
        self.invoice.save()
    
    def __str__(self):
        return f"{self.description} - {self.total_amount} {self.invoice.currency}"


class AuthorRoyalty(models.Model):
    """Gestion des royalties pour les auteurs"""
    
    ROYALTY_TYPES = [
        ('book_sale', 'Vente de livre'),
        ('subscription_share', 'Part d\'abonnement'),
        ('tip', 'Pourboire'),
        ('bonus', 'Bonus'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('calculated', 'Calculée'),
        ('invoiced', 'Facturée'),
        ('paid', 'Payée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='royalties')
    book_uuid = models.UUIDField(null=True, blank=True)
    book_title = models.CharField(max_length=500, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Détails de la royalty
    royalty_type = models.CharField(max_length=20, choices=ROYALTY_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Calculs financiers
    base_amount = models.DecimalField(max_digits=12, decimal_places=2)  # Montant de base
    royalty_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )  # Taux de royalty (0.0 à 1.0)
    royalty_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='XOF')
    
    # Période de calcul
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Métadonnées
    calculation_details = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    calculated_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'billing_author_royalties'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', 'status']),
            models.Index(fields=['book_uuid', 'period_start']),
            models.Index(fields=['status', 'period_end']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculer le montant de royalty
        self.royalty_amount = self.base_amount * self.royalty_rate
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Royalty {self.author.get_full_name()} - {self.royalty_amount} {self.currency}"
    
    def mark_as_calculated(self):
        """Marque la royalty comme calculée"""
        self.status = 'calculated'
        self.calculated_at = timezone.now()
        self.save()
    
    def mark_as_paid(self):
        """Marque la royalty comme payée"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()


class BillingConfiguration(models.Model):
    """Configuration paramètrable du système de facturation"""
    
    CONFIG_TYPES = [
        ('tax_rate', 'Taux de TVA'),
        ('royalty_rate', 'Taux de royalty'),
        ('payment_terms', 'Conditions de paiement'),
        ('invoice_template', 'Template de facture'),
        ('auto_billing', 'Facturation automatique'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Configuration
    config_type = models.CharField(max_length=50, choices=CONFIG_TYPES)
    config_key = models.CharField(max_length=100)
    config_value = models.JSONField()
    
    # Scope de la configuration
    country_code = models.CharField(max_length=10, blank=True)  # Configuration par pays
    user_type = models.CharField(max_length=50, blank=True)  # Configuration par type d'utilisateur
    
    # Métadonnées
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'billing_configurations'
        unique_together = ['config_type', 'config_key', 'country_code', 'user_type']
        ordering = ['config_type', 'config_key']
    
    def __str__(self):
        return f"{self.get_config_type_display()} - {self.config_key}"
    
    @classmethod
    def get_config(cls, config_type: str, config_key: str, country_code: str = '', user_type: str = ''):
        """Récupère une configuration"""
        try:
            config = cls.objects.get(
                config_type=config_type,
                config_key=config_key,
                country_code=country_code,
                user_type=user_type,
                is_active=True
            )
            return config.config_value
        except cls.DoesNotExist:
            # Essayer avec des paramètres moins spécifiques
            if country_code or user_type:
                return cls.get_config(config_type, config_key, '', '')
            return None


class RecurringBilling(models.Model):
    """Gestion de la facturation récurrente"""
    
    FREQUENCY_CHOICES = [
        ('monthly', 'Mensuel'),
        ('quarterly', 'Trimestriel'),
        ('yearly', 'Annuel'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('paused', 'En pause'),
        ('cancelled', 'Annulé'),
        ('expired', 'Expiré'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recurring_billings')
    
    # Configuration de récurrence
    subscription_type = models.CharField(max_length=50)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='XOF')
    
    # Statut et dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField()
    last_billing_date = models.DateTimeField(null=True, blank=True)
    
    # Compteurs
    total_cycles = models.IntegerField(null=True, blank=True)  # Nombre total de cycles (null = illimité)
    completed_cycles = models.IntegerField(default=0)
    failed_attempts = models.IntegerField(default=0)
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_recurring'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['next_billing_date', 'status']),
            models.Index(fields=['subscription_type', 'status']),
        ]
    
    def __str__(self):
        return f"Facturation récurrente {self.user.get_full_name()} - {self.subscription_type}"
    
    def calculate_next_billing_date(self) -> datetime:
        """Calcule la prochaine date de facturation"""
        if self.frequency == 'monthly':
            return self.next_billing_date + timedelta(days=30)
        elif self.frequency == 'quarterly':
            return self.next_billing_date + timedelta(days=90)
        elif self.frequency == 'yearly':
            return self.next_billing_date + timedelta(days=365)
        return self.next_billing_date
    
    def is_due_for_billing(self) -> bool:
        """Vérifie si la facturation est due"""
        return (
            self.status == 'active' and
            self.next_billing_date <= timezone.now() and
            (self.total_cycles is None or self.completed_cycles < self.total_cycles)
        )
    
    def process_billing_cycle(self):
        """Traite un cycle de facturation"""
        if not self.is_due_for_billing():
            return None
        
        # Créer une facture pour ce cycle
        invoice = Invoice.objects.create(
            user=self.user,
            invoice_type='subscription',
            currency=self.currency,
            total_amount=self.amount,
            billing_name=self.user.get_full_name(),
            billing_email=self.user.email,
            billing_country=self.user.country,
            billing_phone=self.user.phone or '',
            metadata={'recurring_billing_id': str(self.id)}
        )
        
        # Ajouter une ligne de facture
        InvoiceItem.objects.create(
            invoice=invoice,
            description=f"Abonnement {self.subscription_type} - {self.get_frequency_display()}",
            quantity=Decimal('1.00'),
            unit_price=self.amount
        )
        
        # Mettre à jour les compteurs
        self.completed_cycles += 1
        self.last_billing_date = timezone.now()
        self.next_billing_date = self.calculate_next_billing_date()
        
        # Vérifier si on a atteint le nombre total de cycles
        if self.total_cycles and self.completed_cycles >= self.total_cycles:
            self.status = 'expired'
        
        self.save()
        
        return invoice