"""Tests pour le système de facturation Coko"""

from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from shared_models.billing import (
    Invoice, InvoiceItem, AuthorRoyalty, BillingConfiguration, RecurringBilling
)
from shared_models.billing_services import (
    InvoiceService, RoyaltyService, RecurringBillingService, BillingAutomationService
)
from shared_models.billing_settings import get_billing_config, validate_billing_config
from shared_models.financial_reports import PaymentTransaction

User = get_user_model()


class BillingModelsTestCase(TestCase):
    """Tests pour les modèles de facturation"""
    
    def setUp(self):
        """Configuration des tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.author = User.objects.create_user(
            username='testauthor',
            email='author@example.com',
            password='testpass123',
            is_author=True
        )
        
        # Configuration de test
        self.billing_config = BillingConfiguration.objects.create(
            config_type='tax_rate',
            config_key='default_rate',
            config_value={'rate': 0.20},
            description='Taux de taxe de test'
        )
    
    def test_invoice_creation(self):
        """Test de création d'une facture"""
        invoice = Invoice.objects.create(
            user=self.user,
            invoice_number='INV-2024-001',
            subtotal=Decimal('100.00'),
            tax_rate=Decimal('20.00'),
            tax_amount=Decimal('20.00'),
            total_amount=Decimal('120.00'),
            currency='EUR',
            status='pending'
        )
        
        self.assertEqual(invoice.user, self.user)
        self.assertEqual(invoice.invoice_number, 'INV-2024-001')
        self.assertEqual(invoice.total_amount, Decimal('120.00'))
        self.assertEqual(invoice.status, 'pending')
        self.assertTrue(invoice.is_pending)
        self.assertFalse(invoice.is_paid)
    
    def test_invoice_item_creation(self):
        """Test de création d'un item de facture"""
        invoice = Invoice.objects.create(
            user=self.user,
            invoice_number='INV-2024-002',
            currency='EUR'
        )
        
        item = InvoiceItem.objects.create(
            invoice=invoice,
            description='Abonnement Premium',
            quantity=1,
            unit_price=Decimal('29.99'),
            total_price=Decimal('29.99'),
            item_type='subscription'
        )
        
        self.assertEqual(item.invoice, invoice)
        self.assertEqual(item.description, 'Abonnement Premium')
        self.assertEqual(item.total_price, Decimal('29.99'))
    
    def test_author_royalty_creation(self):
        """Test de création d'une royalty d'auteur"""
        royalty = AuthorRoyalty.objects.create(
            author=self.author,
            period_start=timezone.now().date().replace(day=1),
            period_end=timezone.now().date(),
            royalty_amount=Decimal('150.00'),
            currency='EUR',
            calculation_details={
                'book_sales': 10,
                'subscription_reads': 50,
                'total_revenue': 300.00
            }
        )
        
        self.assertEqual(royalty.author, self.author)
        self.assertEqual(royalty.royalty_amount, Decimal('150.00'))
        self.assertEqual(royalty.status, 'pending')
        self.assertTrue(royalty.is_pending)
    
    def test_recurring_billing_creation(self):
        """Test de création d'un abonnement récurrent"""
        recurring = RecurringBilling.objects.create(
            user=self.user,
            billing_type='subscription',
            amount=Decimal('29.99'),
            currency='EUR',
            frequency='monthly',
            next_billing_date=timezone.now().date() + timedelta(days=30)
        )
        
        self.assertEqual(recurring.user, self.user)
        self.assertEqual(recurring.amount, Decimal('29.99'))
        self.assertEqual(recurring.frequency, 'monthly')
        self.assertEqual(recurring.status, 'active')
        self.assertTrue(recurring.is_active)
    
    def test_billing_configuration(self):
        """Test de la configuration de facturation"""
        config = BillingConfiguration.objects.create(
            config_type='royalty_rate',
            config_key='sale_rate',
            config_value={'rate': 0.70},
            description='Taux de royalty pour les ventes'
        )
        
        self.assertEqual(config.config_type, 'royalty_rate')
        self.assertEqual(config.config_value['rate'], 0.70)
        self.assertTrue(config.is_active)


class InvoiceServiceTestCase(TestCase):
    """Tests pour le service de facturation"""
    
    def setUp(self):
        """Configuration des tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.invoice_service = InvoiceService()
        
        # Configuration de test
        BillingConfiguration.objects.create(
            config_type='tax_rate',
            config_key='default_rate',
            config_value={'rate': 0.20},
            description='Taux de taxe de test'
        )
    
    def test_create_invoice(self):
        """Test de création d'une facture via le service"""
        items = [
            {
                'description': 'Abonnement Premium',
                'quantity': 1,
                'unit_price': Decimal('29.99'),
                'item_type': 'subscription'
            }
        ]
        
        invoice = self.invoice_service.create_invoice(
            user=self.user,
            items=items,
            currency='EUR'
        )
        
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.user, self.user)
        self.assertEqual(invoice.currency, 'EUR')
        self.assertEqual(invoice.status, 'pending')
        self.assertTrue(invoice.invoice_number.startswith('INV-'))
        
        # Vérifier les items
        invoice_items = invoice.items.all()
        self.assertEqual(invoice_items.count(), 1)
        self.assertEqual(invoice_items.first().description, 'Abonnement Premium')
    
    def test_mark_invoice_as_paid(self):
        """Test de marquage d'une facture comme payée"""
        # Créer une facture
        items = [{
            'description': 'Test Item',
            'quantity': 1,
            'unit_price': Decimal('50.00'),
            'item_type': 'other'
        }]
        
        invoice = self.invoice_service.create_invoice(
            user=self.user,
            items=items,
            currency='EUR'
        )
        
        # Créer une transaction de paiement
        payment = PaymentTransaction.objects.create(
            user=self.user,
            amount=invoice.total_amount,
            currency=invoice.currency,
            transaction_type='subscription',
            status='completed',
            payment_provider='stripe'
        )
        
        # Marquer comme payée
        result = self.invoice_service.mark_invoice_as_paid(
            invoice.invoice_number,
            payment.id
        )
        
        self.assertTrue(result)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
        self.assertEqual(invoice.payment_transaction, payment)
    
    def test_calculate_invoice_totals(self):
        """Test du calcul des totaux de facture"""
        items = [
            {
                'description': 'Item 1',
                'quantity': 2,
                'unit_price': Decimal('25.00'),
                'item_type': 'other'
            },
            {
                'description': 'Item 2',
                'quantity': 1,
                'unit_price': Decimal('50.00'),
                'item_type': 'other'
            }
        ]
        
        invoice = self.invoice_service.create_invoice(
            user=self.user,
            items=items,
            currency='EUR'
        )
        
        # Vérifier les calculs
        self.assertEqual(invoice.subtotal, Decimal('100.00'))  # (2*25) + (1*50)
        self.assertEqual(invoice.tax_amount, Decimal('20.00'))  # 20% de 100
        self.assertEqual(invoice.total_amount, Decimal('120.00'))  # 100 + 20


class RoyaltyServiceTestCase(TestCase):
    """Tests pour le service de royalties"""
    
    def setUp(self):
        """Configuration des tests"""
        self.author = User.objects.create_user(
            username='testauthor',
            email='author@example.com',
            password='testpass123',
            is_author=True
        )
        
        self.royalty_service = RoyaltyService()
        
        # Configuration de test
        BillingConfiguration.objects.create(
            config_type='royalty_rate',
            config_key='sale_rate',
            config_value={'rate': 0.70},
            description='Taux de royalty pour les ventes'
        )
        
        BillingConfiguration.objects.create(
            config_type='royalty_rate',
            config_key='subscription_rate',
            config_value={'rate': 0.50},
            description='Taux de royalty pour les abonnements'
        )
    
    @patch('shared_models.billing_services.RoyaltyService._get_author_transactions')
    def test_calculate_author_royalty(self, mock_get_transactions):
        """Test du calcul de royalty d'un auteur"""
        # Mock des transactions
        mock_get_transactions.return_value = [
            {
                'transaction_type': 'book_purchase',
                'amount': Decimal('20.00'),
                'currency': 'EUR',
                'book_id': 1
            },
            {
                'transaction_type': 'subscription',
                'amount': Decimal('10.00'),
                'currency': 'EUR',
                'reads_count': 5
            }
        ]
        
        royalty = self.royalty_service.calculate_author_royalty(self.author)
        
        self.assertIsNotNone(royalty)
        self.assertEqual(royalty.author, self.author)
        # Calcul: (20 * 0.70) + (10 * 0.50) = 14 + 5 = 19
        self.assertEqual(royalty.royalty_amount, Decimal('19.00'))
        self.assertEqual(royalty.currency, 'EUR')
    
    def test_should_process_author_payment(self):
        """Test de vérification du seuil de paiement"""
        # Créer des royalties en attente
        AuthorRoyalty.objects.create(
            author=self.author,
            period_start=timezone.now().date().replace(day=1),
            period_end=timezone.now().date(),
            royalty_amount=Decimal('75.00'),
            currency='EUR',
            status='pending'
        )
        
        AuthorRoyalty.objects.create(
            author=self.author,
            period_start=(timezone.now().date().replace(day=1) - timedelta(days=30)),
            period_end=(timezone.now().date() - timedelta(days=30)),
            royalty_amount=Decimal('30.00'),
            currency='EUR',
            status='pending'
        )
        
        # Test avec seuil par défaut (100 EUR)
        should_pay = self.royalty_service.should_process_author_payment(self.author)
        self.assertTrue(should_pay)  # 75 + 30 = 105 > 100


class RecurringBillingServiceTestCase(TestCase):
    """Tests pour le service de facturation récurrente"""
    
    def setUp(self):
        """Configuration des tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.recurring_service = RecurringBillingService()
    
    def test_create_recurring_billing(self):
        """Test de création d'un abonnement récurrent"""
        recurring = self.recurring_service.create_recurring_billing(
            user=self.user,
            billing_type='subscription',
            amount=Decimal('29.99'),
            currency='EUR',
            frequency='monthly'
        )
        
        self.assertIsNotNone(recurring)
        self.assertEqual(recurring.user, self.user)
        self.assertEqual(recurring.amount, Decimal('29.99'))
        self.assertEqual(recurring.frequency, 'monthly')
        self.assertEqual(recurring.status, 'active')
    
    def test_process_due_billings(self):
        """Test du traitement des facturations échues"""
        # Créer un abonnement échu
        recurring = RecurringBilling.objects.create(
            user=self.user,
            billing_type='subscription',
            amount=Decimal('29.99'),
            currency='EUR',
            frequency='monthly',
            next_billing_date=timezone.now().date() - timedelta(days=1),
            status='active'
        )
        
        with patch.object(self.recurring_service, '_process_single_billing') as mock_process:
            mock_process.return_value = True
            
            results = self.recurring_service.process_due_billings()
            
            self.assertEqual(len(results), 1)
            mock_process.assert_called_once_with(recurring)


class BillingAutomationServiceTestCase(TestCase):
    """Tests pour le service d'automatisation"""
    
    def setUp(self):
        """Configuration des tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.automation_service = BillingAutomationService()
    
    def test_run_daily_billing(self):
        """Test du traitement quotidien"""
        # Créer une facture en retard
        invoice = Invoice.objects.create(
            user=self.user,
            invoice_number='INV-2024-001',
            total_amount=Decimal('100.00'),
            currency='EUR',
            status='sent',
            due_date=timezone.now().date() - timedelta(days=1)
        )
        
        with patch.object(self.automation_service, '_send_overdue_notifications') as mock_send:
            mock_send.return_value = 1
            
            result = self.automation_service.run_daily_billing()
            
            self.assertIn('invoices_processed', result)
            self.assertIn('notifications_sent', result)
            
            # Vérifier que la facture est marquée comme en retard
            invoice.refresh_from_db()
            self.assertEqual(invoice.status, 'overdue')


class BillingConfigurationTestCase(TestCase):
    """Tests pour la configuration de facturation"""
    
    def test_get_billing_config(self):
        """Test de récupération de la configuration"""
        # Créer une configuration
        BillingConfiguration.objects.create(
            config_type='tax_rate',
            config_key='default_rate',
            config_value={'rate': 0.20},
            description='Taux de taxe par défaut'
        )
        
        config = get_billing_config('tax_rate', 'default_rate')
        self.assertIsNotNone(config)
        self.assertEqual(config['rate'], 0.20)
    
    def test_validate_billing_config(self):
        """Test de validation de la configuration"""
        # Configuration incomplète
        errors = validate_billing_config()
        self.assertTrue(len(errors) > 0)
        
        # Ajouter les configurations requises
        required_configs = [
            ('tax_rate', 'default_rate', {'rate': 0.20}),
            ('royalty_rate', 'sale_rate', {'rate': 0.70}),
            ('royalty_rate', 'subscription_rate', {'rate': 0.50}),
            ('payment_terms', 'default_due_days', {'days': 30}),
            ('currency', 'default_currency', {'currency': 'EUR'})
        ]
        
        for config_type, config_key, config_value in required_configs:
            BillingConfiguration.objects.create(
                config_type=config_type,
                config_key=config_key,
                config_value=config_value,
                description=f'Test {config_type} {config_key}'
            )
        
        # Valider à nouveau
        errors = validate_billing_config()
        self.assertEqual(len(errors), 0)


class BillingIntegrationTestCase(TransactionTestCase):
    """Tests d'intégration pour le système de facturation"""
    
    def setUp(self):
        """Configuration des tests d'intégration"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.author = User.objects.create_user(
            username='testauthor',
            email='author@example.com',
            password='testpass123',
            is_author=True
        )
        
        # Créer les configurations nécessaires
        configs = [
            ('tax_rate', 'default_rate', {'rate': 0.20}),
            ('royalty_rate', 'sale_rate', {'rate': 0.70}),
            ('royalty_rate', 'subscription_rate', {'rate': 0.50}),
            ('payment_terms', 'default_due_days', {'days': 30}),
            ('currency', 'default_currency', {'currency': 'EUR'})
        ]
        
        for config_type, config_key, config_value in configs:
            BillingConfiguration.objects.create(
                config_type=config_type,
                config_key=config_key,
                config_value=config_value,
                description=f'Test {config_type} {config_key}'
            )
    
    def test_complete_billing_workflow(self):
        """Test du workflow complet de facturation"""
        # 1. Créer une facture
        invoice_service = InvoiceService()
        items = [{
            'description': 'Abonnement Premium',
            'quantity': 1,
            'unit_price': Decimal('29.99'),
            'item_type': 'subscription'
        }]
        
        invoice = invoice_service.create_invoice(
            user=self.user,
            items=items,
            currency='EUR'
        )
        
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.status, 'pending')
        
        # 2. Simuler un paiement
        payment = PaymentTransaction.objects.create(
            user=self.user,
            amount=invoice.total_amount,
            currency=invoice.currency,
            transaction_type='subscription',
            status='completed',
            payment_provider='stripe',
            metadata={'invoice_id': invoice.invoice_number}
        )
        
        # 3. Marquer la facture comme payée
        result = invoice_service.mark_invoice_as_paid(
            invoice.invoice_number,
            payment.id
        )
        
        self.assertTrue(result)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
        
        # 4. Calculer les royalties
        royalty_service = RoyaltyService()
        
        with patch.object(royalty_service, '_get_author_transactions') as mock_transactions:
            mock_transactions.return_value = [{
                'transaction_type': 'subscription',
                'amount': invoice.total_amount,
                'currency': 'EUR',
                'reads_count': 1
            }]
            
            royalty = royalty_service.calculate_author_royalty(self.author)
            
            self.assertIsNotNone(royalty)
            self.assertEqual(royalty.status, 'pending')
    
    def test_recurring_billing_workflow(self):
        """Test du workflow d'abonnement récurrent"""
        # 1. Créer un abonnement récurrent
        recurring_service = RecurringBillingService()
        
        recurring = recurring_service.create_recurring_billing(
            user=self.user,
            billing_type='subscription',
            amount=Decimal('29.99'),
            currency='EUR',
            frequency='monthly'
        )
        
        self.assertIsNotNone(recurring)
        self.assertEqual(recurring.status, 'active')
        
        # 2. Simuler une date d'échéance
        recurring.next_billing_date = timezone.now().date() - timedelta(days=1)
        recurring.save()
        
        # 3. Traiter les facturations échues
        with patch.object(recurring_service, '_create_invoice_for_recurring') as mock_create:
            mock_invoice = Invoice.objects.create(
                user=self.user,
                invoice_number='INV-REC-001',
                total_amount=recurring.amount,
                currency=recurring.currency,
                status='pending'
            )
            mock_create.return_value = mock_invoice
            
            results = recurring_service.process_due_billings()
            
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0])
            
            # Vérifier que la prochaine date de facturation a été mise à jour
            recurring.refresh_from_db()
            self.assertGreater(recurring.next_billing_date, timezone.now().date())


class BillingAPITestCase(TestCase):
    """Tests pour les APIs de facturation"""
    
    def setUp(self):
        """Configuration des tests d'API"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer une facture de test
        self.invoice = Invoice.objects.create(
            user=self.user,
            invoice_number='INV-2024-001',
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('20.00'),
            total_amount=Decimal('120.00'),
            currency='EUR',
            status='pending'
        )
    
    def test_invoice_serialization(self):
        """Test de sérialisation des factures"""
        from shared_models.billing_serializers import InvoiceSerializer
        
        serializer = InvoiceSerializer(self.invoice)
        data = serializer.data
        
        self.assertEqual(data['invoice_number'], 'INV-2024-001')
        self.assertEqual(data['total_amount'], '120.00')
        self.assertEqual(data['currency'], 'EUR')
        self.assertEqual(data['status'], 'pending')
    
    def test_invoice_creation_via_api(self):
        """Test de création de facture via l'API"""
        from shared_models.billing_serializers import InvoiceCreateSerializer
        
        data = {
            'user': self.user.id,
            'items': [
                {
                    'description': 'Test Item',
                    'quantity': 1,
                    'unit_price': '50.00',
                    'item_type': 'other'
                }
            ],
            'currency': 'EUR'
        }
        
        serializer = InvoiceCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Note: Le test complet nécessiterait un client de test Django REST
        # pour tester les vues réelles


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'shared_models',
            ],
            SECRET_KEY='test-secret-key'
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['__main__'])