"""Intégration du système de facturation dans Django"""

from django.conf import settings
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


class BillingConfig(AppConfig):
    """Configuration de l'application de facturation"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shared_models'
    verbose_name = 'Système de Facturation Coko'
    
    def ready(self):
        """Initialisation de l'application"""
        # Import des signaux
        from . import billing_signals
        
        # Vérifier la configuration
        self.check_billing_configuration()
        
        # Enregistrer les tâches Celery si disponible
        self.register_celery_tasks()
        
        logger.info('Système de facturation Coko initialisé')
    
    def check_billing_configuration(self):
        """Vérifie la configuration du système de facturation"""
        try:
            from .billing_settings import validate_billing_config
            
            errors = validate_billing_config()
            if errors:
                logger.warning(f'Configuration de facturation incomplète: {", ".join(errors)}')
            else:
                logger.info('Configuration de facturation validée')
                
        except Exception as e:
            logger.error(f'Erreur lors de la validation de la configuration: {str(e)}')
    
    def register_celery_tasks(self):
        """Enregistre les tâches Celery"""
        try:
            from celery import current_app
            from .billing_tasks import (
                process_daily_billing, calculate_monthly_royalties,
                process_recurring_billing, send_invoice_email,
                send_overdue_notifications
            )
            
            # Enregistrer les tâches périodiques
            current_app.conf.beat_schedule.update({
                'daily-billing-processing': {
                    'task': 'shared_models.billing_tasks.process_daily_billing',
                    'schedule': 3600.0,  # Toutes les heures
                },
                'monthly-royalty-calculation': {
                    'task': 'shared_models.billing_tasks.calculate_monthly_royalties',
                    'schedule': 86400.0,  # Tous les jours
                },
                'recurring-billing-processing': {
                    'task': 'shared_models.billing_tasks.process_recurring_billing',
                    'schedule': 3600.0,  # Toutes les heures
                },
                'overdue-notifications': {
                    'task': 'shared_models.billing_tasks.send_overdue_notifications',
                    'schedule': 86400.0,  # Tous les jours
                },
            })
            
            logger.info('Tâches Celery de facturation enregistrées')
            
        except ImportError:
            logger.warning('Celery non disponible - tâches automatisées désactivées')
        except Exception as e:
            logger.error(f'Erreur lors de l\'enregistrement des tâches Celery: {str(e)}')


@receiver(post_migrate)
def create_default_billing_configuration(sender, **kwargs):
    """Crée la configuration par défaut après les migrations"""
    if sender.name == 'shared_models':
        try:
            from .billing import BillingConfiguration
            from .billing_settings import init_billing_config
            
            # Initialiser la configuration par défaut
            init_billing_config()
            
            # Créer les configurations essentielles
            default_configs = [
                {
                    'config_type': 'tax_rate',
                    'config_key': 'default_rate',
                    'config_value': {'rate': 0.20},
                    'description': 'Taux de taxe par défaut (20%)'
                },
                {
                    'config_type': 'royalty_rate',
                    'config_key': 'sale_rate',
                    'config_value': {'rate': 0.70},
                    'description': 'Taux de royalty pour les ventes (70%)'
                },
                {
                    'config_type': 'royalty_rate',
                    'config_key': 'subscription_rate',
                    'config_value': {'rate': 0.50},
                    'description': 'Taux de royalty pour les lectures d\'abonnement (50%)'
                },
                {
                    'config_type': 'payment_terms',
                    'config_key': 'default_due_days',
                    'config_value': {'days': 30},
                    'description': 'Délai de paiement par défaut (30 jours)'
                },
                {
                    'config_type': 'currency',
                    'config_key': 'default_currency',
                    'config_value': {'currency': 'EUR'},
                    'description': 'Devise par défaut'
                }
            ]
            
            created_count = 0
            for config_data in default_configs:
                config, created = BillingConfiguration.objects.get_or_create(
                    config_type=config_data['config_type'],
                    config_key=config_data['config_key'],
                    defaults={
                        'config_value': config_data['config_value'],
                        'description': config_data['description'],
                        'is_active': True
                    }
                )
                if created:
                    created_count += 1
            
            if created_count > 0:
                logger.info(f'Configuration de facturation initialisée: {created_count} configurations créées')
            
        except Exception as e:
            logger.error(f'Erreur lors de la création de la configuration par défaut: {str(e)}')


def get_billing_settings():
    """Retourne les paramètres de facturation pour Django settings"""
    return {
        # Configuration de base
        'BILLING_ENABLED': True,
        'BILLING_AUTO_INVOICE': True,
        'BILLING_AUTO_ROYALTY': True,
        'BILLING_AUTO_RECURRING': True,
        
        # Devises supportées
        'BILLING_CURRENCIES': ['EUR', 'USD', 'XOF', 'XAF'],
        'BILLING_DEFAULT_CURRENCY': 'EUR',
        
        # Fournisseurs de paiement
        'BILLING_PAYMENT_PROVIDERS': {
            'stripe': {
                'enabled': True,
                'webhook_secret': getattr(settings, 'STRIPE_WEBHOOK_SECRET', ''),
                'public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
                'secret_key': getattr(settings, 'STRIPE_SECRET_KEY', ''),
            },
            'paypal': {
                'enabled': True,
                'webhook_id': getattr(settings, 'PAYPAL_WEBHOOK_ID', ''),
                'client_id': getattr(settings, 'PAYPAL_CLIENT_ID', ''),
                'client_secret': getattr(settings, 'PAYPAL_CLIENT_SECRET', ''),
                'sandbox': getattr(settings, 'PAYPAL_SANDBOX', True),
            },
            'orange_money': {
                'enabled': True,
                'api_key': getattr(settings, 'ORANGE_MONEY_API_KEY', ''),
                'merchant_id': getattr(settings, 'ORANGE_MONEY_MERCHANT_ID', ''),
                'webhook_secret': getattr(settings, 'ORANGE_MONEY_WEBHOOK_SECRET', ''),
            },
            'mtn_mobile_money': {
                'enabled': True,
                'api_key': getattr(settings, 'MTN_MM_API_KEY', ''),
                'user_id': getattr(settings, 'MTN_MM_USER_ID', ''),
                'subscription_key': getattr(settings, 'MTN_MM_SUBSCRIPTION_KEY', ''),
            }
        },
        
        # Configuration des emails
        'BILLING_EMAIL_ENABLED': True,
        'BILLING_EMAIL_FROM': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@coko.com'),
        'BILLING_EMAIL_TEMPLATES': {
            'invoice': 'billing/emails/invoice.html',
            'royalty': 'billing/emails/royalty.html',
            'overdue': 'billing/emails/overdue.html',
        },
        
        # Configuration PDF
        'BILLING_PDF_ENABLED': True,
        'BILLING_PDF_LOGO': getattr(settings, 'BILLING_PDF_LOGO', ''),
        'BILLING_COMPANY_INFO': {
            'name': getattr(settings, 'COMPANY_NAME', 'Coko'),
            'address': getattr(settings, 'COMPANY_ADDRESS', ''),
            'phone': getattr(settings, 'COMPANY_PHONE', ''),
            'email': getattr(settings, 'COMPANY_EMAIL', ''),
            'website': getattr(settings, 'COMPANY_WEBSITE', ''),
            'tax_number': getattr(settings, 'COMPANY_TAX_NUMBER', ''),
        },
        
        # Configuration des tâches
        'BILLING_CELERY_ENABLED': True,
        'BILLING_TASK_QUEUE': 'billing',
        'BILLING_TASK_ROUTING': {
            'shared_models.billing_tasks.*': {'queue': 'billing'},
        },
        
        # Configuration de sécurité
        'BILLING_WEBHOOK_TIMEOUT': 30,
        'BILLING_API_RATE_LIMIT': '100/hour',
        'BILLING_REQUIRE_AUTHENTICATION': True,
        
        # Configuration des rapports
        'BILLING_REPORTS_ENABLED': True,
        'BILLING_REPORTS_RETENTION_DAYS': 365,
        'BILLING_CLEANUP_ENABLED': True,
        'BILLING_CLEANUP_RETENTION_DAYS': 2555,  # 7 ans
        
        # Configuration des logs
        'BILLING_LOGGING': {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'billing_file': {
                    'level': 'INFO',
                    'class': 'logging.FileHandler',
                    'filename': 'logs/billing.log',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'shared_models.billing': {
                    'handlers': ['billing_file'],
                    'level': 'INFO',
                    'propagate': True,
                },
            },
        },
    }


def update_django_settings():
    """Met à jour les settings Django avec la configuration de facturation"""
    billing_settings = get_billing_settings()
    
    # Ajouter les apps
    if hasattr(settings, 'INSTALLED_APPS'):
        if 'shared_models' not in settings.INSTALLED_APPS:
            settings.INSTALLED_APPS.append('shared_models')
    
    # Ajouter les URLs
    billing_urls = {
        'BILLING_API_PREFIX': 'api/billing/',
        'BILLING_WEBHOOK_PREFIX': 'webhooks/billing/',
    }
    
    # Ajouter la configuration Celery
    if hasattr(settings, 'CELERY_BEAT_SCHEDULE'):
        settings.CELERY_BEAT_SCHEDULE.update({
            'billing-daily-processing': {
                'task': 'shared_models.billing_tasks.process_daily_billing',
                'schedule': 3600.0,  # Toutes les heures
            },
            'billing-monthly-royalties': {
                'task': 'shared_models.billing_tasks.calculate_monthly_royalties',
                'schedule': 86400.0,  # Tous les jours
            },
            'billing-recurring-processing': {
                'task': 'shared_models.billing_tasks.process_recurring_billing',
                'schedule': 3600.0,  # Toutes les heures
            },
            'billing-overdue-notifications': {
                'task': 'shared_models.billing_tasks.send_overdue_notifications',
                'schedule': 86400.0,  # Tous les jours
            },
        })
    
    # Ajouter les queues Celery
    if hasattr(settings, 'CELERY_TASK_ROUTES'):
        settings.CELERY_TASK_ROUTES.update({
            'shared_models.billing_tasks.*': {'queue': 'billing'},
        })
    
    # Ajouter la configuration de logging
    if hasattr(settings, 'LOGGING'):
        if 'loggers' not in settings.LOGGING:
            settings.LOGGING['loggers'] = {}
        
        settings.LOGGING['loggers']['shared_models.billing'] = {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    
    # Ajouter les paramètres de facturation
    for key, value in billing_settings.items():
        setattr(settings, key, value)
    
    for key, value in billing_urls.items():
        setattr(settings, key, value)
    
    logger.info('Configuration Django mise à jour avec les paramètres de facturation')


# Middleware pour la facturation
class BillingMiddleware:
    """Middleware pour le système de facturation"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Ajouter des informations de facturation au contexte de la requête
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                from .billing import Invoice, AuthorRoyalty
                
                # Ajouter les statistiques de facturation de l'utilisateur
                request.billing_context = {
                    'pending_invoices': Invoice.objects.filter(
                        user=request.user,
                        status__in=['pending', 'sent']
                    ).count(),
                    'pending_royalties': AuthorRoyalty.objects.filter(
                        author=request.user,
                        status='pending'
                    ).count() if hasattr(request.user, 'is_author') and request.user.is_author else 0,
                }
            except Exception:
                request.billing_context = {}
        
        response = self.get_response(request)
        return response


# Context processor pour les templates
def billing_context(request):
    """Context processor pour ajouter les informations de facturation aux templates"""
    context = {
        'billing_enabled': getattr(settings, 'BILLING_ENABLED', False),
        'billing_currencies': getattr(settings, 'BILLING_CURRENCIES', ['EUR']),
        'billing_company': getattr(settings, 'BILLING_COMPANY_INFO', {}),
    }
    
    if hasattr(request, 'billing_context'):
        context.update(request.billing_context)
    
    return context


# Fonctions utilitaires pour l'intégration
def check_billing_dependencies():
    """Vérifie les dépendances du système de facturation"""
    dependencies = {
        'celery': False,
        'reportlab': False,
        'stripe': False,
        'paypal': False,
    }
    
    try:
        import celery
        dependencies['celery'] = True
    except ImportError:
        pass
    
    try:
        import reportlab
        dependencies['reportlab'] = True
    except ImportError:
        pass
    
    try:
        import stripe
        dependencies['stripe'] = True
    except ImportError:
        pass
    
    try:
        import paypalrestsdk
        dependencies['paypal'] = True
    except ImportError:
        pass
    
    return dependencies


def get_billing_health_status():
    """Retourne le statut de santé du système de facturation"""
    try:
        from .billing_settings import validate_billing_config
        from .billing import BillingConfiguration
        
        # Vérifier la configuration
        config_errors = validate_billing_config()
        
        # Vérifier les dépendances
        dependencies = check_billing_dependencies()
        
        # Vérifier la base de données
        try:
            config_count = BillingConfiguration.objects.count()
            db_status = 'ok'
        except Exception as e:
            config_count = 0
            db_status = f'error: {str(e)}'
        
        return {
            'status': 'healthy' if not config_errors and db_status == 'ok' else 'degraded',
            'configuration': {
                'errors': config_errors,
                'configs_count': config_count
            },
            'dependencies': dependencies,
            'database': db_status,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }