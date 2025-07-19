# Configuration de développement sans Docker
# Utilise SQLite au lieu de PostgreSQL pour simplifier le développement local

from .settings import *

# Override database configuration for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'auth_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'auth_db.sqlite3',
    },
    'catalog_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'catalog_db.sqlite3',
    },
    'reading_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'reading_db.sqlite3',
    },
}

# Disable Redis/Celery for development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use dummy cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Use database sessions instead of cache
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Disable Elasticsearch for development
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': []
    },
}

print("🔧 Configuration de développement chargée (SQLite + cache dummy)")