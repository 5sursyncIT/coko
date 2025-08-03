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

# Configuration du système de facturation Coko
BILLING_SETTINGS = {
    'ENABLED': True,
    'DEFAULT_CURRENCY': 'XOF',  # Franc CFA pour l'Afrique de l'Ouest
    'SUPPORTED_CURRENCIES': ['XOF', 'EUR', 'USD', 'MAD', 'EGP'],
    'INVOICE_PREFIX': 'COKO',
    'INVOICE_NUMBER_LENGTH': 8,
    'PAYMENT_PROVIDERS': {
        'STRIPE': {
            'ENABLED': True,
            'PUBLISHABLE_KEY': os.environ.get('STRIPE_PUBLISHABLE_KEY', ''),
            'SECRET_KEY': os.environ.get('STRIPE_SECRET_KEY', ''),
            'WEBHOOK_SECRET': os.environ.get('STRIPE_WEBHOOK_SECRET', ''),
            'SANDBOX': True
        },
        'PAYPAL': {
            'ENABLED': True,
            'CLIENT_ID': os.environ.get('PAYPAL_CLIENT_ID', ''),
            'CLIENT_SECRET': os.environ.get('PAYPAL_CLIENT_SECRET', ''),
            'SANDBOX': True
        },
        'ORANGE_MONEY': {
            'ENABLED': True,
            'API_KEY': os.environ.get('ORANGE_MONEY_API_KEY', ''),
            'SECRET_KEY': os.environ.get('ORANGE_MONEY_SECRET_KEY', ''),
            'SANDBOX': True
        },
        'MTN_MOMO': {
            'ENABLED': True,
            'API_KEY': os.environ.get('MTN_MOMO_API_KEY', ''),
            'SECRET_KEY': os.environ.get('MTN_MOMO_SECRET_KEY', ''),
            'SANDBOX': True
        }
    },
    'ROYALTY_SETTINGS': {
        'DEFAULT_RATE': 0.15,  # 15% par défaut
        'MINIMUM_PAYOUT': 10000,  # 10,000 XOF minimum
        'PAYOUT_SCHEDULE': 'monthly'
    },
    'RECURRING_BILLING': {
        'ENABLED': True,
        'RETRY_ATTEMPTS': 3,
        'RETRY_DELAY_DAYS': [1, 3, 7]
    },
    'NOTIFICATIONS': {
        'SEND_INVOICE_EMAILS': True,
        'SEND_PAYMENT_CONFIRMATIONS': True,
        'SEND_OVERDUE_NOTICES': True,
        'SEND_ROYALTY_NOTIFICATIONS': True
    },
    'REPORTS': {
        'GENERATE_MONTHLY': True,
        'GENERATE_QUARTERLY': True,
        'AUTO_EXPORT_PDF': True
    }
}

# Ajouter le middleware de facturation
MIDDLEWARE.append('shared_models.billing_integration.BillingMiddleware')

print("🔧 Configuration locale chargée - utilisation de SQLite uniquement avec optimisations africaines")
print("💰 Système de facturation Coko activé avec support des paiements mobiles africains")