# Système de géolocalisation et adaptation pour l'Afrique
# Implémente les recommandations pour la détection régionale et l'adaptation du contenu

import json
import requests
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class AfricanGeoLocation:
    """
    Service de géolocalisation spécialisé pour l'Afrique
    """
    
    # Mapping des pays africains avec leurs caractéristiques
    AFRICAN_COUNTRIES = {
        'SN': {
            'name': 'Sénégal',
            'region': 'west_africa',
            'currency': 'XOF',
            'languages': ['fr', 'wo'],
            'timezone': 'Africa/Dakar',
            'mobile_operators': ['orange', 'tigo', 'expresso'],
            'payment_methods': ['orange_money', 'wave'],
            'network_quality': '3g_dominant',
            'cdn_edge': 'dakar'
        },
        'CI': {
            'name': 'Côte d\'Ivoire',
            'region': 'west_africa',
            'currency': 'XOF',
            'languages': ['fr'],
            'timezone': 'Africa/Abidjan',
            'mobile_operators': ['orange', 'mtn', 'moov'],
            'payment_methods': ['orange_money', 'mtn_momo', 'wave'],
            'network_quality': '3g_4g_mixed',
            'cdn_edge': 'abidjan'
        },
        'NG': {
            'name': 'Nigeria',
            'region': 'west_africa',
            'currency': 'NGN',
            'languages': ['en', 'ha', 'ig', 'yo'],
            'timezone': 'Africa/Lagos',
            'mobile_operators': ['mtn', 'glo', 'airtel', '9mobile'],
            'payment_methods': ['mtn_momo', 'paystack', 'flutterwave'],
            'network_quality': '4g_dominant',
            'cdn_edge': 'lagos'
        },
        'GH': {
            'name': 'Ghana',
            'region': 'west_africa',
            'currency': 'GHS',
            'languages': ['en', 'ak', 'ee'],
            'timezone': 'Africa/Accra',
            'mobile_operators': ['mtn', 'vodafone', 'airteltigo'],
            'payment_methods': ['mtn_momo', 'vodafone_cash'],
            'network_quality': '3g_4g_mixed',
            'cdn_edge': 'accra'
        },
        'ML': {
            'name': 'Mali',
            'region': 'west_africa',
            'currency': 'XOF',
            'languages': ['fr', 'bm'],
            'timezone': 'Africa/Bamako',
            'mobile_operators': ['orange', 'malitel'],
            'payment_methods': ['orange_money'],
            'network_quality': '2g_3g_mixed',
            'cdn_edge': 'bamako'
        },
        'BF': {
            'name': 'Burkina Faso',
            'region': 'west_africa',
            'currency': 'XOF',
            'languages': ['fr', 'mo'],
            'timezone': 'Africa/Ouagadougou',
            'mobile_operators': ['orange', 'telmob'],
            'payment_methods': ['orange_money'],
            'network_quality': '2g_3g_mixed',
            'cdn_edge': 'ouagadougou'
        },
        'TG': {
            'name': 'Togo',
            'region': 'west_africa',
            'currency': 'XOF',
            'languages': ['fr', 'ee'],
            'timezone': 'Africa/Lome',
            'mobile_operators': ['togocel', 'moov'],
            'payment_methods': ['togocel_money', 'moov_money'],
            'network_quality': '2g_3g_mixed',
            'cdn_edge': 'lome'
        },
        'BJ': {
            'name': 'Bénin',
            'region': 'west_africa',
            'currency': 'XOF',
            'languages': ['fr', 'yo'],
            'timezone': 'Africa/Porto-Novo',
            'mobile_operators': ['mtn', 'moov'],
            'payment_methods': ['mtn_momo', 'moov_money'],
            'network_quality': '2g_3g_mixed',
            'cdn_edge': 'cotonou'
        },
        'CM': {
            'name': 'Cameroun',
            'region': 'central_africa',
            'currency': 'XAF',
            'languages': ['fr', 'en'],
            'timezone': 'Africa/Douala',
            'mobile_operators': ['mtn', 'orange'],
            'payment_methods': ['mtn_momo', 'orange_money'],
            'network_quality': '3g_4g_mixed',
            'cdn_edge': 'douala'
        },
        'CD': {
            'name': 'République Démocratique du Congo',
            'region': 'central_africa',
            'currency': 'CDF',
            'languages': ['fr', 'ln', 'kg', 'sw'],
            'timezone': 'Africa/Kinshasa',
            'mobile_operators': ['vodacom', 'airtel', 'orange'],
            'payment_methods': ['vodacom_mpesa', 'airtel_money'],
            'network_quality': '2g_3g_mixed',
            'cdn_edge': 'kinshasa'
        }
    }
    
    # Configuration des services de géolocalisation
    GEO_SERVICES = {
        'ipapi': {
            'url': 'http://ip-api.com/json/{ip}',
            'fields': 'status,country,countryCode,region,city,lat,lon,isp,org,as',
            'free_limit': 1000  # par heure
        },
        'ipinfo': {
            'url': 'https://ipinfo.io/{ip}/json',
            'requires_token': True,
            'free_limit': 50000  # par mois
        },
        'cloudflare': {
            'header': 'CF-IPCountry',
            'description': 'Cloudflare country header'
        }
    }
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'GEO_CACHE_TIMEOUT', 3600)  # 1 heure
        self.ipinfo_token = getattr(settings, 'IPINFO_TOKEN', None)
    
    def get_location_from_ip(self, ip_address: str) -> Optional[Dict]:
        """
        Obtient la localisation depuis une adresse IP
        """
        if not ip_address or ip_address in ['127.0.0.1', 'localhost']:
            return self._get_default_location()
        
        # Vérifier le cache
        cache_key = f"geo_location_{ip_address}"
        cached_location = cache.get(cache_key)
        if cached_location:
            return cached_location
        
        # Essayer différents services de géolocalisation
        location = None
        
        # 1. Essayer ip-api.com (gratuit, fiable)
        location = self._get_location_ipapi(ip_address)
        
        # 2. Fallback vers ipinfo.io si configuré
        if not location and self.ipinfo_token:
            location = self._get_location_ipinfo(ip_address)
        
        # 3. Fallback vers une localisation par défaut
        if not location:
            location = self._get_default_location()
        
        # Enrichir avec les données africaines
        if location:
            location = self._enrich_african_data(location)
            
            # Mettre en cache
            cache.set(cache_key, location, self.cache_timeout)
        
        return location
    
    def _get_location_ipapi(self, ip_address: str) -> Optional[Dict]:
        """
        Utilise ip-api.com pour la géolocalisation
        """
        try:
            url = self.GEO_SERVICES['ipapi']['url'].format(ip=ip_address)
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                return {
                    'country_code': data.get('countryCode'),
                    'country_name': data.get('country'),
                    'region': data.get('region'),
                    'city': data.get('city'),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                    'isp': data.get('isp'),
                    'organization': data.get('org'),
                    'source': 'ipapi'
                }
        except Exception as e:
            logger.warning(f"IP-API geolocation failed for {ip_address}: {e}")
        
        return None
    
    def _get_location_ipinfo(self, ip_address: str) -> Optional[Dict]:
        """
        Utilise ipinfo.io pour la géolocalisation
        """
        try:
            url = self.GEO_SERVICES['ipinfo']['url'].format(ip=ip_address)
            headers = {}
            if self.ipinfo_token:
                headers['Authorization'] = f'Bearer {self.ipinfo_token}'
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Parser les coordonnées
            lat, lon = None, None
            if 'loc' in data:
                try:
                    lat, lon = map(float, data['loc'].split(','))
                except ValueError:
                    pass
            
            return {
                'country_code': data.get('country'),
                'country_name': data.get('country'),  # ipinfo ne donne que le code
                'region': data.get('region'),
                'city': data.get('city'),
                'latitude': lat,
                'longitude': lon,
                'isp': data.get('org'),
                'organization': data.get('org'),
                'source': 'ipinfo'
            }
        except Exception as e:
            logger.warning(f"IPInfo geolocation failed for {ip_address}: {e}")
        
        return None
    
    def _get_default_location(self) -> Dict:
        """
        Retourne une localisation par défaut (Sénégal)
        """
        return {
            'country_code': 'SN',
            'country_name': 'Sénégal',
            'region': 'Dakar',
            'city': 'Dakar',
            'latitude': 14.6928,
            'longitude': -17.4467,
            'isp': 'Unknown',
            'organization': 'Unknown',
            'source': 'default'
        }
    
    def _enrich_african_data(self, location: Dict) -> Dict:
        """
        Enrichit les données de localisation avec les informations africaines
        """
        country_code = location.get('country_code')
        
        if country_code in self.AFRICAN_COUNTRIES:
            african_data = self.AFRICAN_COUNTRIES[country_code]
            location.update({
                'is_african': True,
                'african_region': african_data['region'],
                'currency': african_data['currency'],
                'languages': african_data['languages'],
                'timezone': african_data['timezone'],
                'mobile_operators': african_data['mobile_operators'],
                'payment_methods': african_data['payment_methods'],
                'network_quality': african_data['network_quality'],
                'cdn_edge': african_data['cdn_edge']
            })
        else:
            location.update({
                'is_african': False,
                'african_region': None
            })
        
        return location
    
    def get_location_from_request(self, request) -> Dict:
        """
        Extrait la localisation depuis une requête Django
        """
        # 1. Vérifier les headers Cloudflare
        cf_country = request.META.get('HTTP_CF_IPCOUNTRY')
        if cf_country and cf_country in self.AFRICAN_COUNTRIES:
            location = {
                'country_code': cf_country,
                'source': 'cloudflare_header'
            }
            return self._enrich_african_data(location)
        
        # 2. Obtenir l'IP réelle
        ip_address = self._get_real_ip(request)
        
        # 3. Géolocalisation par IP
        return self.get_location_from_ip(ip_address)
    
    def _get_real_ip(self, request) -> str:
        """
        Obtient l'adresse IP réelle depuis une requête
        """
        # Headers possibles pour l'IP réelle
        ip_headers = [
            'HTTP_CF_CONNECTING_IP',  # Cloudflare
            'HTTP_X_FORWARDED_FOR',   # Proxy standard
            'HTTP_X_REAL_IP',         # Nginx
            'HTTP_X_FORWARDED',
            'HTTP_X_CLUSTER_CLIENT_IP',
            'HTTP_FORWARDED_FOR',
            'HTTP_FORWARDED',
            'REMOTE_ADDR'
        ]
        
        for header in ip_headers:
            ip = request.META.get(header)
            if ip:
                # Prendre la première IP si plusieurs
                ip = ip.split(',')[0].strip()
                if self._is_valid_ip(ip):
                    return ip
        
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    def _is_valid_ip(self, ip: str) -> bool:
        """
        Valide une adresse IP
        """
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False
    
    def get_network_recommendations(self, location: Dict) -> Dict:
        """
        Retourne des recommandations réseau basées sur la localisation
        """
        if not location.get('is_african'):
            return {
                'compression': 'standard',
                'image_quality': 'high',
                'cache_strategy': 'normal',
                'cdn_edge': 'global'
            }
        
        network_quality = location.get('network_quality', '2g_3g_mixed')
        
        recommendations = {
            '2g_dominant': {
                'compression': 'aggressive',
                'image_quality': 'low',
                'cache_strategy': 'aggressive',
                'preload_strategy': 'minimal',
                'lazy_loading': True
            },
            '2g_3g_mixed': {
                'compression': 'high',
                'image_quality': 'medium',
                'cache_strategy': 'extended',
                'preload_strategy': 'selective',
                'lazy_loading': True
            },
            '3g_dominant': {
                'compression': 'moderate',
                'image_quality': 'medium',
                'cache_strategy': 'standard',
                'preload_strategy': 'moderate',
                'lazy_loading': False
            },
            '3g_4g_mixed': {
                'compression': 'light',
                'image_quality': 'high',
                'cache_strategy': 'standard',
                'preload_strategy': 'normal',
                'lazy_loading': False
            },
            '4g_dominant': {
                'compression': 'minimal',
                'image_quality': 'high',
                'cache_strategy': 'normal',
                'preload_strategy': 'full',
                'lazy_loading': False
            }
        }
        
        base_recommendations = recommendations.get(network_quality, recommendations['2g_3g_mixed'])
        base_recommendations['cdn_edge'] = location.get('cdn_edge', 'global')
        
        return base_recommendations
    
    def get_localization_preferences(self, location: Dict) -> Dict:
        """
        Retourne les préférences de localisation
        """
        if not location.get('is_african'):
            return {
                'language': 'en',
                'currency': 'USD',
                'timezone': 'UTC',
                'payment_methods': ['paypal', 'stripe']
            }
        
        country_code = location.get('country_code')
        african_data = self.AFRICAN_COUNTRIES.get(country_code, {})
        
        return {
            'language': african_data.get('languages', ['fr'])[0],
            'currency': african_data.get('currency', 'XOF'),
            'timezone': african_data.get('timezone', 'Africa/Dakar'),
            'payment_methods': african_data.get('payment_methods', ['orange_money']),
            'mobile_operators': african_data.get('mobile_operators', [])
        }
    
    def get_performance_targets(self, location: Dict) -> Dict:
        """
        Retourne les objectifs de performance selon la localisation
        """
        if not location.get('is_african'):
            return {
                'target_response_time_ms': 200,
                'target_page_load_ms': 1000,
                'target_image_load_ms': 500
            }
        
        network_quality = location.get('network_quality', '2g_3g_mixed')
        
        targets = {
            '2g_dominant': {
                'target_response_time_ms': 1000,
                'target_page_load_ms': 5000,
                'target_image_load_ms': 3000
            },
            '2g_3g_mixed': {
                'target_response_time_ms': 800,
                'target_page_load_ms': 4000,
                'target_image_load_ms': 2000
            },
            '3g_dominant': {
                'target_response_time_ms': 500,
                'target_page_load_ms': 3000,
                'target_image_load_ms': 1500
            },
            '3g_4g_mixed': {
                'target_response_time_ms': 400,
                'target_page_load_ms': 2000,
                'target_image_load_ms': 1000
            },
            '4g_dominant': {
                'target_response_time_ms': 300,
                'target_page_load_ms': 1500,
                'target_image_load_ms': 800
            }
        }
        
        return targets.get(network_quality, targets['3g_dominant'])


# Instance globale du service de géolocalisation
geo_service = AfricanGeoLocation()


# Fonctions utilitaires
def get_user_location(request) -> Dict:
    """
    Fonction utilitaire pour obtenir la localisation d'un utilisateur
    """
    return geo_service.get_location_from_request(request)


def is_african_user(request) -> bool:
    """
    Vérifie si l'utilisateur est en Afrique
    """
    location = get_user_location(request)
    return location.get('is_african', False)


def get_african_region(request) -> Optional[str]:
    """
    Retourne la région africaine de l'utilisateur
    """
    location = get_user_location(request)
    return location.get('african_region')


def get_network_quality(request) -> str:
    """
    Retourne la qualité réseau estimée
    """
    location = get_user_location(request)
    return location.get('network_quality', '3g_dominant')


def get_preferred_language(request) -> str:
    """
    Retourne la langue préférée selon la localisation
    """
    location = get_user_location(request)
    preferences = geo_service.get_localization_preferences(location)
    return preferences.get('language', 'fr')


def get_available_payment_methods(request) -> list:
    """
    Retourne les méthodes de paiement disponibles
    """
    location = get_user_location(request)
    preferences = geo_service.get_localization_preferences(location)
    return preferences.get('payment_methods', [])


def get_performance_targets(request) -> Dict:
    """
    Retourne les objectifs de performance pour l'utilisateur
    """
    location = get_user_location(request)
    return geo_service.get_performance_targets(location)


def get_network_recommendations(request) -> Dict:
    """
    Retourne les recommandations réseau pour l'utilisateur
    """
    location = get_user_location(request)
    return geo_service.get_network_recommendations(location)