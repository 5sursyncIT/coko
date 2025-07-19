# Système PWA (Progressive Web App) pour l'Afrique
# Implémente les recommandations pour le mode offline et la synchronisation

import json
import hashlib
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AfricanPWAManager:
    """
    Gestionnaire PWA spécialisé pour les conditions africaines
    """
    
    def __init__(self):
        self.cache_version = getattr(settings, 'PWA_CACHE_VERSION', '1.0.0')
        self.offline_pages = [
            '/',
            '/catalog/',
            '/reading/',
            '/profile/',
            '/offline/'
        ]
        self.critical_assets = [
            '/static/css/main.css',
            '/static/js/main.js',
            '/static/js/offline.js',
            '/static/images/logo.png',
            '/static/images/offline.svg'
        ]
    
    def generate_manifest(self, request) -> Dict:
        """
        Génère le manifeste PWA adapté aux conditions africaines
        """
        from .african_geolocation import get_user_location
        
        location = get_user_location(request)
        is_african = location.get('is_african', False)
        
        # Configuration de base
        manifest = {
            "name": "Coko - Plateforme de Lecture Africaine",
            "short_name": "Coko",
            "description": "Plateforme de lecture optimisée pour l'Afrique",
            "start_url": "/",
            "display": "standalone",
            "orientation": "portrait",
            "theme_color": "#2E7D32",
            "background_color": "#FFFFFF",
            "lang": "fr",
            "scope": "/",
            "icons": [
                {
                    "src": "/static/images/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/images/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/images/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/images/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/images/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/images/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/images/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/images/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ],
            "categories": ["education", "books", "reading"],
            "screenshots": [
                {
                    "src": "/static/images/screenshot-mobile.png",
                    "sizes": "320x640",
                    "type": "image/png",
                    "form_factor": "narrow"
                },
                {
                    "src": "/static/images/screenshot-desktop.png",
                    "sizes": "1280x720",
                    "type": "image/png",
                    "form_factor": "wide"
                }
            ]
        }
        
        # Optimisations spécifiques à l'Afrique
        if is_african:
            # Préférer le mode standalone pour économiser la bande passante
            manifest["display"] = "standalone"
            
            # Ajouter des raccourcis pour les fonctions critiques
            manifest["shortcuts"] = [
                {
                    "name": "Lecture Hors-ligne",
                    "short_name": "Offline",
                    "description": "Accéder aux livres téléchargés",
                    "url": "/offline/",
                    "icons": [
                        {
                            "src": "/static/images/offline-icon.png",
                            "sizes": "96x96"
                        }
                    ]
                },
                {
                    "name": "Synchronisation",
                    "short_name": "Sync",
                    "description": "Synchroniser les données",
                    "url": "/sync/",
                    "icons": [
                        {
                            "src": "/static/images/sync-icon.png",
                            "sizes": "96x96"
                        }
                    ]
                }
            ]
            
            # Préférences pour les réseaux lents
            manifest["prefer_related_applications"] = False
            manifest["edge_side_panel"] = {
                "preferred_width": 320
            }
        
        return manifest
    
    def generate_service_worker(self, request) -> str:
        """
        Génère le Service Worker adapté aux conditions africaines
        """
        from .african_geolocation import get_user_location, get_network_recommendations
        
        location = get_user_location(request)
        network_recommendations = get_network_recommendations(request)
        
        # Configuration du cache selon la qualité réseau
        cache_strategy = network_recommendations.get('cache_strategy', 'standard')
        
        cache_config = {
            'aggressive': {
                'static_cache_time': 86400 * 7,  # 7 jours
                'api_cache_time': 3600,  # 1 heure
                'image_cache_time': 86400 * 3,  # 3 jours
                'offline_fallback': True
            },
            'extended': {
                'static_cache_time': 86400 * 3,  # 3 jours
                'api_cache_time': 1800,  # 30 minutes
                'image_cache_time': 86400,  # 1 jour
                'offline_fallback': True
            },
            'standard': {
                'static_cache_time': 86400,  # 1 jour
                'api_cache_time': 600,  # 10 minutes
                'image_cache_time': 3600 * 12,  # 12 heures
                'offline_fallback': False
            }
        }
        
        config = cache_config.get(cache_strategy, cache_config['standard'])
        
        sw_template = f"""
// Service Worker pour Coko - Optimisé pour l'Afrique
// Version: {self.cache_version}
// Stratégie de cache: {cache_strategy}

const CACHE_VERSION = '{self.cache_version}';
const STATIC_CACHE = 'coko-static-v' + CACHE_VERSION;
const API_CACHE = 'coko-api-v' + CACHE_VERSION;
const IMAGE_CACHE = 'coko-images-v' + CACHE_VERSION;
const OFFLINE_CACHE = 'coko-offline-v' + CACHE_VERSION;

// Configuration du cache selon les conditions africaines
const CACHE_CONFIG = {json.dumps(config, indent=2)};

// URLs critiques à mettre en cache
const CRITICAL_URLS = {json.dumps(self.offline_pages + self.critical_assets)};

// Stratégies de cache
const CACHE_STRATEGIES = {{
    'cache-first': ['static', 'images'],
    'network-first': ['api', 'dynamic'],
    'stale-while-revalidate': ['content']
}};

// Installation du Service Worker
self.addEventListener('install', event => {{
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {{
                console.log('Caching critical resources...');
                return cache.addAll(CRITICAL_URLS);
            }})
            .then(() => {{
                console.log('Critical resources cached');
                return self.skipWaiting();
            }})
            .catch(error => {{
                console.error('Error during install:', error);
            }})
    );
}});

// Activation du Service Worker
self.addEventListener('activate', event => {{
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {{
                return Promise.all(
                    cacheNames.map(cacheName => {{
                        if (!cacheName.includes(CACHE_VERSION)) {{
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }}
                    }})
                );
            }})
            .then(() => {{
                console.log('Service Worker activated');
                return self.clients.claim();
            }})
    );
}});

// Interception des requêtes
self.addEventListener('fetch', event => {{
    const request = event.request;
    const url = new URL(request.url);
    
    // Ignorer les requêtes non-HTTP
    if (!request.url.startsWith('http')) {{
        return;
    }}
    
    // Stratégie selon le type de ressource
    if (url.pathname.startsWith('/static/')) {{
        event.respondWith(handleStaticRequest(request));
    }} else if (url.pathname.startsWith('/api/')) {{
        event.respondWith(handleApiRequest(request));
    }} else if (url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg)$/)) {{
        event.respondWith(handleImageRequest(request));
    }} else {{
        event.respondWith(handlePageRequest(request));
    }}
}});

// Gestion des ressources statiques (Cache First)
async function handleStaticRequest(request) {{
    try {{
        const cache = await caches.open(STATIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {{
            return cachedResponse;
        }}
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {{
            cache.put(request, networkResponse.clone());
        }}
        
        return networkResponse;
    }} catch (error) {{
        console.error('Static request failed:', error);
        return new Response('Resource not available offline', {{
            status: 503,
            statusText: 'Service Unavailable'
        }});
    }}
}}

// Gestion des requêtes API (Network First avec fallback)
async function handleApiRequest(request) {{
    try {{
        const networkResponse = await fetch(request, {{
            timeout: 10000  // 10 secondes timeout pour l'Afrique
        }});
        
        if (networkResponse.ok) {{
            const cache = await caches.open(API_CACHE);
            cache.put(request, networkResponse.clone());
        }}
        
        return networkResponse;
    }} catch (error) {{
        console.log('Network failed, trying cache:', error);
        
        const cache = await caches.open(API_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {{
            return cachedResponse;
        }}
        
        // Fallback pour les données critiques
        if (request.url.includes('/user/') || request.url.includes('/profile/')) {{
            return new Response(JSON.stringify({{
                error: 'offline',
                message: 'Données non disponibles hors-ligne'
            }}), {{
                status: 503,
                headers: {{
                    'Content-Type': 'application/json'
                }}
            }});
        }}
        
        throw error;
    }}
}}

// Gestion des images (Cache First avec compression)
async function handleImageRequest(request) {{
    try {{
        const cache = await caches.open(IMAGE_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {{
            return cachedResponse;
        }}
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {{
            cache.put(request, networkResponse.clone());
        }}
        
        return networkResponse;
    }} catch (error) {{
        console.error('Image request failed:', error);
        
        // Fallback vers image placeholder
        return fetch('/static/images/placeholder.svg');
    }}
}}

// Gestion des pages (Stale While Revalidate)
async function handlePageRequest(request) {{
    try {{
        const cache = await caches.open(OFFLINE_CACHE);
        const cachedResponse = await cache.match(request);
        
        // Retourner le cache immédiatement si disponible
        if (cachedResponse) {{
            // Revalider en arrière-plan
            fetch(request)
                .then(networkResponse => {{
                    if (networkResponse.ok) {{
                        cache.put(request, networkResponse.clone());
                    }}
                }})
                .catch(() => {{
                    // Ignorer les erreurs de revalidation
                }});
            
            return cachedResponse;
        }}
        
        // Pas de cache, essayer le réseau
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {{
            cache.put(request, networkResponse.clone());
        }}
        
        return networkResponse;
    }} catch (error) {{
        console.error('Page request failed:', error);
        
        // Fallback vers page offline
        const cache = await caches.open(OFFLINE_CACHE);
        const offlinePage = await cache.match('/offline/');
        
        if (offlinePage) {{
            return offlinePage;
        }}
        
        return new Response(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Hors-ligne - Coko</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .offline {{ color: #666; }}
                    .retry {{ margin-top: 20px; }}
                    button {{ padding: 10px 20px; background: #2E7D32; color: white; border: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="offline">
                    <h1>🌍 Mode Hors-ligne</h1>
                    <p>Vous êtes actuellement hors-ligne. Cette page n'est pas disponible.</p>
                    <div class="retry">
                        <button onclick="window.location.reload()">Réessayer</button>
                        <button onclick="window.location.href='/offline/'">Contenu Hors-ligne</button>
                    </div>
                </div>
            </body>
            </html>
        `, {{
            status: 503,
            headers: {{
                'Content-Type': 'text/html'
            }}
        }});
    }}
}}

// Synchronisation en arrière-plan
self.addEventListener('sync', event => {{
    if (event.tag === 'background-sync') {{
        event.waitUntil(doBackgroundSync());
    }}
}});

// Synchronisation des données
async function doBackgroundSync() {{
    try {{
        console.log('Starting background sync...');
        
        // Synchroniser les données en attente
        const pendingData = await getPendingData();
        
        for (const data of pendingData) {{
            try {{
                await syncData(data);
                await removePendingData(data.id);
            }} catch (error) {{
                console.error('Sync failed for:', data.id, error);
            }}
        }}
        
        console.log('Background sync completed');
    }} catch (error) {{
        console.error('Background sync error:', error);
    }}
}}

// Récupérer les données en attente de synchronisation
async function getPendingData() {{
    // Ici on récupérerait les données depuis IndexedDB
    return [];
}}

// Synchroniser une donnée
async function syncData(data) {{
    const response = await fetch('/api/sync/', {{
        method: 'POST',
        headers: {{
            'Content-Type': 'application/json',
            'X-CSRFToken': await getCSRFToken()
        }},
        body: JSON.stringify(data)
    }});
    
    if (!response.ok) {{
        throw new Error('Sync failed');
    }}
    
    return response.json();
}}

// Supprimer une donnée synchronisée
async function removePendingData(id) {{
    // Ici on supprimerait la donnée d'IndexedDB
}}

// Récupérer le token CSRF
async function getCSRFToken() {{
    const cache = await caches.open(API_CACHE);
    const response = await cache.match('/api/csrf/');
    
    if (response) {{
        const data = await response.json();
        return data.token;
    }}
    
    return '';
}}

// Gestion des notifications push
self.addEventListener('push', event => {{
    if (event.data) {{
        const data = event.data.json();
        
        const options = {{
            body: data.body,
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/badge.png',
            vibrate: [200, 100, 200],
            data: data.data || {{}},
            actions: [
                {{
                    action: 'open',
                    title: 'Ouvrir',
                    icon: '/static/images/open-icon.png'
                }},
                {{
                    action: 'dismiss',
                    title: 'Ignorer',
                    icon: '/static/images/dismiss-icon.png'
                }}
            ]
        }};
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }}
}});

// Gestion des clics sur notifications
self.addEventListener('notificationclick', event => {{
    event.notification.close();
    
    if (event.action === 'open') {{
        const url = event.notification.data.url || '/';
        event.waitUntil(
            clients.openWindow(url)
        );
    }}
}});

console.log('Coko Service Worker loaded - Optimized for Africa');
        """
        
        return sw_template
    
    def get_offline_content(self, request) -> Dict:
        """
        Retourne le contenu disponible hors-ligne
        """
        # Ici on récupérerait le contenu depuis la base de données
        # ou le cache selon ce qui a été téléchargé par l'utilisateur
        
        return {
            'books': [],
            'articles': [],
            'user_data': {},
            'last_sync': None
        }


# Instance globale du gestionnaire PWA
pwa_manager = AfricanPWAManager()


# Vues Django pour PWA
def manifest_view(request):
    """
    Vue pour servir le manifeste PWA
    """
    manifest = pwa_manager.generate_manifest(request)
    
    response = JsonResponse(manifest)
    response['Content-Type'] = 'application/manifest+json'
    response['Cache-Control'] = 'public, max-age=86400'  # Cache 24h
    
    return response


def service_worker_view(request):
    """
    Vue pour servir le Service Worker
    """
    sw_content = pwa_manager.generate_service_worker(request)
    
    response = HttpResponse(sw_content, content_type='application/javascript')
    response['Cache-Control'] = 'no-cache'  # Pas de cache pour le SW
    response['Service-Worker-Allowed'] = '/'
    
    return response


def offline_page_view(request):
    """
    Vue pour la page hors-ligne
    """
    offline_content = pwa_manager.get_offline_content(request)
    
    context = {
        'offline_content': offline_content,
        'is_offline': True
    }
    
    return render_to_string('pwa/offline.html', context, request=request)


@csrf_exempt
@require_http_methods(["POST"])
def sync_api_view(request):
    """
    API pour la synchronisation des données
    """
    try:
        data = json.loads(request.body)
        
        # Traiter les données de synchronisation
        # Ici on implémenterait la logique de sync
        
        return JsonResponse({
            'status': 'success',
            'synced_at': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def pwa_install_prompt_view(request):
    """
    Vue pour gérer l'invite d'installation PWA
    """
    from .african_geolocation import is_african_user
    
    # Encourager l'installation pour les utilisateurs africains
    should_prompt = is_african_user(request)
    
    return JsonResponse({
        'should_prompt': should_prompt,
        'message': 'Installez Coko pour une meilleure expérience hors-ligne' if should_prompt else None
    })


# Fonctions utilitaires
def generate_pwa_meta_tags(request) -> str:
    """
    Génère les meta tags PWA pour les templates
    """
    from .african_geolocation import get_user_location
    
    location = get_user_location(request)
    theme_color = "#2E7D32"  # Vert africain
    
    meta_tags = f"""
    <!-- PWA Meta Tags -->
    <meta name="theme-color" content="{theme_color}">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Coko">
    <meta name="msapplication-TileColor" content="{theme_color}">
    <meta name="msapplication-config" content="/static/browserconfig.xml">
    
    <!-- Manifest -->
    <link rel="manifest" href="/manifest.json">
    
    <!-- Icons -->
    <link rel="icon" type="image/png" sizes="32x32" href="/static/images/icon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/images/icon-16x16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/static/images/icon-180x180.png">
    <link rel="mask-icon" href="/static/images/safari-pinned-tab.svg" color="{theme_color}">
    
    <!-- Service Worker Registration -->
    <script>
        if ('serviceWorker' in navigator) {{
            window.addEventListener('load', function() {{
                navigator.serviceWorker.register('/sw.js')
                    .then(function(registration) {{
                        console.log('SW registered: ', registration);
                    }})
                    .catch(function(registrationError) {{
                        console.log('SW registration failed: ', registrationError);
                    }});
            }});
        }}
    </script>
    """
    
    return meta_tags


def check_pwa_support(request) -> Dict:
    """
    Vérifie le support PWA du navigateur
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    # Détection basique du support PWA
    supports_sw = 'chrome' in user_agent or 'firefox' in user_agent or 'safari' in user_agent
    supports_manifest = supports_sw  # Généralement corrélé
    
    return {
        'supports_service_worker': supports_sw,
        'supports_manifest': supports_manifest,
        'supports_push': supports_sw,
        'is_mobile': 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
    }