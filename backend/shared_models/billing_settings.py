"""Configuration pour le système de facturation Coko"""

from django.conf import settings
from datetime import timedelta
import os

# Configuration de base pour la facturation
BILLING_SETTINGS = {
    # Informations de l'entreprise
    'COMPANY_NAME': getattr(settings, 'COMPANY_NAME', 'Coko'),
    'COMPANY_EMAIL': getattr(settings, 'COMPANY_EMAIL', 'contact@coko.com'),
    'COMPANY_PHONE': getattr(settings, 'COMPANY_PHONE', '+33 1 23 45 67 89'),
    'COMPANY_ADDRESS': getattr(settings, 'COMPANY_ADDRESS', '123 Rue de la Paix, 75001 Paris, France'),
    'COMPANY_WEBSITE': getattr(settings, 'COMPANY_WEBSITE', 'https://coko.com'),
    'COMPANY_LOGO_URL': getattr(settings, 'COMPANY_LOGO_URL', '/static/images/logo.png'),
    
    # Configuration des factures
    'INVOICE_NUMBER_PREFIX': getattr(settings, 'INVOICE_NUMBER_PREFIX', 'COKO'),
    'INVOICE_DUE_DAYS': getattr(settings, 'INVOICE_DUE_DAYS', 30),
    'INVOICE_OVERDUE_GRACE_DAYS': getattr(settings, 'INVOICE_OVERDUE_GRACE_DAYS', 7),
    'DEFAULT_CURRENCY': getattr(settings, 'DEFAULT_CURRENCY', 'EUR'),
    'SUPPORTED_CURRENCIES': getattr(settings, 'SUPPORTED_CURRENCIES', ['EUR', 'USD', 'XOF', 'XAF']),
    
    # Configuration des royalties
    'DEFAULT_ROYALTY_RATES': {
        'sale': 0.70,  # 70% pour les ventes directes
        'subscription_read': 0.50,  # 50% pour les lectures d'abonnement
        'tip': 0.95,  # 95% pour les pourboires
        'premium_access': 0.60,  # 60% pour l'accès premium
    },
    
    # Configuration des taxes par pays
    'TAX_RATES': {
        'FR': 0.20,  # TVA France 20%
        'DE': 0.19,  # TVA Allemagne 19%
        'ES': 0.21,  # TVA Espagne 21%
        'IT': 0.22,  # TVA Italie 22%
        'SN': 0.18,  # TVA Sénégal 18%
        'CI': 0.18,  # TVA Côte d'Ivoire 18%
        'MA': 0.20,  # TVA Maroc 20%
        'default': 0.00,  # Pas de taxe par défaut
    },
    
    # Configuration des abonnements
    'SUBSCRIPTION_PRICES': {
        'premium': {
            'monthly': {'EUR': 9.99, 'USD': 10.99, 'XOF': 6500, 'XAF': 6500},
            'quarterly': {'EUR': 27.99, 'USD': 30.99, 'XOF': 18000, 'XAF': 18000},
            'yearly': {'EUR': 99.99, 'USD': 109.99, 'XOF': 65000, 'XAF': 65000},
        },
        'creator': {
            'monthly': {'EUR': 19.99, 'USD': 21.99, 'XOF': 13000, 'XAF': 13000},
            'quarterly': {'EUR': 54.99, 'USD': 59.99, 'XOF': 35000, 'XAF': 35000},
            'yearly': {'EUR': 199.99, 'USD': 219.99, 'XOF': 130000, 'XAF': 130000},
        },
        'institutional': {
            'monthly': {'EUR': 49.99, 'USD': 54.99, 'XOF': 32500, 'XAF': 32500},
            'quarterly': {'EUR': 139.99, 'USD': 149.99, 'XOF': 90000, 'XAF': 90000},
            'yearly': {'EUR': 499.99, 'USD': 549.99, 'XOF': 325000, 'XAF': 325000},
        },
    },
    
    # Configuration des fournisseurs de paiement
    'PAYMENT_PROVIDERS': {
        'stripe': {
            'enabled': getattr(settings, 'STRIPE_ENABLED', True),
            'public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
            'secret_key': getattr(settings, 'STRIPE_SECRET_KEY', ''),
            'webhook_secret': getattr(settings, 'STRIPE_WEBHOOK_SECRET', ''),
            'supported_currencies': ['EUR', 'USD'],
            'supported_countries': ['FR', 'DE', 'ES', 'IT', 'US', 'CA'],
        },
        'paypal': {
            'enabled': getattr(settings, 'PAYPAL_ENABLED', True),
            'client_id': getattr(settings, 'PAYPAL_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'PAYPAL_CLIENT_SECRET', ''),
            'webhook_secret': getattr(settings, 'PAYPAL_WEBHOOK_SECRET', ''),
            'sandbox': getattr(settings, 'PAYPAL_SANDBOX', True),
            'supported_currencies': ['EUR', 'USD'],
            'supported_countries': ['FR', 'DE', 'ES', 'IT', 'US', 'CA'],
        },
        'orange_money': {
            'enabled': getattr(settings, 'ORANGE_MONEY_ENABLED', True),
            'merchant_key': getattr(settings, 'ORANGE_MONEY_MERCHANT_KEY', ''),
            'api_key': getattr(settings, 'ORANGE_MONEY_API_KEY', ''),
            'webhook_secret': getattr(settings, 'ORANGE_MONEY_WEBHOOK_SECRET', ''),
            'sandbox': getattr(settings, 'ORANGE_MONEY_SANDBOX', True),
            'supported_currencies': ['XOF'],
            'supported_countries': ['SN', 'CI', 'ML', 'BF', 'NE'],
        },
        'mtn_mobile_money': {
            'enabled': getattr(settings, 'MTN_MOBILE_MONEY_ENABLED', False),
            'api_key': getattr(settings, 'MTN_MOBILE_MONEY_API_KEY', ''),
            'api_secret': getattr(settings, 'MTN_MOBILE_MONEY_API_SECRET', ''),
            'sandbox': getattr(settings, 'MTN_MOBILE_MONEY_SANDBOX', True),
            'supported_currencies': ['XAF', 'XOF'],
            'supported_countries': ['CM', 'GH', 'UG', 'ZM'],
        },
    },
    
    # Configuration des emails
    'EMAIL_SETTINGS': {
        'send_invoice_emails': getattr(settings, 'BILLING_SEND_INVOICE_EMAILS', True),
        'send_royalty_notifications': getattr(settings, 'BILLING_SEND_ROYALTY_NOTIFICATIONS', True),
        'send_overdue_notifications': getattr(settings, 'BILLING_SEND_OVERDUE_NOTIFICATIONS', True),
        'overdue_notification_days': [7, 14, 30],  # Jours après échéance pour envoyer des rappels
        'from_email': getattr(settings, 'BILLING_FROM_EMAIL', 'facturation@coko.com'),
        'reply_to_email': getattr(settings, 'BILLING_REPLY_TO_EMAIL', 'support@coko.com'),
    },
    
    # Configuration des rapports
    'REPORTS_SETTINGS': {
        'auto_generate_monthly_reports': getattr(settings, 'BILLING_AUTO_GENERATE_MONTHLY_REPORTS', True),
        'report_recipients': getattr(settings, 'BILLING_REPORT_RECIPIENTS', ['admin@coko.com']),
        'keep_reports_days': getattr(settings, 'BILLING_KEEP_REPORTS_DAYS', 365),
    },
    
    # Configuration de l'automatisation
    'AUTOMATION_SETTINGS': {
        'auto_process_recurring_billing': getattr(settings, 'BILLING_AUTO_PROCESS_RECURRING', True),
        'auto_calculate_royalties': getattr(settings, 'BILLING_AUTO_CALCULATE_ROYALTIES', True),
        'auto_mark_overdue': getattr(settings, 'BILLING_AUTO_MARK_OVERDUE', True),
        'auto_send_notifications': getattr(settings, 'BILLING_AUTO_SEND_NOTIFICATIONS', True),
        'cleanup_old_invoices_days': getattr(settings, 'BILLING_CLEANUP_OLD_INVOICES_DAYS', 2555),  # 7 ans
    },
}

# Configuration Celery pour les tâches de facturation
CELERY_BILLING_TASKS = {
    # Tâches quotidiennes
    'billing-daily-tasks': {
        'task': 'shared_models.billing_tasks.process_daily_billing',
        'schedule': timedelta(hours=24),  # Tous les jours à minuit
        'options': {'queue': 'billing'},
    },
    
    # Tâches mensuelles
    'billing-monthly-royalties': {
        'task': 'shared_models.billing_tasks.calculate_monthly_royalties',
        'schedule': timedelta(days=30),  # Tous les mois
        'options': {'queue': 'billing'},
    },
    
    # Traitement des facturations récurrentes (toutes les heures)
    'billing-recurring-process': {
        'task': 'shared_models.billing_tasks.process_recurring_billing',
        'schedule': timedelta(hours=1),
        'options': {'queue': 'billing'},
    },
    
    # Nettoyage des anciennes factures (une fois par semaine)
    'billing-cleanup': {
        'task': 'shared_models.billing_tasks.cleanup_old_invoices',
        'schedule': timedelta(days=7),
        'options': {'queue': 'billing'},
    },
    
    # Génération des rapports mensuels
    'billing-monthly-reports': {
        'task': 'shared_models.billing_tasks.generate_monthly_report',
        'schedule': timedelta(days=30),
        'options': {'queue': 'billing'},
    },
}

# Configuration des queues Celery
CELERY_BILLING_QUEUES = {
    'billing': {
        'exchange': 'billing',
        'exchange_type': 'direct',
        'routing_key': 'billing',
    },
    'billing_emails': {
        'exchange': 'billing_emails',
        'exchange_type': 'direct',
        'routing_key': 'billing_emails',
    },
    'billing_reports': {
        'exchange': 'billing_reports',
        'exchange_type': 'direct',
        'routing_key': 'billing_reports',
    },
}

# Configuration des routes Celery
CELERY_BILLING_ROUTES = {
    'shared_models.billing_tasks.send_invoice_email': {'queue': 'billing_emails'},
    'shared_models.billing_tasks.send_overdue_notification': {'queue': 'billing_emails'},
    'shared_models.billing_tasks.send_royalty_notification': {'queue': 'billing_emails'},
    'shared_models.billing_tasks.notify_authors_royalties': {'queue': 'billing_emails'},
    'shared_models.billing_tasks.generate_monthly_report': {'queue': 'billing_reports'},
    'shared_models.billing_tasks.process_daily_billing': {'queue': 'billing'},
    'shared_models.billing_tasks.calculate_monthly_royalties': {'queue': 'billing'},
    'shared_models.billing_tasks.process_recurring_billing': {'queue': 'billing'},
    'shared_models.billing_tasks.calculate_author_royalty': {'queue': 'billing'},
    'shared_models.billing_tasks.cleanup_old_invoices': {'queue': 'billing'},
    'shared_models.billing_tasks.sync_payment_transactions': {'queue': 'billing'},
}

# Configuration des permissions
BILLING_PERMISSIONS = {
    'view_invoice': 'shared_models.view_invoice',
    'add_invoice': 'shared_models.add_invoice',
    'change_invoice': 'shared_models.change_invoice',
    'delete_invoice': 'shared_models.delete_invoice',
    
    'view_authorroyalty': 'shared_models.view_authorroyalty',
    'add_authorroyalty': 'shared_models.add_authorroyalty',
    'change_authorroyalty': 'shared_models.change_authorroyalty',
    'delete_authorroyalty': 'shared_models.delete_authorroyalty',
    
    'view_recurringbilling': 'shared_models.view_recurringbilling',
    'add_recurringbilling': 'shared_models.add_recurringbilling',
    'change_recurringbilling': 'shared_models.change_recurringbilling',
    'delete_recurringbilling': 'shared_models.delete_recurringbilling',
    
    'view_billingconfiguration': 'shared_models.view_billingconfiguration',
    'add_billingconfiguration': 'shared_models.add_billingconfiguration',
    'change_billingconfiguration': 'shared_models.change_billingconfiguration',
    'delete_billingconfiguration': 'shared_models.delete_billingconfiguration',
    
    # Permissions spéciales
    'process_billing': 'shared_models.process_billing',
    'view_billing_reports': 'shared_models.view_billing_reports',
    'export_billing_data': 'shared_models.export_billing_data',
}

# Configuration de logging spécifique à la facturation
BILLING_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'billing': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'billing_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(getattr(settings, 'LOG_DIR', '/tmp'), 'billing.log'),
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'billing',
        },
        'billing_error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(getattr(settings, 'LOG_DIR', '/tmp'), 'billing_errors.log'),
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'billing',
        },
    },
    'loggers': {
        'shared_models.billing': {
            'handlers': ['billing_file', 'billing_error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'shared_models.billing_services': {
            'handlers': ['billing_file', 'billing_error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'shared_models.billing_tasks': {
            'handlers': ['billing_file', 'billing_error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'shared_models.billing_webhooks': {
            'handlers': ['billing_file', 'billing_error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Configuration de cache pour la facturation
BILLING_CACHE_SETTINGS = {
    'default_timeout': 300,  # 5 minutes
    'key_prefix': 'billing:',
    'version': 1,
    
    # Timeouts spécifiques
    'invoice_timeout': 600,  # 10 minutes
    'royalty_timeout': 1800,  # 30 minutes
    'dashboard_timeout': 300,  # 5 minutes
    'reports_timeout': 3600,  # 1 heure
}

# Configuration de sécurité
BILLING_SECURITY_SETTINGS = {
    'require_https': getattr(settings, 'BILLING_REQUIRE_HTTPS', True),
    'webhook_ip_whitelist': getattr(settings, 'BILLING_WEBHOOK_IP_WHITELIST', []),
    'max_invoice_amount': getattr(settings, 'BILLING_MAX_INVOICE_AMOUNT', 10000),  # Montant maximum par facture
    'rate_limit_per_user': getattr(settings, 'BILLING_RATE_LIMIT_PER_USER', '100/hour'),
    'encrypt_sensitive_data': getattr(settings, 'BILLING_ENCRYPT_SENSITIVE_DATA', True),
}

# Fonction pour obtenir la configuration complète
def get_billing_config():
    """Retourne la configuration complète du système de facturation"""
    return {
        'billing': BILLING_SETTINGS,
        'celery_tasks': CELERY_BILLING_TASKS,
        'celery_queues': CELERY_BILLING_QUEUES,
        'celery_routes': CELERY_BILLING_ROUTES,
        'permissions': BILLING_PERMISSIONS,
        'logging': BILLING_LOGGING,
        'cache': BILLING_CACHE_SETTINGS,
        'security': BILLING_SECURITY_SETTINGS,
    }

# Fonction pour valider la configuration
def validate_billing_config():
    """Valide la configuration du système de facturation"""
    errors = []
    
    # Vérifier les clés API des fournisseurs de paiement
    for provider, config in BILLING_SETTINGS['PAYMENT_PROVIDERS'].items():
        if config['enabled']:
            if provider == 'stripe':
                if not config.get('secret_key'):
                    errors.append(f"Clé secrète Stripe manquante")
                if not config.get('webhook_secret'):
                    errors.append(f"Secret webhook Stripe manquant")
            elif provider == 'paypal':
                if not config.get('client_secret'):
                    errors.append(f"Secret client PayPal manquant")
            elif provider == 'orange_money':
                if not config.get('api_key'):
                    errors.append(f"Clé API Orange Money manquante")
    
    # Vérifier la configuration email
    if not BILLING_SETTINGS['EMAIL_SETTINGS']['from_email']:
        errors.append("Email d'expéditeur de facturation manquant")
    
    # Vérifier les devises supportées
    if not BILLING_SETTINGS['SUPPORTED_CURRENCIES']:
        errors.append("Aucune devise supportée configurée")
    
    return errors

# Initialisation de la configuration
def init_billing_config():
    """Initialise la configuration du système de facturation"""
    errors = validate_billing_config()
    if errors:
        raise ValueError(f"Erreurs de configuration de facturation: {', '.join(errors)}")
    
    # Configuration du logging
    import logging.config
    logging.config.dictConfig(BILLING_LOGGING)
    
    return True