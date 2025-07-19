#!/bin/bash

# Script de vérification de santé pour Coko
# Monitoring spécifique aux conditions africaines

set -e

BACKEND_DIR="backend"
HOST=${1:-localhost}
PORT=${2:-8000}
TARGET_RESPONSE_TIME=${3:-500}  # 500ms objectif pour l'Afrique

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "🏥 Vérification de santé Coko"
echo "🌍 Monitoring optimisé pour l'Afrique"
echo "====================================="

# Variables de statut
OVERALL_STATUS="healthy"
ERROR_COUNT=0
WARNING_COUNT=0

# Fonction pour enregistrer les erreurs
log_error() {
    ERROR_COUNT=$((ERROR_COUNT + 1))
    OVERALL_STATUS="unhealthy"
    print_error "$1"
}

log_warning() {
    WARNING_COUNT=$((WARNING_COUNT + 1))
    if [ "$OVERALL_STATUS" = "healthy" ]; then
        OVERALL_STATUS="degraded"
    fi
    print_warning "$1"
}

# Test de connectivité de base
test_basic_connectivity() {
    print_status "Test de connectivité de base..."
    
    if curl -s --max-time 5 "http://$HOST:$PORT/health/" > /dev/null; then
        print_success "Serveur accessible"
    else
        log_error "Serveur inaccessible sur $HOST:$PORT"
        return 1
    fi
}

# Test de performance (temps de réponse)
test_response_time() {
    print_status "Test de temps de réponse (objectif: <${TARGET_RESPONSE_TIME}ms)..."
    
    # Mesurer le temps de réponse
    RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" "http://$HOST:$PORT/health/")
    RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc -l | cut -d. -f1)
    
    if [ "$RESPONSE_TIME_MS" -lt "$TARGET_RESPONSE_TIME" ]; then
        print_success "Temps de réponse: ${RESPONSE_TIME_MS}ms (excellent pour l'Afrique)"
    elif [ "$RESPONSE_TIME_MS" -lt "1000" ]; then
        log_warning "Temps de réponse: ${RESPONSE_TIME_MS}ms (acceptable mais peut être amélioré)"
    else
        log_error "Temps de réponse: ${RESPONSE_TIME_MS}ms (trop lent pour les réseaux africains)"
    fi
}

# Test des endpoints critiques
test_critical_endpoints() {
    print_status "Test des endpoints critiques..."
    
    # Test API health
    if curl -s "http://$HOST:$PORT/health/" | grep -q "healthy\|ok"; then
        print_success "Endpoint /health/ fonctionnel"
    else
        log_error "Endpoint /health/ défaillant"
    fi
    
    # Test API principale
    if curl -s --max-time 3 "http://$HOST:$PORT/api/" > /dev/null; then
        print_success "API principale accessible"
    else
        log_warning "API principale lente ou inaccessible"
    fi
    
    # Test GraphQL
    if curl -s --max-time 3 "http://$HOST:$PORT/graphql/" > /dev/null; then
        print_success "GraphQL endpoint accessible"
    else
        log_warning "GraphQL endpoint lent ou inaccessible"
    fi
}

# Test de la base de données
test_database() {
    print_status "Test de connectivité base de données..."
    
    cd $BACKEND_DIR
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        export DJANGO_SETTINGS_MODULE=coko.settings_local
        
        if python manage.py check --database default > /dev/null 2>&1; then
            print_success "Base de données principale accessible"
        else
            log_error "Problème de connectivité base de données principale"
        fi
        
        # Test des autres bases
        for db in auth_db catalog_db reading_db; do
            if python manage.py check --database $db > /dev/null 2>&1; then
                print_success "Base de données $db accessible"
            else
                log_warning "Problème avec la base de données $db"
            fi
        done
    else
        log_warning "Environnement virtuel non trouvé - impossible de tester les BDD"
    fi
    cd ..
}

# Test des ressources système
test_system_resources() {
    print_status "Vérification des ressources système..."
    
    # Test mémoire
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$MEMORY_USAGE" -lt "80" ]; then
        print_success "Utilisation mémoire: ${MEMORY_USAGE}%"
    elif [ "$MEMORY_USAGE" -lt "90" ]; then
        log_warning "Utilisation mémoire élevée: ${MEMORY_USAGE}%"
    else
        log_error "Utilisation mémoire critique: ${MEMORY_USAGE}%"
    fi
    
    # Test espace disque
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt "80" ]; then
        print_success "Utilisation disque: ${DISK_USAGE}%"
    elif [ "$DISK_USAGE" -lt "90" ]; then
        log_warning "Utilisation disque élevée: ${DISK_USAGE}%"
    else
        log_error "Utilisation disque critique: ${DISK_USAGE}%"
    fi
}

# Test spécifique aux optimisations africaines
test_african_optimizations() {
    print_status "Vérification des optimisations africaines..."
    
    # Test compression
    COMPRESSION_HEADER=$(curl -s -H "Accept-Encoding: gzip, deflate, br" -I "http://$HOST:$PORT/" | grep -i "content-encoding")
    if [ -n "$COMPRESSION_HEADER" ]; then
        print_success "Compression activée: $COMPRESSION_HEADER"
    else
        log_warning "Compression non détectée (important pour l'Afrique)"
    fi
    
    # Test cache headers
    CACHE_HEADER=$(curl -s -I "http://$HOST:$PORT/static/" | grep -i "cache-control")
    if [ -n "$CACHE_HEADER" ]; then
        print_success "Headers de cache configurés"
    else
        log_warning "Headers de cache manquants"
    fi
    
    # Test PWA manifest
    if curl -s "http://$HOST:$PORT/static/manifest.json" > /dev/null 2>&1; then
        print_success "PWA manifest disponible"
    else
        log_warning "PWA manifest manquant (important pour mode offline)"
    fi
}

# Génération du rapport
generate_report() {
    echo "====================================="
    echo "📊 RAPPORT DE SANTÉ COKO"
    echo "====================================="
    echo "🕐 Date: $(date)"
    echo "🌍 Serveur: $HOST:$PORT"
    echo "🎯 Objectif temps de réponse: ${TARGET_RESPONSE_TIME}ms"
    echo "====================================="
    
    if [ "$OVERALL_STATUS" = "healthy" ]; then
        print_success "STATUT GLOBAL: SAIN ✅"
    elif [ "$OVERALL_STATUS" = "degraded" ]; then
        print_warning "STATUT GLOBAL: DÉGRADÉ ⚠️"
    else
        print_error "STATUT GLOBAL: DÉFAILLANT ❌"
    fi
    
    echo "📈 Erreurs: $ERROR_COUNT"
    echo "⚠️  Avertissements: $WARNING_COUNT"
    echo "====================================="
    
    if [ "$ERROR_COUNT" -gt "0" ]; then
        echo "🚨 Actions recommandées:"
        echo "  • Vérifier les logs: tail -f backend/logs/django.log"
        echo "  • Redémarrer les services si nécessaire"
        echo "  • Vérifier la connectivité réseau"
    fi
    
    if [ "$WARNING_COUNT" -gt "0" ]; then
        echo "💡 Optimisations suggérées:"
        echo "  • Activer la compression pour réduire la bande passante"
        echo "  • Configurer le cache pour améliorer les performances"
        echo "  • Optimiser les requêtes base de données"
    fi
    
    echo "====================================="
}

# Fonction principale
main() {
    test_basic_connectivity || exit 1
    test_response_time
    test_critical_endpoints
    test_database
    test_system_resources
    test_african_optimizations
    generate_report
    
    # Code de sortie basé sur le statut
    if [ "$OVERALL_STATUS" = "healthy" ]; then
        exit 0
    elif [ "$OVERALL_STATUS" = "degraded" ]; then
        exit 1
    else
        exit 2
    fi
}

# Installation de bc si nécessaire pour les calculs
if ! command -v bc &> /dev/null; then
    print_warning "Installation de 'bc' pour les calculs de performance..."
    apt-get update && apt-get install -y bc > /dev/null 2>&1 || true
fi

# Exécution
main "$@"