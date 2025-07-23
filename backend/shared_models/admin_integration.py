"""
Intégration du dashboard et des nouvelles fonctionnalités dans l'admin Django
Enregistrement des nouveaux modèles et configuration de l'interface
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.contrib.auth import get_user_model

from .financial_reports import PaymentTransaction
from .audit_trail import AuditLog, SecurityAlert

User = get_user_model()


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Administration des transactions de paiement"""
    
    list_display = [
        'id', 'user', 'amount_with_currency', 'payment_provider', 
        'status', 'transaction_type', 'country_code', 'created_at'
    ]
    
    list_filter = [
        'status', 'payment_provider', 'transaction_type', 'currency',
        'country_code', 'created_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'provider_transaction_id',
        'provider_reference', 'phone_number'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'completed_at',
        'provider_transaction_id', 'fees', 'net_amount'
    ]
    
    fieldsets = (
        ('Transaction', {
            'fields': ('id', 'user', 'amount', 'currency', 'transaction_type', 'status')
        }),
        ('Provider', {
            'fields': (
                'payment_provider', 'provider_transaction_id', 
                'provider_reference', 'phone_number', 'country_code'
            )
        }),
        ('Finances', {
            'fields': ('fees', 'net_amount'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('metadata', 'created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'export_transactions']
    
    def amount_with_currency(self, obj):
        """Affiche le montant avec la devise"""
        return f"{obj.amount} {obj.currency}"
    amount_with_currency.short_description = 'Montant'
    
    def mark_as_completed(self, request, queryset):
        """Marque les transactions comme terminées"""
        updated = 0
        for transaction in queryset:
            if transaction.status != 'completed':
                transaction.mark_completed()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} transaction(s) marquée(s) comme terminée(s).'
        )
    mark_as_completed.short_description = 'Marquer comme terminées'
    
    def mark_as_failed(self, request, queryset):
        """Marque les transactions comme échouées"""
        updated = queryset.update(status='failed')
        self.message_user(
            request,
            f'{updated} transaction(s) marquée(s) comme échouée(s).'
        )
    mark_as_failed.short_description = 'Marquer comme échouées'
    
    def export_transactions(self, request, queryset):
        """Redirige vers l'export des transactions"""
        # Construire l'URL d'export avec les IDs sélectionnés
        ids = ','.join(str(t.id) for t in queryset)
        return redirect(f'/admin/api/export/financial-data/?transaction_ids={ids}')
    export_transactions.short_description = 'Exporter les transactions sélectionnées'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Administration des logs d'audit"""
    
    list_display = [
        'timestamp', 'action_type', 'service', 'user', 'risk_level',
        'success', 'ip_address', 'description_short'
    ]
    
    list_filter = [
        'action_type', 'service', 'risk_level', 'success',
        'timestamp', 'device_type'
    ]
    
    search_fields = [
        'user__username', 'description', 'ip_address',
        'user_agent', 'request_url'
    ]
    
    readonly_fields = [
        'id', 'timestamp', 'correlation_id'
    ]
    
    fieldsets = (
        ('Action', {
            'fields': (
                'action_type', 'service', 'risk_level', 'description'
            )
        }),
        ('Utilisateur', {
            'fields': ('user', 'session_key')
        }),
        ('Objet concerné', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Contexte technique', {
            'fields': (
                'ip_address', 'user_agent', 'referer', 
                'request_method', 'request_url', 'device_type'
            ),
            'classes': ('collapse',)
        }),
        ('Géolocalisation', {
            'fields': ('country', 'city'),
            'classes': ('collapse',)
        }),
        ('Résultat', {
            'fields': ('success', 'error_message', 'impact_assessment')
        }),
        ('Métadonnées', {
            'fields': (
                'changes', 'metadata', 'timestamp', 
                'correlation_id', 'parent_log'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_resolved', 'create_security_alert']
    
    def description_short(self, obj):
        """Description tronquée"""
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def mark_as_resolved(self, request, queryset):
        """Marque les incidents comme résolus"""
        updated = 0
        for log in queryset.filter(risk_level__in=['HIGH', 'CRITICAL']):
            log.mark_as_resolved("Résolu depuis l'admin")
            updated += 1
        
        self.message_user(
            request,
            f'{updated} incident(s) marqué(s) comme résolu(s).'
        )
    mark_as_resolved.short_description = 'Marquer les incidents comme résolus'
    
    def create_security_alert(self, request, queryset):
        """Créer une alerte de sécurité pour les logs sélectionnés"""
        high_risk_logs = queryset.filter(risk_level__in=['HIGH', 'CRITICAL'])
        
        if high_risk_logs.exists():
            alert = SecurityAlert.objects.create(
                alert_type='MANUAL_REVIEW',
                severity='WARNING',
                title=f'Alerte manuelle - {high_risk_logs.count()} événements',
                description=f'Alerte créée manuellement depuis l\'admin pour {high_risk_logs.count()} événements à risque.',
                assigned_to=request.user
            )
            alert.related_logs.set(high_risk_logs[:20])  # Limiter à 20 logs
            
            self.message_user(
                request,
                f'Alerte de sécurité créée (ID: {alert.id}) pour {high_risk_logs.count()} événements.'
            )
        else:
            self.message_user(
                request,
                'Aucun événement à risque élevé sélectionné.',
                level='WARNING'
            )
    create_security_alert.short_description = 'Créer une alerte de sécurité'


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    """Administration des alertes de sécurité"""
    
    list_display = [
        'id', 'alert_type', 'severity', 'status', 'user', 
        'risk_score', 'assigned_to', 'created_at'
    ]
    
    list_filter = [
        'alert_type', 'severity', 'status', 'created_at'
    ]
    
    search_fields = [
        'title', 'description', 'user__username', 'ip_address'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Alerte', {
            'fields': ('alert_type', 'severity', 'status', 'title', 'description')
        }),
        ('Contexte', {
            'fields': ('user', 'ip_address', 'risk_score')
        }),
        ('Traitement', {
            'fields': ('assigned_to', 'investigation_notes', 'resolution_notes')
        }),
        ('Règles de détection', {
            'fields': ('detection_rules',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['assign_to_me', 'resolve_alerts', 'escalate_alerts']
    
    def assign_to_me(self, request, queryset):
        """Assigne les alertes à l'utilisateur actuel"""
        updated = queryset.filter(status='OPEN').update(
            assigned_to=request.user,
            status='INVESTIGATING'
        )
        self.message_user(
            request,
            f'{updated} alerte(s) assignée(s) à vous.'
        )
    assign_to_me.short_description = 'M\'assigner ces alertes'
    
    def resolve_alerts(self, request, queryset):
        """Résout les alertes sélectionnées"""
        updated = 0
        for alert in queryset:
            alert.resolve("Résolu depuis l'admin", request.user)
            updated += 1
        
        self.message_user(
            request,
            f'{updated} alerte(s) résolue(s).'
        )
    resolve_alerts.short_description = 'Résoudre les alertes'
    
    def escalate_alerts(self, request, queryset):
        """Escalade les alertes au niveau supérieur"""
        updated = 0
        for alert in queryset:
            if alert.severity != 'CRITICAL':
                alert.escalate()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} alerte(s) escaladée(s).'
        )
    escalate_alerts.short_description = 'Escalader les alertes'


class EnhancedAdminSite(AdminSite):
    """Site d'administration amélioré avec dashboard unifié"""
    
    site_header = "Administration COKO - Plateforme de Lecture Numérique"
    site_title = "COKO Admin"
    index_title = "Dashboard Unifié - Tous les Services"
    
    def get_urls(self):
        """URLs personnalisées pour l'admin"""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard_overview'),
            path('dashboard/african-metrics/', self.admin_view(self.african_metrics_view), name='african_metrics'),
            path('dashboard/financial-reports/', self.admin_view(self.financial_reports_view), name='financial_reports'),
            path('dashboard/security-overview/', self.admin_view(self.security_overview_view), name='security_overview'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Vue du dashboard principal"""
        from .dashboard_views import DashboardOverviewView
        view = DashboardOverviewView.as_view()
        return view(request)
    
    def african_metrics_view(self, request):
        """Vue des métriques africaines"""
        from .dashboard_views import AfricanMetricsView
        view = AfricanMetricsView.as_view()
        return view(request)
    
    def financial_reports_view(self, request):
        """Vue des rapports financiers"""
        from .financial_reports import FinancialReport
        
        report = FinancialReport()
        context = {
            'title': 'Rapports Financiers',
            'revenue_overview': report.get_revenue_overview(),
            'provider_performance': report.get_provider_performance(),
            'african_insights': report.get_african_payment_insights(),
            'subscription_analytics': report.get_subscription_analytics(),
        }
        
        return TemplateResponse(
            request,
            'admin/financial_reports.html',
            context
        )
    
    def security_overview_view(self, request):
        """Vue d'ensemble de la sécurité"""
        from .audit_trail import AuditLogAnalyzer
        
        analyzer = AuditLogAnalyzer()
        recent_alerts = analyzer.analyze_recent_logs(24)  # 24 heures
        
        # Statistiques de sécurité
        total_logs = AuditLog.objects.count()
        high_risk_logs = AuditLog.objects.filter(risk_level__in=['HIGH', 'CRITICAL']).count()
        open_alerts = SecurityAlert.objects.filter(status='OPEN').count()
        
        context = {
            'title': 'Vue d\'ensemble Sécurité',
            'total_logs': total_logs,
            'high_risk_logs': high_risk_logs,
            'open_alerts': open_alerts,
            'recent_alerts': recent_alerts,
            'security_score': max(100 - (high_risk_logs / max(total_logs, 1) * 100), 0)
        }
        
        return TemplateResponse(
            request,
            'admin/security_overview.html',
            context
        )
    
    def index(self, request, extra_context=None):
        """Page d'accueil personnalisée avec liens vers le dashboard"""
        extra_context = extra_context or {}
        
        # Ajouter des liens vers les nouvelles fonctionnalités
        extra_context.update({
            'dashboard_links': [
                {
                    'title': 'Dashboard Unifié',
                    'url': reverse('admin:dashboard_overview'),
                    'icon': 'fas fa-tachometer-alt',
                    'description': 'Vue d\'ensemble de tous les services'
                },
                {
                    'title': 'Métriques Africaines',
                    'url': reverse('admin:african_metrics'),
                    'icon': 'fas fa-globe-africa',
                    'description': 'Optimisations spécifiques à l\'Afrique'
                },
                {
                    'title': 'Rapports Financiers',
                    'url': reverse('admin:financial_reports'),
                    'icon': 'fas fa-chart-line',
                    'description': 'Revenus et paiements mobiles'
                },
                {
                    'title': 'Sécurité',
                    'url': reverse('admin:security_overview'),
                    'icon': 'fas fa-shield-alt',
                    'description': 'Audit trail et alertes'
                }
            ],
            'quick_stats': self._get_quick_stats(),
            'recent_activity': self._get_recent_activity()
        })
        
        return super().index(request, extra_context)
    
    def _get_quick_stats(self):
        """Statistiques rapides pour la page d'accueil"""
        try:
            total_users = User.objects.count()
            active_sessions = AuditLog.objects.filter(
                action_type='LOGIN',
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).count()
            pending_alerts = SecurityAlert.objects.filter(status='OPEN').count()
            
            return {
                'total_users': total_users,
                'active_sessions_24h': active_sessions,
                'pending_alerts': pending_alerts,
                'system_health': 'Healthy' if pending_alerts < 5 else 'Warning'
            }
        except Exception:
            return {
                'total_users': 0,
                'active_sessions_24h': 0,
                'pending_alerts': 0,
                'system_health': 'Unknown'
            }
    
    def _get_recent_activity(self):
        """Activité récente pour la page d'accueil"""
        try:
            recent_logs = AuditLog.objects.filter(
                risk_level__in=['MEDIUM', 'HIGH', 'CRITICAL']
            ).order_by('-timestamp')[:5]
            
            return [
                {
                    'action': log.get_action_type_display(),
                    'user': log.user.username if log.user else 'Système',
                    'timestamp': log.timestamp,
                    'risk_level': log.risk_level
                }
                for log in recent_logs
            ]
        except Exception:
            return []


# Remplacer le site d'admin par défaut
enhanced_admin_site = EnhancedAdminSite(name='enhanced_admin')

# Réenregistrer tous les modèles existants
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

enhanced_admin_site.register(User, UserAdmin)
enhanced_admin_site.register(Group, GroupAdmin)

# Enregistrer les nouveaux modèles
enhanced_admin_site.register(PaymentTransaction, PaymentTransactionAdmin)
enhanced_admin_site.register(AuditLog, AuditLogAdmin)
enhanced_admin_site.register(SecurityAlert, SecurityAlertAdmin)