# Guide de Stabilité - Application Coko

## 🚨 Problèmes Corrigés

### 1. Signaux Django Problématiques

**Problème identifié :**
- Boucles infinies dans les signaux `post_save`
- Erreurs `AttributeError` lors de l'accès à des champs inexistants
- Erreurs de contraintes `NOT NULL` lors de la création d'utilisateurs

**Solutions implémentées :**
- Ajout de gardes avec `hasattr()` pour éviter les erreurs d'attributs
- Utilisation d'attributs temporaires (`_preferences_created`, `_welcome_email_sent`) pour éviter les boucles
- Gestion d'erreurs robuste avec try/except dans tous les signaux
- Utilisation de `getattr()` avec valeurs par défaut pour les champs optionnels

### 2. Dépendances Lourdes Optionnelles

**Problème identifié :**
- `requirements.txt` contenait des dépendances ML/AI très lourdes (TensorFlow, PyTorch)
- Temps de démarrage lents et consommation mémoire excessive
- Conflits potentiels entre versions de bibliothèques

**Solutions implémentées :**
- **`requirements.txt`** : Fichier unique avec dépendances essentielles activées et ML/AI commentées
- **Sections optionnelles** : Dépendances lourdes commentées par défaut, facilement activables
- **`setup_dependencies.py`** : Script d'installation intelligent qui décommente selon le mode

## 🔧 Nouvelles Fonctionnalités

### 1. Middleware de Stabilité

Fichier : `coko/middleware.py`

#### ErrorHandlingMiddleware
- Gestion centralisée des erreurs non capturées
- Logging détaillé avec ID d'erreur unique
- Réponses d'erreur standardisées pour l'API
- Mode debug respecté

#### DatabaseConnectionMiddleware
- Vérification de la santé des connexions DB
- Détection précoce des problèmes de connectivité
- Réponses 503 appropriées en cas de problème

#### RequestLoggingMiddleware
- Logging des requêtes sensibles (auth, admin)
- Détection et logging des requêtes lentes (>2s)
- Métriques de performance

#### SecurityHeadersMiddleware
- En-têtes de sécurité automatiques
- Protection XSS, clickjacking, etc.

### 2. Script de Configuration

Fichier : `setup_dependencies.py`

**Fonctionnement :**
- **Mode minimal** : Installe uniquement les dépendances non-commentées (essentielles)
- **Mode ML** : Décommente et installe les packages ML/AI de base (scikit-learn, transformers, etc.)
- **Mode full** : Décommente et installe toutes les dépendances (y compris TensorFlow, PyTorch)

```bash
# Installation minimale (recommandée pour le développement)
python setup_dependencies.py --mode minimal

# Installation avec ML/AI (décommente automatiquement)
python setup_dependencies.py --mode ml

# Installation complète (décommente tout)
python setup_dependencies.py --mode full
```

## 📋 Configuration Recommandée

### 1. Activer les Middlewares

Ajouter dans `settings.py` :

```python
MIDDLEWARE = [
    'coko.middleware.SecurityHeadersMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'coko.middleware.DatabaseConnectionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'coko.middleware.RequestLoggingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'coko.middleware.ErrorHandlingMiddleware',  # En dernier
]
```

### 2. Configuration Base de Données Robuste

```python
# Ajouter dans settings.py pour la production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
        'CONN_MAX_AGE': 600,  # Réutilisation des connexions
        'OPTIONS': {
            'MAX_CONNS': 20,
            'connect_timeout': 10,
            'command_timeout': 30,
        }
    }
}
```

### 3. Logging Amélioré

```python
# Configuration logging recommandée
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024*1024*10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'coko': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## 🚀 Déploiement

### 1. Installation Rapide

```bash
# Cloner le projet
git clone <repo>
cd coko/backend

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installation minimale (recommandée - dépendances essentielles seulement)
python setup_dependencies.py --mode minimal

# Configuration
cp .env.example .env
# Éditer .env avec vos paramètres

# Démarrage
python manage.py runserver
```

### 2. Pour les Fonctionnalités ML/AI

```bash
# Avec fonctionnalités ML/AI (décommente et installe les packages ML)
python setup_dependencies.py --mode ml

# Installation complète (toutes les dépendances y compris TensorFlow/PyTorch)
python setup_dependencies.py --mode full
```

**Alternative manuelle :**
```bash
# Installation de base
pip install -r requirements.txt

# Pour activer ML/AI : décommentez les lignes dans requirements.txt puis :
pip install -r requirements.txt
```

## 📊 Monitoring

### 1. Health Checks

Endpoints disponibles :
- `/health/` - Santé générale
- `/health/db/` - État des bases de données
- `/health/cache/` - État du cache Redis

### 2. Métriques Importantes

- **Temps de réponse** : Surveillé automatiquement (>2s = warning)
- **Erreurs de base de données** : Loggées avec détails
- **Erreurs d'application** : ID unique pour le debugging
- **Requêtes sensibles** : Authentification, administration

## 🔒 Sécurité

### En-têtes Automatiques
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Bonnes Pratiques
1. Toujours utiliser HTTPS en production
2. Configurer les variables d'environnement sensibles
3. Activer le rate limiting pour les APIs
4. Surveiller les logs d'erreurs régulièrement

## 🐛 Debugging

### Erreurs Communes

1. **Erreur de signal** : Vérifier les logs pour l'ID d'erreur unique
2. **Connexion DB** : Vérifier `/health/db/`
3. **Dépendances manquantes** : Réinstaller avec `setup_dependencies.py`

### Logs Utiles

```bash
# Erreurs générales
tail -f logs/errors.log

# Activité générale
tail -f logs/django.log

# Filtrer par type d'erreur
grep "ERROR" logs/django.log
```

## 📈 Performance

### Optimisations Implémentées
1. Connexions DB réutilisées (CONN_MAX_AGE)
2. Dépendances allégées par défaut
3. Middleware optimisé pour les requêtes fréquentes
4. Logging asynchrone pour les performances

### Recommandations Supplémentaires
1. Utiliser un CDN pour les fichiers statiques
2. Configurer un reverse proxy (Nginx)
3. Implémenter la mise en cache Redis
4. Surveiller l'utilisation mémoire

---

**Note :** Ces améliorations augmentent significativement la stabilité et la maintenabilité de l'application. Pour toute question, consulter les logs ou créer une issue.