# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Coko is a digital reading platform for West Africa with a Django backend using microservices architecture. The platform focuses on African-specific optimizations including low-bandwidth environments, mobile-first design, and local payment integration.

## Development Commands

### Essential Commands (via Makefile)
```bash
# Development setup
make dev-setup          # Initial development environment setup
make install            # Install Python dependencies
make migrate            # Run all database migrations
make runserver          # Start Django development server on 0.0.0.0:8000

# Testing
make test               # Run full test suite with coverage (min 80%)
make test-african       # Run African performance optimization tests
make test-performance   # Run performance-specific tests
pytest -m african_performance  # Run African network performance tests
pytest -m integration  # Run integration tests only

# Code Quality
make lint               # Run flake8 and mypy linting
make format             # Format code with black and isort

# Docker Services
make docker-up          # Start core services (postgres, redis, elasticsearch, minio)
make docker-up-full     # Start all services including Django app
make docker-down        # Stop all Docker services

# Celery
make celery             # Start Celery worker
make celery-beat        # Start Celery beat scheduler
```

### Database Management
```bash
# Multi-database migrations
python manage.py migrate --database=auth_db      # Auth service database
python manage.py migrate --database=catalog_db   # Catalog service database 
python manage.py migrate --database=reading_db   # Reading service database
python manage.py migrate --database=default      # Default database (recommendations, etc.)
```

## Architecture

### Microservices Structure
- **auth_service**: User authentication and management → `coko_auth` database
- **catalog_service**: Book catalog and metadata → `coko_catalog` database  
- **reading_service**: Reading sessions and progress tracking → `coko_reading` database
- **recommendation_service**: AI-powered book recommendations → `coko_main` database
- **shared_models**: Cross-service models and utilities

### Database Routing
The system uses multiple PostgreSQL databases with automatic routing via `coko/db_router.py`. Each service has its dedicated database, with the database router directing models to the correct database based on app labels.

### Key Technologies
- **Framework**: Django 4.2 + Django REST Framework
- **Databases**: PostgreSQL (multi-database setup)
- **Cache**: Redis + Django Cache Framework
- **Search**: Elasticsearch 8.11
- **Storage**: MinIO (S3-compatible) for development
- **Queue**: Celery with Redis broker
- **API**: REST + GraphQL (Graphene)

### African-Specific Features
- Low-bandwidth optimizations with Brotli compression
- Offline-first PWA capabilities
- African payment gateways (Orange Money, MTN MoMo, Wave)
- Geolocation-aware performance monitoring
- Mobile-first responsive design for 2G/3G networks

## Code Standards

### Quality Tools Configuration
- **Formatting**: Black (line length 88) + isort
- **Linting**: flake8 + mypy with strict typing
- **Testing**: pytest with 80% minimum coverage requirement
- **Import Organization**: Django/Third-party/First-party/Local sections

### Test Markers
Use pytest markers for targeted test execution:
- `african_performance`: African network optimization tests
- `african_monitoring`: African-specific monitoring tests  
- `integration`: Cross-service integration tests
- `performance`: General performance tests
- `auth`/`catalog`/`reading`/`recommendation`: Service-specific tests

### Development Workflow
1. Run `make dev-setup` for initial environment setup
2. Use `make docker-up` to start required services
3. Run `make migrate` to set up all databases
4. Start development with `make runserver`
5. Always run `make test` and `make lint` before committing

## Important Patterns

### Service Communication
Services communicate through:
- Direct database queries (within service boundaries)
- Service adapters in `shared_models/services.py`
- Event publishing system in `coko/events.py`
- Celery tasks for async operations

### Performance Considerations
- Multi-database queries require careful connection handling
- African performance tests validate <500ms response times
- Cache strategy optimized for limited bandwidth
- Async task processing for heavy operations

### File Locations
- Service configurations: `coko/settings.py`
- Database routing: `coko/db_router.py` 
- Service interfaces: `coko/interfaces.py`
- Docker services: `docker-compose.yml`
- Dependencies: `requirements.txt`