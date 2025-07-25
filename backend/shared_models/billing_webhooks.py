"""Webhooks pour le système de facturation Coko"""

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
from django.utils import timezone
import json
import hmac
import hashlib
import logging
from decimal import Decimal

from .billing import Invoice, RecurringBilling
from .billing_services import InvoiceService, RecurringBillingService
from .financial_reports import PaymentTransaction

logger = logging.getLogger(__name__)


class WebhookValidator:
    """Validateur pour les webhooks de paiement"""
    
    @staticmethod
    def validate_stripe_signature(payload, signature, secret):
        """Valide la signature Stripe"""
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Stripe envoie la signature avec le préfixe 'sha256='
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Erreur validation signature Stripe: {str(e)}")
            return False
    
    @staticmethod
    def validate_paypal_signature(payload, signature, secret):
        """Valide la signature PayPal"""
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Erreur validation signature PayPal: {str(e)}")
            return False
    
    @staticmethod
    def validate_orange_money_signature(payload, signature, secret):
        """Valide la signature Orange Money"""
        try:
            # Orange Money utilise généralement SHA-256
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Erreur validation signature Orange Money: {str(e)}")
            return False


@csrf_exempt
@require_http_methods(["POST"])
def payment_success_webhook(request):
    """Webhook pour les paiements réussis"""
    try:
        # Récupération des données
        payload = request.body
        signature = request.META.get('HTTP_X_SIGNATURE', '')
        provider = request.META.get('HTTP_X_PAYMENT_PROVIDER', 'unknown')
        
        # Validation de la signature selon le fournisseur
        is_valid = False
        if provider == 'stripe':
            secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
            is_valid = WebhookValidator.validate_stripe_signature(payload, signature, secret)
        elif provider == 'paypal':
            secret = getattr(settings, 'PAYPAL_WEBHOOK_SECRET', '')
            is_valid = WebhookValidator.validate_paypal_signature(payload, signature, secret)
        elif provider == 'orange_money':
            secret = getattr(settings, 'ORANGE_MONEY_WEBHOOK_SECRET', '')
            is_valid = WebhookValidator.validate_orange_money_signature(payload, signature, secret)
        
        if not is_valid:
            logger.warning(f"Signature webhook invalide pour {provider}")
            return HttpResponseBadRequest("Invalid signature")
        
        # Parsing des données JSON
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Données JSON invalides dans le webhook")
            return HttpResponseBadRequest("Invalid JSON")
        
        # Traitement selon le fournisseur
        if provider == 'stripe':
            result = _process_stripe_payment_success(data)
        elif provider == 'paypal':
            result = _process_paypal_payment_success(data)
        elif provider == 'orange_money':
            result = _process_orange_money_payment_success(data)
        else:
            logger.error(f"Fournisseur de paiement non supporté: {provider}")
            return HttpResponseBadRequest("Unsupported payment provider")
        
        if result:
            logger.info(f"Paiement traité avec succès pour {provider}")
            return HttpResponse("Payment processed successfully")
        else:
            logger.error(f"Erreur lors du traitement du paiement pour {provider}")
            return HttpResponseBadRequest("Payment processing failed")
    
    except Exception as e:
        logger.error(f"Erreur dans payment_success_webhook: {str(e)}")
        return HttpResponseBadRequest("Internal error")


@csrf_exempt
@require_http_methods(["POST"])
def payment_failed_webhook(request):
    """Webhook pour les paiements échoués"""
    try:
        payload = request.body
        signature = request.META.get('HTTP_X_SIGNATURE', '')
        provider = request.META.get('HTTP_X_PAYMENT_PROVIDER', 'unknown')
        
        # Validation de la signature
        is_valid = False
        if provider == 'stripe':
            secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
            is_valid = WebhookValidator.validate_stripe_signature(payload, signature, secret)
        elif provider == 'paypal':
            secret = getattr(settings, 'PAYPAL_WEBHOOK_SECRET', '')
            is_valid = WebhookValidator.validate_paypal_signature(payload, signature, secret)
        elif provider == 'orange_money':
            secret = getattr(settings, 'ORANGE_MONEY_WEBHOOK_SECRET', '')
            is_valid = WebhookValidator.validate_orange_money_signature(payload, signature, secret)
        
        if not is_valid:
            logger.warning(f"Signature webhook invalide pour {provider}")
            return HttpResponseBadRequest("Invalid signature")
        
        # Parsing des données
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")
        
        # Traitement de l'échec
        result = _process_payment_failure(data, provider)
        
        if result:
            return HttpResponse("Payment failure processed")
        else:
            return HttpResponseBadRequest("Failed to process payment failure")
    
    except Exception as e:
        logger.error(f"Erreur dans payment_failed_webhook: {str(e)}")
        return HttpResponseBadRequest("Internal error")


@csrf_exempt
@require_http_methods(["POST"])
def subscription_updated_webhook(request):
    """Webhook pour les mises à jour d'abonnement"""
    try:
        payload = request.body
        signature = request.META.get('HTTP_X_SIGNATURE', '')
        provider = request.META.get('HTTP_X_PAYMENT_PROVIDER', 'unknown')
        
        # Validation de la signature
        is_valid = False
        if provider == 'stripe':
            secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
            is_valid = WebhookValidator.validate_stripe_signature(payload, signature, secret)
        
        if not is_valid:
            return HttpResponseBadRequest("Invalid signature")
        
        # Parsing des données
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")
        
        # Traitement de la mise à jour d'abonnement
        result = _process_subscription_update(data, provider)
        
        if result:
            return HttpResponse("Subscription update processed")
        else:
            return HttpResponseBadRequest("Failed to process subscription update")
    
    except Exception as e:
        logger.error(f"Erreur dans subscription_updated_webhook: {str(e)}")
        return HttpResponseBadRequest("Internal error")


def _process_stripe_payment_success(data):
    """Traite un paiement Stripe réussi"""
    try:
        event_type = data.get('type')
        
        if event_type == 'payment_intent.succeeded':
            payment_intent = data['data']['object']
            
            # Récupération des métadonnées
            metadata = payment_intent.get('metadata', {})
            invoice_id = metadata.get('invoice_id')
            transaction_id = metadata.get('transaction_id')
            
            if invoice_id:
                # Mise à jour de la facture
                try:
                    invoice = Invoice.objects.get(id=invoice_id)
                    invoice.mark_as_paid()
                    
                    # Création/mise à jour de la transaction
                    if transaction_id:
                        transaction = PaymentTransaction.objects.filter(id=transaction_id).first()
                        if transaction:
                            transaction.mark_as_completed()
                    
                    logger.info(f"Facture {invoice.invoice_number} marquée comme payée via Stripe")
                    return True
                    
                except Invoice.DoesNotExist:
                    logger.error(f"Facture {invoice_id} non trouvée pour le paiement Stripe")
                    return False
        
        elif event_type == 'invoice.payment_succeeded':
            # Paiement d'abonnement récurrent
            stripe_invoice = data['data']['object']
            subscription_id = stripe_invoice.get('subscription')
            
            if subscription_id:
                # Mise à jour de la facturation récurrente
                recurring_billing = RecurringBilling.objects.filter(
                    metadata__stripe_subscription_id=subscription_id
                ).first()
                
                if recurring_billing:
                    # Créer une nouvelle facture pour ce cycle
                    invoice = RecurringBillingService.create_invoice_from_recurring(
                        recurring_billing
                    )
                    if invoice:
                        invoice.mark_as_paid()
                        recurring_billing.completed_cycles += 1
                        recurring_billing.last_billing_date = timezone.now()
                        recurring_billing.next_billing_date = recurring_billing.calculate_next_billing_date()
                        recurring_billing.save()
                        
                        logger.info(f"Facturation récurrente traitée pour {recurring_billing.user.email}")
                        return True
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur traitement paiement Stripe: {str(e)}")
        return False


def _process_paypal_payment_success(data):
    """Traite un paiement PayPal réussi"""
    try:
        event_type = data.get('event_type')
        
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            resource = data['resource']
            
            # Récupération des informations de paiement
            custom_id = resource.get('custom_id')  # Notre invoice_id
            amount = Decimal(resource['amount']['value'])
            currency = resource['amount']['currency_code']
            
            if custom_id:
                try:
                    invoice = Invoice.objects.get(id=custom_id)
                    
                    # Vérification du montant
                    if invoice.total_amount == amount and invoice.currency == currency:
                        invoice.mark_as_paid()
                        logger.info(f"Facture {invoice.invoice_number} payée via PayPal")
                        return True
                    else:
                        logger.warning(f"Montant PayPal incorrect pour facture {invoice.invoice_number}")
                        return False
                        
                except Invoice.DoesNotExist:
                    logger.error(f"Facture {custom_id} non trouvée pour paiement PayPal")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur traitement paiement PayPal: {str(e)}")
        return False


def _process_orange_money_payment_success(data):
    """Traite un paiement Orange Money réussi"""
    try:
        # Orange Money structure (peut varier selon l'API)
        transaction_id = data.get('transaction_id')
        reference = data.get('reference')  # Notre invoice_id
        amount = Decimal(str(data.get('amount', '0')))
        currency = data.get('currency', 'XOF')
        status = data.get('status')
        
        if status == 'SUCCESS' and reference:
            try:
                invoice = Invoice.objects.get(id=reference)
                
                # Vérification du montant (conversion si nécessaire)
                if invoice.total_amount == amount and invoice.currency == currency:
                    invoice.mark_as_paid()
                    
                    # Enregistrement de la transaction
                    PaymentTransaction.objects.create(
                        user=invoice.user,
                        amount=amount,
                        currency=currency,
                        transaction_type='subscription',  # ou autre selon le contexte
                        status='completed',
                        payment_provider='orange_money',
                        provider_transaction_id=transaction_id,
                        metadata={
                            'invoice_id': str(invoice.id),
                            'orange_money_transaction_id': transaction_id
                        }
                    )
                    
                    logger.info(f"Facture {invoice.invoice_number} payée via Orange Money")
                    return True
                else:
                    logger.warning(f"Montant Orange Money incorrect pour facture {invoice.invoice_number}")
                    return False
                    
            except Invoice.DoesNotExist:
                logger.error(f"Facture {reference} non trouvée pour paiement Orange Money")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur traitement paiement Orange Money: {str(e)}")
        return False


def _process_payment_failure(data, provider):
    """Traite un échec de paiement"""
    try:
        if provider == 'stripe':
            event_type = data.get('type')
            
            if event_type == 'payment_intent.payment_failed':
                payment_intent = data['data']['object']
                metadata = payment_intent.get('metadata', {})
                invoice_id = metadata.get('invoice_id')
                
                if invoice_id:
                    try:
                        invoice = Invoice.objects.get(id=invoice_id)
                        # Marquer comme en échec ou en retard
                        if invoice.status == 'pending':
                            invoice.status = 'overdue'
                            invoice.save()
                        
                        logger.info(f"Échec de paiement traité pour facture {invoice.invoice_number}")
                        return True
                        
                    except Invoice.DoesNotExist:
                        logger.error(f"Facture {invoice_id} non trouvée pour échec Stripe")
                        return False
            
            elif event_type == 'invoice.payment_failed':
                # Échec de paiement d'abonnement
                stripe_invoice = data['data']['object']
                subscription_id = stripe_invoice.get('subscription')
                
                if subscription_id:
                    recurring_billing = RecurringBilling.objects.filter(
                        metadata__stripe_subscription_id=subscription_id
                    ).first()
                    
                    if recurring_billing:
                        recurring_billing.failed_attempts += 1
                        
                        # Suspendre après 3 échecs
                        if recurring_billing.failed_attempts >= 3:
                            recurring_billing.status = 'paused'
                        
                        recurring_billing.save()
                        
                        logger.info(f"Échec facturation récurrente pour {recurring_billing.user.email}")
                        return True
        
        elif provider == 'paypal':
            # Traitement des échecs PayPal
            event_type = data.get('event_type')
            
            if event_type == 'PAYMENT.CAPTURE.DENIED':
                resource = data['resource']
                custom_id = resource.get('custom_id')
                
                if custom_id:
                    try:
                        invoice = Invoice.objects.get(id=custom_id)
                        invoice.status = 'overdue'
                        invoice.save()
                        
                        logger.info(f"Échec PayPal traité pour facture {invoice.invoice_number}")
                        return True
                        
                    except Invoice.DoesNotExist:
                        logger.error(f"Facture {custom_id} non trouvée pour échec PayPal")
                        return False
        
        elif provider == 'orange_money':
            # Traitement des échecs Orange Money
            reference = data.get('reference')
            status = data.get('status')
            
            if status == 'FAILED' and reference:
                try:
                    invoice = Invoice.objects.get(id=reference)
                    invoice.status = 'overdue'
                    invoice.save()
                    
                    logger.info(f"Échec Orange Money traité pour facture {invoice.invoice_number}")
                    return True
                    
                except Invoice.DoesNotExist:
                    logger.error(f"Facture {reference} non trouvée pour échec Orange Money")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur traitement échec de paiement: {str(e)}")
        return False


def _process_subscription_update(data, provider):
    """Traite une mise à jour d'abonnement"""
    try:
        if provider == 'stripe':
            event_type = data.get('type')
            
            if event_type == 'customer.subscription.updated':
                subscription = data['data']['object']
                subscription_id = subscription['id']
                status = subscription['status']
                
                # Mise à jour de la facturation récurrente
                recurring_billing = RecurringBilling.objects.filter(
                    metadata__stripe_subscription_id=subscription_id
                ).first()
                
                if recurring_billing:
                    if status == 'active':
                        recurring_billing.status = 'active'
                    elif status == 'canceled':
                        recurring_billing.status = 'cancelled'
                        recurring_billing.end_date = timezone.now()
                    elif status == 'past_due':
                        recurring_billing.status = 'paused'
                    
                    recurring_billing.save()
                    
                    logger.info(f"Abonnement mis à jour pour {recurring_billing.user.email}")
                    return True
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur traitement mise à jour abonnement: {str(e)}")
        return False