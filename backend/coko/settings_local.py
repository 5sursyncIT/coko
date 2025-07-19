# Configuration locale pour le développement sans PostgreSQL
from .settings import *

# Utiliser SQLite pour le développement local - une seule base de données
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'auth_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'catalog_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'reading_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'recommendation_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Désactiver le routage de base de données pour le développement local
DATABASE_ROUTERS = []

# Désactiver les services externes pour les tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Configuration Redis locale (optionnelle)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Désactiver Elasticsearch pour le développement local
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': []  # Liste vide pour désactiver complètement
    },
}

# Configuration de logging simplifiée
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Désactiver les vérifications de sécurité pour le développement
DEBUG = True
ALLOWED_HOSTS = ['*']

# Configuration des médias pour le développement avec optimisations africaines
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuration CDN pour l'Afrique
USE_CDN = False  # Désactivé en développement
AFRICAN_CDN_BASE = 'https://african-cdn.example.com'
GLOBAL_CDN_BASE = 'https://global-cdn.example.com'

# Optimisation des images
IMAGE_OPTIMIZATION = {
    'QUALITY': 85,
    'MAX_WIDTH': 1920,
    'FORMATS': ['JPEG', 'PNG', 'WEBP']
}

# Configuration des sessions pour SQLite
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 heures

# Configuration Redis désactivée pour le développement local
REDIS_URL = None
CELERY_BROKER_URL = None
CELERY_RESULT_BACKEND = None

# Configuration des middlewares avec optimisations africaines
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'coko.african_performance.AfricanPerformanceMiddleware',
    'coko.african_performance.AfricanCacheMiddleware',
    'coko.african_performance.AfricanCompressionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'coko.african_languages.AfricanLanguageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'coko.african_middleware.AfricanNetworkOptimizationMiddleware',
    'coko.african_middleware.AfricanPerformanceMonitoringMiddleware',
    'coko.african_middleware.AfricanCompressionMiddleware',
    'coko.african_middleware.AfricanCacheOptimizationMiddleware',
]

# Internationalization avec support africain
LANGUAGE_CODE = 'fr'  # Français par défaut pour l'Afrique
TIME_ZONE = 'Africa/Dakar'  # Fuseau horaire africain
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Langues supportées
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('ar', 'العربية'),
    ('pt', 'Português'),
    ('sw', 'Kiswahili'),
    ('ha', 'Harshen Hausa'),
    ('yo', 'Èdè Yorùbá'),
    ('ig', 'Asụsụ Igbo'),
    ('am', 'አማርኛ'),
    ('zu', 'isiZulu'),
    ('xh', 'isiXhosa'),
    ('af', 'Afrikaans'),
]

# Répertoires de traduction
import os
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Configuration spécifique à l'Afrique
AFRICAN_SETTINGS = {
    'ENABLE_OFFLINE_MODE': True,
    'AGGRESSIVE_CACHING': True,
    'MOBILE_OPTIMIZATION': True,
    'LOW_BANDWIDTH_MODE': True,
    'AFRICAN_PAYMENTS': {
        'ORANGE_MONEY': {
            'API_KEY': os.environ.get('ORANGE_MONEY_API_KEY', ''),
            'SECRET_KEY': os.environ.get('ORANGE_MONEY_SECRET_KEY', ''),
            'SANDBOX': True
        },
        'MTN_MOMO': {
            'API_KEY': os.environ.get('MTN_MOMO_API_KEY', ''),
            'SECRET_KEY': os.environ.get('MTN_MOMO_SECRET_KEY', ''),
            'SANDBOX': True
        },
        'WAVE': {
            'API_KEY': os.environ.get('WAVE_API_KEY', ''),
            'SECRET_KEY': os.environ.get('WAVE_SECRET_KEY', ''),
            'SANDBOX': True
        }
    },
    'GEOLOCATION': {
        'ENABLE_IP_DETECTION': True,
        'FALLBACK_COUNTRY': 'SN',  # Sénégal par défaut
        'CACHE_TIMEOUT': 3600
    },
    'PERFORMANCE': {
        'COMPRESSION_LEVEL': 'balanced',
        'CACHE_STRATEGY': 'aggressive',
        'IMAGE_OPTIMIZATION': True,
        'LAZY_LOADING': True
    }
}

# Configuration PWA
PWA_CACHE_VERSION = '1.0.0'
PWA_OFFLINE_PAGES = [
    '/',
    '/catalog/',
    '/reading/',
    '/profile/',
    '/offline/'
]

# Monitoring africain
AFRICAN_MONITORING = {
    'ENABLE_METRICS': True,
    'ALERT_THRESHOLDS': {
        'RESPONSE_TIME': 2.0,  # 2 secondes
        'ERROR_RATE': 0.05,    # 5%
        'MEMORY_USAGE': 0.80   # 80%
    },
    'CLEANUP_INTERVAL': 86400  # 24 heures
}

print("🔧 Configuration locale chargée - utilisation de SQLite uniquement avec optimisations africaines")