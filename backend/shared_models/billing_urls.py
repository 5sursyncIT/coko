"""URLs pour les APIs de facturation Coko"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .billing_apis import (
    InvoiceViewSet, AuthorRoyaltyViewSet, RecurringBillingViewSet,
    BillingConfigurationViewSet, BillingDashboardViewSet
)

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'royalties', AuthorRoyaltyViewSet, basename='royalty')
router.register(r'recurring-billing', RecurringBillingViewSet, basename='recurring-billing')
router.register(r'configurations', BillingConfigurationViewSet, basename='billing-config')
router.register(r'dashboard', BillingDashboardViewSet, basename='billing-dashboard')

# URLs de l'application billing
app_name = 'billing'

urlpatterns = [
    # APIs REST
    path('api/v1/', include(router.urls)),
    
    # URLs spécifiques pour les actions personnalisées
    path('api/v1/invoices/<uuid:invoice_id>/pdf/', 
         InvoiceViewSet.as_view({'get': 'download_pdf'}), 
         name='invoice-pdf'),
    
    path('api/v1/invoices/<uuid:invoice_id>/send/', 
         InvoiceViewSet.as_view({'post': 'send_email'}), 
         name='invoice-send'),
    
    path('api/v1/invoices/<uuid:invoice_id>/mark-paid/', 
         InvoiceViewSet.as_view({'post': 'mark_as_paid'}), 
         name='invoice-mark-paid'),
    
    path('api/v1/royalties/calculate/', 
         AuthorRoyaltyViewSet.as_view({'post': 'calculate_royalties'}), 
         name='calculate-royalties'),
    
    path('api/v1/royalties/generate-invoices/', 
         AuthorRoyaltyViewSet.as_view({'post': 'generate_invoices'}), 
         name='generate-royalty-invoices'),
    
    path('api/v1/royalties/<uuid:royalty_id>/pdf/', 
         AuthorRoyaltyViewSet.as_view({'get': 'download_report_pdf'}), 
         name='royalty-pdf'),
    
    path('api/v1/recurring-billing/process-due/', 
         RecurringBillingViewSet.as_view({'post': 'process_due_billings'}), 
         name='process-due-billings'),
    
    path('api/v1/dashboard/overview/', 
         BillingDashboardViewSet.as_view({'get': 'overview'}), 
         name='billing-overview'),
    
    path('api/v1/dashboard/revenue-chart/', 
         BillingDashboardViewSet.as_view({'get': 'revenue_chart'}), 
         name='revenue-chart'),
    
    path('api/v1/dashboard/export-report/', 
         BillingDashboardViewSet.as_view({'get': 'export_report'}), 
         name='export-billing-report'),
]

# URLs pour les webhooks de paiement (optionnel)
webhook_patterns = [
    path('webhooks/payment-success/', 
         'shared_models.billing_webhooks.payment_success_webhook', 
         name='payment-success-webhook'),
    
    path('webhooks/payment-failed/', 
         'shared_models.billing_webhooks.payment_failed_webhook', 
         name='payment-failed-webhook'),
    
    path('webhooks/subscription-updated/', 
         'shared_models.billing_webhooks.subscription_updated_webhook', 
         name='subscription-updated-webhook'),
]

# Ajouter les webhooks aux URLs principales
urlpatterns += webhook_patterns