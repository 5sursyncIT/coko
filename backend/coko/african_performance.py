# Système d'optimisation des performances pour l'Afrique
# Implémente les recommandations pour la compression, mise en cache et CDN

import gzip
import brotli
import json
import hashlib
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.cache import get_cache_key
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.middleware.gzip import GZipMiddleware
from django.utils import timezone
from typing import Dict, List, Optional, Tuple
import logging
import time
import os

logger = logging.getLogger(__name__)

class AfricanPerformanceOptimizer:
    """
    Optimiseur de performances spécialisé pour les conditions africaines
    """
    
    def __init__(self):
        self.compression_levels = {
            'aggressive': {
                'gzip_level': 9,
                'brotli_level': 11,
                'min_size': 500,  # Compresser dès 500 bytes
                'cache_time': 86400 * 7  # 7 jours
            },
            'balanced': {
                'gzip_level': 6,
                'brotli_level': 6,
                'min_size': 1024,  # 1KB
                'cache_time': 86400 * 3  # 3 jours
            },
            'light': {
                'gzip_level': 3,
                'brotli_level': 3,
                'min_size': 2048,  # 2KB
                'cache_time': 86400  # 1 jour
            }
        }
        
        # Types MIME à compresser
        self.compressible_types = {
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'application/json',
            'application/xml',
            'text/xml',
            'text/plain',
            'application/rss+xml',
            'application/atom+xml',
            'image/svg+xml'
        }
        
        # Configuration CDN pour l'Afrique
        self.african_cdn_config = {
            'primary': {
                'name': 'CloudFlare',
                'endpoints': [
                    'https://cdnjs.cloudflare.com',
                    'https://cdn.jsdelivr.net'
                ],
                'regions': ['africa', 'europe']
            },
            'fallback': {
                'name': 'Local',
                'endpoints': ['/static/'],
                'regions': ['local']
            }
        }
    
    def get_compression_strategy(self, request) -> str:
        """
        Détermine la stratégie de compression selon les conditions réseau
        """
        from .african_geolocation import get_network_recommendations
        
        network_info = get_network_recommendations(request)
        connection_quality = network_info.get('connection_quality', 'medium')
        
        # Stratégie selon la qualité de connexion
        if connection_quality in ['very_slow', 'slow']:
            return 'aggressive'
        elif connection_quality in ['medium']:
            return 'balanced'
        else:
            return 'light'
    
    def compress_content(self, content: bytes, content_type: str, strategy: str = 'balanced') -> Tuple[bytes, str]:
        """
        Compresse le contenu selon la stratégie choisie
        """
        if content_type not in self.compressible_types:
            return content, 'identity'
        
        config = self.compression_levels[strategy]
        
        if len(content) < config['min_size']:
            return content, 'identity'
        
        # Essayer Brotli en premier (meilleure compression)
        try:
            compressed_brotli = brotli.compress(content, quality=config['brotli_level'])
            if len(compressed_brotli) < len(content) * 0.9:  # Au moins 10% de gain
                return compressed_brotli, 'br'
        except Exception as e:
            logger.warning(f"Brotli compression failed: {e}")
        
        # Fallback vers gzip
        try:
            compressed_gzip = gzip.compress(content, compresslevel=config['gzip_level'])
            if len(compressed_gzip) < len(content) * 0.9:
                return compressed_gzip, 'gzip'
        except Exception as e:
            logger.warning(f"Gzip compression failed: {e}")
        
        return content, 'identity'
    
    def get_cache_strategy(self, request, content_type: str) -> Dict:
        """
        Détermine la stratégie de cache selon le type de contenu
        """
        from .african_geolocation import get_network_recommendations
        
        network_info = get_network_recommendations(request)
        cache_strategy = network_info.get('cache_strategy', 'standard')
        
        # Configuration de base selon le type de contenu
        base_config = {
            'text/css': {'max_age': 86400 * 30, 'public': True, 'immutable': True},
            'application/javascript': {'max_age': 86400 * 30, 'public': True, 'immutable': True},
            'image/png': {'max_age': 86400 * 7, 'public': True},
            'image/jpeg': {'max_age': 86400 * 7, 'public': True},
            'image/svg+xml': {'max_age': 86400 * 7, 'public': True},
            'application/json': {'max_age': 300, 'public': False},
            'text/html': {'max_age': 0, 'public': False, 'no_cache': True}
        }
        
        config = base_config.get(content_type, {'max_age': 3600, 'public': False})
        
        # Ajustements selon la stratégie réseau
        if cache_strategy == 'aggressive':
            config['max_age'] *= 2
            config['stale_while_revalidate'] = config['max_age'] // 2
        elif cache_strategy == 'extended':
            config['max_age'] = int(config['max_age'] * 1.5)
        
        return config
    
    def generate_cache_headers(self, cache_config: Dict) -> Dict[str, str]:
        """
        Génère les en-têtes de cache
        """
        headers = {}
        
        if cache_config.get('no_cache'):
            headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            headers['Pragma'] = 'no-cache'
            headers['Expires'] = '0'
        else:
            cache_control = []
            
            if cache_config.get('public'):
                cache_control.append('public')
            else:
                cache_control.append('private')
            
            max_age = cache_config.get('max_age', 3600)
            cache_control.append(f'max-age={max_age}')
            
            if cache_config.get('immutable'):
                cache_control.append('immutable')
            
            if cache_config.get('stale_while_revalidate'):
                swr = cache_config['stale_while_revalidate']
                cache_control.append(f'stale-while-revalidate={swr}')
            
            headers['Cache-Control'] = ', '.join(cache_control)
            
            # ETag pour la validation
            if 'etag' in cache_config:
                headers['ETag'] = cache_config['etag']
        
        return headers
    
    def optimize_images(self, image_path: str, target_quality: int = 85) -> str:
        """
        Optimise les images pour les conditions africaines
        """
        try:
            from PIL import Image
            import io
            
            with Image.open(image_path) as img:
                # Convertir en RGB si nécessaire
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Redimensionner si trop grande
                max_width = 1920
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Sauvegarder avec compression
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=target_quality, optimize=True)
                
                # Sauvegarder le fichier optimisé
                optimized_path = image_path.replace('.', '_optimized.')
                with open(optimized_path, 'wb') as f:
                    f.write(output.getvalue())
                
                return optimized_path
        
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return image_path
    
    def get_cdn_url(self, asset_path: str, request=None) -> str:
        """
        Retourne l'URL CDN optimale pour un asset
        """
        from .african_geolocation import get_user_location
        
        # Vérifier si on doit utiliser un CDN
        use_cdn = getattr(settings, 'USE_CDN', False)
        if not use_cdn:
            return asset_path
        
        # Déterminer la région de l'utilisateur
        if request:
            location = get_user_location(request)
            is_african = location.get('is_african', False)
        else:
            is_african = True
        
        # Choisir le CDN approprié
        if is_african:
            # Préférer les CDN avec présence africaine
            cdn_base = getattr(settings, 'AFRICAN_CDN_BASE', 'https://cdn.example.com')
        else:
            cdn_base = getattr(settings, 'GLOBAL_CDN_BASE', 'https://global-cdn.example.com')
        
        return f"{cdn_base}{asset_path}"
    
    def preload_critical_resources(self, request) -> List[str]:
        """
        Génère les directives de préchargement pour les ressources critiques
        """
        critical_resources = [
            {'url': '/static/css/critical.css', 'as': 'style'},
            {'url': '/static/js/critical.js', 'as': 'script'},
            {'url': '/static/fonts/main.woff2', 'as': 'font', 'type': 'font/woff2', 'crossorigin': True}
        ]
        
        preload_headers = []
        for resource in critical_resources:
            cdn_url = self.get_cdn_url(resource['url'], request)
            
            header = f"<{cdn_url}>; rel=preload; as={resource['as']}"
            
            if resource.get('type'):
                header += f"; type={resource['type']}"
            
            if resource.get('crossorigin'):
                header += "; crossorigin"
            
            preload_headers.append(header)
        
        return preload_headers
    
    def generate_service_worker_cache_list(self) -> List[str]:
        """
        Génère la liste des ressources à mettre en cache par le Service Worker
        """
        cache_list = [
            # Pages critiques
            '/',
            '/catalog/',
            '/reading/',
            '/offline/',
            
            # CSS critique
            '/static/css/main.css',
            '/static/css/critical.css',
            
            # JavaScript critique
            '/static/js/main.js',
            '/static/js/offline.js',
            
            # Images essentielles
            '/static/images/logo.png',
            '/static/images/offline.svg',
            '/static/images/placeholder.svg',
            
            # Polices
            '/static/fonts/main.woff2',
            
            # Manifeste PWA
            '/manifest.json'
        ]
        
        return cache_list


# Instance globale de l'optimiseur
performance_optimizer = AfricanPerformanceOptimizer()


class AfricanCompressionMiddleware:
    """
    Middleware de compression adapté aux conditions africaines
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Vérifier si la compression est supportée
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if not any(enc in accept_encoding for enc in ['gzip', 'br']):
            return response
        
        # Vérifier le type de contenu
        content_type = response.get('Content-Type', '').split(';')[0]
        
        if hasattr(response, 'content') and response.content:
            # Déterminer la stratégie de compression
            strategy = performance_optimizer.get_compression_strategy(request)
            
            # Compresser le contenu
            compressed_content, encoding = performance_optimizer.compress_content(
                response.content, content_type, strategy
            )
            
            if encoding != 'identity':
                response.content = compressed_content
                response['Content-Encoding'] = encoding
                response['Content-Length'] = str(len(compressed_content))
                response['Vary'] = 'Accept-Encoding'
        
        return response


class AfricanCacheMiddleware:
    """
    Middleware de cache optimisé pour l'Afrique
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier le cache avant de traiter la requête
        cache_key = self.get_cache_key(request)
        cached_response = cache.get(cache_key)
        
        if cached_response and self.is_cache_valid(request, cached_response):
            # Ajouter les en-têtes de cache hit
            cached_response['X-Cache'] = 'HIT'
            cached_response['X-Cache-Key'] = cache_key
            return cached_response
        
        response = self.get_response(request)
        
        # Mettre en cache la réponse si approprié
        if self.should_cache_response(request, response):
            cache_config = performance_optimizer.get_cache_strategy(
                request, response.get('Content-Type', '')
            )
            
            # Ajouter les en-têtes de cache
            cache_headers = performance_optimizer.generate_cache_headers(cache_config)
            for header, value in cache_headers.items():
                response[header] = value
            
            # Mettre en cache
            cache_timeout = cache_config.get('max_age', 3600)
            cache.set(cache_key, response, cache_timeout)
            
            response['X-Cache'] = 'MISS'
            response['X-Cache-Key'] = cache_key
        
        return response
    
    def get_cache_key(self, request) -> str:
        """
        Génère une clé de cache unique
        """
        key_parts = [
            request.method,
            request.get_full_path(),
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            request.META.get('HTTP_ACCEPT_ENCODING', '')
        ]
        
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def is_cache_valid(self, request, cached_response) -> bool:
        """
        Vérifie si le cache est encore valide
        """
        # Vérifier l'ETag si présent
        if_none_match = request.META.get('HTTP_IF_NONE_MATCH')
        etag = cached_response.get('ETag')
        
        if if_none_match and etag and if_none_match == etag:
            return True
        
        # Vérifier la date de modification
        if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE')
        last_modified = cached_response.get('Last-Modified')
        
        if if_modified_since and last_modified:
            try:
                from django.utils.http import parse_http_date
                if_modified_timestamp = parse_http_date(if_modified_since)
                last_modified_timestamp = parse_http_date(last_modified)
                
                if if_modified_timestamp >= last_modified_timestamp:
                    return True
            except ValueError:
                pass
        
        return True
    
    def should_cache_response(self, request, response) -> bool:
        """
        Détermine si la réponse doit être mise en cache
        """
        # Ne pas cacher les erreurs
        if response.status_code >= 400:
            return False
        
        # Ne pas cacher les requêtes POST/PUT/DELETE
        if request.method not in ['GET', 'HEAD']:
            return False
        
        # Ne pas cacher si explicitement désactivé
        cache_control = response.get('Cache-Control', '')
        if 'no-cache' in cache_control or 'no-store' in cache_control:
            return False
        
        return True


class AfricanPerformanceMiddleware:
    """
    Middleware principal pour l'optimisation des performances
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Mesurer le temps de réponse
        response_time = time.time() - start_time
        response['X-Response-Time'] = f"{response_time:.3f}s"
        
        # Ajouter les en-têtes de préchargement
        preload_headers = performance_optimizer.preload_critical_resources(request)
        if preload_headers:
            response['Link'] = ', '.join(preload_headers)
        
        # Ajouter les hints de performance
        self.add_performance_hints(request, response)
        
        return response
    
    def add_performance_hints(self, request, response):
        """
        Ajoute les hints de performance
        """
        from .african_geolocation import get_network_recommendations
        
        network_info = get_network_recommendations(request)
        
        # DNS prefetch pour les domaines externes
        dns_prefetch = [
            '//fonts.googleapis.com',
            '//cdn.jsdelivr.net',
            '//cdnjs.cloudflare.com'
        ]
        
        # Preconnect pour les ressources critiques
        preconnect = []
        if network_info.get('connection_quality') in ['fast', 'medium']:
            preconnect.extend([
                '//fonts.gstatic.com',
                '//api.example.com'
            ])
        
        # Ajouter les hints
        hints = []
        for domain in dns_prefetch:
            hints.append(f"<{domain}>; rel=dns-prefetch")
        
        for domain in preconnect:
            hints.append(f"<{domain}>; rel=preconnect")
        
        if hints:
            existing_link = response.get('Link', '')
            if existing_link:
                response['Link'] = existing_link + ', ' + ', '.join(hints)
            else:
                response['Link'] = ', '.join(hints)


# Vues pour l'optimisation des performances
def performance_metrics_view(request):
    """
    Vue pour exposer les métriques de performance
    """
    from .african_monitoring import get_performance_metrics
    
    metrics = get_performance_metrics()
    
    return JsonResponse({
        'metrics': metrics,
        'timestamp': datetime.now().isoformat(),
        'optimizations': {
            'compression': 'enabled',
            'caching': 'enabled',
            'cdn': getattr(settings, 'USE_CDN', False)
        }
    })


def cache_status_view(request):
    """
    Vue pour vérifier le statut du cache
    """
    cache_stats = {
        'cache_backend': str(cache),
        'cache_key_prefix': getattr(settings, 'CACHE_KEY_PREFIX', ''),
        'cache_timeout': getattr(settings, 'CACHE_TIMEOUT', 300)
    }
    
    # Test du cache
    test_key = 'cache_test'
    test_value = 'test_value'
    
    cache.set(test_key, test_value, 60)
    retrieved_value = cache.get(test_key)
    
    cache_stats['cache_working'] = retrieved_value == test_value
    
    return JsonResponse(cache_stats)


def optimize_assets_view(request):
    """
    Vue pour optimiser les assets statiques
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Optimiser les images
        static_dir = getattr(settings, 'STATIC_ROOT', '')
        if static_dir and os.path.exists(static_dir):
            optimized_count = 0
            
            for root, dirs, files in os.walk(static_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        file_path = os.path.join(root, file)
                        optimized_path = performance_optimizer.optimize_images(file_path)
                        if optimized_path != file_path:
                            optimized_count += 1
            
            return JsonResponse({
                'status': 'success',
                'optimized_images': optimized_count
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Static directory not found'
            })
    
    except Exception as e:
        logger.error(f"Asset optimization failed: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# Fonctions utilitaires
def get_performance_score(request) -> Dict:
    """
    Calcule un score de performance pour la requête actuelle
    """
    from .african_geolocation import get_network_recommendations
    from .african_monitoring import get_current_metrics
    
    network_info = get_network_recommendations(request)
    metrics = get_current_metrics()
    
    # Calculer le score basé sur différents facteurs
    score = 100
    
    # Pénalité pour connexion lente
    connection_quality = network_info.get('connection_quality', 'medium')
    if connection_quality == 'very_slow':
        score -= 30
    elif connection_quality == 'slow':
        score -= 20
    elif connection_quality == 'medium':
        score -= 10
    
    # Pénalité pour temps de réponse élevé
    avg_response_time = metrics.get('avg_response_time', 0)
    if avg_response_time > 2.0:
        score -= 25
    elif avg_response_time > 1.0:
        score -= 15
    elif avg_response_time > 0.5:
        score -= 10
    
    # Bonus pour optimisations activées
    if getattr(settings, 'USE_CDN', False):
        score += 5
    
    if 'gzip' in request.META.get('HTTP_ACCEPT_ENCODING', ''):
        score += 5
    
    return {
        'score': max(0, min(100, score)),
        'factors': {
            'connection_quality': connection_quality,
            'response_time': avg_response_time,
            'cdn_enabled': getattr(settings, 'USE_CDN', False),
            'compression_supported': 'gzip' in request.META.get('HTTP_ACCEPT_ENCODING', '')
        },
        'recommendations': get_performance_recommendations(score, network_info)
    }


def get_performance_recommendations(score: int, network_info: Dict) -> List[str]:
    """
    Génère des recommandations d'optimisation
    """
    recommendations = []
    
    if score < 70:
        recommendations.append("Activer la compression Brotli/Gzip")
        recommendations.append("Optimiser les images")
        recommendations.append("Utiliser un CDN")
    
    if network_info.get('connection_quality') in ['very_slow', 'slow']:
        recommendations.append("Réduire la taille des ressources")
        recommendations.append("Implémenter le lazy loading")
        recommendations.append("Utiliser le cache agressif")
    
    if score < 50:
        recommendations.append("Minifier CSS et JavaScript")
        recommendations.append("Optimiser les requêtes base de données")
        recommendations.append("Implémenter le Service Worker")
    
    return recommendations