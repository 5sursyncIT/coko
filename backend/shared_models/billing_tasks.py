"""Tâches automatisées pour le système de facturation Coko"""

from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import logging

from .billing_services import (
    BillingAutomationService, 
    InvoiceService, 
    RoyaltyService,
    RecurringBillingService
)
from .billing import Invoice, AuthorRoyalty, RecurringBilling
from .financial_reports import PaymentTransaction

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_daily_billing(self):
    """Tâche quotidienne de facturation"""
    try:
        logger.info("Début de la tâche quotidienne de facturation")
        
        result = BillingAutomationService.run_daily_billing_tasks()
        
        # Envoyer des notifications si nécessaire
        if result['overdue_invoices'] > 0:
            send_overdue_notifications.delay()
        
        logger.info(f"Tâche quotidienne terminée avec succès: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Erreur dans la tâche quotidienne de facturation: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)  # Retry après 5 minutes


@shared_task(bind=True, max_retries=3)
def process_monthly_royalties(self):
    """Tâche mensuelle de calcul des royalties"""
    try:
        logger.info("Début du calcul mensuel des royalties")
        
        result = BillingAutomationService.run_monthly_royalty_calculation()
        
        # Envoyer des notifications aux auteurs
        if result['invoices_generated'] > 0:
            notify_authors_royalties.delay(result['invoices'])
        
        logger.info(f"Calcul mensuel des royalties terminé: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Erreur dans le calcul mensuel des royalties: {exc}")
        raise self.retry(exc=exc, countdown=60 * 10)  # Retry après 10 minutes


@shared_task
def process_recurring_billing():
    """Traite les facturations récurrentes dues"""
    try:
        logger.info("Traitement des facturations récurrentes")
        
        invoices = RecurringBillingService.process_due_billings()
        
        # Envoyer les factures par email
        for invoice in invoices:
            send_invoice_email.delay(invoice.id)
        
        logger.info(f"{len(invoices)} factures récurrentes traitées")
        return {
            'processed_count': len(invoices),
            'invoice_ids': [str(inv.id) for inv in invoices]
        }
        
    except Exception as exc:
        logger.error(f"Erreur dans le traitement des facturations récurrentes: {exc}")
        raise exc


@shared_task
def calculate_author_royalties(author_id, period_start_str, period_end_str):
    """Calcule les royalties pour un auteur spécifique"""
    try:
        author = User.objects.get(id=author_id)
        period_start = datetime.fromisoformat(period_start_str)
        period_end = datetime.fromisoformat(period_end_str)
        
        logger.info(f"Calcul des royalties pour {author.get_full_name()}")
        
        royalties = RoyaltyService.calculate_author_royalties(author, period_start, period_end)
        
        if royalties:
            invoice = RoyaltyService.generate_royalty_invoices(author, royalties)
            if invoice:
                # Envoyer notification à l'auteur
                send_royalty_notification.delay(author.id, invoice.id)
                
                logger.info(f"Facture de royalties {invoice.invoice_number} créée pour {author.get_full_name()}")
                return {
                    'author_id': author_id,
                    'invoice_id': str(invoice.id),
                    'royalties_count': len(royalties),
                    'total_amount': str(invoice.total_amount)
                }
        
        logger.info(f"Aucune royalty à facturer pour {author.get_full_name()}")
        return {
            'author_id': author_id,
            'invoice_id': None,
            'royalties_count': 0,
            'total_amount': '0.00'
        }
        
    except User.DoesNotExist:
        logger.error(f"Auteur {author_id} non trouvé")
        raise
    except Exception as exc:
        logger.error(f"Erreur dans le calcul des royalties pour l'auteur {author_id}: {exc}")
        raise exc


@shared_task
def send_invoice_email(invoice_id):
    """Envoie une facture par email"""
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        
        subject = f"Facture {invoice.invoice_number} - Coko"
        
        if invoice.invoice_type == 'author_royalty':
            message = f"""
Bonjour {invoice.billing_name},

Votre facture de royalties est disponible.

Numéro de facture: {invoice.invoice_number}
Montant: {invoice.total_amount} {invoice.currency}
Date d'échéance: {invoice.due_date.strftime('%d/%m/%Y')}

Vous pouvez consulter le détail de vos royalties dans votre espace auteur.

Cordialement,
L'équipe Coko
"""
        else:
            message = f"""
Bonjour {invoice.billing_name},

Votre facture est disponible.

Numéro de facture: {invoice.invoice_number}
Type: {invoice.get_invoice_type_display()}
Montant: {invoice.total_amount} {invoice.currency}
Date d'échéance: {invoice.due_date.strftime('%d/%m/%Y')}

Cordialement,
L'équipe Coko
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invoice.billing_email],
            fail_silently=False
        )
        
        # Marquer la facture comme envoyée
        if invoice.status == 'draft':
            invoice.status = 'sent'
            invoice.save()
        
        logger.info(f"Facture {invoice.invoice_number} envoyée par email à {invoice.billing_email}")
        return True
        
    except Invoice.DoesNotExist:
        logger.error(f"Facture {invoice_id} non trouvée")
        return False
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi de la facture {invoice_id}: {exc}")
        raise exc


@shared_task
def send_overdue_notifications():
    """Envoie des notifications pour les factures en retard"""
    try:
        overdue_invoices = Invoice.objects.filter(status='overdue')
        
        sent_count = 0
        for invoice in overdue_invoices:
            subject = f"Facture en retard {invoice.invoice_number} - Coko"
            message = f"""
Bonjour {invoice.billing_name},

Votre facture est en retard de paiement.

Numéro de facture: {invoice.invoice_number}
Montant: {invoice.total_amount} {invoice.currency}
Date d'échéance: {invoice.due_date.strftime('%d/%m/%Y')}
Jours de retard: {invoice.days_overdue}

Merci de régulariser votre situation dans les plus brefs délais.

Cordialement,
L'équipe Coko
"""
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[invoice.billing_email],
                    fail_silently=False
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la notification de retard pour {invoice.invoice_number}: {e}")
        
        logger.info(f"{sent_count} notifications de retard envoyées")
        return sent_count
        
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi des notifications de retard: {exc}")
        raise exc


@shared_task
def send_royalty_notification(author_id, invoice_id):
    """Envoie une notification de royalties à un auteur"""
    try:
        author = User.objects.get(id=author_id)
        invoice = Invoice.objects.get(id=invoice_id)
        
        subject = f"Vos royalties sont disponibles - Coko"
        message = f"""
Bonjour {author.get_full_name()},

Vos royalties pour la période écoulée ont été calculées et sont maintenant disponibles.

Montant total: {invoice.total_amount} {invoice.currency}
Numéro de facture: {invoice.invoice_number}

Vous pouvez consulter le détail de vos royalties dans votre espace auteur.

Félicitations pour votre travail !

Cordialement,
L'équipe Coko
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[author.email],
            fail_silently=False
        )
        
        logger.info(f"Notification de royalties envoyée à {author.get_full_name()}")
        return True
        
    except (User.DoesNotExist, Invoice.DoesNotExist) as e:
        logger.error(f"Erreur: {e}")
        return False
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi de la notification de royalties: {exc}")
        raise exc


@shared_task
def notify_authors_royalties(invoice_ids):
    """Notifie plusieurs auteurs de leurs royalties"""
    try:
        sent_count = 0
        for invoice_id in invoice_ids:
            try:
                invoice = Invoice.objects.get(id=invoice_id)
                if invoice.invoice_type == 'author_royalty':
                    send_royalty_notification.delay(invoice.user.id, invoice_id)
                    sent_count += 1
            except Invoice.DoesNotExist:
                logger.error(f"Facture {invoice_id} non trouvée")
        
        logger.info(f"{sent_count} notifications de royalties programmées")
        return sent_count
        
    except Exception as exc:
        logger.error(f"Erreur lors de la notification des royalties: {exc}")
        raise exc


@shared_task
def cleanup_old_invoices():
    """Nettoie les anciennes factures (archivage)"""
    try:
        # Archiver les factures payées de plus de 2 ans
        cutoff_date = timezone.now() - timedelta(days=730)
        
        old_invoices = Invoice.objects.filter(
            status='paid',
            paid_date__lt=cutoff_date
        )
        
        # Dans un vrai système, on déplacerait vers un système d'archivage
        # Ici, on se contente de marquer comme archivées
        count = old_invoices.update(
            metadata={
                **{inv.metadata for inv in old_invoices},
                'archived_at': timezone.now().isoformat()
            }
        )
        
        logger.info(f"{count} factures anciennes marquées comme archivées")
        return count
        
    except Exception as exc:
        logger.error(f"Erreur lors du nettoyage des anciennes factures: {exc}")
        raise exc


@shared_task
def generate_billing_reports():
    """Génère les rapports de facturation périodiques"""
    try:
        # Statistiques générales
        stats = InvoiceService.get_invoice_statistics()
        
        # Statistiques par type d'utilisateur
        author_stats = InvoiceService.get_invoice_statistics(
            User.objects.filter(subscription_type='creator')
        )
        
        # Royalties en attente
        pending_royalties = AuthorRoyalty.objects.filter(
            status__in=['pending', 'calculated']
        ).count()
        
        # Facturations récurrentes actives
        active_recurring = RecurringBilling.objects.filter(
            status='active'
        ).count()
        
        report = {
            'generated_at': timezone.now().isoformat(),
            'general_stats': stats,
            'author_stats': author_stats,
            'pending_royalties': pending_royalties,
            'active_recurring_billings': active_recurring
        }
        
        logger.info(f"Rapport de facturation généré: {report}")
        return report
        
    except Exception as exc:
        logger.error(f"Erreur lors de la génération du rapport de facturation: {exc}")
        raise exc


@shared_task
def sync_payment_transactions():
    """Synchronise les transactions de paiement avec les factures"""
    try:
        # Trouver les transactions complétées sans facture
        transactions_without_invoice = PaymentTransaction.objects.filter(
            status='completed',
            invoice__isnull=True
        )
        
        created_count = 0
        for transaction in transactions_without_invoice:
            try:
                invoice = InvoiceService.create_invoice_from_transaction(transaction)
                if invoice:
                    created_count += 1
                    logger.info(f"Facture {invoice.invoice_number} créée pour la transaction {transaction.id}")
            except Exception as e:
                logger.error(f"Erreur lors de la création de facture pour la transaction {transaction.id}: {e}")
        
        logger.info(f"{created_count} factures créées à partir des transactions")
        return {
            'transactions_processed': transactions_without_invoice.count(),
            'invoices_created': created_count
        }
        
    except Exception as exc:
        logger.error(f"Erreur lors de la synchronisation des transactions: {exc}")
        raise exc