"""Signaux Django pour le système de facturation automatisé"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='shared_models.PaymentTransaction')
def handle_payment_transaction_created(sender, instance, created, **kwargs):
    """Traite les nouvelles transactions de paiement"""
    if created and instance.status == 'completed':
        try:
            from .billing_services import InvoiceService, RoyaltyService
            
            # Si c'est un paiement de facture, marquer la facture comme payée
            if hasattr(instance, 'metadata') and instance.metadata.get('invoice_id'):
                invoice_service = InvoiceService()
                invoice_service.mark_invoice_as_paid(
                    instance.metadata['invoice_id'],
                    instance.id
                )
                logger.info(f'Facture {instance.metadata["invoice_id"]} marquée comme payée')
            
            # Si c'est un achat de livre ou un abonnement, calculer les royalties
            if instance.transaction_type in ['book_purchase', 'subscription']:
                royalty_service = RoyaltyService()
                
                # Calculer les royalties pour les auteurs concernés
                if instance.transaction_type == 'book_purchase':
                    # Logique pour identifier le livre et l'auteur
                    book_id = instance.metadata.get('book_id') if instance.metadata else None
                    if book_id:
                        royalty_service.calculate_book_purchase_royalty(
                            book_id, instance.amount, instance.currency
                        )
                        logger.info(f'Royalty calculée pour l\'achat du livre {book_id}')
                
                elif instance.transaction_type == 'subscription':
                    # Calculer les royalties d'abonnement
                    royalty_service.calculate_subscription_royalties(
                        instance.user, instance.amount, instance.currency
                    )
                    logger.info(f'Royalties d\'abonnement calculées pour {instance.user.username}')
            
        except Exception as e:
            logger.error(f'Erreur lors du traitement de la transaction {instance.id}: {str(e)}')


@receiver(post_save, sender='shared_models.Invoice')
def handle_invoice_status_change(sender, instance, created, **kwargs):
    """Traite les changements de statut des factures"""
    try:
        from .billing_services import InvoiceService
        from .billing_tasks import send_invoice_email
        
        if created:
            # Nouvelle facture créée
            logger.info(f'Nouvelle facture créée: {instance.invoice_number}')
            
            # Envoyer l'email de facture si activé
            if getattr(settings, 'BILLING_EMAIL_ENABLED', True):
                send_invoice_email.delay(instance.id)
        
        else:
            # Facture mise à jour
            if instance.status == 'paid':
                logger.info(f'Facture {instance.invoice_number} marquée comme payée')
                
                # Traiter les actions post-paiement
                invoice_service = InvoiceService()
                invoice_service.process_post_payment_actions(instance)
            
            elif instance.status == 'overdue':
                logger.warning(f'Facture {instance.invoice_number} en retard')
                
                # Envoyer notification de retard
                from .billing_tasks import send_overdue_notification
                send_overdue_notification.delay(instance.id)
    
    except Exception as e:
        logger.error(f'Erreur lors du traitement de la facture {instance.id}: {str(e)}')


@receiver(post_save, sender='shared_models.AuthorRoyalty')
def handle_royalty_created(sender, instance, created, **kwargs):
    """Traite les nouvelles royalties d'auteur"""
    if created:
        try:
            logger.info(f'Nouvelle royalty créée pour {instance.author.username}: {instance.royalty_amount} {instance.currency}')
            
            # Envoyer notification à l'auteur
            if getattr(settings, 'BILLING_EMAIL_ENABLED', True):
                from .billing_tasks import send_royalty_notification
                send_royalty_notification.delay(instance.id)
            
            # Vérifier si l'auteur a atteint le seuil de paiement
            from .billing_services import RoyaltyService
            royalty_service = RoyaltyService()
            
            if royalty_service.should_process_author_payment(instance.author):
                logger.info(f'Seuil de paiement atteint pour {instance.author.username}')
                # Ici, on pourrait déclencher un processus de paiement automatique
        
        except Exception as e:
            logger.error(f'Erreur lors du traitement de la royalty {instance.id}: {str(e)}')


@receiver(post_save, sender='shared_models.RecurringBilling')
def handle_recurring_billing_change(sender, instance, created, **kwargs):
    """Traite les changements d'abonnements récurrents"""
    try:
        if created:
            logger.info(f'Nouvel abonnement récurrent créé pour {instance.user.username}')
            
            # Programmer la première facturation
            from .billing_services import RecurringBillingService
            recurring_service = RecurringBillingService()
            recurring_service.schedule_next_billing(instance)
        
        else:
            # Abonnement mis à jour
            if instance.status == 'cancelled':
                logger.info(f'Abonnement récurrent annulé pour {instance.user.username}')
                
                # Traiter l\'annulation
                from .billing_services import RecurringBillingService
                recurring_service = RecurringBillingService()
                recurring_service.process_cancellation(instance)
            
            elif instance.status == 'paused':
                logger.info(f'Abonnement récurrent mis en pause pour {instance.user.username}')
    
    except Exception as e:
        logger.error(f'Erreur lors du traitement de l\'abonnement récurrent {instance.id}: {str(e)}')


@receiver(pre_save, sender='shared_models.Invoice')
def update_invoice_due_date(sender, instance, **kwargs):
    """Met à jour automatiquement la date d'échéance des factures"""
    if not instance.due_date and instance.created_at:
        try:
            from .billing import BillingConfiguration
            
            # Récupérer les termes de paiement par défaut
            config = BillingConfiguration.objects.filter(
                config_type='payment_terms',
                config_key='default_due_days',
                is_active=True
            ).first()
            
            due_days = 30  # Valeur par défaut
            if config and 'days' in config.config_value:
                due_days = config.config_value['days']
            
            instance.due_date = (instance.created_at + timedelta(days=due_days)).date()
            
        except Exception as e:
            logger.error(f'Erreur lors du calcul de la date d\'échéance: {str(e)}')
            # Utiliser la valeur par défaut
            instance.due_date = (timezone.now() + timedelta(days=30)).date()


@receiver(pre_save, sender='shared_models.Invoice')
def calculate_invoice_totals(sender, instance, **kwargs):
    """Calcule automatiquement les totaux des factures"""
    try:
        if instance.pk:
            # Recalculer les totaux basés sur les items
            from django.db.models import Sum
            from .billing import InvoiceItem
            
            items_total = InvoiceItem.objects.filter(
                invoice=instance
            ).aggregate(
                total=Sum('total_price')
            )['total'] or 0
            
            instance.subtotal = items_total
            
            # Calculer les taxes
            if instance.tax_rate > 0:
                instance.tax_amount = instance.subtotal * (instance.tax_rate / 100)
            else:
                instance.tax_amount = 0
            
            # Calculer le total
            instance.total_amount = instance.subtotal + instance.tax_amount
    
    except Exception as e:
        logger.error(f'Erreur lors du calcul des totaux de la facture: {str(e)}')


@receiver(post_save, sender='shared_models.InvoiceItem')
def update_invoice_on_item_change(sender, instance, **kwargs):
    """Met à jour la facture quand un item change"""
    try:
        if instance.invoice:
            # Déclencher le recalcul des totaux
            instance.invoice.save()
    
    except Exception as e:
        logger.error(f'Erreur lors de la mise à jour de la facture: {str(e)}')


@receiver(post_delete, sender='shared_models.InvoiceItem')
def update_invoice_on_item_delete(sender, instance, **kwargs):
    """Met à jour la facture quand un item est supprimé"""
    try:
        if instance.invoice:
            # Déclencher le recalcul des totaux
            instance.invoice.save()
    
    except Exception as e:
        logger.error(f'Erreur lors de la mise à jour de la facture: {str(e)}')


@receiver(user_logged_in)
def check_user_billing_status(sender, request, user, **kwargs):
    """Vérifie le statut de facturation de l'utilisateur à la connexion"""
    try:
        from .billing import Invoice, AuthorRoyalty
        
        # Vérifier les factures en retard
        overdue_invoices = Invoice.objects.filter(
            user=user,
            status='overdue'
        ).count()
        
        if overdue_invoices > 0:
            logger.warning(f'Utilisateur {user.username} a {overdue_invoices} facture(s) en retard')
            # Ajouter un message dans la session
            if hasattr(request, 'session'):
                request.session['billing_overdue_count'] = overdue_invoices
        
        # Vérifier les royalties en attente pour les auteurs
        if hasattr(user, 'is_author') and user.is_author:
            pending_royalties = AuthorRoyalty.objects.filter(
                author=user,
                status='pending'
            ).count()
            
            if pending_royalties > 0:
                logger.info(f'Auteur {user.username} a {pending_royalties} royalty(ies) en attente')
                if hasattr(request, 'session'):
                    request.session['billing_pending_royalties'] = pending_royalties
    
    except Exception as e:
        logger.error(f'Erreur lors de la vérification du statut de facturation: {str(e)}')


@receiver(post_save, sender='shared_models.BillingConfiguration')
def handle_billing_config_change(sender, instance, **kwargs):
    """Traite les changements de configuration de facturation"""
    try:
        logger.info(f'Configuration de facturation mise à jour: {instance.config_type}.{instance.config_key}')
        
        # Invalider le cache de configuration
        from django.core.cache import cache
        cache_key = f'billing_config_{instance.config_type}_{instance.config_key}'
        cache.delete(cache_key)
        
        # Actions spécifiques selon le type de configuration
        if instance.config_type == 'tax_rate':
            logger.info('Taux de taxe mis à jour - recalcul des factures en attente recommandé')
        
        elif instance.config_type == 'royalty_rate':
            logger.info('Taux de royalty mis à jour - recalcul des royalties futures')
        
        elif instance.config_type == 'payment_terms':
            logger.info('Termes de paiement mis à jour - nouvelles factures affectées')
    
    except Exception as e:
        logger.error(f'Erreur lors du traitement du changement de configuration: {str(e)}')


# Signal personnalisé pour les événements de facturation
from django.dispatch import Signal

# Signaux personnalisés
invoice_paid = Signal()  # Envoyé quand une facture est payée
royalty_calculated = Signal()  # Envoyé quand une royalty est calculée
recurring_billing_processed = Signal()  # Envoyé quand un abonnement récurrent est traité
payment_failed = Signal()  # Envoyé quand un paiement échoue


@receiver(invoice_paid)
def handle_invoice_paid(sender, invoice, payment_transaction, **kwargs):
    """Traite les factures payées"""
    try:
        logger.info(f'Signal: Facture {invoice.invoice_number} payée')
        
        # Envoyer un email de confirmation
        from .billing_tasks import send_payment_confirmation
        send_payment_confirmation.delay(invoice.id, payment_transaction.id)
        
        # Traiter les actions post-paiement spécifiques
        if invoice.invoice_type == 'subscription':
            # Activer ou prolonger l'abonnement
            from .billing_services import RecurringBillingService
            recurring_service = RecurringBillingService()
            recurring_service.activate_subscription(invoice.user)
    
    except Exception as e:
        logger.error(f'Erreur lors du traitement du signal invoice_paid: {str(e)}')


@receiver(royalty_calculated)
def handle_royalty_calculated(sender, royalty, **kwargs):
    """Traite les royalties calculées"""
    try:
        logger.info(f'Signal: Royalty calculée pour {royalty.author.username}: {royalty.royalty_amount}')
        
        # Vérifier si l'auteur doit être payé
        from .billing_services import RoyaltyService
        royalty_service = RoyaltyService()
        
        if royalty_service.should_process_author_payment(royalty.author):
            # Déclencher le processus de paiement
            from .billing_tasks import process_author_payment
            process_author_payment.delay(royalty.author.id)
    
    except Exception as e:
        logger.error(f'Erreur lors du traitement du signal royalty_calculated: {str(e)}')


@receiver(payment_failed)
def handle_payment_failed(sender, invoice, error_message, **kwargs):
    """Traite les échecs de paiement"""
    try:
        logger.warning(f'Signal: Échec de paiement pour la facture {invoice.invoice_number}: {error_message}')
        
        # Marquer la facture comme échouée
        invoice.status = 'failed'
        invoice.save()
        
        # Envoyer une notification d'échec
        from .billing_tasks import send_payment_failed_notification
        send_payment_failed_notification.delay(invoice.id, error_message)
        
        # Programmer une nouvelle tentative si configuré
        from .billing_services import InvoiceService
        invoice_service = InvoiceService()
        invoice_service.schedule_payment_retry(invoice)
    
    except Exception as e:
        logger.error(f'Erreur lors du traitement du signal payment_failed: {str(e)}')


# Fonctions utilitaires pour déclencher les signaux
def trigger_invoice_paid(invoice, payment_transaction):
    """Déclenche le signal invoice_paid"""
    invoice_paid.send(
        sender=invoice.__class__,
        invoice=invoice,
        payment_transaction=payment_transaction
    )


def trigger_royalty_calculated(royalty):
    """Déclenche le signal royalty_calculated"""
    royalty_calculated.send(
        sender=royalty.__class__,
        royalty=royalty
    )


def trigger_payment_failed(invoice, error_message):
    """Déclenche le signal payment_failed"""
    payment_failed.send(
        sender=invoice.__class__,
        invoice=invoice,
        error_message=error_message
    )