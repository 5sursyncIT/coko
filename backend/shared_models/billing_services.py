"""Services de facturation automatisée pour Coko"""

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q, Count
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from .billing import (
    Invoice, InvoiceItem, AuthorRoyalty, BillingConfiguration, 
    RecurringBilling
)
from .financial_reports import PaymentTransaction

User = get_user_model()
logger = logging.getLogger(__name__)


class InvoiceService:
    """Service de gestion des factures"""
    
    @staticmethod
    def create_invoice_from_transaction(payment_transaction: PaymentTransaction) -> Invoice:
        """Crée une facture à partir d'une transaction de paiement"""
        with transaction.atomic():
            # Récupérer la configuration de TVA
            tax_rate = BillingConfiguration.get_config(
                'tax_rate', 'default', 
                payment_transaction.user.country or '', 
                getattr(payment_transaction.user, 'subscription_type', 'basic')
            ) or Decimal('0.00')
            
            invoice = Invoice.objects.create(
                user=payment_transaction.user,
                payment_transaction=payment_transaction,
                invoice_type=payment_transaction.transaction_type,
                currency=payment_transaction.currency,
                tax_rate=tax_rate,
                billing_name=payment_transaction.user.get_full_name(),
                billing_email=payment_transaction.user.email,
                billing_country=getattr(payment_transaction.user, 'country', '') or '',
                billing_phone=getattr(payment_transaction.user, 'phone', '') or '',
                status='pending' if payment_transaction.status == 'pending' else 'paid',
                paid_date=payment_transaction.completed_at if payment_transaction.status == 'completed' else None,
                metadata={
                    'transaction_id': str(payment_transaction.id),
                    'payment_provider': payment_transaction.payment_provider
                }
            )
            
            # Créer la ligne de facture
            description = InvoiceService._get_transaction_description(payment_transaction)
            InvoiceItem.objects.create(
                invoice=invoice,
                description=description,
                quantity=Decimal('1.00'),
                unit_price=payment_transaction.amount,
                metadata=payment_transaction.metadata
            )
            
            logger.info(f"Facture {invoice.invoice_number} créée pour la transaction {payment_transaction.id}")
            return invoice
    
    @staticmethod
    def _get_transaction_description(payment_transaction: PaymentTransaction) -> str:
        """Génère une description pour la ligne de facture"""
        descriptions = {
            'subscription': f"Abonnement {getattr(payment_transaction.user, 'subscription_type', 'basic')}",
            'book_purchase': f"Achat de livre: {payment_transaction.metadata.get('book_title', 'Livre')}",
            'premium_upgrade': "Mise à niveau vers Premium",
            'tip': f"Pourboire pour l'auteur: {payment_transaction.metadata.get('author_name', 'Auteur')}",
            'refund': "Remboursement"
        }
        return descriptions.get(payment_transaction.transaction_type, "Transaction")
    
    @staticmethod
    def mark_overdue_invoices():
        """Marque les factures en retard"""
        overdue_invoices = Invoice.objects.filter(
            status__in=['pending', 'sent'],
            due_date__lt=timezone.now()
        )
        
        count = overdue_invoices.update(status='overdue')
        logger.info(f"{count} factures marquées comme en retard")
        return count
    
    @staticmethod
    def get_invoice_statistics(user: User = None) -> Dict:
        """Récupère les statistiques des factures"""
        queryset = Invoice.objects.all()
        if user:
            queryset = queryset.filter(user=user)
        
        stats = {
            'total_invoices': queryset.count(),
            'pending_invoices': queryset.filter(status='pending').count(),
            'paid_invoices': queryset.filter(status='paid').count(),
            'overdue_invoices': queryset.filter(status='overdue').count(),
            'total_amount': queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
            'paid_amount': queryset.filter(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
            'pending_amount': queryset.filter(status__in=['pending', 'sent']).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
        }
        
        return stats


class RoyaltyService:
    """Service de gestion des royalties pour les auteurs"""
    
    @staticmethod
    def calculate_author_royalties(author: User, period_start: datetime, period_end: datetime) -> List[AuthorRoyalty]:
        """Calcule les royalties d'un auteur pour une période donnée"""
        royalties = []
        
        # Royalties des ventes de livres
        book_sales = RoyaltyService._calculate_book_sales_royalties(author, period_start, period_end)
        royalties.extend(book_sales)
        
        # Royalties des abonnements (part des revenus d'abonnement)
        subscription_share = RoyaltyService._calculate_subscription_share_royalties(author, period_start, period_end)
        if subscription_share:
            royalties.append(subscription_share)
        
        # Pourboires reçus
        tips = RoyaltyService._calculate_tip_royalties(author, period_start, period_end)
        royalties.extend(tips)
        
        return royalties
    
    @staticmethod
    def _calculate_book_sales_royalties(author: User, period_start: datetime, period_end: datetime) -> List[AuthorRoyalty]:
        """Calcule les royalties des ventes de livres"""
        # Récupérer les transactions d'achat de livres pour cet auteur
        book_purchases = PaymentTransaction.objects.filter(
            transaction_type='book_purchase',
            status='completed',
            completed_at__range=[period_start, period_end],
            metadata__author_id=str(author.id)
        )
        
        royalties = []
        for purchase in book_purchases:
            # Récupérer le taux de royalty configuré
            royalty_rate = BillingConfiguration.get_config(
                'royalty_rate', 'book_sale',
                author.country or '',
                'author'
            ) or Decimal('0.30')  # 30% par défaut
            
            royalty = AuthorRoyalty.objects.create(
                author=author,
                book_uuid=purchase.metadata.get('book_uuid'),
                book_title=purchase.metadata.get('book_title', ''),
                royalty_type='book_sale',
                base_amount=purchase.amount,
                royalty_rate=royalty_rate,
                currency=purchase.currency,
                period_start=period_start,
                period_end=period_end,
                calculation_details={
                    'transaction_id': str(purchase.id),
                    'sale_amount': str(purchase.amount),
                    'royalty_rate': str(royalty_rate)
                }
            )
            royalty.mark_as_calculated()
            royalties.append(royalty)
        
        return royalties
    
    @staticmethod
    def _calculate_subscription_share_royalties(author: User, period_start: datetime, period_end: datetime) -> Optional[AuthorRoyalty]:
        """Calcule la part des revenus d'abonnement pour un auteur"""
        # Récupérer les revenus d'abonnement de la période
        subscription_revenue = PaymentTransaction.objects.filter(
            transaction_type='subscription',
            status='completed',
            completed_at__range=[period_start, period_end]
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        if subscription_revenue == Decimal('0.00'):
            return None
        
        # Calculer la part de l'auteur basée sur l'engagement de ses livres
        # (Simulation - dans un vrai système, cela serait basé sur les métriques de lecture)
        author_engagement_score = RoyaltyService._calculate_author_engagement(author, period_start, period_end)
        total_engagement = RoyaltyService._calculate_total_engagement(period_start, period_end)
        
        if total_engagement == 0:
            return None
        
        # Calculer la part proportionnelle
        author_share_rate = Decimal(str(author_engagement_score / total_engagement))
        
        # Appliquer le taux de partage configuré
        sharing_rate = BillingConfiguration.get_config(
            'royalty_rate', 'subscription_share',
            author.country or '',
            'author'
        ) or Decimal('0.50')  # 50% des revenus d'abonnement redistribués
        
        base_amount = subscription_revenue * sharing_rate
        
        royalty = AuthorRoyalty.objects.create(
            author=author,
            royalty_type='subscription_share',
            base_amount=base_amount,
            royalty_rate=author_share_rate,
            currency='XOF',  # Devise par défaut
            period_start=period_start,
            period_end=period_end,
            calculation_details={
                'total_subscription_revenue': str(subscription_revenue),
                'sharing_rate': str(sharing_rate),
                'author_engagement_score': author_engagement_score,
                'total_engagement': total_engagement,
                'author_share_rate': str(author_share_rate)
            }
        )
        royalty.mark_as_calculated()
        
        return royalty
    
    @staticmethod
    def _calculate_tip_royalties(author: User, period_start: datetime, period_end: datetime) -> List[AuthorRoyalty]:
        """Calcule les royalties des pourboires"""
        tips = PaymentTransaction.objects.filter(
            transaction_type='tip',
            status='completed',
            completed_at__range=[period_start, period_end],
            metadata__author_id=str(author.id)
        )
        
        royalties = []
        for tip in tips:
            # Les pourboires sont généralement à 100% pour l'auteur moins les frais
            royalty_rate = BillingConfiguration.get_config(
                'royalty_rate', 'tip',
                author.country or '',
                'author'
            ) or Decimal('0.95')  # 95% (5% de frais de traitement)
            
            royalty = AuthorRoyalty.objects.create(
                author=author,
                book_uuid=tip.metadata.get('book_uuid'),
                book_title=tip.metadata.get('book_title', ''),
                royalty_type='tip',
                base_amount=tip.amount,
                royalty_rate=royalty_rate,
                currency=tip.currency,
                period_start=period_start,
                period_end=period_end,
                calculation_details={
                    'transaction_id': str(tip.id),
                    'tip_amount': str(tip.amount),
                    'tipper_id': tip.metadata.get('tipper_id')
                }
            )
            royalty.mark_as_calculated()
            royalties.append(royalty)
        
        return royalties
    
    @staticmethod
    def _calculate_author_engagement(author: User, period_start: datetime, period_end: datetime) -> float:
        """Calcule le score d'engagement d'un auteur (simulation)"""
        # Dans un vrai système, cela serait basé sur :
        # - Nombre de lectures de ses livres
        # - Temps de lecture total
        # - Interactions (likes, commentaires)
        # - Téléchargements
        
        # Simulation basée sur les transactions liées à ses livres
        book_transactions = PaymentTransaction.objects.filter(
            Q(metadata__author_id=str(author.id)) |
            Q(transaction_type='tip', metadata__author_id=str(author.id)),
            completed_at__range=[period_start, period_end]
        ).count()
        
        return float(book_transactions * 10)  # Score arbitraire
    
    @staticmethod
    def _calculate_total_engagement(period_start: datetime, period_end: datetime) -> float:
        """Calcule l'engagement total de la plateforme"""
        total_transactions = PaymentTransaction.objects.filter(
            completed_at__range=[period_start, period_end]
        ).count()
        
        return float(total_transactions * 10)  # Score arbitraire
    
    @staticmethod
    def generate_royalty_invoices(author: User, royalties: List[AuthorRoyalty]) -> Optional[Invoice]:
        """Génère une facture de royalties pour un auteur"""
        if not royalties:
            return None
        
        total_amount = sum(r.royalty_amount for r in royalties)
        if total_amount <= Decimal('0.00'):
            return None
        
        with transaction.atomic():
            invoice = Invoice.objects.create(
                user=author,
                invoice_type='author_royalty',
                currency=royalties[0].currency,
                billing_name=author.get_full_name(),
                billing_email=author.email,
                billing_country=author.country or '',
                billing_phone=author.phone or '',
                status='pending',
                metadata={
                    'royalty_period_start': royalties[0].period_start.isoformat(),
                    'royalty_period_end': royalties[0].period_end.isoformat(),
                    'royalty_count': len(royalties)
                }
            )
            
            # Créer les lignes de facture
            for royalty in royalties:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=f"Royalty {royalty.get_royalty_type_display()} - {royalty.book_title or 'Général'}",
                    quantity=Decimal('1.00'),
                    unit_price=royalty.royalty_amount,
                    book_uuid=royalty.book_uuid,
                    book_title=royalty.book_title,
                    metadata=royalty.calculation_details
                )
                
                # Lier la royalty à la facture
                royalty.invoice = invoice
                royalty.status = 'invoiced'
                royalty.save()
            
            logger.info(f"Facture de royalties {invoice.invoice_number} créée pour {author.get_full_name()}")
            return invoice


class RecurringBillingService:
    """Service de facturation récurrente"""
    
    @staticmethod
    def process_due_billings() -> List[Invoice]:
        """Traite toutes les facturations récurrentes dues"""
        due_billings = RecurringBilling.objects.filter(
            status='active',
            next_billing_date__lte=timezone.now()
        )
        
        invoices = []
        for billing in due_billings:
            try:
                if billing.total_cycles is None or billing.completed_cycles < billing.total_cycles:
                    invoice = billing.process_billing_cycle()
                    if invoice:
                        invoices.append(invoice)
                        logger.info(f"Facturation récurrente traitée: {invoice.invoice_number}")
            except Exception as e:
                billing.failed_attempts += 1
                billing.save()
                logger.error(f"Erreur lors du traitement de la facturation récurrente {billing.id}: {e}")
                
                # Suspendre après 3 échecs
                if billing.failed_attempts >= 3:
                    billing.status = 'paused'
                    billing.save()
                    logger.warning(f"Facturation récurrente {billing.id} suspendue après 3 échecs")
        
        return invoices
    
    @staticmethod
    def create_subscription_billing(user: User, subscription_type: str, frequency: str, amount: Decimal) -> RecurringBilling:
        """Crée une facturation récurrente pour un abonnement"""
        billing = RecurringBilling.objects.create(
            user=user,
            subscription_type=subscription_type,
            frequency=frequency,
            amount=amount,
            currency=user.country and 'XOF' or 'USD',  # Devise basée sur le pays
            start_date=timezone.now(),
            next_billing_date=timezone.now() + timedelta(days=30 if frequency == 'monthly' else 365),
            metadata={
                'created_from': 'subscription_upgrade',
                'original_subscription': user.subscription_type
            }
        )
        
        logger.info(f"Facturation récurrente créée pour {user.get_full_name()} - {subscription_type}")
        return billing
    
    @staticmethod
    def cancel_user_billings(user: User, reason: str = ''):
        """Annule toutes les facturations récurrentes d'un utilisateur"""
        active_billings = RecurringBilling.objects.filter(
            user=user,
            status='active'
        )
        
        count = active_billings.update(
            status='cancelled',
            end_date=timezone.now(),
            metadata={
                'cancellation_reason': reason,
                'cancelled_at': timezone.now().isoformat()
            }
        )
        
        logger.info(f"{count} facturations récurrentes annulées pour {user.get_full_name()}")
        return count


class BillingAutomationService:
    """Service principal d'automatisation de la facturation"""
    
    @staticmethod
    def run_daily_billing_tasks():
        """Exécute les tâches quotidiennes de facturation"""
        logger.info("Début des tâches quotidiennes de facturation")
        
        # Marquer les factures en retard
        overdue_count = InvoiceService.mark_overdue_invoices()
        
        # Traiter les facturations récurrentes
        new_invoices = RecurringBillingService.process_due_billings()
        
        logger.info(f"Tâches quotidiennes terminées: {overdue_count} factures en retard, {len(new_invoices)} nouvelles factures")
        
        return {
            'overdue_invoices': overdue_count,
            'new_recurring_invoices': len(new_invoices),
            'new_invoices': new_invoices
        }
    
    @staticmethod
    def run_monthly_royalty_calculation():
        """Calcule et génère les factures de royalties mensuelles"""
        logger.info("Début du calcul mensuel des royalties")
        
        # Période du mois précédent
        today = timezone.now().date()
        period_end = datetime.combine(today.replace(day=1), datetime.min.time()) - timedelta(days=1)
        period_start = datetime.combine(period_end.replace(day=1), datetime.min.time())
        
        # Récupérer tous les auteurs actifs
        authors = User.objects.filter(
            is_active=True,
            # Filtrer les utilisateurs qui ont des livres ou des transactions
        ).distinct()
        
        generated_invoices = []
        
        for author in authors:
            try:
                # Calculer les royalties
                royalties = RoyaltyService.calculate_author_royalties(author, period_start, period_end)
                
                if royalties:
                    # Générer la facture
                    invoice = RoyaltyService.generate_royalty_invoices(author, royalties)
                    if invoice:
                        generated_invoices.append(invoice)
                        
            except Exception as e:
                logger.error(f"Erreur lors du calcul des royalties pour {author.get_full_name()}: {e}")
        
        logger.info(f"Calcul mensuel des royalties terminé: {len(generated_invoices)} factures générées")
        
        return {
            'period_start': period_start,
            'period_end': period_end,
            'authors_processed': authors.count(),
            'invoices_generated': len(generated_invoices),
            'invoices': generated_invoices
        }