# Système de paiements mobiles africains
# Implémente les recommandations pour Orange Money, MTN MoMo, Wave, etc.

import json
import requests
import hashlib
import hmac
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class AfricanPaymentError(Exception):
    """Exception pour les erreurs de paiement africain"""
    pass

class BaseAfricanPaymentProvider:
    """
    Classe de base pour tous les fournisseurs de paiement africains
    """
    
    def __init__(self, config):
        self.config = config
        self.validate_config()
    
    def validate_config(self):
        """Valide la configuration du fournisseur"""
        required_fields = self.get_required_config_fields()
        for field in required_fields:
            if field not in self.config:
                raise ImproperlyConfigured(f"Missing {field} in payment config")
    
    def get_required_config_fields(self):
        """Retourne les champs de configuration requis"""
        return ['api_key', 'merchant_id']
    
    def initiate_payment(self, amount, phone_number, reference, callback_url=None):
        """Initie un paiement"""
        raise NotImplementedError
    
    def check_payment_status(self, transaction_id):
        """Vérifie le statut d'un paiement"""
        raise NotImplementedError
    
    def process_callback(self, callback_data):
        """Traite un callback de paiement"""
        raise NotImplementedError


class OrangeMoneyProvider(BaseAfricanPaymentProvider):
    """
    Fournisseur Orange Money pour l'Afrique de l'Ouest
    """
    
    def __init__(self, config):
        self.base_url = config.get('base_url', 'https://api.orange.com/orange-money-webpay/dev/v1')
        super().__init__(config)
    
    def get_required_config_fields(self):
        return ['api_key', 'merchant_id', 'client_secret']
    
    def get_access_token(self):
        """Obtient un token d'accès OAuth2"""
        auth_url = f"{self.base_url}/oauth/token"
        
        headers = {
            'Authorization': f"Basic {self.config['api_key']}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(auth_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            return response.json()['access_token']
        except requests.RequestException as e:
            logger.error(f"Orange Money auth error: {e}")
            raise AfricanPaymentError(f"Authentication failed: {e}")
    
    def initiate_payment(self, amount, phone_number, reference, callback_url=None):
        """Initie un paiement Orange Money"""
        token = self.get_access_token()
        
        # Formater le numéro de téléphone (format international)
        if not phone_number.startswith('+'):
            # Ajouter le code pays selon la région
            country_codes = {
                'senegal': '+221',
                'cote_ivoire': '+225',
                'mali': '+223',
                'burkina_faso': '+226'
            }
            # Par défaut Sénégal si pas spécifié
            phone_number = country_codes.get('senegal', '+221') + phone_number
        
        payment_url = f"{self.base_url}/webpayment"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'merchant_key': self.config['merchant_id'],
            'currency': 'XOF',  # Franc CFA
            'order_id': reference,
            'amount': int(amount * 100),  # Convertir en centimes
            'return_url': callback_url or settings.PAYMENT_CALLBACK_URL,
            'cancel_url': callback_url or settings.PAYMENT_CALLBACK_URL,
            'notif_url': callback_url or settings.PAYMENT_CALLBACK_URL,
            'lang': 'fr',
            'reference': reference
        }
        
        try:
            response = requests.post(payment_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return {
                'transaction_id': result.get('pay_token'),
                'payment_url': result.get('payment_url'),
                'status': 'initiated',
                'provider': 'orange_money'
            }
        except requests.RequestException as e:
            logger.error(f"Orange Money payment initiation error: {e}")
            raise AfricanPaymentError(f"Payment initiation failed: {e}")
    
    def check_payment_status(self, transaction_id):
        """Vérifie le statut d'un paiement Orange Money"""
        token = self.get_access_token()
        
        status_url = f"{self.base_url}/webpayment/{transaction_id}"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(status_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Mapper les statuts Orange Money vers nos statuts
            status_mapping = {
                'SUCCESS': 'completed',
                'PENDING': 'pending',
                'FAILED': 'failed',
                'EXPIRED': 'expired'
            }
            
            return {
                'status': status_mapping.get(result.get('status'), 'unknown'),
                'transaction_id': transaction_id,
                'amount': result.get('amount', 0) / 100,
                'currency': 'XOF',
                'provider': 'orange_money'
            }
        except requests.RequestException as e:
            logger.error(f"Orange Money status check error: {e}")
            raise AfricanPaymentError(f"Status check failed: {e}")


class MTNMoMoProvider(BaseAfricanPaymentProvider):
    """
    Fournisseur MTN Mobile Money
    """
    
    def __init__(self, config):
        self.base_url = config.get('base_url', 'https://sandbox.momodeveloper.mtn.com')
        super().__init__(config)
    
    def get_required_config_fields(self):
        return ['api_key', 'user_id', 'subscription_key']
    
    def get_access_token(self):
        """Obtient un token d'accès MTN MoMo"""
        auth_url = f"{self.base_url}/collection/token/"
        
        headers = {
            'Authorization': f"Basic {self.config['api_key']}",
            'Ocp-Apim-Subscription-Key': self.config['subscription_key']
        }
        
        try:
            response = requests.post(auth_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()['access_token']
        except requests.RequestException as e:
            logger.error(f"MTN MoMo auth error: {e}")
            raise AfricanPaymentError(f"Authentication failed: {e}")
    
    def initiate_payment(self, amount, phone_number, reference, callback_url=None):
        """Initie un paiement MTN MoMo"""
        token = self.get_access_token()
        
        payment_url = f"{self.base_url}/collection/v1_0/requesttopay"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Reference-Id': reference,
            'X-Target-Environment': self.config.get('environment', 'sandbox'),
            'Ocp-Apim-Subscription-Key': self.config['subscription_key'],
            'Content-Type': 'application/json'
        }
        
        payload = {
            'amount': str(amount),
            'currency': 'XOF',
            'externalId': reference,
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': phone_number.replace('+', '')
            },
            'payerMessage': 'Paiement Coko',
            'payeeNote': f'Commande {reference}'
        }
        
        try:
            response = requests.post(payment_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            return {
                'transaction_id': reference,
                'status': 'initiated',
                'provider': 'mtn_momo'
            }
        except requests.RequestException as e:
            logger.error(f"MTN MoMo payment initiation error: {e}")
            raise AfricanPaymentError(f"Payment initiation failed: {e}")


class WaveProvider(BaseAfricanPaymentProvider):
    """
    Fournisseur Wave (Sénégal, Côte d'Ivoire)
    """
    
    def __init__(self, config):
        self.base_url = config.get('base_url', 'https://api.wave.com/v1')
        super().__init__(config)
    
    def get_required_config_fields(self):
        return ['api_key', 'secret_key']
    
    def generate_signature(self, payload):
        """Génère une signature HMAC pour Wave"""
        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.config['secret_key'].encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def initiate_payment(self, amount, phone_number, reference, callback_url=None):
        """Initie un paiement Wave"""
        payment_url = f"{self.base_url}/checkout/sessions"
        
        payload = {
            'amount': int(amount * 100),  # Centimes
            'currency': 'XOF',
            'error_url': callback_url or settings.PAYMENT_CALLBACK_URL,
            'success_url': callback_url or settings.PAYMENT_CALLBACK_URL,
            'checkout_intent': 'web_payment',
            'client_reference': reference
        }
        
        headers = {
            'Authorization': f'Bearer {self.config["api_key"]}',
            'Content-Type': 'application/json',
            'X-Wave-Signature': self.generate_signature(payload)
        }
        
        try:
            response = requests.post(payment_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return {
                'transaction_id': result.get('id'),
                'payment_url': result.get('wave_launch_url'),
                'status': 'initiated',
                'provider': 'wave'
            }
        except requests.RequestException as e:
            logger.error(f"Wave payment initiation error: {e}")
            raise AfricanPaymentError(f"Payment initiation failed: {e}")


class AfricanPaymentManager:
    """
    Gestionnaire principal pour tous les paiements mobiles africains
    """
    
    def __init__(self):
        self.providers = {}
        self.load_providers()
    
    def load_providers(self):
        """Charge les fournisseurs de paiement depuis les settings"""
        payment_config = getattr(settings, 'AFRICAN_PAYMENTS', {})
        
        if 'orange_money' in payment_config:
            self.providers['orange_money'] = OrangeMoneyProvider(payment_config['orange_money'])
        
        if 'mtn_momo' in payment_config:
            self.providers['mtn_momo'] = MTNMoMoProvider(payment_config['mtn_momo'])
        
        if 'wave' in payment_config:
            self.providers['wave'] = WaveProvider(payment_config['wave'])
    
    def get_available_providers(self, country_code=None):
        """Retourne les fournisseurs disponibles pour un pays"""
        if not country_code:
            return list(self.providers.keys())
        
        # Mapping des fournisseurs par pays
        country_providers = {
            'SN': ['orange_money', 'wave'],  # Sénégal
            'CI': ['orange_money', 'mtn_momo', 'wave'],  # Côte d'Ivoire
            'ML': ['orange_money', 'mtn_momo'],  # Mali
            'BF': ['orange_money', 'mtn_momo'],  # Burkina Faso
            'NG': ['mtn_momo'],  # Nigeria
            'GH': ['mtn_momo'],  # Ghana
        }
        
        available = country_providers.get(country_code, [])
        return [p for p in available if p in self.providers]
    
    def initiate_payment(self, provider_name, amount, phone_number, reference, callback_url=None):
        """Initie un paiement avec le fournisseur spécifié"""
        if provider_name not in self.providers:
            raise AfricanPaymentError(f"Provider {provider_name} not available")
        
        provider = self.providers[provider_name]
        
        try:
            result = provider.initiate_payment(amount, phone_number, reference, callback_url)
            
            # Log du paiement initié
            logger.info(
                f"Payment initiated: {provider_name}, amount: {amount}, "
                f"phone: {phone_number}, ref: {reference}"
            )
            
            return result
        except Exception as e:
            logger.error(f"Payment initiation failed: {e}")
            raise
    
    def check_payment_status(self, provider_name, transaction_id):
        """Vérifie le statut d'un paiement"""
        if provider_name not in self.providers:
            raise AfricanPaymentError(f"Provider {provider_name} not available")
        
        provider = self.providers[provider_name]
        return provider.check_payment_status(transaction_id)
    
    def get_payment_statistics(self):
        """Retourne les statistiques de paiement"""
        # Cette méthode pourrait être étendue pour récupérer
        # des statistiques depuis la base de données
        return {
            'available_providers': list(self.providers.keys()),
            'total_providers': len(self.providers),
            'supported_countries': ['SN', 'CI', 'ML', 'BF', 'NG', 'GH'],
            'supported_currencies': ['XOF', 'NGN', 'GHS']
        }


# Instance globale du gestionnaire de paiements
payment_manager = AfricanPaymentManager()


# Fonctions utilitaires
def detect_phone_country(phone_number):
    """Détecte le pays depuis un numéro de téléphone"""
    phone = phone_number.replace('+', '').replace(' ', '')
    
    country_codes = {
        '221': 'SN',  # Sénégal
        '225': 'CI',  # Côte d'Ivoire
        '223': 'ML',  # Mali
        '226': 'BF',  # Burkina Faso
        '234': 'NG',  # Nigeria
        '233': 'GH',  # Ghana
    }
    
    for code, country in country_codes.items():
        if phone.startswith(code):
            return country
    
    return None


def format_african_currency(amount, currency='XOF'):
    """Formate une devise africaine"""
    if currency == 'XOF':
        return f"{amount:,.0f} FCFA"
    elif currency == 'NGN':
        return f"₦{amount:,.2f}"
    elif currency == 'GHS':
        return f"GH₵{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def validate_african_phone(phone_number):
    """Valide un numéro de téléphone africain"""
    phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
    
    # Vérifier la longueur (8-15 chiffres)
    if not phone.isdigit() or len(phone) < 8 or len(phone) > 15:
        return False
    
    # Vérifier les codes pays africains
    african_codes = ['221', '225', '223', '226', '234', '233']
    
    for code in african_codes:
        if phone.startswith(code):
            return True
    
    return False