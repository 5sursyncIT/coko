# Système de Facturation Coko

## Vue d'ensemble

Le système de facturation Coko est une solution complète, automatisée et paramètrable pour gérer :
- La facturation des clients
- Les royalties des auteurs
- Les abonnements récurrents
- Les paiements multi-fournisseurs
- La génération de rapports et d'analyses

## Fonctionnalités principales

### 🧾 Facturation automatisée
- Génération automatique de factures
- Calcul automatique des taxes et totaux
- Numérotation séquentielle des factures
- Gestion des échéances et relances
- Support multi-devises (EUR, USD, XOF, XAF)

### 👨‍💼 Gestion des royalties d'auteurs
- Calcul automatique des royalties basé sur les ventes et lectures
- Taux configurables par type de transaction
- Seuils de paiement personnalisables
- Rapports détaillés par auteur et période

### 🔄 Facturation récurrente
- Abonnements mensuels, trimestriels, annuels
- Gestion des échecs de paiement et reprises
- Pause et annulation d'abonnements
- Notifications automatiques

### 💳 Intégration multi-fournisseurs
- Stripe (cartes bancaires internationales)
- PayPal (portefeuille numérique)
- Orange Money (mobile money Afrique)
- MTN Mobile Money (mobile money Afrique)
- Webhooks pour synchronisation temps réel

### 📊 Rapports et analyses
- Tableaux de bord en temps réel
- Rapports financiers détaillés
- Analyses de performance par fournisseur
- Métriques d'abonnement (MRR, ARPU, Churn)

### ⚙️ Configuration flexible
- Taux de taxes personnalisables
- Termes de paiement configurables
- Templates d'emails personnalisables
- Seuils et limites ajustables

## Architecture

### Modèles de données

```
Invoice (Facture)
├── InvoiceItem (Articles de facture)
├── PaymentTransaction (Transaction de paiement)
└── User (Utilisateur)

AuthorRoyalty (Royalty d'auteur)
├── Author (Auteur)
└── PaymentTransaction (Transactions sources)

RecurringBilling (Facturation récurrente)
├── User (Utilisateur)
└── Invoice (Factures générées)

BillingConfiguration (Configuration)
├── Type de configuration
├── Clé de configuration
└── Valeurs JSON
```

### Services

- **InvoiceService** : Gestion des factures
- **RoyaltyService** : Calcul des royalties
- **RecurringBillingService** : Abonnements récurrents
- **BillingAutomationService** : Automatisation
- **EmailTemplateService** : Notifications email
- **PDFInvoiceGenerator** : Génération PDF

### APIs REST

- `/api/billing/invoices/` : Gestion des factures
- `/api/billing/royalties/` : Royalties d'auteurs
- `/api/billing/recurring/` : Abonnements récurrents
- `/api/billing/config/` : Configuration
- `/api/billing/dashboard/` : Tableau de bord

### Tâches automatisées (Celery)

- Traitement quotidien des factures
- Calcul mensuel des royalties
- Traitement des abonnements récurrents
- Envoi de notifications
- Nettoyage des anciennes données

## Installation et configuration

### 1. Dépendances

```bash
pip install celery redis reportlab stripe paypalrestsdk
```

### 2. Configuration Django

Ajouter à `settings.py` :

```python
INSTALLED_APPS = [
    # ... autres apps
    'shared_models',
]

# Configuration de facturation
BILLING_ENABLED = True
BILLING_DEFAULT_CURRENCY = 'EUR'
BILLING_COMPANY_INFO = {
    'name': 'Votre Entreprise',
    'address': 'Adresse complète',
    'phone': '+33 1 23 45 67 89',
    'email': 'contact@votreentreprise.com',
    'website': 'https://votreentreprise.com',
    'tax_number': 'FR12345678901',
}

# Fournisseurs de paiement
STRIPE_PUBLIC_KEY = 'pk_test_...'
STRIPE_SECRET_KEY = 'sk_test_...'
STRIPE_WEBHOOK_SECRET = 'whsec_...'

PAYPAL_CLIENT_ID = 'your_paypal_client_id'
PAYPAL_CLIENT_SECRET = 'your_paypal_client_secret'
PAYPAL_SANDBOX = True  # False en production

ORANGE_MONEY_API_KEY = 'your_orange_money_api_key'
ORANGE_MONEY_MERCHANT_ID = 'your_merchant_id'

MTN_MM_API_KEY = 'your_mtn_api_key'
MTN_MM_USER_ID = 'your_mtn_user_id'

# Configuration Celery
CELERY_BEAT_SCHEDULE = {
    'billing-daily-processing': {
        'task': 'shared_models.billing_tasks.process_daily_billing',
        'schedule': 3600.0,  # Toutes les heures
    },
    'billing-monthly-royalties': {
        'task': 'shared_models.billing_tasks.calculate_monthly_royalties',
        'schedule': 86400.0,  # Tous les jours
    },
}
```

### 3. URLs

Ajouter à `urls.py` :

```python
from django.urls import path, include

urlpatterns = [
    # ... autres URLs
    path('api/billing/', include('shared_models.billing_urls')),
    path('webhooks/billing/', include('shared_models.billing_webhooks')),
]
```

### 4. Migrations

```bash
python manage.py makemigrations shared_models
python manage.py migrate
```

### 5. Initialisation

```bash
python manage.py manage_billing init
```

## Utilisation

### Commandes de gestion

```bash
# Statut du système
python manage.py manage_billing status

# Traitement quotidien
python manage.py manage_billing process_daily

# Calcul des royalties
python manage.py manage_billing calculate_royalties

# Statistiques
python manage.py manage_billing stats --days 30

# Test de création de facture
python manage.py manage_billing test_invoice --user-id 1 --amount 100

# Nettoyage des anciennes données
python manage.py manage_billing cleanup --days 365
```

### API Examples

#### Créer une facture

```python
from shared_models.billing_services import InvoiceService

invoice_service = InvoiceService()
items = [
    {
        'description': 'Abonnement Premium',
        'quantity': 1,
        'unit_price': 29.99,
        'item_type': 'subscription'
    }
]

invoice = invoice_service.create_invoice(
    user=user,
    items=items,
    currency='EUR'
)
```

#### Calculer les royalties

```python
from shared_models.billing_services import RoyaltyService

royalty_service = RoyaltyService()
royalty = royalty_service.calculate_author_royalty(author)
```

#### Créer un abonnement récurrent

```python
from shared_models.billing_services import RecurringBillingService

recurring_service = RecurringBillingService()
recurring = recurring_service.create_recurring_billing(
    user=user,
    billing_type='subscription',
    amount=29.99,
    currency='EUR',
    frequency='monthly'
)
```

### Webhooks

Configurer les webhooks chez vos fournisseurs de paiement :

- **Stripe** : `https://votre-domaine.com/webhooks/billing/stripe/`
- **PayPal** : `https://votre-domaine.com/webhooks/billing/paypal/`
- **Orange Money** : `https://votre-domaine.com/webhooks/billing/orange-money/`
- **MTN Mobile Money** : `https://votre-domaine.com/webhooks/billing/mtn-mobile-money/`

## Configuration avancée

### Taux de royalties

```python
from shared_models.billing import BillingConfiguration

# Taux pour les ventes directes
BillingConfiguration.objects.create(
    config_type='royalty_rate',
    config_key='sale_rate',
    config_value={'rate': 0.70},  # 70%
    description='Taux de royalty pour les ventes'
)

# Taux pour les lectures d'abonnement
BillingConfiguration.objects.create(
    config_type='royalty_rate',
    config_key='subscription_rate',
    config_value={'rate': 0.50},  # 50%
    description='Taux de royalty pour les abonnements'
)
```

### Seuils de paiement

```python
# Seuil minimum pour déclencher un paiement
BillingConfiguration.objects.create(
    config_type='payment_threshold',
    config_key='minimum_amount',
    config_value={'amount': 100.00, 'currency': 'EUR'},
    description='Seuil minimum de paiement'
)
```

### Templates d'emails

Personaliser les templates dans :
- `templates/billing/emails/invoice.html`
- `templates/billing/emails/royalty.html`
- `templates/billing/emails/overdue.html`

## Monitoring et logs

### Logs

Les logs sont disponibles dans :
- `logs/billing.log` : Logs généraux
- `logs/celery.log` : Logs des tâches automatisées

### Métriques

```python
from shared_models.billing_services import BillingAutomationService

automation = BillingAutomationService()
metrics = automation.get_billing_metrics()
```

### Health Check

```python
from shared_models.billing_integration import get_billing_health_status

status = get_billing_health_status()
```

## Sécurité

### Validation des webhooks

Tous les webhooks sont validés avec les signatures des fournisseurs :
- Stripe : Signature HMAC
- PayPal : Certificat SSL
- Orange Money : Clé secrète
- MTN Mobile Money : Token d'authentification

### Chiffrement des données

Les données sensibles sont chiffrées :
- Métadonnées de paiement
- Informations bancaires (si stockées)
- Clés d'API (variables d'environnement)

### Audit trail

Toutes les actions sont loggées :
- Création/modification de factures
- Calculs de royalties
- Paiements et échecs
- Modifications de configuration

## Tests

```bash
# Tests unitaires
python manage.py test shared_models.tests.test_billing

# Tests d'intégration
python manage.py test shared_models.tests.test_billing.BillingIntegrationTestCase

# Coverage
coverage run --source='.' manage.py test shared_models.tests.test_billing
coverage report
```

## Déploiement

### Production

1. **Variables d'environnement** :
   ```bash
   export STRIPE_SECRET_KEY="sk_live_..."
   export PAYPAL_SANDBOX="False"
   export BILLING_EMAIL_ENABLED="True"
   ```

2. **Celery workers** :
   ```bash
   celery -A coko worker -Q billing -l info
   celery -A coko beat -l info
   ```

3. **Monitoring** :
   - Configurer Sentry pour les erreurs
   - Mettre en place des alertes sur les métriques
   - Surveiller les queues Celery

### Backup

```bash
# Backup des données de facturation
pg_dump -t billing_* coko_db > billing_backup.sql

# Backup des configurations
python manage.py dumpdata shared_models.BillingConfiguration > billing_config.json
```

## Support et maintenance

### Mise à jour

```bash
# Vérifier les migrations
python manage.py showmigrations shared_models

# Appliquer les mises à jour
python manage.py migrate shared_models

# Valider la configuration
python manage.py manage_billing validate
```

### Dépannage

#### Problèmes courants

1. **Factures non générées** :
   - Vérifier la configuration des taux
   - Contrôler les logs Celery
   - Valider les permissions utilisateur

2. **Webhooks en échec** :
   - Vérifier les signatures
   - Contrôler la connectivité réseau
   - Valider les URLs de webhook

3. **Royalties incorrectes** :
   - Vérifier les taux de configuration
   - Contrôler les données de transaction
   - Valider les calculs manuellement

#### Debug

```python
# Activer le debug pour la facturation
import logging
logging.getLogger('shared_models.billing').setLevel(logging.DEBUG)

# Tester une facture spécifique
from shared_models.billing_services import InvoiceService
invoice_service = InvoiceService()
invoice_service.debug_invoice('INV-2024-001')
```

## Roadmap

### Version 1.1
- [ ] Support de nouvelles devises (GHS, NGN)
- [ ] Intégration avec des systèmes comptables (QuickBooks, Sage)
- [ ] API GraphQL
- [ ] Interface d'administration avancée

### Version 1.2
- [ ] Machine learning pour la détection de fraude
- [ ] Facturation basée sur l'usage
- [ ] Support multi-tenant
- [ ] Intégration avec des banques locales

### Version 2.0
- [ ] Refactoring en microservices
- [ ] Support blockchain pour les paiements
- [ ] IA pour l'optimisation des revenus
- [ ] Marketplace de plugins

## Licence

Ce système de facturation est développé pour Coko et est soumis aux termes de la licence du projet principal.

## Contact

Pour toute question ou support :
- Email : dev@coko.com
- Documentation : https://docs.coko.com/billing
- Issues : https://github.com/coko/coko/issues