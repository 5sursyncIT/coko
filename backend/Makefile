# Makefile for Coko Backend Development

.PHONY: help install dev-setup migrate test lint format clean docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install              - Install Python dependencies"
	@echo "  dev-setup            - Set up development environment"
	@echo "  migrate              - Run database migrations"
	@echo "  test                 - Run tests"
	@echo "  test-african         - Run complete African performance tests"
	@echo "  test-african-quick   - Run quick African performance check"
	@echo "  test-performance     - Run performance tests only"
	@echo "  lint                 - Run code linting"
	@echo "  format               - Format code with black and isort"
	@echo "  clean                - Clean up temporary files"
	@echo "  docker-up            - Start development services with Docker"
	@echo "  docker-down          - Stop development services"
	@echo "  runserver            - Start Django development server"
	@echo "  celery               - Start Celery worker"
	@echo "  celery-beat          - Start Celery beat scheduler"

# Install dependencies
install:
	pip install -r requirements.txt

# Set up development environment
dev-setup: install
	cp .env.example .env
	@echo "Please edit .env file with your configuration"
	mkdir -p logs media staticfiles

# Database migrations
migrate:
	python manage.py makemigrations
	python manage.py migrate --database=default
	python manage.py migrate --database=auth_db
	python manage.py migrate --database=catalog_db
	python manage.py migrate --database=reading_db

# Create superuser
createsuperuser:
	python manage.py createsuperuser

# Run tests
test:
	pytest --cov=. --cov-report=html --cov-report=term

# African performance tests
test-african:
	python scripts/test_african_performance.py

# Quick African performance check
test-african-quick:
	pytest -m african_performance -v

# African monitoring tests
test-african-monitoring:
	pytest -m african_monitoring -v

# Performance tests only
test-performance:
	pytest -m performance -v

# Code linting
lint:
	flake8 .
	mypy .

# Code formatting
format:
	black .
	isort .

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Docker commands
docker-up:
	docker-compose up -d postgres redis elasticsearch minio

# Start all services including Django
docker-up-full:
	docker-compose --profile full up -d

# Stop Docker services
docker-down:
	docker-compose down

# Django development server
runserver:
	python manage.py runserver 0.0.0.0:8000

# Celery worker
celery:
	celery -A coko worker --loglevel=info

# Celery beat scheduler
celery-beat:
	celery -A coko beat --loglevel=info

# Collect static files
collectstatic:
	python manage.py collectstatic --noinput

# Load initial data
loaddata:
	python manage.py loaddata fixtures/*.json

# Create fixtures
dumpdata:
	python manage.py dumpdata auth_service.User --indent=2 > fixtures/users.json
	python manage.py dumpdata catalog_service --indent=2 > fixtures/catalog.json

# Check deployment readiness
check:
	python manage.py check --deploy

# Database shell
dbshell:
	python manage.py dbshell

# Django shell
shell:
	python manage.py shell

# Show Django URLs
show-urls:
	python manage.py show_urls

# Reset database (WARNING: This will delete all data)
reset-db:
	@echo "WARNING: This will delete all data. Press Ctrl+C to cancel."
	@sleep 5
	docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS coko_main;"
	docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS coko_auth;"
	docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS coko_catalog;"
	docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS coko_reading;"
	docker-compose exec postgres psql -U postgres -f /docker-entrypoint-initdb.d/init-databases.sql
	make migrate