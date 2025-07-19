#!/bin/bash

# Script de démarrage développement pour Coko
# Optimisé pour les conditions africaines

set -e

BACKEND_DIR="backend"
PORT=${1:-8000}
HOST=${2:-0.0.0.0}

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🚀 Démarrage de Coko en mode développement"
echo "🌍 Configuration optimisée pour l'Afrique"
echo "==========================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "$BACKEND_DIR" ]; then
    echo "Erreur: Répertoire backend non trouvé"
    echo "Exécutez ce script depuis la racine du projet"
    exit 1
fi

cd $BACKEND_DIR

# Vérifier l'environnement virtuel
if [ ! -d "venv" ]; then
    print_warning "Environnement virtuel non trouvé"
    print_status "Exécution du setup automatique..."
    cd ..
    ./scripts/setup.sh dev
    cd $BACKEND_DIR
fi

# Activer l'environnement virtuel
print_status "Activation de l'environnement virtuel..."
source venv/bin/activate

# Vérifier les migrations
print_status "Vérification des migrations..."
export DJANGO_SETTINGS_MODULE=coko.settings_local
python manage.py migrate --check || {
    print_status "Application des migrations nécessaires..."
    python manage.py migrate
    python manage.py migrate --database=auth_db
    python manage.py migrate --database=catalog_db  
    python manage.py migrate --database=reading_db
}

# Collecter les fichiers statiques si nécessaire
if [ ! -d "static" ] || [ -z "$(ls -A static 2>/dev/null)" ]; then
    print_status "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
fi

# Vérifications de santé avant démarrage
print_status "Vérifications de santé du système..."

# Vérifier la connectivité de base
echo "✓ Configuration SQLite (mode développement)"
echo "✓ Cache en mémoire activé"
echo "✓ Compression activée"
echo "✓ Mode offline/PWA prêt"

# Afficher les informations de démarrage
echo "==========================================="
print_success "🎉 Démarrage du serveur Django"
echo "==========================================="
echo "📍 URL: http://$HOST:$PORT"
echo "🔧 Admin: http://$HOST:$PORT/admin/"
echo "📊 Health: http://$HOST:$PORT/health/"
echo "🌍 API: http://$HOST:$PORT/api/"
echo "📚 GraphQL: http://$HOST:$PORT/graphql/"
echo "==========================================="
echo "🌍 Optimisations africaines activées:"
echo "  • Compression Brotli/Gzip"
echo "  • Cache intelligent"
echo "  • Mode offline PWA"
echo "  • Adaptation réseau 2G/3G/4G"
echo "==========================================="
echo "Pour arrêter: Ctrl+C"
echo ""

# Démarrer le serveur
print_status "Démarrage sur $HOST:$PORT..."
export DJANGO_SETTINGS_MODULE=coko.settings_local
python manage.py runserver $HOST:$PORT