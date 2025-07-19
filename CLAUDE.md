# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Coko is a Django-based digital content distribution platform for West Africa. It's a microservices architecture designed for reading, publishing, and distributing digital content (ebooks, audiobooks, magazines, educational content).

**Main Languages:** Python (Django), JavaScript (planned frontend)
**Architecture:** Django microservices with multi-database setup
**Target Region:** West Africa (French-speaking markets)

## Common Development Commands

### Setup and Installation
```bash
# Navigate to backend directory
cd backend

# Install dependencies
make install
# OR
pip install -r requirements.txt

# Setup development environment
make dev-setup

# Start external services (PostgreSQL, Redis, Elasticsearch, MinIO)
make docker-up

# Run database migrations on all databases
make migrate

# Create superuser
make createsuperuser
```

### Development Server
```bash
# Start Django development server
make runserver
# OR
python manage.py runserver 0.0.0.0:8000

# Start Celery worker for async tasks
make celery

# Start Celery beat scheduler
make celery-beat
```

### Testing and Quality
```bash
# Run all tests with coverage
make test
# OR
pytest --cov=. --cov-report=html --cov-report=term

# Run specific service tests
pytest auth_service/tests/
pytest catalog_service/tests/
pytest reading_service/tests/
pytest recommendation_service/tests/

# Run single test
pytest -k "test_user_creation"

# Code linting and type checking
make lint
# OR
flake8 .
mypy .

# Code formatting
make format
# OR
black .
isort .
```

### Database Operations
```bash
# Create migrations for specific services
python manage.py makemigrations auth_service
python manage.py makemigrations catalog_service
python manage.py makemigrations reading_service
python manage.py makemigrations recommendation_service

# Apply migrations to specific databases
python manage.py migrate --database=auth_db
python manage.py migrate --database=catalog_db
python manage.py migrate --database=reading_db
python manage.py migrate --database=default

# Database shell
make dbshell

# Django shell
make shell
```

### Docker Operations
```bash
# Start all infrastructure services
make docker-up

# Start all services including Django app
make docker-up-full

# Stop all services
make docker-down

# Reset databases (WARNING: destructive)
make reset-db
```

## Code Architecture

### Multi-Database Architecture
The project uses Django's multi-database routing with 4 separate databases:

- **`coko_main` (default):** Main database for shared models and recommendation service
- **`coko_auth`:** User authentication and profiles
- **`coko_catalog`:** Book catalog and metadata
- **`coko_reading`:** Reading sessions and progress tracking

**Database Router:** `coko/db_router.py` automatically routes models to appropriate databases based on app labels.

### Service Structure
```
backend/
├── coko/                     # Django project configuration
│   ├── settings.py          # Main settings with multi-DB config
│   ├── db_router.py         # Database routing logic
│   ├── celery.py           # Celery configuration
│   └── urls.py             # Main URL routing
├── auth_service/           # User authentication & management
├── catalog_service/        # Book catalog & search
├── reading_service/        # Reading sessions & progress
└── recommendation_service/ # ML recommendations & analytics
```

### Key Technologies
- **Backend Framework:** Django 4.2 + Django REST Framework
- **Databases:** PostgreSQL (multi-database setup)
- **Search:** Elasticsearch
- **Cache/Queue:** Redis + Celery
- **File Storage:** S3/MinIO
- **API:** REST + GraphQL (Graphene)

### Authentication
- **JWT-based authentication** using `djangorestframework-simplejwt`
- **Custom User model:** `auth_service.User`
- **Session management:** Redis-backed sessions

### Async Task Processing
- **Celery workers** for background tasks (recommendations, cleanup)
- **Celery beat** for scheduled tasks
- **Management commands** in `recommendation_service/management/commands/`

## Important Configuration Notes

### Environment Variables
Key environment variables (check `.env.example` in backend/):
- `DEBUG`: Set to False for production
- `SECRET_KEY`: Django secret key
- `DB_*`: Database connection settings
- `REDIS_URL`: Redis connection
- `ELASTICSEARCH_URL`: Search engine connection

### Multi-Database Model Usage
When working with models, they're automatically routed to correct databases:
```python
# These go to appropriate databases automatically
from auth_service.models import User        # → coko_auth
from catalog_service.models import Book     # → coko_catalog
from reading_service.models import Session # → coko_reading
```

### Test Configuration
- **pytest configuration:** `pytest.ini`
- **Coverage requirement:** ≥80%
- **Test markers:** Available for different test types (unit, integration, api, etc.)
- **Database isolation:** Tests use `--reuse-db` flag for performance

## Development Workflow

1. **Start services:** `make docker-up`
2. **Run migrations:** `make migrate` 
3. **Start dev server:** `make runserver`
4. **Run tests before committing:** `make test`
5. **Format code:** `make format`
6. **Check code quality:** `make lint`

## Performance Considerations

- **Target audience:** West African users with potentially slower connections
- **Core Web Vitals targets:** LCP ≤ 2.5s, FID ≤ 100ms, CLS ≤ 0.1
- **API response time target:** ≤ 500ms from Africa
- **Mobile 3G target:** ≤ 3s page load time

## Internationalization

- **Primary language:** French (`LANGUAGE_CODE = 'fr'`)
- **Timezone:** `Africa/Dakar`
- **Supported languages:** French, English, Wolof, Arabic
- **Cultural focus:** West African markets