# Middleware spécialisé pour les optimisations africaines
# Implémente les recommandations du fichier RECOMMENDATIONS.md

import json
import time
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class AfricanNetworkOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser l'expérience utilisateur selon les conditions réseau africaines
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Détecter la qualité du réseau depuis les headers
        network_quality = self.detect_network_quality(request)
        request.network_quality = network_quality
        
        # Adapter le contenu selon la qualité réseau
        if network_quality in ['2g', 'slow-2g']:
            request.lightweight_mode = True
            request.image_quality = 'low'
        elif network_quality == '3g':
            request.lightweight_mode = False
            request.image_quality = 'medium'
        else:
            request.lightweight_mode = False
            request.image_quality = 'high'
        
        # Géolocalisation africaine
        request.african_region = self.detect_african_region(request)
        
        return None
    
    def process_response(self, request, response):
        # Ajouter headers d'optimisation
        if hasattr(request, 'network_quality'):
            response['X-Network-Quality'] = request.network_quality
            response['X-African-Region'] = getattr(request, 'african_region', 'unknown')
        
        # Compression adaptative
        if hasattr(request, 'lightweight_mode') and request.lightweight_mode:
            response['X-Content-Optimized'] = 'african-2g'
        
        return response
    
    def detect_network_quality(self, request):
        """
        Détecte la qualité du réseau depuis les headers du navigateur
        """
        # Header standard pour la qualité réseau
        network_info = request.META.get('HTTP_DOWNLINK', '')
        connection_type = request.META.get('HTTP_CONNECTION_TYPE', '')
        
        # Détection basée sur User-Agent (approximative)
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'opera mini' in user_agent or 'ucweb' in user_agent:
            return '2g'  # Navigateurs optimisés pour réseaux lents
        
        # Détection par IP (si base de données géo disponible)
        # Ici on pourrait intégrer une détection plus sophistiquée
        
        return '4g'  # Par défaut
    
    def detect_african_region(self, request):
        """
        Détecte la région africaine de l'utilisateur
        """
        # Récupérer depuis les headers ou la session
        region = request.META.get('HTTP_CF_IPCOUNTRY', '')  # Cloudflare
        
        african_countries = {
            'SN': 'senegal',
            'CI': 'cote_ivoire', 
            'NG': 'nigeria',
            'GH': 'ghana',
            'ML': 'mali',
            'BF': 'burkina_faso',
            'TG': 'togo',
            'BJ': 'benin',
            'CM': 'cameroon',
            'CD': 'congo_drc'
        }
        
        return african_countries.get(region, 'west_africa')


class AfricanPerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware pour surveiller les performances spécifiques aux conditions africaines
    """
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            response_time = (time.time() - request.start_time) * 1000  # en ms
            
            # Log si le temps de réponse dépasse l'objectif africain (500ms)
            if response_time > 500:
                logger.warning(
                    f"Slow response for African user: {response_time:.2f}ms "
                    f"for {request.path} from {request.META.get('REMOTE_ADDR')}"
                )
            
            # Ajouter header de performance
            response['X-Response-Time'] = f"{response_time:.2f}ms"
            
            # Métriques pour monitoring
            self.record_african_metrics(request, response_time)
        
        return response
    
    def record_african_metrics(self, request, response_time):
        """
        Enregistre les métriques spécifiques à l'Afrique
        """
        try:
            # Utiliser le cache pour stocker les métriques temporairement
            cache_key = f"african_metrics_{int(time.time() // 60)}"  # Par minute
            metrics = cache.get(cache_key, {
                'total_requests': 0,
                'slow_requests': 0,
                'avg_response_time': 0,
                'network_quality_stats': {}
            })
            
            metrics['total_requests'] += 1
            if response_time > 500:
                metrics['slow_requests'] += 1
            
            # Moyenne mobile du temps de réponse
            current_avg = metrics['avg_response_time']
            total = metrics['total_requests']
            metrics['avg_response_time'] = ((current_avg * (total - 1)) + response_time) / total
            
            # Stats par qualité réseau
            network_quality = getattr(request, 'network_quality', 'unknown')
            if network_quality not in metrics['network_quality_stats']:
                metrics['network_quality_stats'][network_quality] = 0
            metrics['network_quality_stats'][network_quality] += 1
            
            cache.set(cache_key, metrics, 300)  # 5 minutes
            
        except Exception as e:
            logger.error(f"Error recording African metrics: {e}")


class AfricanCompressionMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser la compression selon les recommandations africaines
    """
    
    def process_response(self, request, response):
        # Forcer la compression pour les réseaux lents
        if hasattr(request, 'network_quality'):
            if request.network_quality in ['2g', '3g', 'slow-2g']:
                # Ajouter headers pour forcer la compression
                response['Vary'] = 'Accept-Encoding'
                
                # Recommander la compression côté client
                if 'gzip' not in response.get('Content-Encoding', ''):
                    response['X-Compression-Recommended'] = 'gzip,br'
        
        return response


class AfricanCacheOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware pour optimiser le cache selon les conditions africaines
    """
    
    def process_response(self, request, response):
        # Cache plus agressif pour les utilisateurs africains
        if hasattr(request, 'african_region') and request.african_region != 'unknown':
            # Cache plus long pour le contenu statique
            if request.path.startswith('/static/') or request.path.startswith('/media/'):
                response['Cache-Control'] = 'public, max-age=86400'  # 24h
            
            # Cache API pour réduire les requêtes
            elif request.path.startswith('/api/'):
                if request.method == 'GET':
                    response['Cache-Control'] = 'public, max-age=300'  # 5min
        
        return response


class AfricanOfflineSupportMiddleware(MiddlewareMixin):
    """
    Middleware pour supporter le mode offline selon les recommandations PWA
    """
    
    def process_response(self, request, response):
        # Ajouter headers PWA pour le mode offline
        if request.path == '/' or request.path.startswith('/app/'):
            response['X-PWA-Enabled'] = 'true'
            response['X-Offline-Support'] = 'available'
        
        # Service Worker headers
        if request.path.endswith('sw.js'):
            response['Cache-Control'] = 'no-cache'
            response['Service-Worker-Allowed'] = '/'
        
        return response


class AfricanLanguageMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer les langues africaines
    """
    
    def process_request(self, request):
        # Détecter la langue préférée selon la région
        african_region = getattr(request, 'african_region', None)
        
        language_mapping = {
            'senegal': 'fr',
            'cote_ivoire': 'fr',
            'nigeria': 'en',
            'ghana': 'en',
            'mali': 'fr',
            'burkina_faso': 'fr'
        }
        
        if african_region in language_mapping:
            preferred_lang = language_mapping[african_region]
            if not request.session.get('django_language'):
                request.session['django_language'] = preferred_lang
        
        return None


class AfricanSecurityMiddleware(MiddlewareMixin):
    """
    Middleware de sécurité adapté aux conditions africaines
    """
    
    def process_response(self, request, response):
        # Headers de sécurité adaptés
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # CSP adapté pour les CDN africains
        if hasattr(settings, 'CDN_URL') and settings.CDN_URL:
            csp = f"default-src 'self' {settings.CDN_URL}; script-src 'self' 'unsafe-inline'"
            response['Content-Security-Policy'] = csp
        
        return response


# Fonction utilitaire pour obtenir les métriques africaines
def get_african_metrics():
    """
    Récupère les métriques de performance africaines
    """
    current_minute = int(time.time() // 60)
    metrics = {}
    
    # Récupérer les métriques des 10 dernières minutes
    for i in range(10):
        cache_key = f"african_metrics_{current_minute - i}"
        minute_metrics = cache.get(cache_key)
        if minute_metrics:
            metrics[f"minute_{i}"] = minute_metrics
    
    return metrics


# Vue pour exposer les métriques africaines
def african_metrics_view(request):
    """
    Vue pour exposer les métriques de performance africaines
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    metrics = get_african_metrics()
    
    # Calculer des statistiques globales
    total_requests = sum(m.get('total_requests', 0) for m in metrics.values())
    total_slow = sum(m.get('slow_requests', 0) for m in metrics.values())
    
    summary = {
        'total_requests_10min': total_requests,
        'slow_requests_10min': total_slow,
        'slow_percentage': (total_slow / total_requests * 100) if total_requests > 0 else 0,
        'target_response_time_ms': 500,
        'african_optimizations_active': True,
        'detailed_metrics': metrics
    }
    
    return JsonResponse(summary, json_dumps_params={'indent': 2})