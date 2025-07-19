# Documentation Technique - Projet Coko

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture Système](#architecture-système)
3. [Guide de Développement](#guide-de-développement)
4. [API Documentation](#api-documentation)
5. [Base de Données](#base-de-données)
6. [Déploiement](#déploiement)
7. [Monitoring et Observabilité](#monitoring-et-observabilité)
8. [Sécurité](#sécurité)
9. [Performance](#performance)
10. [Troubleshooting](#troubleshooting)

---

## Vue d'Ensemble

### Présentation du Projet

**Coko** est une plateforme de lecture numérique conçue spécifiquement pour l'Afrique, offrant un accès démocratisé aux livres numériques avec des fonctionnalités adaptées aux réalités locales.

### Objectifs Techniques

- **Scalabilité** : Architecture microservices pour supporter la croissance
- **Performance** : Optimisations pour les connexions limitées
- **Accessibilité** : Support multi-langues et interfaces adaptées
- **Fiabilité** : Haute disponibilité et récupération automatique
- **Sécurité** : Protection des données et transactions

### Stack Technologique

```yaml
Frontend:
  - Framework: Next.js + React + TypeScript
  - Build: Next.js (SSR/SSG)
  - UI: Tailwind CSS + Framer Motion
  - State: Redux Toolkit / Zustand
  - Testing: Jest + Cypress

Backend:
  - Language: Python
  - Framework: Django + Django REST Framework
  - GraphQL: Graphene-Django
  - API: REST + GraphQL
  - Message Queue: Celery + Redis
  - Task Scheduler: Celery Beat

Database:
  - Primary: PostgreSQL 15
  - Cache: Redis 7
  - Search: Elasticsearch 8
  - Storage: AWS S3 / MinIO

Infrastructure:
  - Containers: Docker
  - Orchestration: Kubernetes
  - Cloud: AWS
  - CI/CD: GitHub Actions
  - Monitoring: Prometheus + Grafana
  - Tracing: Jaeger
```

---

## Architecture Système

### Architecture Globale

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web App]
        MOBILE[Mobile App]
        PWA[PWA]
    end
    
    subgraph "API Gateway"
        GATEWAY[API Gateway]
        LB[Load Balancer]
    end
    
    subgraph "Microservices"
        AUTH[Auth Service]
        CATALOG[Catalog Service]
        READING[Reading Service]
        PAYMENT[Payment Service]
        GAMIF[Gamification Service]
        COMMUNITY[Community Service]
        ADMIN[Admin Service]
        NOTIF[Notification Service]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis)]
        ELASTIC[(Elasticsearch)]
        MINIO[(MinIO)]
    end
    
    WEB --> GATEWAY
    MOBILE --> GATEWAY
    PWA --> GATEWAY
    
    GATEWAY --> AUTH
    GATEWAY --> CATALOG
    GATEWAY --> READING
    GATEWAY --> PAYMENT
    GATEWAY --> GAMIF
    GATEWAY --> COMMUNITY
    GATEWAY --> ADMIN
    GATEWAY --> NOTIF
    
    AUTH --> POSTGRES
    CATALOG --> POSTGRES
    CATALOG --> ELASTIC
    READING --> POSTGRES
    PAYMENT --> POSTGRES
    GAMIF --> POSTGRES
    COMMUNITY --> POSTGRES
    
    AUTH --> REDIS
    CATALOG --> REDIS
    READING --> REDIS
    
    CATALOG --> MINIO
    READING --> MINIO
```

### Microservices Détaillés

#### 1. API Gateway

**Responsabilités :**
- Routage des requêtes
- Authentification et autorisation
- Rate limiting
- Load balancing
- Monitoring des requêtes

**Technologies :**
- Django + Django REST Framework
- JWT pour l'authentification (django-rest-framework-simplejwt)
- Redis pour le cache de session
- CORS handling (django-cors-headers)

**Endpoints principaux :**
```
GET  /health              # Health check
POST /api/v1/auth/*      # Proxy vers Auth Service
GET  /api/v1/catalog/*   # Proxy vers Catalog Service
POST /api/v1/reading/*   # Proxy vers Reading Service
POST /api/v1/payment/*   # Proxy vers Payment Service
POST /graphql            # GraphQL endpoint
```

#### 2. Auth Service

**Responsabilités :**
- Gestion des utilisateurs
- Authentification (JWT)
- Autorisation (RBAC)
- Gestion des sessions
- Vérification email
- Réinitialisation mot de passe

**Technologies :**
- Django + Django REST Framework
- django-rest-framework-simplejwt
- Custom User Model
- Django Permissions & Groups

**Base de données :** `coko_auth`

**Modèles Django principaux :**
```python
# models.py
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2)
    language = models.CharField(max_length=5, default='fr')
    subscription_status = models.CharField(max_length=20, default='free')
    is_email_verified = models.BooleanField(default=False)
    profile = models.JSONField(default=dict)
    
class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=50, unique=True)
    permissions = models.JSONField(default=list)
    
class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
```

**API Endpoints :**
```
POST /api/v1/auth/register/       # Inscription
POST /api/v1/auth/login/          # Connexion
POST /api/v1/auth/logout/         # Déconnexion
POST /api/v1/auth/refresh/        # Refresh token
GET  /api/v1/auth/profile/        # Profil utilisateur
PUT  /api/v1/auth/profile/        # Mise à jour profil
POST /api/v1/auth/forgot-password/ # Mot de passe oublié
POST /api/v1/auth/reset-password/  # Réinitialisation
POST /api/v1/auth/verify-email/    # Vérification email
```

#### 3. Catalog Service

**Responsabilités :**
- Gestion du catalogue de livres
- Recherche et filtrage (Elasticsearch)
- Métadonnées des livres
- Gestion des catégories
- Upload et traitement des fichiers

**Technologies :**
- Django + Django REST Framework
- django-elasticsearch-dsl
- django-filter
- Pillow (traitement d'images)
- django-storages (AWS S3)

**Base de données :** `coko_catalog`

**Modèles Django principaux :**
```python
# models.py
class Author(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=200)
    biography = models.TextField(blank=True)
    photo = models.ImageField(upload_to='authors/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)

class Publisher(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=300)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    isbn = models.CharField(max_length=17, unique=True, blank=True)
    language = models.CharField(max_length=5, default='fr')
    publication_date = models.DateField(null=True, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    format = models.CharField(max_length=10, choices=[('pdf', 'PDF'), ('epub', 'EPUB'), ('mobi', 'MOBI')])
    cover = models.ImageField(upload_to='covers/')
    file = models.FileField(upload_to='books/')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='XOF')
    is_free = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    authors = models.ManyToManyField(Author, related_name='books')
    categories = models.ManyToManyField(Category, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**API Endpoints :**
```
GET  /api/v1/catalog/books/           # Liste des livres
GET  /api/v1/catalog/books/{id}/      # Détails d'un livre
GET  /api/v1/catalog/books/search/    # Recherche de livres
GET  /api/v1/catalog/authors/         # Liste des auteurs
GET  /api/v1/catalog/categories/      # Liste des catégories
GET  /api/v1/catalog/publishers/      # Liste des éditeurs
POST /api/v1/catalog/books/           # Ajouter un livre (admin)
PUT  /api/v1/catalog/books/{id}/      # Modifier un livre (admin)
DELETE /api/v1/catalog/books/{id}/    # Supprimer un livre (admin)
```

#### 4. Reading Service

**Responsabilités :**
- Gestion de la lecture
- Synchronisation des progrès
- Annotations et marque-pages
- Mode hors ligne
- Export des notes (PDF/Markdown)
- Statistiques de lecture

**Technologies :**
- Django + Django REST Framework
- django-channels (WebSocket pour sync temps réel)
- ReportLab (génération PDF)
- django-storages (stockage annotations)

**Base de données :** `coko_reading`

**Modèles Django principaux :**
```python
# models.py
class ReadingProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('auth_service.User', on_delete=models.CASCADE)
    book = models.ForeignKey('catalog_service.Book', on_delete=models.CASCADE)
    current_page = models.PositiveIntegerField(default=0)
    total_pages = models.PositiveIntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    reading_time = models.DurationField(default=timedelta(0))
    last_read_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'book']

class Annotation(models.Model):
    ANNOTATION_TYPES = [
        ('highlight', 'Surlignage'),
        ('note', 'Note'),
        ('bookmark', 'Marque-page'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('auth_service.User', on_delete=models.CASCADE)
    book = models.ForeignKey('catalog_service.Book', on_delete=models.CASCADE)
    annotation_type = models.CharField(max_length=20, choices=ANNOTATION_TYPES)
    page_number = models.PositiveIntegerField()
    content = models.TextField(blank=True)
    selected_text = models.TextField(blank=True)
    position = models.JSONField(default=dict)  # Coordonnées, range, etc.
    color = models.CharField(max_length=7, default='#ffff00')  # Hex color
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ReadingSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey('auth_service.User', on_delete=models.CASCADE)
    book = models.ForeignKey('catalog_service.Book', on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    pages_read = models.PositiveIntegerField(default=0)
    device_type = models.CharField(max_length=20, default='web')
```

#### 5. Payment Service

**Responsabilités :**
- Gestion des abonnements
- Intégration Orange Money / Wave
- Historique des transactions
- Gestion des factures
- Micropaiements

**Technologies :**
- Django + Django REST Framework
- django-payments
- Celery (tâches asynchrones)
- django-subscriptions

**Intégrations :**
- Orange Money API
- Wave API
- Stripe (international)
- PayPal (international)

#### 6. Gamification Service

**Responsabilités :**
- Système de badges
- Points et niveaux
- Défis de lecture
- Classements
- Récompenses

**Technologies :**
- Django + Django REST Framework
- django-gamification
- Redis (cache des scores)
- Celery (calculs de points)

#### 7. Community Service

**Responsabilités :**
- Forums de discussion
- Critiques et notes
- Groupes de lecture
- Partage social
- Modération de contenu

**Technologies :**
- Django + Django REST Framework
- django-mptt (arbre de commentaires)
- django-taggit (tags)
- django-moderation

#### 8. Notification Service

**Responsabilités :**
- Notifications push
- Emails
- SMS
- Notifications in-app
- Templates de notifications

**Technologies :**
- Django + Django REST Framework
- django-notifications-hq
- Celery (envoi asynchrone)
- FCM (Firebase Cloud Messaging)
- Twilio (SMS)
- SendGrid (Email)

---

## Guide de Développement

### Prérequis

```bash
# Outils requis
Python >= 3.11
Docker >= 20.10
Docker Compose >= 2.0
Node.js >= 18 (pour le frontend)
PostgreSQL >= 15
Redis >= 7
Git >= 2.30

# Outils Python recommandés
pip >= 23.0
virtualenv ou conda
poetry (gestion des dépendances)

# Outils recommandés
VS Code avec extensions:
- Python
- Django
- React/Next.js
- Docker
- Kubernetes
- GitLens
- PostgreSQL
```

### Configuration de l'Environnement

#### 1. Clonage du Repository

```bash
git clone https://github.com/coko-africa/coko-platform.git
cd coko-platform
```

#### 2. Configuration des Variables d'Environnement

```bash
# Copier les fichiers d'exemple
cp .env.example .env
cp frontend/.env.example frontend/.env.local

# Éditer les variables selon votre environnement
vim .env
```

#### 3. Configuration de l'Environnement Python

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Ou avec Poetry
poetry install
poetry shell
```

#### 4. Démarrage de l'Environnement de Développement

```bash
# Démarrer les services d'infrastructure (PostgreSQL, Redis, Elasticsearch)
docker-compose -f docker-compose.dev.yml up -d postgres redis elasticsearch

# Vérifier que tous les services sont en cours d'exécution
docker-compose -f docker-compose.dev.yml ps

# Voir les logs
docker-compose -f docker-compose.dev.yml logs -f
```

#### 5. Initialisation de la Base de Données

```bash
# Créer les bases de données
python manage.py migrate --database=default
python manage.py migrate --database=auth_db
python manage.py migrate --database=catalog_db

# Créer un superutilisateur
python manage.py createsuperuser

# Charger les données de test
python manage.py loaddata fixtures/initial_data.json

# Ou utiliser les commandes personnalisées
python manage.py seed_database
```

#### 6. Démarrage du Serveur de Développement

```bash
# Démarrer le serveur Django
python manage.py runserver 0.0.0.0:8000

# Démarrer Celery (dans un autre terminal)
celery -A coko worker -l info

# Démarrer Celery Beat (planificateur de tâches)
celery -A coko beat -l info

# Démarrer le frontend (dans un autre terminal)
cd frontend
npm run dev
```

### Workflow de Développement

#### 1. Création d'une Nouvelle Feature

```bash
# Créer une branche depuis develop
git checkout develop
git pull origin develop
git checkout -b feature/nouvelle-fonctionnalite

# Développer la fonctionnalité
# ...

# Tester localement
make test

# Commit et push
git add .
git commit -m "feat: ajouter nouvelle fonctionnalité"
git push origin feature/nouvelle-fonctionnalite

# Créer une Pull Request
```

#### 2. Standards de Code

**Python/Django :**
```bash
# Formatting avec Black
black .

# Import sorting avec isort
isort .

# Linting avec flake8
flake8 .

# Type checking avec mypy
mypy .

# Tests avec pytest
pytest -v

# Coverage
pytest --cov=. --cov-report=html

# Django checks
python manage.py check
python manage.py check --deploy
```

**Frontend (Next.js/React) :**
```bash
# Linting
npm run lint

# Formatting avec Prettier
npm run format

# Type checking
npm run type-check

# Tests
npm run test

# Tests E2E
npm run test:e2e
```

#### 3. Convention de Commits

```
feat: nouvelle fonctionnalité
fix: correction de bug
chore: tâche de maintenance
docs: documentation
style: formatage
refactor: refactoring
test: ajout de tests
perf: amélioration de performance
```

### Tests

#### Tests Unitaires

**Backend (Django) :**
```python
# tests/test_auth_service.py
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_user(self):
        """Test creating a new user"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

class AuthAPITest(APITestCase):
    def test_register_user(self):
        """Test user registration via API"""
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'country': 'SN',
            'language': 'fr'
        }
        
        response = self.client.post('/api/v1/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

# tests/test_catalog_service.py
@pytest.mark.django_db
class TestBookModel:
    def test_book_creation(self):
        """Test creating a book instance"""
        from catalog_service.models import Book, Author
        
        author = Author.objects.create(name='Test Author')
        book = Book.objects.create(
            title='Test Book',
            description='A test book',
            language='fr',
            format='pdf'
        )
        book.authors.add(author)
        
        assert book.title == 'Test Book'
        assert book.authors.count() == 1
        assert str(book) == 'Test Book'
```

**Frontend (React/Next.js) :**
```typescript
// __tests__/components/BookCard.test.tsx
import { render, screen } from '@testing-library/react'
import { BookCard } from '@/components/BookCard'
import type { Book } from '@/types'

const mockBook: Book = {
  id: '1',
  title: 'Test Book',
  authors: [{ id: '1', name: 'Test Author' }],
  cover_url: '/test-cover.jpg',
  price: 1500,
  currency: 'XOF'
}

describe('BookCard', () => {
  it('renders book information correctly', () => {
    render(<BookCard book={mockBook} />)
    
    expect(screen.getByText('Test Book')).toBeInTheDocument()
    expect(screen.getByText('Test Author')).toBeInTheDocument()
    expect(screen.getByText('1500 XOF')).toBeInTheDocument()
  })
  
  it('displays book cover image', () => {
    render(<BookCard book={mockBook} />)
    
    const coverImage = screen.getByAltText('Test Book cover')
    expect(coverImage).toHaveAttribute('src', '/test-cover.jpg')
  })
})
```

#### Tests d'Intégration

**Django Tests d'Intégration :**
```bash
# Tests avec base de données de test
python manage.py test --settings=coko.settings.test

# Tests d'intégration avec Docker
docker-compose -f docker-compose.test.yml up --build

# Tests API complets avec pytest
pytest tests/integration/ -v

# Tests avec coverage
pytest --cov=. --cov-report=html tests/integration/
```

**Tests End-to-End :**
```bash
# Tests E2E avec Playwright
npm run test:e2e

# Tests E2E en mode headless
npm run test:e2e:headless

# Tests E2E avec rapport
npm run test:e2e:report
```

---

## API Documentation

### Authentification

Toutes les API (sauf `/auth/login` et `/auth/register`) nécessitent un token JWT.

**Header requis :**
```
Authorization: Bearer <jwt_token>
```

### Endpoints Principaux

#### Auth Service

```yaml
POST /auth/register:
  description: Inscription d'un nouvel utilisateur
  body:
    email: string (required)
    password: string (required, min 8 chars)
    name: string (required)
    country: string (required)
    language: string (optional, default: 'fr')
  response:
    201:
      user: User
      token: string
    400:
      error: string

POST /auth/login:
  description: Connexion utilisateur
  body:
    email: string (required)
    password: string (required)
  response:
    200:
      user: User
      token: string
    401:
      error: string

GET /auth/profile:
  description: Récupérer le profil utilisateur
  headers:
    Authorization: Bearer <token>
  response:
    200:
      user: User
    401:
      error: string
```

#### Catalog Service

```yaml
GET /catalog/books:
  description: Liste des livres avec pagination
  query:
    page: integer (default: 1)
    limit: integer (default: 20, max: 100)
    category: string (optional)
    language: string (optional)
    search: string (optional)
  response:
    200:
      books: Book[]
      pagination:
        page: integer
        limit: integer
        total: integer
        totalPages: integer

GET /catalog/books/{id}:
  description: Détails d'un livre
  params:
    id: string (UUID)
  response:
    200:
      book: Book
    404:
      error: string

GET /catalog/books/search:
  description: Recherche de livres
  query:
    q: string (required, min 3 chars)
    filters: object (optional)
  response:
    200:
      books: Book[]
      facets: object
      total: integer
```

### Modèles de Données

#### User
```typescript
interface User {
  id: string
  email: string
  name: string
  avatar?: string
  country: string
  language: string
  subscription?: Subscription
  preferences: UserPreferences
  createdAt: string
  updatedAt: string
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  fontSize: 'small' | 'medium' | 'large'
  notifications: {
    email: boolean
    push: boolean
    sms: boolean
  }
}
```

#### Book
```typescript
interface Book {
  id: string
  title: string
  description: string
  isbn?: string
  language: string
  authors: Author[]
  categories: Category[]
  publisher?: Publisher
  publishedAt?: string
  pageCount?: number
  fileUrl: string
  coverUrl: string
  metadata: BookMetadata
  stats: BookStats
  createdAt: string
  updatedAt: string
}

interface BookMetadata {
  format: 'pdf' | 'epub' | 'mobi'
  fileSize: number
  drm: boolean
  quality: 'low' | 'medium' | 'high'
}

interface BookStats {
  downloads: number
  rating: number
  reviewCount: number
}
```

### Codes d'Erreur

```yaml
HTTP Status Codes:
  200: OK - Requête réussie
  201: Created - Ressource créée
  400: Bad Request - Données invalides
  401: Unauthorized - Non authentifié
  403: Forbidden - Non autorisé
  404: Not Found - Ressource non trouvée
  409: Conflict - Conflit (ex: email déjà utilisé)
  422: Unprocessable Entity - Validation échouée
  429: Too Many Requests - Rate limit dépassé
  500: Internal Server Error - Erreur serveur
  503: Service Unavailable - Service indisponible

Error Response Format:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Les données fournies sont invalides",
    "details": {
      "field": "email",
      "reason": "Format d'email invalide"
    }
  }
}
```

---

## Base de Données

### Architecture

Chaque microservice possède sa propre base de données PostgreSQL pour assurer l'isolation et la scalabilité.

```
coko_auth        # Service d'authentification
coko_catalog     # Catalogue de livres
coko_reading     # Gestion de la lecture
coko_payment     # Paiements et abonnements
coko_gamification # Système de gamification
coko_community   # Communauté et social
```

### Migrations

#### Structure des Migrations

```
migrations/
├── auth/
│   ├── 001_create_users_table.up.sql
│   ├── 001_create_users_table.down.sql
│   ├── 002_create_roles_table.up.sql
│   └── 002_create_roles_table.down.sql
├── catalog/
│   ├── 001_create_books_table.up.sql
│   └── 001_create_books_table.down.sql
└── ...
```

#### Exécution des Migrations

```bash
# Appliquer toutes les migrations
make db-migrate

# Appliquer les migrations d'un service spécifique
make db-migrate-auth

# Rollback de la dernière migration
make db-rollback

# Statut des migrations
make db-status
```

### Optimisations

#### Index Recommandés

```sql
-- Table users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Table books
CREATE INDEX idx_books_title ON books USING gin(to_tsvector('french', title));
CREATE INDEX idx_books_language ON books(language);
CREATE INDEX idx_books_created_at ON books(created_at);

-- Table reading_progress
CREATE INDEX idx_reading_progress_user_book ON reading_progress(user_id, book_id);
CREATE INDEX idx_reading_progress_last_read ON reading_progress(last_read_at);
```

#### Partitioning

```sql
-- Partitioning par date pour les logs
CREATE TABLE audit_logs (
    id UUID DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Partitions mensuelles
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Backup et Restauration

#### Backup Automatique

```bash
#!/bin/bash
# Script de backup quotidien

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup de chaque base
for db in coko_auth coko_catalog coko_reading coko_payment coko_gamification coko_community; do
    pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $db > $BACKUP_DIR/${db}_${DATE}.sql
    gzip $BACKUP_DIR/${db}_${DATE}.sql
done

# Upload vers S3
aws s3 sync $BACKUP_DIR s3://coko-backups/$(date +%Y/%m/%d)/

# Nettoyage des backups locaux > 7 jours
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

#### Restauration

```bash
# Restaurer une base spécifique
gunzip -c backup_file.sql.gz | psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $DATABASE_NAME

# Restauration point-in-time
pg_basebackup -h $POSTGRES_HOST -D /var/lib/postgresql/restore -U $POSTGRES_USER -v -P -W
```

---

## Déploiement

### Environnements

```yaml
Environments:
  development:
    url: http://localhost:5173
    api: http://localhost:3000
    database: Local PostgreSQL
    
  staging:
    url: https://staging.coko.africa
    api: https://api-staging.coko.africa
    database: AWS RDS
    
  production:
    url: https://coko.africa
    api: https://api.coko.africa
    database: AWS RDS (Multi-AZ)
```

### Infrastructure AWS

#### Architecture

```
VPC (10.0.0.0/16)
├── Public Subnets (10.0.1.0/24, 10.0.2.0/24)
│   ├── NAT Gateway
│   ├── Application Load Balancer
│   └── Bastion Host
├── Private Subnets (10.0.10.0/24, 10.0.11.0/24)
│   ├── EKS Worker Nodes
│   ├── RDS Instances
│   └── ElastiCache
└── Database Subnets (10.0.20.0/24, 10.0.21.0/24)
    └── RDS Subnet Group
```

#### Services AWS Utilisés

```yaml
Compute:
  - EKS (Kubernetes)
  - EC2 (Worker Nodes)
  - Fargate (Serverless containers)

Database:
  - RDS PostgreSQL (Multi-AZ)
  - ElastiCache Redis
  - OpenSearch (Elasticsearch)

Storage:
  - S3 (Fichiers statiques)
  - EFS (Shared storage)
  - EBS (Block storage)

Networking:
  - VPC
  - Application Load Balancer
  - CloudFront (CDN)
  - Route 53 (DNS)

Security:
  - IAM
  - Secrets Manager
  - Certificate Manager
  - WAF

Monitoring:
  - CloudWatch
  - X-Ray
  - Config
```

### Déploiement Kubernetes

#### Structure des Manifests

```
k8s/
├── base/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   └── services/
│       ├── django-backend/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   └── hpa.yaml
│       ├── celery-worker/
│       │   ├── deployment.yaml
│       │   └── hpa.yaml
│       ├── celery-beat/
│       │   └── deployment.yaml
│       ├── postgres/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   └── pvc.yaml
│       ├── redis/
│       │   ├── deployment.yaml
│       │   └── service.yaml
│       └── elasticsearch/
│           ├── deployment.yaml
│           ├── service.yaml
│           └── pvc.yaml
├── overlays/
│   ├── development/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   └── production/
│       ├── kustomization.yaml
│       └── patches/
└── monitoring/
    ├── prometheus/
    ├── grafana/
    └── jaeger/
```

#### Déploiement avec Kustomize

```bash
# Déploiement staging
kubectl apply -k k8s/overlays/staging

# Vérification du déploiement
kubectl get pods -n coko-staging
kubectl get services -n coko-staging

# Rollout status
kubectl rollout status deployment/django-backend -n coko-staging
```

#### Déploiement Docker Compose

**Production :**
```yaml
version: '3.8'
services:
  django-backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=coko.settings.production
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://coko_user:${POSTGRES_PASSWORD}@postgres:5432/coko_prod
      - REDIS_URL=redis://redis:6379/0
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    depends_on:
      - postgres
      - redis
      - elasticsearch
    volumes:
      - media_files:/app/media
      - static_files:/app/staticfiles

  celery-worker:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A coko worker -l info
    environment:
      - DJANGO_SETTINGS_MODULE=coko.settings.production
      - DATABASE_URL=postgresql://coko_user:${POSTGRES_PASSWORD}@postgres:5432/coko_prod
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - media_files:/app/media

  celery-beat:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A coko beat -l info
    environment:
      - DJANGO_SETTINGS_MODULE=coko.settings.production
      - DATABASE_URL=postgresql://coko_user:${POSTGRES_PASSWORD}@postgres:5432/coko_prod
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - media_files:/app/media

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: coko_prod
      POSTGRES_USER: coko_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - static_files:/var/www/static
      - media_files:/var/www/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - django-backend

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
  media_files:
  static_files:
```

#### Blue/Green Deployment

```yaml
# Service avec sélecteur version
apiVersion: v1
kind: Service
metadata:
  name: django-backend
  namespace: coko-prod
spec:
  selector:
    app: django-backend
    version: blue  # Changé vers 'green' lors du switch
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP

---
# Deployment Blue
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-backend-blue
  namespace: coko-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: django-backend
      version: blue
  template:
    metadata:
      labels:
        app: django-backend
        version: blue
    spec:
      containers:
      - name: django-backend
        image: coko/django-backend:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DJANGO_SETTINGS_MODULE
          value: "coko.settings.production"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: django-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### CI/CD Pipeline

#### GitHub Actions Workflow

```yaml
name: Deploy Django Backend to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: coko/django-backend

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_coko
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_coko
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          python manage.py test
          pytest --cov=. --cov-report=xml
          
      - name: Code quality checks
        run: |
          cd backend
          black --check .
          isort --check-only .
          flake8 .
          mypy .

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v3
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --region us-west-2 --name coko-prod-cluster
      
      - name: Deploy to production
        run: |
          kubectl apply -k k8s/overlays/production
          kubectl rollout status deployment -n coko-prod --timeout=600s
      
      - name: Run smoke tests
        run: |
          ./scripts/smoke-tests.sh https://api.coko.africa
```

---

## Monitoring et Observabilité

### Stack de Monitoring

```yaml
Metrics:
  - Prometheus (Collection)
  - Grafana (Visualisation)
  - AlertManager (Alertes)

Logs:
  - Fluentd (Collection)
  - Elasticsearch (Stockage)
  - Kibana (Visualisation)

Tracing:
  - Jaeger (Distributed tracing)
  - OpenTelemetry (Instrumentation)

Uptime:
  - Pingdom (External monitoring)
  - StatusPage (Status page)
```

### Métriques Clés

#### Application Metrics

```yaml
Performance:
  - response_time_seconds (histogram)
  - request_duration_seconds (histogram)
  - requests_total (counter)
  - requests_per_second (gauge)

Business:
  - user_registrations_total (counter)
  - book_downloads_total (counter)
  - payment_transactions_total (counter)
  - active_users (gauge)

Errors:
  - error_rate (gauge)
  - http_errors_total (counter)
  - database_errors_total (counter)

Infrastructure:
  - cpu_usage_percent (gauge)
  - memory_usage_percent (gauge)
  - disk_usage_percent (gauge)
  - network_io_bytes (counter)
```

#### Dashboards Grafana

**Dashboard Application :**
```json
{
  "dashboard": {
    "title": "Coko Application Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### Alertes

#### Règles d'Alerte Prometheus

```yaml
groups:
- name: coko.rules
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"
  
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }} seconds"
  
  - alert: DatabaseConnectionsHigh
    expr: pg_stat_activity_count > 80
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High number of database connections"
      description: "{{ $value }} active connections to database"
```

#### Configuration AlertManager

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@coko.africa'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'critical-alerts'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/...'
    channel: '#alerts-critical'
    title: 'Critical Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
  
- name: 'warning-alerts'
  email_configs:
  - to: 'devops@coko.africa'
    subject: 'Warning Alert'
    body: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### Logging

#### Structure des Logs

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "service": "auth-service",
  "trace_id": "abc123def456",
  "span_id": "789ghi012",
  "user_id": "user-123",
  "message": "User login successful",
  "metadata": {
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "duration_ms": 150
  }
}
```

#### Configuration Fluentd

```xml
<source>
  @type tail
  path /var/log/containers/*.log
  pos_file /var/log/fluentd-containers.log.pos
  tag kubernetes.*
  format json
  time_key timestamp
  time_format %Y-%m-%dT%H:%M:%S.%NZ
</source>

<filter kubernetes.**>
  @type kubernetes_metadata
</filter>

<match kubernetes.**>
  @type elasticsearch
  host elasticsearch.monitoring.svc.cluster.local
  port 9200
  index_name coko-logs
  type_name _doc
</match>
```

---

## Sécurité

### Authentification et Autorisation

#### JWT Configuration

```yaml
JWT_Settings:
  algorithm: RS256
  access_token_expiry: 15m
  refresh_token_expiry: 7d
  issuer: "coko.africa"
  audience: "coko-api"
```

#### RBAC (Role-Based Access Control)

```yaml
Roles:
  admin:
    permissions:
      - "users:*"
      - "books:*"
      - "system:*"
  
  moderator:
    permissions:
      - "books:read"
      - "books:update"
      - "users:read"
      - "community:moderate"
  
  user:
    permissions:
      - "books:read"
      - "profile:update"
      - "reading:*"
      - "community:participate"
  
  guest:
    permissions:
      - "books:read:public"
      - "catalog:browse"
```

### Chiffrement

#### Données en Transit

```yaml
TLS_Configuration:
  version: TLS 1.3
  cipher_suites:
    - TLS_AES_256_GCM_SHA384
    - TLS_CHACHA20_POLY1305_SHA256
    - TLS_AES_128_GCM_SHA256
  
  certificates:
    - domain: "*.coko.africa"
      issuer: "Let's Encrypt"
      auto_renewal: true
```

#### Données au Repos

```yaml
Encryption_at_Rest:
  database:
    engine: PostgreSQL
    encryption: AES-256
    key_management: AWS KMS
  
  storage:
    s3_encryption: AES-256
    kms_key: "arn:aws:kms:us-west-2:123456789:key/..."
  
  secrets:
    kubernetes_secrets: encrypted
    aws_secrets_manager: true
```

### Sécurité des API

#### Rate Limiting

```yaml
Rate_Limits:
  authentication:
    login: 5 requests/minute
    register: 3 requests/minute
    password_reset: 2 requests/hour
  
  api_calls:
    authenticated: 1000 requests/hour
    anonymous: 100 requests/hour
  
  downloads:
    book_download: 10 downloads/hour
    concurrent_downloads: 3
```

#### Input Validation

```go
// Exemple de validation en Go
type CreateUserRequest struct {
    Email    string `json:"email" validate:"required,email,max=255"`
    Password string `json:"password" validate:"required,min=8,max=128"`
    Name     string `json:"name" validate:"required,min=2,max=100"`
    Country  string `json:"country" validate:"required,iso3166_1_alpha2"`
}

func (r *CreateUserRequest) Validate() error {
    validate := validator.New()
    return validate.Struct(r)
}
```

### Audit et Compliance

#### Audit Logs

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index pour les requêtes fréquentes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

#### GDPR Compliance

```yaml
GDPR_Features:
  data_export:
    endpoint: "/api/user/export"
    format: JSON
    includes: ["profile", "reading_history", "preferences"]
  
  data_deletion:
    endpoint: "/api/user/delete"
    soft_delete: true
    retention_period: 30 days
    anonymization: true
  
  consent_management:
    tracking_consent: required
    marketing_consent: optional
    analytics_consent: optional
```

---

## Performance

### Optimisations Frontend

#### Code Splitting

```typescript
// Vue.js lazy loading
const BookReader = () => import('@/components/BookReader.vue')
const AdminPanel = () => import('@/views/AdminPanel.vue')

// Route-based splitting
const routes = [
  {
    path: '/read/:id',
    component: () => import('@/views/ReadingView.vue')
  },
  {
    path: '/admin',
    component: () => import('@/views/AdminView.vue')
  }
]
```

#### Asset Optimization

```javascript
// Vite configuration
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          ui: ['@headlessui/vue', '@heroicons/vue']
        }
      }
    }
  },
  
  // Image optimization
  plugins: [
    vue(),
    viteImageOptimize({
      gifsicle: { optimizationLevel: 7 },
      mozjpeg: { quality: 80 },
      pngquant: { quality: [0.65, 0.8] },
      svgo: { plugins: [{ name: 'removeViewBox', active: false }] }
    })
  ]
})
```

#### Caching Strategy

```typescript
// Service Worker pour le cache
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/books/')) {
    event.respondWith(
      caches.open('books-cache').then(cache => {
        return cache.match(event.request).then(response => {
          if (response) {
            // Retourner depuis le cache
            return response
          }
          
          // Fetch et cache
          return fetch(event.request).then(fetchResponse => {
            cache.put(event.request, fetchResponse.clone())
            return fetchResponse
          })
        })
      })
    )
  }
})
```

### Optimisations Backend

#### Database Query Optimization

```sql
-- Requête optimisée avec index
EXPLAIN ANALYZE
SELECT b.*, a.name as author_name
FROM books b
JOIN book_authors ba ON b.id = ba.book_id
JOIN authors a ON ba.author_id = a.id
WHERE b.language = 'fr'
  AND b.created_at > '2024-01-01'
ORDER BY b.created_at DESC
LIMIT 20;

-- Index composite pour cette requête
CREATE INDEX idx_books_language_created_at 
ON books(language, created_at DESC);
```

#### Connection Pooling

```go
// Configuration du pool de connexions
config := pgxpool.Config{
    MaxConns:        30,
    MinConns:        5,
    MaxConnLifetime: time.Hour,
    MaxConnIdleTime: time.Minute * 30,
}

pool, err := pgxpool.ConnectConfig(context.Background(), &config)
if err != nil {
    log.Fatal("Failed to create connection pool:", err)
}
```

#### Caching avec Redis

```go
// Cache des résultats de recherche
func (s *CatalogService) SearchBooks(query string) ([]Book, error) {
    cacheKey := fmt.Sprintf("search:%s", query)
    
    // Vérifier le cache
    cached, err := s.redis.Get(cacheKey).Result()
    if err == nil {
        var books []Book
        json.Unmarshal([]byte(cached), &books)
        return books, nil
    }
    
    // Recherche en base
    books, err := s.db.SearchBooks(query)
    if err != nil {
        return nil, err
    }
    
    // Mettre en cache (5 minutes)
    booksJSON, _ := json.Marshal(books)
    s.redis.Set(cacheKey, booksJSON, 5*time.Minute)
    
    return books, nil
}
```

### CDN et Optimisations Réseau

#### CloudFront Configuration

```yaml
CloudFront_Settings:
  origins:
    - domain: api.coko.africa
      path_pattern: "/api/*"
      cache_policy: no-cache
    
    - domain: assets.coko.africa
      path_pattern: "/static/*"
      cache_policy: max-age=31536000
  
  behaviors:
    - path_pattern: "*.js"
      compress: true
      cache_policy: max-age=86400
    
    - path_pattern: "*.css"
      compress: true
      cache_policy: max-age=86400
    
    - path_pattern: "*.pdf"
      compress: false
      cache_policy: max-age=604800
```

#### Compression

```nginx
# Configuration Nginx
server {
    listen 80;
    server_name api.coko.africa;
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Headers de cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API sans cache
    location /api/ {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        proxy_pass http://backend;
    }
}
```

---

## Troubleshooting

### Problèmes Courants

#### 1. Service Indisponible

**Symptômes :**
- Erreurs 503 Service Unavailable
- Timeouts de connexion
- Pods en état CrashLoopBackOff

**Diagnostic :**
```bash
# Vérifier l'état des pods
kubectl get pods -n coko-staging

# Logs du pod en erreur
kubectl logs <pod-name> -n coko-staging --previous

# Décrire le pod pour voir les events
kubectl describe pod <pod-name> -n coko-staging

# Vérifier les ressources
kubectl top pods -n coko-staging
```

**Solutions :**
```bash
# Redémarrer le deployment
kubectl rollout restart deployment/<service-name> -n coko-staging

# Scaler temporairement
kubectl scale deployment/<service-name> --replicas=3 -n coko-staging

# Vérifier les limites de ressources
kubectl edit deployment/<service-name> -n coko-staging
```

#### 2. Performance Dégradée

**Symptômes :**
- Temps de réponse élevés
- Timeouts fréquents
- CPU/Mémoire élevés

**Diagnostic :**
```bash
# Métriques Prometheus
curl -G 'http://prometheus:9090/api/v1/query' \
  --data-urlencode 'query=rate(http_request_duration_seconds_sum[5m])/rate(http_request_duration_seconds_count[5m])'

# Profiling Go
go tool pprof http://service:8080/debug/pprof/profile

# Analyse des requêtes lentes PostgreSQL
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

**Solutions :**
```sql
-- Optimiser les requêtes lentes
EXPLAIN ANALYZE <slow_query>;

-- Ajouter des index manquants
CREATE INDEX CONCURRENTLY idx_name ON table(column);

-- Analyser les statistiques
ANALYZE table_name;
```

#### 3. Problèmes de Base de Données

**Symptômes :**
- Connexions refusées
- Deadlocks
- Corruption de données

**Diagnostic :**
```sql
-- Vérifier les connexions actives
SELECT count(*) FROM pg_stat_activity;

-- Identifier les requêtes bloquantes
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity 
    ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity 
    ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Vérifier l'intégrité
CHECKDB;
```

### Procédures d'Urgence

#### Rollback de Déploiement

```bash
#!/bin/bash
# Script de rollback d'urgence

NAMESPACE="coko-production"
SERVICE="$1"

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service-name>"
    exit 1
fi

echo "Rolling back $SERVICE in $NAMESPACE..."

# Rollback vers la version précédente
kubectl rollout undo deployment/$SERVICE -n $NAMESPACE

# Attendre que le rollback soit terminé
kubectl rollout status deployment/$SERVICE -n $NAMESPACE --timeout=300s

# Vérifier la santé du service
kubectl get pods -l app=$SERVICE -n $NAMESPACE

# Test de santé
SERVICE_URL=$(kubectl get service $SERVICE -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -f http://$SERVICE_URL/health || echo "Health check failed!"

echo "Rollback completed for $SERVICE"
```

#### Maintenance d'Urgence

```bash
#!/bin/bash
# Mode maintenance

# Activer la page de maintenance
kubectl patch ingress coko-ingress -n coko-production -p '{
  "metadata": {
    "annotations": {
      "nginx.ingress.kubernetes.io/default-backend": "maintenance-service"
    }
  }
}'

# Scaler les services à 0 (sauf critiques)
for service in catalog reading community gamification; do
    kubectl scale deployment $service --replicas=0 -n coko-production
done

echo "Maintenance mode activated"
echo "To disable: kubectl patch ingress coko-ingress -n coko-production -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/default-backend":null}}}'"
```

### Contacts d'Urgence

```yaml
Escalation_Matrix:
  Level_1_Support:
    - name: "Équipe DevOps"
      slack: "#devops-alerts"
      phone: "+221 XX XXX XXXX"
    
  Level_2_Support:
    - name: "Tech Lead"
      email: "tech-lead@coko.africa"
      phone: "+221 XX XXX XXXX"
    
  Level_3_Support:
    - name: "CTO"
      email: "cto@coko.africa"
      phone: "+221 XX XXX XXXX"

External_Vendors:
  AWS_Support:
    plan: "Business"
    phone: "+1-206-266-4064"
    case_url: "https://console.aws.amazon.com/support/"
  
  Database_Expert:
    company: "PostgreSQL Consulting"
    email: "emergency@pgconsulting.com"
    phone: "+33 X XX XX XX XX"
```

---

## Annexes

### Glossaire

- **API Gateway** : Point d'entrée unique pour toutes les requêtes API
- **Microservice** : Service autonome avec sa propre base de données
- **JWT** : JSON Web Token pour l'authentification
- **RBAC** : Role-Based Access Control
- **CDN** : Content Delivery Network
- **SLA** : Service Level Agreement
- **SLI** : Service Level Indicator
- **SLO** : Service Level Objective

### Références

- [Documentation Kubernetes](https://kubernetes.io/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Vue.js Guide](https://vuejs.org/guide/)
- [Go Documentation](https://golang.org/doc/)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)

---

*Cette documentation est maintenue par l'équipe technique de Coko.*
*Dernière mise à jour : Janvier 2024*
*Version : 1.0.0*