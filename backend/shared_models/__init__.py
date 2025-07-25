"""Module shared_models avec système de facturation intégré"""

# Les modèles seront importés de manière paresseuse pour éviter AppRegistryNotReady
# from .admin_integration import PaymentTransactionAdmin
# from .api_client import CokoAPIClient
# from .dashboard import get_dashboard_data
# from .export_apis import AuthorExportAPI, PublisherExportAPI
# from .services import CokoService

# Import des nouveaux modèles de facturation (commentés pour éviter AppRegistryNotReady)
# try:
#     from .billing import (
#         Invoice, InvoiceItem, AuthorRoyalty, 
#         BillingConfiguration, RecurringBilling
#     )
#     
#     # Import des services de facturation
#     from .billing_services import (
#         InvoiceService, RoyaltyService, RecurringBillingService,
#         BillingAutomationService
#     )
#     
#     # Import des APIs de facturation
#     from .billing_apis import (
#         InvoiceViewSet, AuthorRoyaltyViewSet, RecurringBillingViewSet,
#         BillingConfigurationViewSet, BillingDashboardViewSet
#     )
#     
#     # Import des templates et générateurs
#     from .billing_templates import (
#         EmailTemplateService, PDFInvoiceGenerator, BillingReportGenerator
#     )
#     
#     # Import de la configuration
#     from .billing_settings import (
#         BILLING_SETTINGS, get_billing_config, validate_billing_config,
#         init_billing_config
#     )
#     
#     BILLING_AVAILABLE = True
# except ImportError as e:
#     # Les imports de facturation peuvent échouer si les dépendances ne sont pas installées
#     BILLING_AVAILABLE = False
#     print(f"Billing system not available: {e}")
BILLING_AVAILABLE = True

# Version du module
__version__ = '2.0.0'

# Métadonnées du système de facturation
BILLING_SYSTEM_INFO = {
    'name': 'Coko Billing System',
    'version': '1.0.0',
    'description': 'Système de facturation complet, automatisé et paramètrable pour Coko',
    'features': [
        'Facturation automatisée',
        'Gestion des royalties d\'auteurs',
        'Facturation récurrente',
        'Intégration multi-fournisseurs de paiement',
        'Génération de PDF',
        'Notifications par email',
        'Rapports et analytics',
        'Configuration flexible',
        'Webhooks de paiement',
        'Interface d\'administration',
        'APIs REST complètes',
        'Tâches automatisées avec Celery'
    ],
    'supported_currencies': ['EUR', 'USD', 'XOF', 'XAF'],
    'supported_payment_providers': ['Stripe', 'PayPal', 'Orange Money', 'MTN Mobile Money'],
    'supported_languages': ['fr', 'en'],
}

# Export des classes principales (simplifié pour éviter les erreurs d'import)
__all__ = [
    'BILLING_AVAILABLE', 
    'BILLING_SYSTEM_INFO',
    '__version__'
]