"""
Development settings for Coko project
This file overrides settings.py for development environment
"""

from .settings import *

# Override for development
DEBUG = True
ALLOWED_HOSTS = ['*']

# Use SQLite for development
USE_SQLITE = True

# Simplified database configuration for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'dev_db.sqlite3',
    },
    # Use the same database for all services in development
    'auth_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'dev_db.sqlite3',
    },
    'catalog_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'dev_db.sqlite3',
    },
    'reading_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'dev_db.sqlite3',
    },
}

# Disable database routing in development
DATABASE_ROUTERS = []

# Disable external services in development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Local memory cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Disable Elasticsearch in development
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': []
    },
}

# Session configuration for development
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Simplified middleware for development
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add African optimization middlewares only if enabled
if env('ENABLE_AFRICAN_OPTIMIZATIONS', default=False):
    MIDDLEWARE.extend([
        'coko.african_middleware.AfricanNetworkOptimizationMiddleware',
        'coko.african_middleware.AfricanPerformanceMonitoringMiddleware',
        'coko.african_middleware.AfricanCompressionMiddleware',
        'coko.african_middleware.AfricanCacheOptimizationMiddleware',
    ])

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable security features for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Static files
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_ROOT = BASE_DIR / 'media'

# Create necessary directories
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
os.makedirs(BASE_DIR / 'media', exist_ok=True)
os.makedirs(BASE_DIR / 'static', exist_ok=True)

print("🔧 Development settings loaded")
print(f"📁 Using SQLite database: {DATABASES['default']['NAME']}")
print(f"🚀 Debug mode: {DEBUG}")
print(f"🌍 African optimizations: {env('ENABLE_AFRICAN_OPTIMIZATIONS', default=False)}")
