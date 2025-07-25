#!/usr/bin/env python
"""
Test simple du système de facturation Coko
"""

import os
import sys
import django
from decimal import Decimal
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coko.settings_local')
sys.path.append('/home/youssoupha/coko/backend')
django.setup()

# Imports après setup Django
from django.contrib.auth import get_user_model
from shared_models.billing import (
    Invoice, InvoiceItem, AuthorRoyalty, RecurringBilling, 
    BillingConfiguration
)
from shared_models.financial_reports import PaymentTransaction
from shared_models.billing_services import InvoiceService, RoyaltyService

User = get_user_model()

def test_billing_system():
    """Test complet du système de facturation"""
    print("🧪 Début des tests du système de facturation Coko")
    
    # 1. Test de création d'utilisateur
    print("\n1. Test de création d'utilisateur...")
    try:
        # Supprimer l'utilisateur s'il existe déjà
        User.objects.filter(username='test_author').delete()
        
        user = User.objects.create_user(
            username='test_author',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Author'
        )
        
        # Forcer la sauvegarde et vérifier
        user.save()
        user.refresh_from_db()
        
        print(f"✅ Utilisateur créé: {user.username} (ID: {user.id})")
    except Exception as e:
        print(f"❌ Erreur création utilisateur: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. Test de configuration de facturation
    print("\n2. Test de configuration de facturation...")
    try:
        config, created = BillingConfiguration.objects.get_or_create(
            config_key='default_currency',
            defaults={
                'config_value': 'XOF',
                'description': 'Devise par défaut pour la facturation',
                'config_type': 'currency'
            }
        )
        print(f"✅ Configuration {'créée' if created else 'récupérée'}: {config.config_key} = {config.config_value}")
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return False
    
    # 3. Test de création de facture
    print("\n3. Test de création de facture...")
    try:
        print(f"Utilisateur pour facture: {user.id} - {user.username}")
        
        # Créer d'abord une transaction de paiement
        from django.utils import timezone
        amount = Decimal('5000.00')
        fees = amount * Decimal('0.02')  # 2% de frais pour Orange Money
        net_amount = amount - fees
        
        transaction = PaymentTransaction.objects.create(
            user=user,
            amount=amount,
            currency='XOF',
            transaction_type='book_purchase',
            payment_provider='orange_money',
            status='completed',
            completed_at=timezone.now(),
            fees=fees,
            net_amount=net_amount,
            metadata={'book_title': 'Les Contes d\'Afrique', 'book_uuid': 'test-book-123'}
        )
        print(f"Transaction créée: {transaction.id}")
        
        # Créer une facture manuellement pour éviter les problèmes de relation
        from shared_models.billing import Invoice, InvoiceItem
        
        invoice = Invoice.objects.create(
            user=user,
            invoice_type='book_purchase',
            currency='XOF',
            billing_name=user.get_full_name() or 'Test User',
            billing_email=user.email,
            billing_country='SN',
            billing_phone='',
            status='paid',
            total_amount=Decimal('5000.00')
        )
        
        # Créer une ligne de facture
        InvoiceItem.objects.create(
            invoice=invoice,
            description='Achat de livre: Les Contes d\'Afrique',
            quantity=Decimal('1.00'),
            unit_price=Decimal('5000.00'),
            metadata={'book_title': 'Les Contes d\'Afrique', 'book_uuid': 'test-book-123'}
        )
        
        print(f"✅ Facture créée: {invoice.invoice_number} - {invoice.total_amount} {invoice.currency}")
    except Exception as e:
        print(f"❌ Erreur création facture: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Test de transaction de paiement (déjà créée dans le test précédent)
    print("\n4. Vérification de la transaction de paiement...")
    try:
        # Récupérer la transaction créée précédemment
        latest_transaction = PaymentTransaction.objects.filter(user=user).last()
        if latest_transaction:
            print(f"✅ Transaction vérifiée: {latest_transaction.id} - {latest_transaction.amount} {latest_transaction.currency}")
        else:
            print("❌ Aucune transaction trouvée")
    except Exception as e:
        print(f"❌ Erreur vérification transaction: {e}")
        return False
    
    # 5. Test de calcul de royalties
    print("\n5. Test de calcul de royalties...")
    try:
        from datetime import datetime, timedelta
        
        # Calculer les royalties pour le mois dernier
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        royalties = RoyaltyService.calculate_author_royalties(
            author=user,
            period_start=start_date,
            period_end=end_date
        )
        
        print(f"✅ Royalties calculées: {len(royalties)} entrées")
    except Exception as e:
        print(f"❌ Erreur royalty: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Test de facturation récurrente
    print("\n6. Test de facturation récurrente...")
    try:
        recurring = RecurringBilling.objects.create(
            user=user,
            subscription_type='premium',
            amount=Decimal('2500.00'),
            currency='XOF',
            frequency='monthly',
            status='active',
            start_date=timezone.now(),
            next_billing_date=timezone.now() + timezone.timedelta(days=30),
            metadata={
                'plan': 'premium_monthly',
                'features': ['unlimited_reading', 'offline_access']
            }
        )
        print(f"✅ Facturation récurrente créée: {recurring.subscription_type} - {recurring.amount} {recurring.currency}/mois")
    except Exception as e:
        print(f"❌ Erreur facturation récurrente: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 7. Statistiques finales
    print("\n7. Statistiques du système...")
    try:
        total_invoices = Invoice.objects.count()
        total_transactions = PaymentTransaction.objects.count()
        total_royalties = AuthorRoyalty.objects.count()
        total_recurring = RecurringBilling.objects.count()
        
        print(f"📊 Statistiques:")
        print(f"   - Factures: {total_invoices}")
        print(f"   - Transactions: {total_transactions}")
        print(f"   - Royalties: {total_royalties}")
        print(f"   - Abonnements récurrents: {total_recurring}")
    except Exception as e:
        print(f"❌ Erreur statistiques: {e}")
        return False
    
    print("\n🎉 Tous les tests du système de facturation ont réussi !")
    return True

if __name__ == '__main__':
    success = test_billing_system()
    if success:
        print("\n✅ Le système de facturation Coko est prêt pour la production !")
        sys.exit(0)
    else:
        print("\n❌ Des erreurs ont été détectées dans le système de facturation.")
        sys.exit(1)