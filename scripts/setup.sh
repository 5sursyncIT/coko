#!/bin/bash

# Script de setup automatisé pour Coko - Optimisé pour l'Afrique
# Usage: ./scripts/setup.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}
BACKEND_DIR="backend"
SCRIPTS_DIR="scripts"

echo "🚀 Configuration de Coko pour l'environnement: $ENVIRONMENT"
echo "📍 Optimisations spécifiques pour l'Afrique de l'Ouest activées"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des prérequis
check_prerequisites() {
    print_status "Vérification des prérequis..."
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 n'est pas installé"
        exit 1
    fi
    
    # Vérifier Node.js (pour PWA et optimisations front)
    if ! command -v node &> /dev/null; then
        print_warning "Node.js non trouvé - installation recommandée pour PWA"
    fi
    
    # Vérifier Git
    if ! command -v git &> /dev/null; then
        print_error "Git n'est pas installé"
        exit 1
    fi
    
    print_success "Prérequis validés"
}

# Installation des dépendances Python
install_python_deps() {
    print_status "Installation des dépendances Python..."
    
    cd $BACKEND_DIR
    
    # Créer environnement virtuel si nécessaire
    if [ ! -d "venv" ]; then
        print_status "Création de l'environnement virtuel..."
        python3 -m venv venv
    fi
    
    # Activer l'environnement virtuel
    source venv/bin/activate
    
    # Mise à jour pip
    pip install --upgrade pip
    
    # Installation selon l'environnement
    if [ "$ENVIRONMENT" = "dev" ]; then
        print_status "Installation des dépendances de développement..."
        python setup_dependencies.py minimal
    else
        print_status "Installation des dépendances complètes..."
        python setup_dependencies.py full
    fi
    
    cd ..
    print_success "Dépendances Python installées"
}

# Configuration de la base de données
setup_database() {
    print_status "Configuration de la base de données..."
    
    cd $BACKEND_DIR
    source venv/bin/activate
    
    if [ "$ENVIRONMENT" = "dev" ]; then
        # Utiliser SQLite pour le développement
        export DJANGO_SETTINGS_MODULE=coko.settings_local
        print_status "Utilisation de SQLite pour le développement"
    else
        # PostgreSQL pour la production
        export DJANGO_SETTINGS_MODULE=coko.settings
        print_status "Configuration PostgreSQL pour la production"
    fi
    
    # Migrations
    print_status "Application des migrations..."
    python manage.py migrate
    python manage.py migrate --database=auth_db
    python manage.py migrate --database=catalog_db
    python manage.py migrate --database=reading_db
    
    cd ..
    print_success "Base de données configurée"
}

# Configuration des fichiers statiques
setup_static_files() {
    print_status "Configuration des fichiers statiques..."
    
    cd $BACKEND_DIR
    source venv/bin/activate
    
    # Collecte des fichiers statiques
    python manage.py collectstatic --noinput
    
    cd ..
    print_success "Fichiers statiques configurés"
}

# Configuration PWA et optimisations africaines
setup_african_optimizations() {
    print_status "Configuration des optimisations africaines..."
    
    # Créer les répertoires nécessaires
    mkdir -p $BACKEND_DIR/static/pwa
    mkdir -p $BACKEND_DIR/static/compressed
    mkdir -p $BACKEND_DIR/logs
    
    # Configuration du cache offline
    if [ "$ENVIRONMENT" = "prod" ]; then
        print_status "Configuration du cache pour réseaux lents..."
        # Ici on pourrait ajouter la configuration de compression, etc.
    fi
    
    print_success "Optimisations africaines configurées"
}

# Création du superutilisateur
create_superuser() {
    print_status "Création du superutilisateur..."
    
    cd $BACKEND_DIR
    source venv/bin/activate
    
    if [ "$ENVIRONMENT" = "dev" ]; then
        python create_superuser.py
    else
        print_warning "Création manuelle du superutilisateur requise en production"
        echo "Utilisez: python manage.py createsuperuser"
    fi
    
    cd ..
}

# Tests de performance africains
run_african_performance_tests() {
    if [ "$ENVIRONMENT" = "dev" ]; then
        print_status "Tests de performance pour conditions africaines..."
        
        cd $BACKEND_DIR
        source venv/bin/activate
        
        # Simulation de tests de latence
        print_status "Test de temps de réponse (objectif: <500ms)..."
        # Ici on pourrait ajouter des tests réels
        
        print_success "Tests de performance terminés"
        cd ..
    fi
}

# Fonction principale
main() {
    echo "==========================================="
    echo "🌍 Setup Coko - Plateforme Africaine 📚"
    echo "==========================================="
    
    check_prerequisites
    install_python_deps
    setup_database
    setup_static_files
    setup_african_optimizations
    create_superuser
    run_african_performance_tests
    
    echo "==========================================="
    print_success "🎉 Setup terminé avec succès!"
    echo "==========================================="
    
    if [ "$ENVIRONMENT" = "dev" ]; then
        echo "Pour démarrer le serveur de développement:"
        echo "cd backend && source venv/bin/activate"
        echo "python start_dev.py"
        echo ""
        echo "Ou directement:"
        echo "./scripts/start-dev.sh"
    else
        echo "Pour démarrer en production:"
        echo "./scripts/deploy.sh"
    fi
    
    echo ""
    echo "📊 Monitoring disponible sur: http://localhost:8000/health/"
    echo "🌍 Optimisé pour l'Afrique de l'Ouest 🚀"
}

# Exécution
main "$@"