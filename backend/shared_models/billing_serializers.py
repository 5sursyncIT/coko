"""Serializers pour le système de facturation Coko"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime

from .billing import (
    Invoice, InvoiceItem, AuthorRoyalty, BillingConfiguration, 
    RecurringBilling
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les utilisateurs"""
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'subscription_type']
        read_only_fields = fields
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['full_name'] = instance.get_full_name()
        return data


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer pour les lignes de facture"""
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'description', 'quantity', 'unit_price', 'total_amount',
            'book_uuid', 'book_title', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'total_amount', 'created_at']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être positive")
        return value
    
    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Le prix unitaire ne peut pas être négatif")
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer pour les factures"""
    
    user = UserBasicSerializer(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    invoice_type_display = serializers.CharField(source='get_invoice_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'user', 'invoice_type', 'invoice_type_display',
            'status', 'status_display', 'currency', 'currency_display',
            'subtotal', 'tax_rate', 'tax_amount', 'discount_amount', 'total_amount',
            'billing_name', 'billing_email', 'billing_address', 'billing_country', 'billing_phone',
            'issue_date', 'due_date', 'paid_date', 'notes', 'metadata',
            'created_at', 'updated_at', 'items', 'days_overdue', 'is_overdue'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'subtotal', 'tax_amount', 'total_amount',
            'created_at', 'updated_at', 'days_overdue', 'is_overdue'
        ]
    
    def validate_tax_rate(self, value):
        if value < 0 or value > 1:
            raise serializers.ValidationError("Le taux de TVA doit être entre 0 et 1")
        return value
    
    def validate_discount_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Le montant de remise ne peut pas être négatif")
        return value


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de factures"""
    
    items = InvoiceItemSerializer(many=True, required=False)
    
    class Meta:
        model = Invoice
        fields = [
            'user', 'invoice_type', 'currency', 'tax_rate', 'discount_amount',
            'billing_name', 'billing_email', 'billing_address', 'billing_country', 'billing_phone',
            'due_date', 'notes', 'metadata', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        
        # Créer la facture
        invoice = Invoice.objects.create(**validated_data)
        
        # Créer les lignes de facture
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        return invoice
    
    def validate(self, data):
        # Validation des données de facturation
        if not data.get('billing_name'):
            if data.get('user'):
                data['billing_name'] = data['user'].get_full_name()
            else:
                raise serializers.ValidationError("Le nom de facturation est requis")
        
        if not data.get('billing_email'):
            if data.get('user'):
                data['billing_email'] = data['user'].email
            else:
                raise serializers.ValidationError("L'email de facturation est requis")
        
        return data


class AuthorRoyaltySerializer(serializers.ModelSerializer):
    """Serializer pour les royalties d'auteurs"""
    
    author = UserBasicSerializer(read_only=True)
    invoice = InvoiceSerializer(read_only=True)
    royalty_type_display = serializers.CharField(source='get_royalty_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AuthorRoyalty
        fields = [
            'id', 'author', 'book_uuid', 'book_title', 'invoice',
            'royalty_type', 'royalty_type_display', 'status', 'status_display',
            'base_amount', 'royalty_rate', 'royalty_amount', 'currency',
            'period_start', 'period_end', 'calculation_details', 'notes',
            'created_at', 'updated_at', 'calculated_at', 'paid_at'
        ]
        read_only_fields = [
            'id', 'royalty_amount', 'created_at', 'updated_at', 
            'calculated_at', 'paid_at'
        ]
    
    def validate_royalty_rate(self, value):
        if value < 0 or value > 1:
            raise serializers.ValidationError("Le taux de royalty doit être entre 0 et 1")
        return value
    
    def validate_base_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Le montant de base ne peut pas être négatif")
        return value
    
    def validate(self, data):
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        
        if period_start and period_end and period_start >= period_end:
            raise serializers.ValidationError(
                "La date de début doit être antérieure à la date de fin"
            )
        
        return data


class RecurringBillingSerializer(serializers.ModelSerializer):
    """Serializer pour la facturation récurrente"""
    
    user = UserBasicSerializer(read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_due_for_billing = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = RecurringBilling
        fields = [
            'id', 'user', 'subscription_type', 'frequency', 'frequency_display',
            'amount', 'currency', 'status', 'status_display',
            'start_date', 'end_date', 'next_billing_date', 'last_billing_date',
            'total_cycles', 'completed_cycles', 'failed_attempts',
            'metadata', 'created_at', 'updated_at', 'is_due_for_billing'
        ]
        read_only_fields = [
            'id', 'completed_cycles', 'failed_attempts', 'last_billing_date',
            'created_at', 'updated_at', 'is_due_for_billing'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif")
        return value
    
    def validate_total_cycles(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Le nombre total de cycles doit être positif")
        return value
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        next_billing_date = data.get('next_billing_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError(
                "La date de début doit être antérieure à la date de fin"
            )
        
        if start_date and next_billing_date and next_billing_date < start_date:
            raise serializers.ValidationError(
                "La prochaine date de facturation ne peut pas être antérieure à la date de début"
            )
        
        return data


class BillingConfigurationSerializer(serializers.ModelSerializer):
    """Serializer pour la configuration de facturation"""
    
    config_type_display = serializers.CharField(source='get_config_type_display', read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = BillingConfiguration
        fields = [
            'id', 'config_type', 'config_type_display', 'config_key', 'config_value',
            'country_code', 'user_type', 'description', 'is_active',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_config_value(self, value):
        # Validation basique du format JSON
        if not isinstance(value, (dict, list, str, int, float, bool)):
            raise serializers.ValidationError(
                "La valeur de configuration doit être un type JSON valide"
            )
        return value
    
    def validate(self, data):
        # Vérifier l'unicité de la configuration
        config_type = data.get('config_type')
        config_key = data.get('config_key')
        country_code = data.get('country_code', '')
        user_type = data.get('user_type', '')
        
        # Exclure l'instance actuelle lors de la mise à jour
        queryset = BillingConfiguration.objects.filter(
            config_type=config_type,
            config_key=config_key,
            country_code=country_code,
            user_type=user_type
        )
        
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Une configuration avec ces paramètres existe déjà"
            )
        
        return data


class RoyaltyCalculationSerializer(serializers.Serializer):
    """Serializer pour les paramètres de calcul de royalties"""
    
    author_id = serializers.UUIDField(required=False, allow_null=True)
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()
    
    def validate(self, data):
        period_start = data['period_start']
        period_end = data['period_end']
        
        if period_start >= period_end:
            raise serializers.ValidationError(
                "La date de début doit être antérieure à la date de fin"
            )
        
        # Vérifier que la période n'est pas trop longue (max 1 an)
        if (period_end - period_start).days > 365:
            raise serializers.ValidationError(
                "La période ne peut pas dépasser 1 an"
            )
        
        return data


class InvoiceStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de factures"""
    
    total_invoices = serializers.IntegerField()
    pending_invoices = serializers.IntegerField()
    paid_invoices = serializers.IntegerField()
    overdue_invoices = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class RoyaltySummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des royalties"""
    
    total_royalties = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_royalties = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_royalties = serializers.DecimalField(max_digits=12, decimal_places=2)
    royalties_by_type = serializers.DictField()
    last_calculation = serializers.DateTimeField(allow_null=True)


class BulkInvoiceActionSerializer(serializers.Serializer):
    """Serializer pour les actions en lot sur les factures"""
    
    invoice_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    payment_date = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate_invoice_ids(self, value):
        # Vérifier que toutes les factures existent
        existing_count = Invoice.objects.filter(id__in=value).count()
        if existing_count != len(value):
            raise serializers.ValidationError(
                "Certaines factures spécifiées n'existent pas"
            )
        return value


class RecurringBillingActionSerializer(serializers.Serializer):
    """Serializer pour les actions sur la facturation récurrente"""
    
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class BillingAutomationTaskSerializer(serializers.Serializer):
    """Serializer pour les tâches d'automatisation"""
    
    TASK_CHOICES = [
        ('daily', 'Tâches quotidiennes'),
        ('monthly_royalties', 'Calcul mensuel des royalties'),
    ]
    
    task_type = serializers.ChoiceField(choices=TASK_CHOICES)


class ConfigurationRequestSerializer(serializers.Serializer):
    """Serializer pour les requêtes de configuration"""
    
    config_type = serializers.CharField(max_length=50)
    config_key = serializers.CharField(max_length=100)
    country_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    user_type = serializers.CharField(max_length=50, required=False, allow_blank=True)