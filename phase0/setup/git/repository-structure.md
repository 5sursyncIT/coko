# Configuration Repositories Git - Projet Coko

## Stratégie Repository

### Approche Choisie : Monorepo

**Justification :**
- **Cohérence** : Versioning unifié de tous les microservices
- **Simplicité** : Un seul repository à gérer
- **Collaboration** : Facilite les changements cross-services
- **CI/CD** : Pipeline unifié avec détection des changements
- **Tooling** : Outils partagés et configurations communes

---

## Structure du Repository

```
coko/
├── .github/
│   ├── workflows/              # GitHub Actions
│   ├── ISSUE_TEMPLATE/         # Templates issues
│   ├── PULL_REQUEST_TEMPLATE/  # Templates PR
│   └── dependabot.yml          # Dependabot config
├── docs/
│   ├── README.md               # Documentation principale
│   ├── CONTRIBUTING.md         # Guide contribution
│   ├── CHANGELOG.md            # Historique des versions
│   └── architecture/           # Documentation architecture
├── services/
│   ├── api-gateway/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── auth-service/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── catalog-service/
│   ├── reading-service/
│   ├── payment-service/
│   ├── recommendation-service/
│   ├── gamification-service/
│   ├── publication-service/
│   ├── community-service/
│   ├── admin-service/
│   └── notification-service/
├── frontend/
│   ├── web-app/                # Next.js app
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   └── README.md
│   ├── mobile-app/             # React Native app
│   │   ├── src/
│   │   ├── android/
│   │   ├── ios/
│   │   ├── package.json
│   │   └── README.md
│   └── admin-panel/            # React admin
│       ├── src/
│       ├── public/
│       ├── package.json
│       └── README.md
├── infrastructure/
│   ├── kubernetes/
│   │   ├── base/               # Kustomize base
│   │   ├── overlays/
│   │   │   ├── development/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   └── monitoring/
│   ├── terraform/              # Infrastructure as Code
│   │   ├── modules/
│   │   ├── environments/
│   │   └── README.md
│   └── helm/                   # Helm charts
│       ├── coko-platform/
│       └── monitoring/
├── shared/
│   ├── libraries/              # Librairies partagées
│   │   ├── python/
│   │   │   ├── coko-common/
│   │   │   └── coko-auth/
│   │   └── typescript/
│   │       ├── coko-types/
│   │       └── coko-utils/
│   ├── configs/                # Configurations partagées
│   │   ├── eslint/
│   │   ├── prettier/
│   │   └── docker/
│   └── scripts/                # Scripts utilitaires
│       ├── setup.sh
│       ├── test.sh
│       └── deploy.sh
├── tools/
│   ├── development/            # Outils de développement
│   │   ├── docker-compose.yml  # Environnement local
│   │   ├── Makefile
│   │   └── scripts/
│   ├── testing/                # Outils de test
│   │   ├── e2e/
│   │   ├── load-testing/
│   │   └── fixtures/
│   └── monitoring/             # Configuration monitoring
│       ├── prometheus/
│       ├── grafana/
│       └── alertmanager/
├── .gitignore
├── .gitattributes
├── .editorconfig
├── .pre-commit-config.yaml
├── Makefile
├── docker-compose.yml          # Développement local
├── package.json                # Scripts globaux
├── README.md
└── LICENSE
```

---

## Configuration Git

### .gitignore Global

```gitignore
# OS
.DS_Store
.DS_Store?
Thumbs.db

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.env
.venv

# Secrets
.env.local
.env.*.local
secrets/
*.key
*.pem
*.p12
*.pfx

# Build outputs
build/
dist/
out/
target/
*.jar
*.war
*.ear

# Testing
coverage/
.coverage
.pytest_cache/
.tox/
.nox/
junit.xml

# Docker
.dockerignore

# Kubernetes
*.kubeconfig

# Terraform
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl

# Temporary files
*.tmp
*.temp
*.bak
*.backup
```

### .gitattributes

```gitattributes
# Auto detect text files and perform LF normalization
* text=auto

# Source code
*.py text eol=lf
*.js text eol=lf
*.ts text eol=lf
*.jsx text eol=lf
*.tsx text eol=lf
*.json text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
*.md text eol=lf
*.txt text eol=lf
*.sh text eol=lf
*.sql text eol=lf

# Documentation
*.md text eol=lf
*.txt text eol=lf
*.rst text eol=lf

# Configuration files
*.ini text eol=lf
*.cfg text eol=lf
*.conf text eol=lf
*.toml text eol=lf

# Scripts
*.sh text eol=lf
*.bash text eol=lf
*.zsh text eol=lf
*.fish text eol=lf

# Windows scripts
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.svg binary
*.pdf binary
*.zip binary
*.tar.gz binary
*.tgz binary
*.rar binary
*.7z binary
*.exe binary
*.dll binary
*.so binary
*.dylib binary

# Fonts
*.woff binary
*.woff2 binary
*.eot binary
*.ttf binary
*.otf binary

# Archives
*.zip binary
*.tar binary
*.gz binary
*.bz2 binary
*.xz binary

# Media
*.mp4 binary
*.mp3 binary
*.wav binary
*.flac binary
*.ogg binary
*.avi binary
*.mov binary
*.wmv binary
*.flv binary
```

---

## Permissions et Accès

### Équipes GitHub

```yaml
Teams:
  coko-admins:
    permissions: admin
    members:
      - tech-lead
      - devops-lead
      - product-owner
  
  coko-developers:
    permissions: write
    members:
      - backend-dev-1
      - backend-dev-2
      - frontend-dev-1
      - frontend-dev-2
      - mobile-dev-1
  
  coko-reviewers:
    permissions: read
    members:
      - senior-dev-1
      - senior-dev-2
      - qa-lead
```

### Branch Protection Rules

```yaml
Branch_Protection:
  main:
    required_status_checks:
      - "ci/tests"
      - "ci/security-scan"
      - "ci/lint"
    enforce_admins: true
    required_pull_request_reviews:
      required_approving_review_count: 2
      dismiss_stale_reviews: true
      require_code_owner_reviews: true
    restrictions:
      push: ["coko-admins"]
      merge: ["coko-admins", "coko-developers"]
  
  develop:
    required_status_checks:
      - "ci/tests"
      - "ci/lint"
    required_pull_request_reviews:
      required_approving_review_count: 1
    restrictions:
      push: ["coko-developers"]
  
  release/*:
    required_status_checks:
      - "ci/tests"
      - "ci/security-scan"
      - "ci/lint"
      - "ci/e2e-tests"
    enforce_admins: true
    required_pull_request_reviews:
      required_approving_review_count: 2
      require_code_owner_reviews: true
```

---

## CODEOWNERS

```
# Global owners
* @tech-lead @devops-lead

# Documentation
/docs/ @tech-lead @product-owner
/README.md @tech-lead @product-owner

# Infrastructure
/infrastructure/ @devops-lead
/.github/ @devops-lead
/docker-compose.yml @devops-lead

# Backend services
/services/ @backend-lead
/services/auth-service/ @backend-dev-1 @security-lead
/services/payment-service/ @backend-dev-2 @security-lead
/services/catalog-service/ @backend-dev-1
/services/reading-service/ @backend-dev-2
/services/recommendation-service/ @ml-engineer

# Frontend
/frontend/web-app/ @frontend-lead @frontend-dev-1
/frontend/mobile-app/ @mobile-lead @mobile-dev-1
/frontend/admin-panel/ @frontend-dev-2

# Shared libraries
/shared/ @tech-lead @backend-lead

# Configuration files
/.gitignore @devops-lead
/.gitattributes @devops-lead
/package.json @tech-lead
/Makefile @devops-lead

# Security sensitive
/services/auth-service/ @security-lead
/services/payment-service/ @security-lead
/infrastructure/kubernetes/base/secrets/ @devops-lead @security-lead
```

---

## Scripts d'Initialisation

### setup.sh

```bash
#!/bin/bash

# Coko Project Setup Script
set -e

echo "🚀 Initialisation du projet Coko..."

# Vérification des prérequis
command -v git >/dev/null 2>&1 || { echo "Git requis mais non installé." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker requis mais non installé." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js requis mais non installé." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 requis mais non installé." >&2; exit 1; }

# Installation des hooks Git
echo "📋 Installation des hooks Git..."
cp shared/scripts/hooks/* .git/hooks/
chmod +x .git/hooks/*

# Installation des dépendances globales
echo "📦 Installation des dépendances..."
npm install

# Setup des environnements Python
echo "🐍 Configuration des environnements Python..."
for service in services/*/; do
    if [ -f "$service/requirements.txt" ]; then
        echo "Setting up $service"
        cd "$service"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ../..
    fi
done

# Setup des environnements Node.js
echo "📱 Configuration des environnements Node.js..."
for frontend in frontend/*/; do
    if [ -f "$frontend/package.json" ]; then
        echo "Setting up $frontend"
        cd "$frontend"
        npm install
        cd ../..
    fi
done

# Configuration de l'environnement de développement
echo "⚙️ Configuration de l'environnement..."
cp .env.example .env
echo "Veuillez configurer le fichier .env avec vos paramètres."

# Démarrage des services de développement
echo "🐳 Démarrage des services Docker..."
docker-compose up -d postgres redis elasticsearch

echo "✅ Setup terminé ! Utilisez 'make help' pour voir les commandes disponibles."
```

---

## Makefile Global

```makefile
.PHONY: help setup clean test lint format build deploy

# Variables
PROJECT_NAME := coko
DOCKER_COMPOSE := docker-compose
KUBECTL := kubectl

# Couleurs pour l'affichage
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

help: ## Affiche cette aide
	@echo "$(BLUE)Commandes disponibles pour $(PROJECT_NAME):$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

setup: ## Initialise le projet
	@echo "$(YELLOW)Initialisation du projet...$(RESET)"
	@./shared/scripts/setup.sh

clean: ## Nettoie les fichiers temporaires
	@echo "$(YELLOW)Nettoyage...$(RESET)"
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

test: ## Lance tous les tests
	@echo "$(YELLOW)Exécution des tests...$(RESET)"
	@./shared/scripts/test.sh

lint: ## Vérifie le code avec les linters
	@echo "$(YELLOW)Vérification du code...$(RESET)"
	@./shared/scripts/lint.sh

format: ## Formate le code
	@echo "$(YELLOW)Formatage du code...$(RESET)"
	@./shared/scripts/format.sh

build: ## Build tous les services
	@echo "$(YELLOW)Build des services...$(RESET)"
	@$(DOCKER_COMPOSE) build

dev-up: ## Démarre l'environnement de développement
	@echo "$(YELLOW)Démarrage de l'environnement de développement...$(RESET)"
	@$(DOCKER_COMPOSE) up -d

dev-down: ## Arrête l'environnement de développement
	@echo "$(YELLOW)Arrêt de l'environnement de développement...$(RESET)"
	@$(DOCKER_COMPOSE) down

dev-logs: ## Affiche les logs de développement
	@$(DOCKER_COMPOSE) logs -f

deploy-dev: ## Déploie en environnement de développement
	@echo "$(YELLOW)Déploiement en développement...$(RESET)"
	@$(KUBECTL) apply -k infrastructure/kubernetes/overlays/development

deploy-staging: ## Déploie en environnement de staging
	@echo "$(YELLOW)Déploiement en staging...$(RESET)"
	@$(KUBECTL) apply -k infrastructure/kubernetes/overlays/staging

monitor: ## Ouvre les dashboards de monitoring
	@echo "$(BLUE)Ouverture des dashboards...$(RESET)"
	@open http://localhost:3000  # Grafana
	@open http://localhost:9090  # Prometheus

security-scan: ## Lance un scan de sécurité
	@echo "$(YELLOW)Scan de sécurité...$(RESET)"
	@./shared/scripts/security-scan.sh

backup: ## Sauvegarde les données
	@echo "$(YELLOW)Sauvegarde...$(RESET)"
	@./shared/scripts/backup.sh

restore: ## Restaure les données
	@echo "$(YELLOW)Restauration...$(RESET)"
	@./shared/scripts/restore.sh

docs: ## Génère la documentation
	@echo "$(YELLOW)Génération de la documentation...$(RESET)"
	@./shared/scripts/generate-docs.sh

update-deps: ## Met à jour les dépendances
	@echo "$(YELLOW)Mise à jour des dépendances...$(RESET)"
	@./shared/scripts/update-deps.sh
```

---

## Avantages de cette Structure

### ✅ Avantages

1. **Cohérence** : Versioning unifié de tous les composants
2. **Simplicité** : Un seul repository à cloner et gérer
3. **Collaboration** : Facilite les changements cross-services
4. **CI/CD** : Pipeline unifié avec détection intelligente des changements
5. **Tooling** : Outils et configurations partagés
6. **Documentation** : Centralisée et cohérente
7. **Refactoring** : Facilite les refactorings cross-services

### ⚠️ Inconvénients et Mitigations

1. **Taille du repository** → Utilisation de Git LFS pour les gros fichiers
2. **Permissions granulaires** → CODEOWNERS et branch protection
3. **CI/CD complexe** → Détection des changements par service
4. **Conflits potentiels** → Branching strategy claire

---

## Métriques et Monitoring

### Métriques Git

```yaml
Metrics_to_Track:
  - commit_frequency
  - pull_request_size
  - review_time
  - merge_conflicts
  - branch_lifetime
  - code_coverage_evolution
  - security_vulnerabilities
```

### Dashboards

- **GitHub Insights** : Activité du repository
- **Code Climate** : Qualité du code
- **Dependabot** : Sécurité des dépendances
- **SonarQube** : Analyse statique

---

*Cette structure sera validée par l'équipe avant implémentation.*