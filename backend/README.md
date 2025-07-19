# Coko Backend

Backend Django pour la plateforme Coko - une plateforme de lecture numérique pour l'Afrique de l'Ouest.

## Architecture

Le backend est organisé en microservices Django :

- **auth_service** : Authentification et gestion des utilisateurs
- **catalog_service** : Catalogue de livres et métadonnées
- **reading_service** : Sessions de lecture et progression
- **recommendation_service** : Recommandations basées sur l'IA

## Technologies

- **Framework** : Django 4.2 + Django REST Framework
- **Base de données** : PostgreSQL (multi-base)
- **Cache/Queue** : Redis + Celery
- **Recherche** : Elasticsearch
- **Stockage** : MinIO/S3
- **API** : REST + GraphQL

## Installation

### Prérequis

- Python 3.11+
- Docker et Docker Compose
- PostgreSQL 15+
- Redis 7+
- Elasticsearch 8+

### Configuration rapide

1. **Cloner et configurer**
```bash
cd backend
cp .env.example .env
# Éditer .env avec vos paramètres
```

2. **Démarrer les services**
```bash
make docker-up
```

3. **Installer les dépendances**
```bash
make install
```

4. **Configurer la base de données**
```bash
make migrate
make createsuperuser
```

5. **Démarrer le serveur**
```bash
make runserver
```

## Commandes utiles

```bash
# Développement
make dev-setup          # Configuration initiale
make runserver          # Serveur Django
make celery             # Worker Celery
make celery-beat        # Planificateur Celery

# Tests et qualité
make test               # Tests avec coverage
make lint               # Vérification du code
make format             # Formatage automatique

# Docker
make docker-up          # Services de base
make docker-up-full     # Tous les services
make docker-down        # Arrêter les services

# Base de données
make migrate            # Migrations
make reset-db           # Réinitialiser (ATTENTION)
```

## Structure des bases de données

- `coko_main` : Base principale
- `coko_auth` : Utilisateurs et authentification
- `coko_catalog` : Catalogue de livres
- `coko_reading` : Sessions et progression de lecture

## API Endpoints

### REST API
- `/api/v1/auth/` - Authentification
- `/api/v1/catalog/` - Catalogue
- `/api/v1/reading/` - Lecture
- `/api/v1/recommendations/` - Recommandations

### GraphQL
- `/graphql/` - Endpoint GraphQL avec interface GraphiQL

### Monitoring
- `/health/` - Vérification de santé
- `/admin/` - Interface d'administration

## Configuration des services

### Variables d'environnement

Voir `.env.example` pour la liste complète des variables.

### Bases de données multiples

Le routeur de base de données (`coko/db_router.py`) dirige automatiquement les modèles vers les bonnes bases :

```python
# Exemple d'utilisation
from auth_service.models import User  # → coko_auth
from catalog_service.models import Book  # → coko_catalog
```

### Celery

Tâches asynchrones configurées :
- Mise à jour des séries de lecture
- Génération de recommandations
- Nettoyage des sessions expirées

## Développement

### Structure du code

```
backend/
├── coko/                   # Configuration Django
│   ├── settings.py         # Paramètres
│   ├── urls.py            # URLs principales
│   ├── celery.py          # Configuration Celery
│   └── db_router.py       # Routeur de bases
├── auth_service/          # Service d'authentification
├── catalog_service/       # Service de catalogue
├── reading_service/       # Service de lecture
├── recommendation_service/ # Service de recommandations
├── requirements.txt       # Dépendances Python
├── docker-compose.yml     # Services Docker
└── Makefile              # Commandes de développement
```

### Standards de code

- **Formatage** : Black + isort
- **Linting** : flake8 + mypy
- **Tests** : pytest + coverage
- **Documentation** : Docstrings Google style

### Tests

```bash
# Tous les tests
make test

# Tests spécifiques
pytest auth_service/tests/
pytest -k "test_user_creation"
```

### Migrations

```bash
# Créer des migrations
python manage.py makemigrations auth_service

# Appliquer sur une base spécifique
python manage.py migrate --database=auth_db
```

## Déploiement

### Production

1. **Variables d'environnement**
```bash
DEBUG=False
SECRET_KEY=your-production-secret
ALLOWED_HOSTS=your-domain.com
```

2. **Base de données**
```bash
python manage.py check --deploy
python manage.py collectstatic
```

3. **Services**
- Gunicorn pour WSGI
- Nginx pour proxy inverse
- Supervisor pour gestion des processus

### Docker

```bash
# Build de l'image
docker build -t coko-backend .

# Déploiement avec compose
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

- **Santé** : `/health/` endpoint
- **Métriques** : Prometheus + Grafana
- **Logs** : Structured logging
- **Erreurs** : Sentry integration

## Sécurité

- JWT pour l'authentification
- CORS configuré
- Rate limiting
- Validation des données
- Chiffrement des mots de passe

## Support

Pour les questions de développement :
1. Vérifier la documentation
2. Consulter les logs : `tail -f logs/django.log`
3. Utiliser les health checks
4. Contacter l'équipe de développement

## Licence

Ce projet est sous licence propriétaire Coko.