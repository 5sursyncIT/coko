"""Interface d'administration Django pour le système de facturation Coko"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from datetime import datetime, timedelta
import csv

from .billing import (
    Invoice, InvoiceItem, AuthorRoyalty, BillingConfiguration, 
    RecurringBilling
)
from .billing_services import (
    InvoiceService, RoyaltyService, RecurringBillingService,
    BillingAutomationService
)


class InvoiceItemInline(admin.TabularInline):
    """Inline pour les lignes de facture"""
    model = InvoiceItem
    extra = 0
    readonly_fields = ['total_amount', 'created_at']
    fields = [
        'description', 'quantity', 'unit_price', 'total_amount',
        'book_uuid', 'book_title', 'created_at'
    ]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Administration des factures"""
    
    list_display = [
        'invoice_number', 'user_link', 'invoice_type', 'status_badge',
        'total_amount', 'currency', 'issue_date', 'due_date', 'days_overdue_display'
    ]
    list_filter = [
        'status', 'invoice_type', 'currency', 'issue_date', 'due_date'
    ]
    search_fields = [
        'invoice_number', 'user__first_name', 'user__last_name', 
        'user__email', 'billing_name', 'billing_email'
    ]
    readonly_fields = [
        'id', 'invoice_number', 'subtotal', 'tax_amount', 'total_amount',
        'created_at', 'updated_at', 'days_overdue', 'is_overdue'
    ]
    fieldsets = [
        ('Informations générales', {
            'fields': [
                'id', 'invoice_number', 'user', 'payment_transaction',
                'invoice_type', 'status', 'currency'
            ]
        }),
        ('Montants', {
            'fields': [
                'subtotal', 'tax_rate', 'tax_amount', 'discount_amount', 'total_amount'
            ]
        }),
        ('Informations de facturation', {
            'fields': [
                'billing_name', 'billing_email', 'billing_address',
                'billing_country', 'billing_phone'
            ]
        }),
        ('Dates', {
            'fields': [
                'issue_date', 'due_date', 'paid_date',
                'created_at', 'updated_at'
            ]
        }),
        ('Métadonnées', {
            'fields': ['notes', 'metadata'],
            'classes': ['collapse']
        }),
        ('Statut', {
            'fields': ['days_overdue', 'is_overdue'],
            'classes': ['collapse']
        })
    ]
    inlines = [InvoiceItemInline]
    actions = [
        'mark_as_paid', 'mark_as_sent', 'export_to_csv',
        'send_invoice_emails', 'mark_as_overdue'
    ]
    
    def user_link(self, obj):
        """Lien vers l'utilisateur"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    user_link.short_description = 'Utilisateur'
    
    def status_badge(self, obj):
        """Badge coloré pour le statut"""
        colors = {
            'draft': 'gray',
            'pending': 'orange',
            'sent': 'blue',
            'paid': 'green',
            'overdue': 'red',
            'cancelled': 'gray',
            'refunded': 'purple'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def days_overdue_display(self, obj):
        """Affichage des jours de retard"""
        if obj.is_overdue():
            return format_html(
                '<span style="color: red; font-weight: bold;">{} jours</span>',
                obj.days_overdue
            )
        return '-'
    days_overdue_display.short_description = 'Retard'
    
    def mark_as_paid(self, request, queryset):
        """Marque les factures sélectionnées comme payées"""
        count = 0
        for invoice in queryset.filter(status__in=['pending', 'sent', 'overdue']):
            invoice.mark_as_paid()
            count += 1
        
        self.message_user(
            request,
            f'{count} facture(s) marquée(s) comme payée(s).',
            messages.SUCCESS
        )
    mark_as_paid.short_description = 'Marquer comme payées'
    
    def mark_as_sent(self, request, queryset):
        """Marque les factures comme envoyées"""
        count = queryset.filter(status='draft').update(status='sent')
        self.message_user(
            request,
            f'{count} facture(s) marquée(s) comme envoyée(s).',
            messages.SUCCESS
        )
    mark_as_sent.short_description = 'Marquer comme envoyées'
    
    def mark_as_overdue(self, request, queryset):
        """Marque les factures en retard"""
        count = InvoiceService.mark_overdue_invoices()
        self.message_user(
            request,
            f'{count} facture(s) marquée(s) comme en retard.',
            messages.INFO
        )
    mark_as_overdue.short_description = 'Mettre à jour les retards'
    
    def export_to_csv(self, request, queryset):
        """Exporte les factures en CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="factures.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Numéro', 'Utilisateur', 'Type', 'Statut', 'Montant', 'Devise',
            'Date émission', 'Date échéance', 'Date paiement'
        ])
        
        for invoice in queryset:
            writer.writerow([
                invoice.invoice_number,
                invoice.user.get_full_name(),
                invoice.get_invoice_type_display(),
                invoice.get_status_display(),
                str(invoice.total_amount),
                invoice.currency,
                invoice.issue_date.strftime('%Y-%m-%d'),
                invoice.due_date.strftime('%Y-%m-%d'),
                invoice.paid_date.strftime('%Y-%m-%d') if invoice.paid_date else ''
            ])
        
        return response
    export_to_csv.short_description = 'Exporter en CSV'
    
    def send_invoice_emails(self, request, queryset):
        """Envoie les factures par email"""
        from .billing_tasks import send_invoice_email
        
        count = 0
        for invoice in queryset.filter(status__in=['draft', 'pending']):
            send_invoice_email.delay(str(invoice.id))
            count += 1
        
        self.message_user(
            request,
            f'{count} email(s) de facture programmé(s).',
            messages.SUCCESS
        )
    send_invoice_emails.short_description = 'Envoyer par email'


@admin.register(AuthorRoyalty)
class AuthorRoyaltyAdmin(admin.ModelAdmin):
    """Administration des royalties d'auteurs"""
    
    list_display = [
        'author_link', 'royalty_type', 'book_title_short', 'status_badge',
        'base_amount', 'royalty_rate_percent', 'royalty_amount', 'currency',
        'period_start', 'period_end'
    ]
    list_filter = [
        'status', 'royalty_type', 'currency', 'period_start', 'period_end'
    ]
    search_fields = [
        'author__first_name', 'author__last_name', 'author__email',
        'book_title', 'book_uuid'
    ]
    readonly_fields = [
        'id', 'royalty_amount', 'created_at', 'updated_at',
        'calculated_at', 'paid_at'
    ]
    fieldsets = [
        ('Informations générales', {
            'fields': [
                'id', 'author', 'book_uuid', 'book_title', 'invoice'
            ]
        }),
        ('Détails de la royalty', {
            'fields': [
                'royalty_type', 'status', 'base_amount', 'royalty_rate',
                'royalty_amount', 'currency'
            ]
        }),
        ('Période', {
            'fields': ['period_start', 'period_end']
        }),
        ('Calculs', {
            'fields': ['calculation_details', 'notes'],
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': [
                'created_at', 'updated_at', 'calculated_at', 'paid_at'
            ],
            'classes': ['collapse']
        })
    ]
    actions = [
        'mark_as_calculated', 'mark_as_paid', 'generate_invoices',
        'export_to_csv'
    ]
    
    def author_link(self, obj):
        """Lien vers l'auteur"""
        url = reverse('admin:auth_user_change', args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', url, obj.author.get_full_name())
    author_link.short_description = 'Auteur'
    
    def book_title_short(self, obj):
        """Titre du livre tronqué"""
        if obj.book_title:
            return obj.book_title[:50] + '...' if len(obj.book_title) > 50 else obj.book_title
        return '-'
    book_title_short.short_description = 'Livre'
    
    def status_badge(self, obj):
        """Badge coloré pour le statut"""
        colors = {
            'pending': 'orange',
            'calculated': 'blue',
            'invoiced': 'purple',
            'paid': 'green'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def royalty_rate_percent(self, obj):
        """Taux de royalty en pourcentage"""
        return f'{float(obj.royalty_rate * 100):.2f}%'
    royalty_rate_percent.short_description = 'Taux'
    
    def mark_as_calculated(self, request, queryset):
        """Marque les royalties comme calculées"""
        count = 0
        for royalty in queryset.filter(status='pending'):
            royalty.mark_as_calculated()
            count += 1
        
        self.message_user(
            request,
            f'{count} royalty(ies) marquée(s) comme calculée(s).',
            messages.SUCCESS
        )
    mark_as_calculated.short_description = 'Marquer comme calculées'
    
    def mark_as_paid(self, request, queryset):
        """Marque les royalties comme payées"""
        count = 0
        for royalty in queryset.filter(status__in=['calculated', 'invoiced']):
            royalty.mark_as_paid()
            count += 1
        
        self.message_user(
            request,
            f'{count} royalty(ies) marquée(s) comme payée(s).',
            messages.SUCCESS
        )
    mark_as_paid.short_description = 'Marquer comme payées'
    
    def generate_invoices(self, request, queryset):
        """Génère des factures pour les royalties calculées"""
        # Grouper par auteur
        authors_royalties = {}
        for royalty in queryset.filter(status='calculated', invoice__isnull=True):
            if royalty.author not in authors_royalties:
                authors_royalties[royalty.author] = []
            authors_royalties[royalty.author].append(royalty)
        
        invoice_count = 0
        for author, royalties in authors_royalties.items():
            invoice = RoyaltyService.generate_royalty_invoices(author, royalties)
            if invoice:
                invoice_count += 1
        
        self.message_user(
            request,
            f'{invoice_count} facture(s) de royalties générée(s).',
            messages.SUCCESS
        )
    generate_invoices.short_description = 'Générer les factures'
    
    def export_to_csv(self, request, queryset):
        """Exporte les royalties en CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="royalties.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Auteur', 'Type', 'Livre', 'Montant base', 'Taux', 'Montant royalty',
            'Devise', 'Statut', 'Période début', 'Période fin'
        ])
        
        for royalty in queryset:
            writer.writerow([
                royalty.author.get_full_name(),
                royalty.get_royalty_type_display(),
                royalty.book_title or '',
                str(royalty.base_amount),
                str(royalty.royalty_rate),
                str(royalty.royalty_amount),
                royalty.currency,
                royalty.get_status_display(),
                royalty.period_start.strftime('%Y-%m-%d'),
                royalty.period_end.strftime('%Y-%m-%d')
            ])
        
        return response
    export_to_csv.short_description = 'Exporter en CSV'


@admin.register(RecurringBilling)
class RecurringBillingAdmin(admin.ModelAdmin):
    """Administration de la facturation récurrente"""
    
    list_display = [
        'user_link', 'subscription_type', 'frequency', 'status_badge',
        'amount', 'currency', 'next_billing_date', 'completed_cycles',
        'failed_attempts'
    ]
    list_filter = [
        'status', 'frequency', 'subscription_type', 'currency',
        'next_billing_date'
    ]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__email',
        'subscription_type'
    ]
    readonly_fields = [
        'id', 'completed_cycles', 'last_billing_date',
        'created_at', 'updated_at'
    ]
    fieldsets = [
        ('Informations générales', {
            'fields': [
                'id', 'user', 'subscription_type', 'frequency',
                'amount', 'currency', 'status'
            ]
        }),
        ('Dates', {
            'fields': [
                'start_date', 'end_date', 'next_billing_date',
                'last_billing_date'
            ]
        }),
        ('Compteurs', {
            'fields': [
                'total_cycles', 'completed_cycles', 'failed_attempts'
            ]
        }),
        ('Métadonnées', {
            'fields': ['metadata'],
            'classes': ['collapse']
        }),
        ('Audit', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    actions = [
        'pause_billing', 'resume_billing', 'cancel_billing',
        'process_due_billings', 'export_to_csv'
    ]
    
    def user_link(self, obj):
        """Lien vers l'utilisateur"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    user_link.short_description = 'Utilisateur'
    
    def status_badge(self, obj):
        """Badge coloré pour le statut"""
        colors = {
            'active': 'green',
            'paused': 'orange',
            'cancelled': 'red',
            'expired': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def pause_billing(self, request, queryset):
        """Met en pause les facturations sélectionnées"""
        count = queryset.filter(status='active').update(status='paused')
        self.message_user(
            request,
            f'{count} facturation(s) mise(s) en pause.',
            messages.SUCCESS
        )
    pause_billing.short_description = 'Mettre en pause'
    
    def resume_billing(self, request, queryset):
        """Reprend les facturations en pause"""
        count = 0
        for billing in queryset.filter(status='paused'):
            billing.status = 'active'
            billing.next_billing_date = billing.calculate_next_billing_date()
            billing.save()
            count += 1
        
        self.message_user(
            request,
            f'{count} facturation(s) reprise(s).',
            messages.SUCCESS
        )
    resume_billing.short_description = 'Reprendre'
    
    def cancel_billing(self, request, queryset):
        """Annule les facturations sélectionnées"""
        count = 0
        for billing in queryset.exclude(status='cancelled'):
            billing.status = 'cancelled'
            billing.end_date = timezone.now()
            billing.save()
            count += 1
        
        self.message_user(
            request,
            f'{count} facturation(s) annulée(s).',
            messages.SUCCESS
        )
    cancel_billing.short_description = 'Annuler'
    
    def process_due_billings(self, request, queryset):
        """Traite les facturations dues"""
        invoices = RecurringBillingService.process_due_billings()
        
        self.message_user(
            request,
            f'{len(invoices)} facturation(s) récurrente(s) traitée(s).',
            messages.SUCCESS
        )
    process_due_billings.short_description = 'Traiter les facturations dues'
    
    def export_to_csv(self, request, queryset):
        """Exporte les facturations récurrentes en CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="facturations_recurrentes.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Utilisateur', 'Type abonnement', 'Fréquence', 'Montant', 'Devise',
            'Statut', 'Prochaine facturation', 'Cycles complétés', 'Échecs'
        ])
        
        for billing in queryset:
            writer.writerow([
                billing.user.get_full_name(),
                billing.subscription_type,
                billing.get_frequency_display(),
                str(billing.amount),
                billing.currency,
                billing.get_status_display(),
                billing.next_billing_date.strftime('%Y-%m-%d %H:%M'),
                billing.completed_cycles,
                billing.failed_attempts
            ])
        
        return response
    export_to_csv.short_description = 'Exporter en CSV'


@admin.register(BillingConfiguration)
class BillingConfigurationAdmin(admin.ModelAdmin):
    """Administration de la configuration de facturation"""
    
    list_display = [
        'config_type', 'config_key', 'country_code', 'user_type',
        'is_active', 'created_at'
    ]
    list_filter = [
        'config_type', 'is_active', 'country_code', 'user_type'
    ]
    search_fields = ['config_key', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = [
        ('Configuration', {
            'fields': [
                'config_type', 'config_key', 'config_value',
                'country_code', 'user_type'
            ]
        }),
        ('Métadonnées', {
            'fields': ['description', 'is_active']
        }),
        ('Audit', {
            'fields': ['id', 'created_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Actions personnalisées pour l'administration
class BillingAdminActions:
    """Actions personnalisées pour l'administration de la facturation"""
    
    @staticmethod
    def run_daily_tasks(modeladmin, request, queryset):
        """Lance les tâches quotidiennes de facturation"""
        result = BillingAutomationService.run_daily_billing_tasks()
        
        modeladmin.message_user(
            request,
            f"Tâches quotidiennes exécutées: {result['overdue_invoices']} factures en retard, "
            f"{result['new_recurring_invoices']} nouvelles factures récurrentes.",
            messages.SUCCESS
        )
    
    @staticmethod
    def run_monthly_royalties(modeladmin, request, queryset):
        """Lance le calcul mensuel des royalties"""
        result = BillingAutomationService.run_monthly_royalty_calculation()
        
        modeladmin.message_user(
            request,
            f"Calcul mensuel des royalties terminé: {result['authors_processed']} auteurs traités, "
            f"{result['invoices_generated']} factures générées.",
            messages.SUCCESS
        )


# Ajouter les actions aux modèles appropriés
InvoiceAdmin.actions.extend([
    BillingAdminActions.run_daily_tasks,
    BillingAdminActions.run_monthly_royalties
])