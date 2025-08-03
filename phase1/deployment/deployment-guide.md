# Guide de Déploiement - Projet Coko

## 🎯 Vue d'Ensemble

Ce guide détaille le processus de déploiement de la plateforme Coko, optimisée pour le marché africain avec support des paiements mobiles natifs.

### Architecture de Déploiement

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION ENVIRONMENT                   │
├─────────────────────────────────────────────────────────────┤
│  Load Balancer (Nginx)                                     │
│  ├── Frontend (Next.js) - Vercel/AWS CloudFront           │
│  └── Backend (Django) - AWS ECS/DigitalOcean              │
├─────────────────────────────────────────────────────────────┤
│  Database Layer                                             │
│  ├── PostgreSQL (AWS RDS/DigitalOcean Managed)            │
│  ├── Redis (AWS ElastiCache/DigitalOcean)                 │
│  └── Elasticsearch (AWS OpenSearch/Self-hosted)           │
├─────────────────────────────────────────────────────────────┤
│  Storage & CDN                                              │
│  ├── Static Files (AWS S3/DigitalOcean Spaces)           │
│  ├── Media Files (AWS S3/DigitalOcean Spaces)             │
│  └── CDN (CloudFront/DigitalOcean CDN)                    │
├─────────────────────────────────────────────────────────────┤
│  Monitoring & Logging                                       │
│  ├── Application Monitoring (Sentry)                       │
│  ├── Infrastructure Monitoring (Prometheus/Grafana)        │
│  └── Log Aggregation (ELK Stack/Loki)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌍 Stratégie Multi-Région

### Régions Cibles

1. **Région Principale** : Europe (Paris/Frankfurt)
   - Latence optimale pour l'Afrique de l'Ouest
   - Conformité RGPD
   - Coûts réduits

2. **Région Secondaire** : Afrique du Sud (Cape Town)
   - Latence réduite pour l'Afrique australe
   - Redondance géographique
   - Conformité locale

3. **Edge Locations** : CDN global
   - Cache statique proche des utilisateurs
   - Optimisation des performances

### Configuration Multi-Région

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Frontend
  frontend:
    image: coko/frontend:latest
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=${API_URL}
      - NEXT_PUBLIC_CDN_URL=${CDN_URL}
      - NEXT_PUBLIC_REGION=${DEPLOYMENT_REGION}
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure

  # Backend API
  backend:
    image: coko/backend:latest
    environment:
      - DJANGO_SETTINGS_MODULE=coko.settings.production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
      - REGION=${DEPLOYMENT_REGION}
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Worker Celery
  worker:
    image: coko/backend:latest
    command: celery -A coko worker -l info
    environment:
      - DJANGO_SETTINGS_MODULE=coko.settings.production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure

  # Scheduler Celery
  scheduler:
    image: coko/backend:latest
    command: celery -A coko beat -l info
    environment:
      - DJANGO_SETTINGS_MODULE=coko.settings.production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure

  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure

networks:
  default:
    driver: overlay
    attachable: true

volumes:
  postgres_data:
  redis_data:
```

---

## 🐳 Configuration Docker

### Dockerfile Backend

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Création de l'utilisateur non-root
RUN useradd --create-home --shell /bin/bash coko

# Répertoire de travail
WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Permissions
RUN chown -R coko:coko /app
USER coko

# Collection des fichiers statiques
RUN python manage.py collectstatic --noinput

# Port d'exposition
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Commande par défaut
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "coko.wsgi:application"]
```

### Dockerfile Frontend

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

# Répertoire de travail
WORKDIR /app

# Installation des dépendances
COPY package*.json ./
RUN npm ci --only=production

# Copie du code source
COPY . .

# Build de l'application
RUN npm run build

# Image de production
FROM node:18-alpine AS runner

# Variables d'environnement
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Création de l'utilisateur non-root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Répertoire de travail
WORKDIR /app

# Copie des fichiers nécessaires
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Permissions
RUN chown -R nextjs:nodejs /app
USER nextjs

# Port d'exposition
EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Commande par défaut
CMD ["node", "server.js"]
```

---

## ☁️ Déploiement Cloud

### AWS Deployment

#### Infrastructure as Code (Terraform)

```hcl
# infrastructure/aws/main.tf
provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "coko_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "coko-vpc"
    Environment = var.environment
  }
}

# Subnets
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.coko_vpc.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  map_public_ip_on_launch = true

  tags = {
    Name = "coko-public-subnet-${count.index + 1}"
    Environment = var.environment
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.coko_vpc.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "coko-private-subnet-${count.index + 1}"
    Environment = var.environment
  }
}

# RDS Database
resource "aws_db_instance" "coko_db" {
  identifier = "coko-${var.environment}"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true
  
  db_name  = "coko"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.coko.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = var.environment != "production"
  
  tags = {
    Name = "coko-db"
    Environment = var.environment
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "coko" {
  name = "coko-${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name = "coko-cluster"
    Environment = var.environment
  }
}

# ECS Service
resource "aws_ecs_service" "coko_backend" {
  name            = "coko-backend"
  cluster         = aws_ecs_cluster.coko.id
  task_definition = aws_ecs_task_definition.coko_backend.arn
  desired_count   = var.backend_desired_count
  
  launch_type = "FARGATE"
  
  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs_tasks.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.coko_backend.arn
    container_name   = "coko-backend"
    container_port   = 8000
  }
  
  depends_on = [aws_lb_listener.coko]
  
  tags = {
    Name = "coko-backend-service"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "coko" {
  name               = "coko-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  
  enable_deletion_protection = var.environment == "production"
  
  tags = {
    Name = "coko-alb"
    Environment = var.environment
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "coko_frontend" {
  origin {
    domain_name = var.frontend_domain
    origin_id   = "coko-frontend"
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  
  aliases = [var.frontend_domain]
  
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "coko-frontend"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }
  
  # Cache behavior pour les assets statiques
  ordered_cache_behavior {
    path_pattern     = "/static/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "coko-frontend"
    compress         = true
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    viewer_protocol_policy = "redirect-to-https"
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    acm_certificate_arn = aws_acm_certificate.coko.arn
    ssl_support_method  = "sni-only"
  }
  
  tags = {
    Name = "coko-cloudfront"
    Environment = var.environment
  }
}
```

#### Déploiement avec GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: eu-west-3
  ECR_REPOSITORY_BACKEND: coko/backend
  ECR_REPOSITORY_FRONTEND: coko/frontend
  ECS_SERVICE: coko-backend
  ECS_CLUSTER: coko-production
  ECS_TASK_DEFINITION: coko-backend

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Run tests
      run: |
        # Tests backend
        cd backend
        python -m pytest
        
        # Tests frontend
        cd ../frontend
        npm ci
        npm run test

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build and push backend image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        cd backend
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG
        echo "backend_image=$ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG" >> $GITHUB_OUTPUT
    
    - name: Deploy to Vercel (Frontend)
      uses: amondnet/vercel-action@v25
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        vercel-args: '--prod'
        working-directory: ./frontend
    
    - name: Update ECS service
      run: |
        # Mettre à jour la définition de tâche
        aws ecs update-service \
          --cluster $ECS_CLUSTER \
          --service $ECS_SERVICE \
          --force-new-deployment
    
    - name: Wait for deployment
      run: |
        aws ecs wait services-stable \
          --cluster $ECS_CLUSTER \
          --services $ECS_SERVICE
    
    - name: Notify deployment
      if: always()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 🔧 Configuration de Production

### Settings Django

```python
# backend/coko/settings/production.py
from .base import *
import os
import dj_database_url
from urllib.parse import urlparse

# Security
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Database
DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL')),
    'auth_db': dj_database_url.parse(os.getenv('AUTH_DATABASE_URL')),
    'catalog_db': dj_database_url.parse(os.getenv('CATALOG_DATABASE_URL')),
    'reading_db': dj_database_url.parse(os.getenv('READING_DATABASE_URL')),
    'recommendation_db': dj_database_url.parse(os.getenv('RECOMMENDATION_DATABASE_URL')),
}

# Cache
redis_url = urlparse(os.getenv('REDIS_URL'))
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'coko',
        'TIMEOUT': 300,
    }
}

# Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Storage
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'eu-west-3')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Static files
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'sentry': {
            'class': 'sentry_sdk.integrations.logging.SentryHandler',
            'level': 'ERROR',
        },
    },
    'root': {
        'handlers': ['console', 'sentry'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
        'coko': {
            'handlers': ['console', 'sentry'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Sentry
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(auto_enabling=True),
        CeleryIntegration(auto_enabling=True),
    ],
    traces_sample_rate=0.1,
    send_default_pii=True,
    environment=os.getenv('ENVIRONMENT', 'production'),
)

# Email
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'eu-west-1'
AWS_SES_REGION_ENDPOINT = 'email.eu-west-1.amazonaws.com'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@coko.africa')

# African Payment Providers
ORANGE_MONEY_API_KEY = os.getenv('ORANGE_MONEY_API_KEY')
ORANGE_MONEY_SECRET = os.getenv('ORANGE_MONEY_SECRET')
MTN_MOMO_API_KEY = os.getenv('MTN_MOMO_API_KEY')
MTN_MOMO_SECRET = os.getenv('MTN_MOMO_SECRET')
WAVE_API_KEY = os.getenv('WAVE_API_KEY')
WAVE_SECRET = os.getenv('WAVE_SECRET')

# Performance
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# CORS
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
```

### Configuration Nginx

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
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
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;
    
    # Upstream backend
    upstream backend {
        least_conn;
        server backend:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
    
    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name api.coko.africa;
        return 301 https://$server_name$request_uri;
    }
    
    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name api.coko.africa;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/coko.crt;
        ssl_certificate_key /etc/nginx/ssl/coko.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        
        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy "strict-origin-when-cross-origin";
        
        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
            
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }
        
        # Auth endpoints (stricter rate limiting)
        location /api/v1/auth/ {
            limit_req zone=auth burst=10 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health/ {
            proxy_pass http://backend;
            access_log off;
        }
        
        # Static files
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options nosniff;
        }
        
        # Media files
        location /media/ {
            expires 30d;
            add_header Cache-Control "public";
            add_header X-Content-Type-Options nosniff;
        }
    }
}
```

---

## 📊 Monitoring et Observabilité

### Configuration Prometheus

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  # Django application
  - job_name: 'django'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
  
  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  
  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
  
  # Nginx
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
  
  # Node exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Alertes Prometheus

```yaml
# monitoring/alert_rules.yml
groups:
- name: coko_alerts
  rules:
  # High error rate
  - alert: HighErrorRate
    expr: rate(django_http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"
  
  # High response time
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(django_http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }} seconds"
  
  # Database connection issues
  - alert: DatabaseConnectionHigh
    expr: django_db_connections_total > 80
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High database connections"
      description: "Database connections: {{ $value }}"
  
  # Memory usage
  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value | humanizePercentage }}"
  
  # Disk usage
  - alert: HighDiskUsage
    expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High disk usage"
      description: "Disk usage is {{ $value | humanizePercentage }}"
```

### Dashboard Grafana

```json
{
  "dashboard": {
    "title": "Coko Platform Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(django_http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(django_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(django_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "singlestat",
        "targets": [
          {
            "expr": "django_db_connections_total"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "legendFormat": "Memory Usage %"
          }
        ]
      }
    ]
  }
}
```

---

## 🔄 Processus de Déploiement

### Checklist Pré-Déploiement

- [ ] Tests unitaires passent (85%+ couverture)
- [ ] Tests d'intégration validés
- [ ] Tests E2E fonctionnels
- [ ] Audit de sécurité effectué
- [ ] Performance validée
- [ ] Base de données migrée
- [ ] Variables d'environnement configurées
- [ ] Certificats SSL valides
- [ ] Monitoring configuré
- [ ] Sauvegardes planifiées
- [ ] Plan de rollback préparé

### Script de Déploiement

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# Configuration
ENVIRONMENT=${1:-production}
REGION=${2:-eu-west-3}
VERSION=$(git rev-parse --short HEAD)

echo "🚀 Déploiement Coko v$VERSION en $ENVIRONMENT"

# Vérifications pré-déploiement
echo "🔍 Vérifications pré-déploiement..."

# Tests
echo "🧪 Exécution des tests..."
cd backend && python -m pytest --cov=. --cov-fail-under=85
cd ../frontend && npm run test

# Build des images
echo "🏗️ Build des images Docker..."
docker build -t coko/backend:$VERSION backend/
docker build -t coko/frontend:$VERSION frontend/

# Push vers le registry
echo "📤 Push vers ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
docker tag coko/backend:$VERSION $ECR_REGISTRY/coko/backend:$VERSION
docker tag coko/frontend:$VERSION $ECR_REGISTRY/coko/frontend:$VERSION
docker push $ECR_REGISTRY/coko/backend:$VERSION
docker push $ECR_REGISTRY/coko/frontend:$VERSION

# Déploiement infrastructure
echo "🏗️ Déploiement infrastructure..."
cd infrastructure/aws
terraform plan -var="image_tag=$VERSION" -var="environment=$ENVIRONMENT"
terraform apply -auto-approve -var="image_tag=$VERSION" -var="environment=$ENVIRONMENT"

# Migration base de données
echo "🗄️ Migration base de données..."
aws ecs run-task \
  --cluster coko-$ENVIRONMENT \
  --task-definition coko-migrate:latest \
  --overrides '{
    "containerOverrides": [{
      "name": "migrate",
      "command": ["python", "manage.py", "migrate"]
    }]
  }'

# Déploiement application
echo "🚀 Déploiement application..."
aws ecs update-service \
  --cluster coko-$ENVIRONMENT \
  --service coko-backend \
  --task-definition coko-backend:latest \
  --force-new-deployment

# Attendre la stabilité
echo "⏳ Attente de la stabilité du service..."
aws ecs wait services-stable \
  --cluster coko-$ENVIRONMENT \
  --services coko-backend

# Tests post-déploiement
echo "🔍 Tests post-déploiement..."
curl -f https://api.coko.africa/health/ || exit 1

# Déploiement frontend
echo "🎨 Déploiement frontend..."
cd ../../frontend
vercel --prod --token $VERCEL_TOKEN

echo "✅ Déploiement terminé avec succès!"
echo "🌍 Frontend: https://coko.africa"
echo "🔗 API: https://api.coko.africa"
echo "📊 Monitoring: https://monitoring.coko.africa"

# Notification
slack-notify "🚀 Coko v$VERSION déployé en $ENVIRONMENT avec succès!"
```

### Rollback

```bash
#!/bin/bash
# scripts/rollback.sh

set -e

PREVIOUS_VERSION=${1}
ENVIRONMENT=${2:-production}

echo "🔄 Rollback vers la version $PREVIOUS_VERSION"

# Rollback backend
aws ecs update-service \
  --cluster coko-$ENVIRONMENT \
  --service coko-backend \
  --task-definition coko-backend:$PREVIOUS_VERSION

# Rollback frontend
vercel rollback --token $VERCEL_TOKEN

# Vérification
curl -f https://api.coko.africa/health/

echo "✅ Rollback terminé"
```

---

## 🔐 Sécurité en Production

### Checklist Sécurité

- [ ] HTTPS obligatoire
- [ ] Headers de sécurité configurés
- [ ] Rate limiting activé
- [ ] WAF configuré
- [ ] Secrets chiffrés
- [ ] Accès basé sur les rôles
- [ ] Logs de sécurité activés
- [ ] Monitoring des intrusions
- [ ] Sauvegardes chiffrées
- [ ] Plan de réponse aux incidents

### Configuration WAF

```json
{
  "Name": "CokoWAF",
  "Rules": [
    {
      "Name": "SQLInjectionRule",
      "Priority": 1,
      "Statement": {
        "SqliMatchStatement": {
          "FieldToMatch": {
            "AllQueryArguments": {}
          },
          "TextTransformations": [
            {
              "Priority": 0,
              "Type": "URL_DECODE"
            }
          ]
        }
      },
      "Action": {
        "Block": {}
      }
    },
    {
      "Name": "XSSRule",
      "Priority": 2,
      "Statement": {
        "XssMatchStatement": {
          "FieldToMatch": {
            "AllQueryArguments": {}
          },
          "TextTransformations": [
            {
              "Priority": 0,
              "Type": "URL_DECODE"
            }
          ]
        }
      },
      "Action": {
        "Block": {}
      }
    }
  ]
}
```

---

## 📈 Optimisation des Performances

### Métriques Cibles

| Métrique | Cible | Critique |
|----------|-------|----------|
| TTFB API | < 200ms | < 500ms |
| TTI Frontend | < 3s | < 5s |
| Throughput | > 1000 req/s | > 500 req/s |
| Disponibilité | > 99.9% | > 99.5% |
| Erreur Rate | < 0.1% | < 1% |

### Configuration Auto-Scaling

```yaml
# Auto-scaling ECS
TargetTrackingScalingPolicies:
  - TargetValue: 70.0
    ScaleInCooldown: 300
    ScaleOutCooldown: 300
    PredefinedMetricSpecification:
      PredefinedMetricType: ECSServiceAverageCPUUtilization
  
  - TargetValue: 80.0
    ScaleInCooldown: 300
    ScaleOutCooldown: 300
    PredefinedMetricSpecification:
      PredefinedMetricType: ECSServiceAverageMemoryUtilization
```

---

*Ce guide de déploiement assure une mise en production robuste, sécurisée et optimisée de la plateforme Coko, avec une architecture adaptée au marché africain.*