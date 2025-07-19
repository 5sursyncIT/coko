# Scripts d'Automatisation - Projet Coko

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Scripts de Déploiement](#scripts-de-déploiement)
3. [Scripts de Maintenance](#scripts-de-maintenance)
4. [Scripts de Monitoring](#scripts-de-monitoring)
5. [Scripts de Backup](#scripts-de-backup)
6. [Scripts de Développement](#scripts-de-développement)
7. [Scripts d'Urgence](#scripts-durgence)
8. [Configuration et Variables](#configuration-et-variables)

---

## Vue d'Ensemble

Cette documentation présente l'ensemble des scripts d'automatisation utilisés pour le projet Coko. Ces scripts facilitent le déploiement, la maintenance, le monitoring et la gestion des environnements.

### Structure des Scripts

```
scripts/
├── deployment/
│   ├── deploy.sh
│   ├── rollback.sh
│   ├── blue-green-deploy.sh
│   └── canary-deploy.sh
├── maintenance/
│   ├── database-maintenance.sh
│   ├── cleanup.sh
│   ├── update-dependencies.sh
│   └── security-scan.sh
├── monitoring/
│   ├── health-check.sh
│   ├── performance-test.sh
│   ├── load-test.sh
│   └── metrics-collector.sh
├── backup/
│   ├── backup-databases.sh
│   ├── backup-files.sh
│   ├── restore-database.sh
│   └── restore-files.sh
├── development/
│   ├── setup-dev-env.sh
│   ├── run-tests.sh
│   ├── build-images.sh
│   └── local-deploy.sh
├── emergency/
│   ├── emergency-rollback.sh
│   ├── scale-services.sh
│   ├── maintenance-mode.sh
│   └── disaster-recovery.sh
└── utils/
    ├── common.sh
    ├── logging.sh
    └── notifications.sh
```

---

## Scripts de Déploiement

### 1. Script de Déploiement Principal

**Fichier :** `scripts/deployment/deploy.sh`

```bash
#!/bin/bash

# Script de déploiement principal pour Coko
# Usage: ./deploy.sh <environment> <version>

set -euo pipefail

# Import des fonctions communes
source "$(dirname "$0")/../utils/common.sh"
source "$(dirname "$0")/../utils/logging.sh"
source "$(dirname "$0")/../utils/notifications.sh"

# Variables
ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
NAMESPACE="coko-${ENVIRONMENT}"
KUBECONFIG_PATH="${HOME}/.kube/config"

# Validation des paramètres
validate_environment() {
    case $ENVIRONMENT in
        development|staging|production)
            log_info "Déploiement vers l'environnement: $ENVIRONMENT"
            ;;
        *)
            log_error "Environnement invalide: $ENVIRONMENT"
            log_info "Environnements supportés: development, staging, production"
            exit 1
            ;;
    esac
}

# Vérification des prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    # Vérifier kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl n'est pas installé"
        exit 1
    fi
    
    # Vérifier la connexion au cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Impossible de se connecter au cluster Kubernetes"
        exit 1
    fi
    
    # Vérifier l'existence du namespace
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warn "Le namespace $NAMESPACE n'existe pas, création..."
        kubectl create namespace "$NAMESPACE"
    fi
    
    log_success "Prérequis validés"
}

# Mise à jour des images Docker
update_images() {
    log_info "Mise à jour des images Docker vers la version $VERSION..."
    
    local services=("api-gateway" "auth-service" "catalog-service" "reading-service" 
                   "payment-service" "gamification-service" "community-service" 
                   "admin-service" "notification-service")
    
    for service in "${services[@]}"; do
        log_info "Mise à jour de $service..."
        kubectl set image deployment/$service \
            $service=coko/$service:$VERSION \
            -n "$NAMESPACE"
    done
    
    log_success "Images mises à jour"
}

# Attendre le déploiement
wait_for_deployment() {
    log_info "Attente du déploiement..."
    
    local services=("api-gateway" "auth-service" "catalog-service")
    
    for service in "${services[@]}"; do
        log_info "Attente du déploiement de $service..."
        kubectl rollout status deployment/$service -n "$NAMESPACE" --timeout=600s
        
        if [ $? -eq 0 ]; then
            log_success "$service déployé avec succès"
        else
            log_error "Échec du déploiement de $service"
            return 1
        fi
    done
    
    log_success "Tous les services sont déployés"
}

# Tests de santé
run_health_checks() {
    log_info "Exécution des tests de santé..."
    
    # Attendre que les pods soient prêts
    sleep 30
    
    # Vérifier l'API Gateway
    local api_url
    if [ "$ENVIRONMENT" = "production" ]; then
        api_url="https://api.coko.africa"
    else
        api_url="https://api-${ENVIRONMENT}.coko.africa"
    fi
    
    log_info "Test de l'API Gateway: $api_url"
    if curl -f "$api_url/health" &> /dev/null; then
        log_success "API Gateway accessible"
    else
        log_error "API Gateway inaccessible"
        return 1
    fi
    
    # Vérifier les services internes
    local services=("auth-service" "catalog-service")
    for service in "${services[@]}"; do
        log_info "Test de $service..."
        if kubectl exec -n "$NAMESPACE" \
            deployment/$service -- curl -f http://localhost:8080/health &> /dev/null; then
            log_success "$service fonctionne correctement"
        else
            log_error "$service ne répond pas"
            return 1
        fi
    done
    
    log_success "Tous les tests de santé sont passés"
}

# Tests de fumée
run_smoke_tests() {
    log_info "Exécution des tests de fumée..."
    
    # Test d'authentification
    log_info "Test d'authentification..."
    local auth_response
    auth_response=$(curl -s -X POST "$api_url/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@coko.africa","password":"testpassword"}')
    
    if echo "$auth_response" | grep -q "token"; then
        log_success "Test d'authentification réussi"
    else
        log_warn "Test d'authentification échoué (peut être normal si pas de données de test)"
    fi
    
    # Test du catalogue
    log_info "Test du catalogue..."
    if curl -f "$api_url/catalog/books?limit=1" &> /dev/null; then
        log_success "Test du catalogue réussi"
    else
        log_warn "Test du catalogue échoué"
    fi
    
    log_success "Tests de fumée terminés"
}

# Notification de déploiement
notify_deployment() {
    local status="$1"
    local message
    
    if [ "$status" = "success" ]; then
        message="✅ Déploiement réussi de Coko $VERSION vers $ENVIRONMENT"
    else
        message="❌ Échec du déploiement de Coko $VERSION vers $ENVIRONMENT"
    fi
    
    log_info "Envoi de notification..."
    send_slack_notification "$message"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        send_email_notification "$message" "devops@coko.africa"
    fi
}

# Fonction principale
main() {
    log_info "Début du déploiement de Coko $VERSION vers $ENVIRONMENT"
    
    validate_environment
    check_prerequisites
    
    # Sauvegarde de l'état actuel pour rollback
    log_info "Sauvegarde de l'état actuel..."
    kubectl get deployments -n "$NAMESPACE" -o yaml > "/tmp/coko-${ENVIRONMENT}-backup-$(date +%Y%m%d_%H%M%S).yaml"
    
    # Déploiement
    if update_images && wait_for_deployment && run_health_checks; then
        log_success "Déploiement réussi!"
        run_smoke_tests
        notify_deployment "success"
    else
        log_error "Échec du déploiement"
        notify_deployment "failure"
        
        # Proposer un rollback automatique
        if [ "$ENVIRONMENT" = "production" ]; then
            log_warn "Rollback automatique recommandé pour la production"
            read -p "Voulez-vous effectuer un rollback automatique? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Lancement du rollback..."
                "$(dirname "$0")/rollback.sh" "$ENVIRONMENT"
            fi
        fi
        
        exit 1
    fi
    
    log_success "Déploiement terminé avec succès!"
}

# Gestion des signaux
trap 'log_error "Déploiement interrompu"; exit 1' INT TERM

# Exécution
main "$@"
```

### 2. Script de Rollback

**Fichier :** `scripts/deployment/rollback.sh`

```bash
#!/bin/bash

# Script de rollback pour Coko
# Usage: ./rollback.sh <environment> [steps]

set -euo pipefail

source "$(dirname "$0")/../utils/common.sh"
source "$(dirname "$0")/../utils/logging.sh"
source "$(dirname "$0")/../utils/notifications.sh"

ENVIRONMENT="${1:-staging}"
STEPS="${2:-1}"
NAMESPACE="coko-${ENVIRONMENT}"

# Validation
validate_environment() {
    case $ENVIRONMENT in
        development|staging|production)
            log_info "Rollback vers l'environnement: $ENVIRONMENT"
            ;;
        *)
            log_error "Environnement invalide: $ENVIRONMENT"
            exit 1
            ;;
    esac
}

# Rollback des services
rollback_services() {
    log_info "Rollback de $STEPS étape(s)..."
    
    local services=("api-gateway" "auth-service" "catalog-service" "reading-service" 
                   "payment-service" "gamification-service" "community-service" 
                   "admin-service" "notification-service")
    
    for service in "${services[@]}"; do
        log_info "Rollback de $service..."
        
        # Vérifier l'historique des rollouts
        local history
        history=$(kubectl rollout history deployment/$service -n "$NAMESPACE" 2>/dev/null || echo "")
        
        if [ -z "$history" ]; then
            log_warn "Pas d'historique de rollout pour $service"
            continue
        fi
        
        # Effectuer le rollback
        if kubectl rollout undo deployment/$service -n "$NAMESPACE" --to-revision=$(($(kubectl rollout history deployment/$service -n "$NAMESPACE" | wc -l) - $STEPS)); then
            log_success "Rollback de $service réussi"
        else
            log_error "Échec du rollback de $service"
            return 1
        fi
    done
}

# Attendre le rollback
wait_for_rollback() {
    log_info "Attente du rollback..."
    
    local services=("api-gateway" "auth-service" "catalog-service")
    
    for service in "${services[@]}"; do
        log_info "Attente du rollback de $service..."
        kubectl rollout status deployment/$service -n "$NAMESPACE" --timeout=300s
        
        if [ $? -eq 0 ]; then
            log_success "Rollback de $service terminé"
        else
            log_error "Échec du rollback de $service"
            return 1
        fi
    done
}

# Fonction principale
main() {
    log_info "Début du rollback de Coko vers $ENVIRONMENT"
    
    validate_environment
    
    # Confirmation pour la production
    if [ "$ENVIRONMENT" = "production" ]; then
        log_warn "ATTENTION: Rollback en production!"
        read -p "Êtes-vous sûr de vouloir continuer? (yes/no): " -r
        if [ "$REPLY" != "yes" ]; then
            log_info "Rollback annulé"
            exit 0
        fi
    fi
    
    if rollback_services && wait_for_rollback; then
        log_success "Rollback réussi!"
        
        # Vérification rapide
        sleep 30
        "$(dirname "$0")/../monitoring/health-check.sh" "$ENVIRONMENT"
        
        # Notification
        send_slack_notification "🔄 Rollback réussi de Coko vers $ENVIRONMENT"
    else
        log_error "Échec du rollback"
        send_slack_notification "❌ Échec du rollback de Coko vers $ENVIRONMENT"
        exit 1
    fi
}

main "$@"
```

### 3. Script de Déploiement Blue/Green

**Fichier :** `scripts/deployment/blue-green-deploy.sh`

```bash
#!/bin/bash

# Déploiement Blue/Green pour Coko
# Usage: ./blue-green-deploy.sh <environment> <version>

set -euo pipefail

source "$(dirname "$0")/../utils/common.sh"
source "$(dirname "$0")/../utils/logging.sh"

ENVIRONMENT="${1:-production}"
VERSION="${2:-latest}"
NAMESPACE="coko-${ENVIRONMENT}"

# Déterminer la couleur actuelle
get_current_color() {
    local current_selector
    current_selector=$(kubectl get service api-gateway-service -n "$NAMESPACE" -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "blue")
    echo "$current_selector"
}

# Déterminer la nouvelle couleur
get_new_color() {
    local current="$1"
    if [ "$current" = "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Déployer la nouvelle version
deploy_new_version() {
    local new_color="$1"
    
    log_info "Déploiement de la version $new_color..."
    
    # Créer les nouveaux deployments avec la nouvelle couleur
    local services=("api-gateway" "auth-service" "catalog-service")
    
    for service in "${services[@]}"; do
        log_info "Déploiement de $service-$new_color..."
        
        # Copier le deployment existant et modifier la couleur
        kubectl get deployment $service -n "$NAMESPACE" -o yaml | \
            sed "s/name: $service/name: $service-$new_color/g" | \
            sed "s/version: .*/version: $new_color/g" | \
            sed "s|image: coko/$service:.*|image: coko/$service:$VERSION|g" | \
            kubectl apply -f -
        
        # Attendre que le deployment soit prêt
        kubectl rollout status deployment/$service-$new_color -n "$NAMESPACE" --timeout=600s
    done
    
    log_success "Version $new_color déployée"
}

# Tester la nouvelle version
test_new_version() {
    local new_color="$1"
    
    log_info "Test de la version $new_color..."
    
    # Créer un service temporaire pour tester
    kubectl patch service api-gateway-service -n "$NAMESPACE" \
        -p '{"spec":{"selector":{"version":"'$new_color'"}}}'
    
    sleep 30
    
    # Exécuter les tests
    if "$(dirname "$0")/../monitoring/health-check.sh" "$ENVIRONMENT"; then
        log_success "Tests de la version $new_color réussis"
        return 0
    else
        log_error "Tests de la version $new_color échoués"
        return 1
    fi
}

# Basculer vers la nouvelle version
switch_to_new_version() {
    local new_color="$1"
    local old_color="$2"
    
    log_info "Basculement vers la version $new_color..."
    
    # Mettre à jour tous les services
    local services=("api-gateway" "auth-service" "catalog-service")
    
    for service in "${services[@]}"; do
        kubectl patch service $service-service -n "$NAMESPACE" \
            -p '{"spec":{"selector":{"version":"'$new_color'"}}}'
    done
    
    log_success "Basculement terminé"
    
    # Attendre et vérifier
    sleep 60
    if "$(dirname "$0")/../monitoring/health-check.sh" "$ENVIRONMENT"; then
        log_success "Nouvelle version active et fonctionnelle"
        
        # Nettoyer l'ancienne version
        cleanup_old_version "$old_color"
    else
        log_error "Problème détecté, rollback..."
        rollback_to_old_version "$old_color" "$new_color"
        return 1
    fi
}

# Nettoyer l'ancienne version
cleanup_old_version() {
    local old_color="$1"
    
    log_info "Nettoyage de l'ancienne version $old_color..."
    
    local services=("api-gateway" "auth-service" "catalog-service")
    
    for service in "${services[@]}"; do
        kubectl delete deployment $service-$old_color -n "$NAMESPACE" --ignore-not-found
    done
    
    log_success "Ancienne version nettoyée"
}

# Rollback vers l'ancienne version
rollback_to_old_version() {
    local old_color="$1"
    local new_color="$2"
    
    log_warn "Rollback vers la version $old_color..."
    
    local services=("api-gateway" "auth-service" "catalog-service")
    
    for service in "${services[@]}"; do
        kubectl patch service $service-service -n "$NAMESPACE" \
            -p '{"spec":{"selector":{"version":"'$old_color'"}}}'
    done
    
    # Nettoyer la nouvelle version défaillante
    for service in "${services[@]}"; do
        kubectl delete deployment $service-$new_color -n "$NAMESPACE" --ignore-not-found
    done
    
    log_success "Rollback terminé"
}

# Fonction principale
main() {
    log_info "Début du déploiement Blue/Green de Coko $VERSION vers $ENVIRONMENT"
    
    local current_color
    current_color=$(get_current_color)
    local new_color
    new_color=$(get_new_color "$current_color")
    
    log_info "Couleur actuelle: $current_color"
    log_info "Nouvelle couleur: $new_color"
    
    if deploy_new_version "$new_color" && \
       test_new_version "$new_color" && \
       switch_to_new_version "$new_color" "$current_color"; then
        
        log_success "Déploiement Blue/Green réussi!"
        send_slack_notification "🟢 Déploiement Blue/Green réussi de Coko $VERSION vers $ENVIRONMENT"
    else
        log_error "Échec du déploiement Blue/Green"
        send_slack_notification "🔴 Échec du déploiement Blue/Green de Coko $VERSION vers $ENVIRONMENT"
        exit 1
    fi
}

main "$@"
```

---

## Scripts de Maintenance

### 1. Maintenance de Base de Données

**Fichier :** `scripts/maintenance/database-maintenance.sh`

```bash
#!/bin/bash

# Script de maintenance des bases de données
# Usage: ./database-maintenance.sh <environment> [operation]

set -euo pipefail

source "$(dirname "$0")/../utils/common.sh"
source "$(dirname "$0")/../utils/logging.sh"

ENVIRONMENT="${1:-staging}"
OPERATION="${2:-analyze}"
NAMESPACE="coko-${ENVIRONMENT}"

# Obtenir les informations de connexion
get_db_connection() {
    local db_host
    local db_password
    
    db_host=$(kubectl get configmap postgres-config -n "$NAMESPACE" -o jsonpath='{.data.POSTGRES_HOST}')
    db_password=$(kubectl get secret coko-secrets -n "$NAMESPACE" -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
    
    echo "host=$db_host password=$db_password"
}

# Analyser les statistiques
analyze_databases() {
    log_info "Analyse des statistiques des bases de données..."
    
    local connection
    connection=$(get_db_connection)
    
    local databases=("coko_auth" "coko_catalog" "coko_reading" "coko_payment" "coko_gamification" "coko_community")
    
    for db in "${databases[@]}"; do
        log_info "Analyse de $db..."
        
        kubectl exec -n "$NAMESPACE" deployment/postgres -- \
            psql -h localhost -U postgres -d "$db" -c "ANALYZE;"
        
        if [ $? -eq 0 ]; then
            log_success "Analyse de $db terminée"
        else
            log_error "Échec de l'analyse de $db"
        fi
    done
}

# Vacuum des bases de données
vacuum_databases() {
    log_info "Vacuum des bases de données..."
    
    local databases=("coko_auth" "coko_catalog" "coko_reading" "coko_payment" "coko_gamification" "coko_community")
    
    for db in "${databases[@]}"; do
        log_info "Vacuum de $db..."
        
        kubectl exec -n "$NAMESPACE" deployment/postgres -- \
            psql -h localhost -U postgres -d "$db" -c "VACUUM;"
        
        if [ $? -eq 0 ]; then
            log_success "Vacuum de $db terminé"
        else
            log_error "Échec du vacuum de $db"
        fi
    done
}

# Reindex des bases de données
reindex_databases() {
    log_info "Reindex des bases de données..."
    
    local databases=("coko_auth" "coko_catalog" "coko_reading" "coko_payment" "coko_gamification" "coko_community")
    
    for db in "${databases[@]}"; do
        log_info "Reindex de $db..."
        
        kubectl exec -n "$NAMESPACE" deployment/postgres -- \
            psql -h localhost -U postgres -d "$db" -c "REINDEX DATABASE $db;"
        
        if [ $? -eq 0 ]; then
            log_success "Reindex de $db terminé"
        else
            log_error "Échec du reindex de $db"
        fi
    done
}

# Vérifier l'intégrité
check_integrity() {
    log_info "Vérification de l'intégrité des bases de données..."
    
    local databases=("coko_auth" "coko_catalog" "coko_reading" "coko_payment" "coko_gamification" "coko_community")
    
    for db in "${databases[@]}"; do
        log_info "Vérification de $db..."
        
        # Vérifier les contraintes
        local violations
        violations=$(kubectl exec -n "$NAMESPACE" deployment/postgres -- \
            psql -h localhost -U postgres -d "$db" -t -c "
            SELECT COUNT(*) FROM (
                SELECT conname, conrelid::regclass
                FROM pg_constraint
                WHERE NOT pg_catalog.pg_relation_is_updatable(conrelid::regclass,false)
            ) AS violations;")
        
        if [ "$violations" -eq 0 ]; then
            log_success "Intégrité de $db OK"
        else
            log_warn "$violations violations d'intégrité trouvées dans $db"
        fi
    done
}

# Statistiques des performances
performance_stats() {
    log_info "Collecte des statistiques de performance..."
    
    kubectl exec -n "$NAMESPACE" deployment/postgres -- \
        psql -h localhost -U postgres -c "
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation
        FROM pg_stats 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename;
        "
    
    # Requêtes lentes
    log_info "Top 10 des requêtes lentes:"
    kubectl exec -n "$NAMESPACE" deployment/postgres -- \
        psql -h localhost -U postgres -c "
        SELECT 
            query,
            calls,
            total_time,
            mean_time,
            rows
        FROM pg_stat_statements 
        ORDER BY mean_time DESC 
        LIMIT 10;
        "
}

# Fonction principale
main() {
    log_info "Début de la maintenance des bases de données - $ENVIRONMENT"
    
    case $OPERATION in
        analyze)
            analyze_databases
            ;;
        vacuum)
            vacuum_databases
            ;;
        reindex)
            reindex_databases
            ;;
        integrity)
            check_integrity
            ;;
        stats)
            performance_stats
            ;;
        full)
            analyze_databases
            vacuum_databases
            check_integrity
            performance_stats
            ;;
        *)
            log_error "Opération invalide: $OPERATION"
            log_info "Opérations disponibles: analyze, vacuum, reindex, integrity, stats, full"
            exit 1
            ;;
    esac
    
    log_success "Maintenance terminée"
}

main "$@"
```

### 2. Script de Nettoyage

**Fichier :** `scripts/maintenance/cleanup.sh`

```bash
#!/bin/bash

# Script de nettoyage pour Coko
# Usage: ./cleanup.sh <environment> [type]

set -euo pipefail

source "$(dirname "$0")/../utils/common.sh"
source "$(dirname "$0")/../utils/logging.sh"

ENVIRONMENT="${1:-staging}"
CLEANUP_TYPE="${2:-logs}"
NAMESPACE="coko-${ENVIRONMENT}"

# Nettoyage des logs
cleanup_logs() {
    log_info "Nettoyage des logs..."
    
    # Logs Elasticsearch (> 30 jours)
    log_info "Suppression des logs Elasticsearch anciens..."
    kubectl exec -n "$NAMESPACE" deployment/elasticsearch -- \
        curl -X DELETE "localhost:9200/coko-logs-*" \
        -H "Content-Type: application/json" \
        -d '{
            "query": {
                "range": {
                    "@timestamp": {
                        "lt": "now-30d"
                    }
                }
            }
        }'
    
    # Logs des pods (garder les 1000 dernières lignes)
    log_info "Rotation des logs des pods..."
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')
    
    for pod in $pods; do
        log_info "Rotation des logs de $pod..."
        kubectl logs "$pod" -n "$NAMESPACE" --tail=1000 > "/tmp/${pod}_logs.txt" 2>/dev/null || true
    done
    
    log_success "Nettoyage des logs terminé"
}

# Nettoyage des images Docker
cleanup_images() {
    log_info "Nettoyage des images Docker..."
    
    # Obtenir la liste des nodes
    local nodes
    nodes=$(kubectl get nodes -o jsonpath='{.items[*].metadata.name}')
    
    for node in $nodes; do
        log_info "Nettoyage des images sur $node..."
        
        # Exécuter le nettoyage sur chaque node
        kubectl debug node/$node -it --image=alpine -- \
            chroot /host sh -c '
                docker system prune -f
                docker image prune -a -f --filter "until=72h"
            ' 2>/dev/null || true
    done
    
    log_success "Nettoyage des images terminé"
}

# Nettoyage des volumes
cleanup_volumes() {
    log_info "Nettoyage des volumes..."
    
    # Volumes orphelins
    log_info "Recherche des volumes orphelins..."
    local orphaned_pvcs
    orphaned_pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers | \
        awk '$2 != "Bound" {print $1}')
    
    if [ -n "$orphaned_pvcs" ]; then
        log_warn "Volumes orphelins trouvés: $orphaned_pvcs"
        # Ne pas supprimer automatiquement, juste signaler
    else
        log_success "Aucun volume orphelin trouvé"
    fi
    
    # Nettoyage des données temporaires dans MinIO
    log_info "Nettoyage des fichiers temporaires MinIO..."
    kubectl exec -n "$NAMESPACE" deployment/minio -- \
        find /data -name "*.tmp" -mtime +1 -delete 2>/dev/null || true
    
    log_success "Nettoyage des volumes terminé"
}

# Nettoyage de la base de données
cleanup_database() {
    log_info "Nettoyage de la base de données..."
    
    # Sessions expirées
    log_info "Suppression des sessions expirées..."
    kubectl exec -n "$NAMESPACE" deployment/postgres -- \
        psql -h localhost -U postgres -d coko_auth -c "
        DELETE FROM sessions WHERE expires_at < NOW();
        "
    
    # Logs d'audit anciens (> 90 jours)
    log_info "Suppression des logs d'audit anciens..."
    kubectl exec -n "$NAMESPACE" deployment/postgres -- \
        psql -h localhost -U postgres -d coko_auth -c "
        DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';
        "
    
    # Notifications lues anciennes (> 30 jours)
    log_info "Suppression des notifications anciennes..."
    kubectl exec -n "$NAMESPACE" deployment/postgres -- \
        psql -h localhost -U postgres -d coko_community -c "
        DELETE FROM notifications 
        WHERE read_at IS NOT NULL 
        AND read_at < NOW() - INTERVAL '30 days';
        "
    
    log_success "Nettoyage de la base de données terminé"
}

# Nettoyage du cache
cleanup_cache() {
    log_info "Nettoyage du cache Redis..."
    
    # Clés expirées
    kubectl exec -n "$NAMESPACE" deployment/redis -- \
        redis-cli --scan --pattern "*:expired:*" | \
        xargs -r kubectl exec -n "$NAMESPACE" deployment/redis -- redis-cli DEL
    
    # Cache de session ancien
    kubectl exec -n "$NAMESPACE" deployment/redis -- \
        redis-cli --scan --pattern "session:*" | \
        while read key; do
            ttl=$(kubectl exec -n "$NAMESPACE" deployment/redis -- redis-cli TTL "$key")
            if [ "$ttl" -eq -1 ]; then
                kubectl exec -n "$NAMESPACE" deployment/redis -- redis-cli DEL "$key"
            fi
        done
    
    log_success "Nettoyage du cache terminé"
}

# Nettoyage complet
cleanup_all() {
    log_info "Nettoyage complet..."
    
    cleanup_logs
    cleanup_database
    cleanup_cache
    cleanup_volumes
    
    # Ne pas nettoyer les images en production automatiquement
    if [ "$ENVIRONMENT" != "production" ]; then
        cleanup_images
    fi
    
    log_success "Nettoyage complet terminé"
}

# Fonction principale
main() {
    log_info "Début du nettoyage - $ENVIRONMENT ($CLEANUP_TYPE)"
    
    case $CLEANUP_TYPE in
        logs)
            cleanup_logs
            ;;
        images)
            cleanup_images
            ;;
        volumes)
            cleanup_volumes
            ;;
        database)
            cleanup_database
            ;;
        cache)
            cleanup_cache
            ;;
        all)
            cleanup_all
            ;;
        *)
            log_error "Type de nettoyage invalide: $CLEANUP_TYPE"
            log_info "Types disponibles: logs, images, volumes, database, cache, all"
            exit 1
            ;;
    esac
    
    log_success "Nettoyage terminé"
}

main "$@"
```

---

## Scripts de Monitoring

### 1. Health Check

**Fichier :** `scripts/monitoring/health-check.sh`

```bash
#!/bin/bash

# Script de vérification de santé pour Coko
# Usage: ./health-check.sh <environment>

set -euo pipefail

source "$(dirname "$0")/../utils/common.sh"
source "$(dirname "$0")/../utils/logging.sh"

ENVIRONMENT="${1:-staging}"
NAMESPACE="coko-${ENVIRONMENT}"
FAILED_CHECKS=0

# URL de base selon l'environnement
get_base_url() {
    case $ENVIRONMENT in
        production)
            echo "https://api.coko.africa"
            ;;
        staging)
            echo "https://api-staging.coko.africa"
            ;;
        development)
            echo "http://localhost:3000"
            ;;
        *)
            echo "http://api-gateway-service.${NAMESPACE}.svc.cluster.local:3000"
            ;;
    esac
}

# Vérifier un endpoint
check_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    log_info "Vérification de $name..."
    
    local response
    local status_code
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "\n000")
    status_code=$(echo "$response" | tail -n1)
    
    if [ "$status_code" = "$expected_status" ]; then
        log_success "$name OK (HTTP $status_code)"
        return 0
    else
        log_error "$name FAILED (HTTP $status_code)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Vérifier les pods
check_pods() {
    log_info "Vérification des pods..."
    
    local services=("api-gateway" "auth-service" "catalog-service" "postgres" "redis")
    
    for service in "${services[@]}"; do
        local ready_pods
        local total_pods
        
        ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$service" \
            -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | \
            grep -o "True" | wc -l)
        
        total_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$service" \
            --no-headers | wc -l)
        
        if [ "$ready_pods" -eq "$total_pods" ] && [ "$total_pods" -gt 0 ]; then
            log_success "$service: $ready_pods/$total_pods pods prêts"
        else
            log_error "$service: $ready_pods/$total_pods pods prêts"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            
            # Afficher les pods en erreur
            kubectl get pods -n "$NAMESPACE" -l app="$service" | grep -v Running || true
        fi
    done
}

# Vérifier les services
check_services() {
    log_info "Vérification des services..."
    
    local base_url
    base_url=$(get_base_url)
    
    # Health check général
    check_endpoint "API Gateway Health" "$base_url/health"
    
    # Endpoints spécifiques
    check_endpoint "Auth Service" "$base_url/auth/health"
    check_endpoint "Catalog Service" "$base_url/catalog/health"
    
    # Test de fonctionnalité
    check_endpoint "Catalog Books" "$base_url/catalog/books?limit=1"
}

# Vérifier la base de données
check_database() {
    log_info "Vérification de la base de données..."
    
    # Test de connexion PostgreSQL
    if kubectl exec -n "$NAMESPACE" deployment/postgres -- \
        pg_isready -h localhost -U postgres &>/dev/null; then
        log_success "PostgreSQL accessible"
    else
        log_error "PostgreSQL inaccessible"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
    
    # Test des bases de données
    local databases=("coko_auth" "coko_catalog")
    for db in "${databases[@]}"; do
        if kubectl exec -n "$NAMESPACE" deployment/postgres -- \
            psql -h localhost -U postgres -d "$db" -c "SELECT 1;" &>/dev/null; then
            log_success "Base de données $db accessible"
        else
            log_error "Base de données $db inaccessible"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    done
}

# Vérifier Redis
check_redis() {
    log_info "Vérification de Redis..."
    
    if kubectl exec -n "$NAMESPACE" deployment/redis -- \
        redis-cli ping | grep -q "PONG"; then
        log_success "Redis accessible"
    else
        log_error "Redis inaccessible"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
    
    # Test d'écriture/lecture
    local test_key="health_check_$(date +%s)"
    if kubectl exec -n "$NAMESPACE" deployment/redis -- \
        redis-cli set "$test_key" "test" &>/dev/null && \
       kubectl exec -n "$NAMESPACE" deployment/redis -- \
        redis-cli get "$test_key" | grep -q "test"; then
        log_success "Redis lecture/écriture OK"
        kubectl exec -n "$NAMESPACE" deployment/redis -- \
            redis-cli del "$test_key" &>/dev/null
    else
        log_error "Redis lecture/écriture FAILED"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Vérifier les ressources
check_resources() {
    log_info "Vérification des ressources..."
    
    # CPU et mémoire des pods
    local high_cpu_pods
    high_cpu_pods=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | \
        awk '$2 ~ /[0-9]+m/ && $2+0 > 500 {print $1}' || true)
    
    if [ -n "$high_cpu_pods" ]; then
        log_warn "Pods avec CPU élevé: $high_cpu_pods"
    else
        log_success "Utilisation CPU normale"
    fi
    
    # Espace disque
    local disk_usage
    disk_usage=$(kubectl exec -n "$NAMESPACE" deployment/postgres -- \
        df -h /var/lib/postgresql/data | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -gt 80 ]; then
        log_warn "Utilisation disque élevée: ${disk_usage}%"
    else
        log_success "Utilisation disque normale: ${disk_usage}%"
    fi
}

# Générer un rapport
generate_report() {
    log_info "Génération du rapport de santé..."
    
    local report_file="/tmp/coko-health-report-${ENVIRONMENT}-$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== Rapport de Santé Coko - $ENVIRONMENT ==="
        echo "Date: $(date)"
        echo "Namespace: $NAMESPACE"
        echo ""
        
        echo "=== Statut des Pods ==="
        kubectl get pods -n "$NAMESPACE"
        echo ""
        
        echo "=== Statut des Services ==="
        kubectl get services -n "$NAMESPACE"
        echo ""
        
        echo "=== Utilisation des Ressources ==="
        kubectl top pods -n "$NAMESPACE" 2>/dev/null || echo "Metrics non disponibles"
        echo ""
        
        echo "=== Événements Récents ==="
        kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10
        
    } > "$report_file"
    
    log_info "Rapport généré: $report_file"
}

# Fonction principale
main() {
    log_info "Début du health check - $ENVIRONMENT"
    
    check_pods
    check_database
    check_redis
    check_services
    check_resources
    
    generate_report
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        log_success "Tous les checks sont passés! ✅"
        exit 0
    else
        log_error "$FAILED_CHECKS check(s) ont échoué! ❌"
        exit 1
    fi
}

main "$@"
```

---

## Scripts Utilitaires

### 1. Fonctions Communes

**Fichier :** `scripts/utils/common.sh`

```bash
#!/bin/bash

# Fonctions communes pour les scripts Coko

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Vérifier si une commande existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Vérifier les prérequis
check_prerequisites() {
    local required_commands=("kubectl" "curl" "jq")
    
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            echo "Erreur: $cmd n'est pas installé" >&2
            return 1
        fi
    done
    
    return 0
}

# Obtenir la version actuelle d'un service
get_current_version() {
    local service="$1"
    local namespace="$2"
    
    kubectl get deployment "$service" -n "$namespace" \
        -o jsonpath='{.spec.template.spec.containers[0].image}' | \
        cut -d':' -f2
}

# Attendre qu'un pod soit prêt
wait_for_pod() {
    local pod_selector="$1"
    local namespace="$2"
    local timeout="${3:-300}"
    
    kubectl wait --for=condition=ready pod \
        -l "$pod_selector" \
        -n "$namespace" \
        --timeout="${timeout}s"
}

# Obtenir l'IP d'un service
get_service_ip() {
    local service="$1"
    local namespace="$2"
    
    kubectl get service "$service" -n "$namespace" \
        -o jsonpath='{.spec.clusterIP}'
}

# Vérifier si un namespace existe
namespace_exists() {
    local namespace="$1"
    
    kubectl get namespace "$namespace" >/dev/null 2>&1
}

# Créer un namespace s'il n'existe pas
ensure_namespace() {
    local namespace="$1"
    
    if ! namespace_exists "$namespace"; then
        kubectl create namespace "$namespace"
    fi
}

# Obtenir le statut d'un deployment
get_deployment_status() {
    local deployment="$1"
    local namespace="$2"
    
    kubectl get deployment "$deployment" -n "$namespace" \
        -o jsonpath='{.status.conditions[?(@.type=="Available")].status}'
}

# Vérifier si un deployment est prêt
is_deployment_ready() {
    local deployment="$1"
    local namespace="$2"
    
    local status
    status=$(get_deployment_status "$deployment" "$namespace")
    
    [ "$status" = "True" ]
}

# Obtenir les logs d'un pod
get_pod_logs() {
    local pod_selector="$1"
    local namespace="$2"
    local lines="${3:-100}"
    
    kubectl logs -l "$pod_selector" -n "$namespace" --tail="$lines"
}

# Exécuter une commande dans un pod
exec_in_pod() {
    local pod_selector="$1"
    local namespace="$2"
    local command="$3"
    
    local pod
    pod=$(kubectl get pods -l "$pod_selector" -n "$namespace" \
        -o jsonpath='{.items[0].metadata.name}')
    
    if [ -n "$pod" ]; then
        kubectl exec "$pod" -n "$namespace" -- $command
    else
        echo "Aucun pod trouvé avec le sélecteur: $pod_selector" >&2
        return 1
    fi
}

# Obtenir la charge CPU d'un pod
get_pod_cpu_usage() {
    local pod="$1"
    local namespace="$2"
    
    kubectl top pod "$pod" -n "$namespace" --no-headers | awk '{print $2}'
}

# Obtenir l'utilisation mémoire d'un pod
get_pod_memory_usage() {
    local pod="$1"
    local namespace="$2"
    
    kubectl top pod "$pod" -n "$namespace" --no-headers | awk '{print $3}'
}

# Formatter une taille en bytes
format_bytes() {
    local bytes="$1"
    
    if [ "$bytes" -ge 1073741824 ]; then
        echo "$(( bytes / 1073741824 ))GB"
    elif [ "$bytes" -ge 1048576 ]; then
        echo "$(( bytes / 1048576 ))MB"
    elif [ "$bytes" -ge 1024 ]; then
        echo "$(( bytes / 1024 ))KB"
    else
        echo "${bytes}B"
    fi
}

# Obtenir le timestamp actuel
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Valider un format d'email
validate_email() {
    local email="$1"
    
    [[ "$email" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]
}

# Générer un mot de passe aléatoire
generate_password() {
    local length="${1:-16}"
    
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

# Encoder en base64
base64_encode() {
    local input="$1"
    
    echo -n "$input" | base64 -w 0
}

# Décoder depuis base64
base64_decode() {
    local input="$1"
    
    echo "$input" | base64 -d
}

# Vérifier si un port est ouvert
check_port() {
    local host="$1"
    local port="$2"
    local timeout="${3:-5}"
    
    timeout "$timeout" bash -c "</dev/tcp/$host/$port" 2>/dev/null
}

# Attendre qu'un port soit ouvert
wait_for_port() {
    local host="$1"
    local port="$2"
    local timeout="${3:-60}"
    
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        if check_port "$host" "$port" 1; then
            return 0
        fi
        
        sleep 1
        elapsed=$((elapsed + 1))
    done
    
    return 1
}

# Obtenir l'adresse IP publique
get_public_ip() {
    curl -s https://ipinfo.io/ip 2>/dev/null || \
    curl -s https://icanhazip.com 2>/dev/null || \
    echo "unknown"
}

# Vérifier la connectivité internet
check_internet() {
    curl -s --connect-timeout 5 https://google.com >/dev/null 2>&1
}

# Cleanup function pour les scripts
cleanup() {
    local temp_files=("$@")
    
    for file in "${temp_files[@]}"; do
        if [ -f "$file" ]; then
            rm -f "$file"
        fi
    done
}

# Trap pour cleanup automatique
setup_cleanup_trap() {
    local temp_files=("$@")
    
    trap "cleanup ${temp_files[*]}" EXIT INT TERM
}
```

### 2. Fonctions de Logging

**Fichier :** `scripts/utils/logging.sh`

```bash
#!/bin/bash

# Fonctions de logging pour les scripts Coko

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration du logging
LOG_LEVEL="${LOG_LEVEL:-INFO}"
LOG_FILE="${LOG_FILE:-}"
LOG_FORMAT="${LOG_FORMAT:-standard}"

# Niveaux de log
LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_WARN=2
LOG_LEVEL_ERROR=3

# Obtenir le niveau numérique
get_log_level_num() {
    case "${LOG_LEVEL^^}" in
        DEBUG) echo $LOG_LEVEL_DEBUG ;;
        INFO)  echo $LOG_LEVEL_INFO ;;
        WARN)  echo $LOG_LEVEL_WARN ;;
        ERROR) echo $LOG_LEVEL_ERROR ;;
        *)     echo $LOG_LEVEL_INFO ;;
    esac
}

# Fonction de log générique
log_message() {
    local level="$1"
    local level_num="$2"
    local color="$3"
    local message="$4"
    
    local current_level_num
    current_level_num=$(get_log_level_num)
    
    # Vérifier si on doit afficher ce niveau
    if [ "$level_num" -lt "$current_level_num" ]; then
        return 0
    fi
    
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    local formatted_message
    case "$LOG_FORMAT" in
        json)
            formatted_message=$(printf '{"timestamp":"%s","level":"%s","message":"%s"}' \
                "$timestamp" "$level" "$message")
            ;;
        structured)
            formatted_message=$(printf '[%s] %-5s %s' "$timestamp" "$level" "$message")
            ;;
        *)
            formatted_message=$(printf '%s[%s]%s %-5s %s' \
                "$color" "$timestamp" "$NC" "$level" "$message")
            ;;
    esac
    
    # Afficher sur stdout/stderr
    if [ "$level_num" -ge "$LOG_LEVEL_ERROR" ]; then
        echo -e "$formatted_message" >&2
    else
        echo -e "$formatted_message"
    fi
    
    # Écrire dans le fichier de log si configuré
    if [ -n "$LOG_FILE" ]; then
        # Enlever les couleurs pour le fichier
        local clean_message
        clean_message=$(echo "$formatted_message" | sed 's/\x1b\[[0-9;]*m//g')
        echo "$clean_message" >> "$LOG_FILE"
    fi
}

# Fonctions de log spécifiques
log_debug() {
    log_message "DEBUG" $LOG_LEVEL_DEBUG "$CYAN" "$1"
}

log_info() {
    log_message "INFO" $LOG_LEVEL_INFO "$BLUE" "$1"
}

log_success() {
    log_message "SUCCESS" $LOG_LEVEL_INFO "$GREEN" "$1"
}

log_warn() {
    log_message "WARN" $LOG_LEVEL_WARN "$YELLOW" "$1"
}

log_error() {
    log_message "ERROR" $LOG_LEVEL_ERROR "$RED" "$1"
}

# Log avec contexte
log_with_context() {
    local context="$1"
    local level="$2"
    local message="$3"
    
    case "$level" in
        debug) log_debug "[$context] $message" ;;
        info)  log_info "[$context] $message" ;;
        warn)  log_warn "[$context] $message" ;;
        error) log_error "[$context] $message" ;;
        success) log_success "[$context] $message" ;;
        *) log_info "[$context] $message" ;;
    esac
}

# Initialiser le logging
init_logging() {
    local log_dir="${1:-/var/log/coko}"
    
    if [ -n "$LOG_FILE" ] && [ "$LOG_FILE" != "/dev/null" ]; then
        # Créer le répertoire de log si nécessaire
        mkdir -p "$(dirname "$LOG_FILE")"
        
        # Rotation des logs si le fichier est trop gros (>10MB)
        if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]; then
            mv "$LOG_FILE" "${LOG_FILE}.old"
        fi
        
        # Initialiser le fichier de log
        echo "=== Début de session - $(date) ===" >> "$LOG_FILE"
    fi
}

# Finaliser le logging
finalize_logging() {
    if [ -n "$LOG_FILE" ] && [ "$LOG_FILE" != "/dev/null" ]; then
        echo "=== Fin de session - $(date) ===" >> "$LOG_FILE"
    fi
}

# Progress bar
show_progress() {
    local current="$1"
    local total="$2"
    local message="${3:-}"
    
    local percent=$((current * 100 / total))
    local filled=$((percent / 2))
    local empty=$((50 - filled))
    
    printf "\r%s [" "$message"
    printf "%*s" $filled | tr ' ' '='
    printf "%*s" $empty | tr ' ' '-'
    printf "] %d%% (%d/%d)" $percent $current $total
    
    if [ $current -eq $total ]; then
        echo
    fi
}
```

### 3. Fonctions de Notifications

**Fichier :** `scripts/utils/notifications.sh`

```bash
#!/bin/bash

# Fonctions de notification pour les scripts Coko

# Configuration
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
EMAIL_SMTP_SERVER="${EMAIL_SMTP_SERVER:-}"
EMAIL_FROM="${EMAIL_FROM:-noreply@coko.africa}"
TEAMS_WEBHOOK_URL="${TEAMS_WEBHOOK_URL:-}"

# Envoyer une notification Slack
send_slack_notification() {
    local message="$1"
    local channel="${2:-#devops}"
    local username="${3:-Coko Bot}"
    
    if [ -z "$SLACK_WEBHOOK_URL" ]; then
        log_warn "SLACK_WEBHOOK_URL non configuré, notification ignorée"
        return 0
    fi
    
    local payload
    payload=$(cat <<EOF
{
    "channel": "$channel",
    "username": "$username",
    "text": "$message",
    "icon_emoji": ":robot_face:"
}
EOF
    )
    
    if curl -s -X POST -H 'Content-type: application/json' \
        --data "$payload" "$SLACK_WEBHOOK_URL" >/dev/null; then
        log_debug "Notification Slack envoyée"
    else
        log_error "Échec de l'envoi de la notification Slack"
    fi
}

# Envoyer un email
send_email_notification() {
    local message="$1"
    local to="$2"
    local subject="${3:-Notification Coko}"
    
    if [ -z "$EMAIL_SMTP_SERVER" ]; then
        log_warn "EMAIL_SMTP_SERVER non configuré, email ignoré"
        return 0
    fi
    
    # Utiliser mail ou sendmail selon disponibilité
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "$subject" "$to"
    elif command -v sendmail >/dev/null 2>&1; then
        {
            echo "To: $to"
            echo "From: $EMAIL_FROM"
            echo "Subject: $subject"
            echo ""
            echo "$message"
        } | sendmail "$to"
    else
        log_error "Aucun client email disponible"
        return 1
    fi
    
    log_debug "Email envoyé à $to"
}

# Envoyer une notification Teams
send_teams_notification() {
    local message="$1"
    local title="${2:-Notification Coko}"
    
    if [ -z "$TEAMS_WEBHOOK_URL" ]; then
        log_warn "TEAMS_WEBHOOK_URL non configuré, notification ignorée"
        return 0
    fi
    
    local payload
    payload=$(cat <<EOF
{
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "$title",
    "sections": [{
        "activityTitle": "$title",
        "activitySubtitle": "$(date)",
        "text": "$message",
        "markdown": true
    }]
}
EOF
    )
    
    if curl -s -X POST -H 'Content-Type: application/json' \
        --data "$payload" "$TEAMS_WEBHOOK_URL" >/dev/null; then
        log_debug "Notification Teams envoyée"
    else
        log_error "Échec de l'envoi de la notification Teams"
    fi
}

# Notification multi-canal
send_notification() {
    local message="$1"
    local level="${2:-info}"
    local channels="${3:-slack}"
    
    # Ajouter des emojis selon le niveau
    local emoji
    case "$level" in
        success) emoji="✅" ;;
        warning) emoji="⚠️" ;;
        error)   emoji="❌" ;;
        info)    emoji="ℹ️" ;;
        *)       emoji="📢" ;;
    esac
    
    local formatted_message="$emoji $message"
    
    # Envoyer selon les canaux demandés
    IFS=',' read -ra CHANNEL_ARRAY <<< "$channels"
    for channel in "${CHANNEL_ARRAY[@]}"; do
        case "$channel" in
            slack)
                send_slack_notification "$formatted_message"
                ;;
            email)
                send_email_notification "$message" "devops@coko.africa" "Coko - $level"
                ;;
            teams)
                send_teams_notification "$message" "Coko - $level"
                ;;
            *)
                log_warn "Canal de notification inconnu: $channel"
                ;;
        esac
    done
}
```

---

## Configuration et Variables

### Variables d'Environnement

```bash
# Configuration générale
export COKO_ENVIRONMENT="staging"  # development, staging, production
export COKO_VERSION="latest"
export COKO_NAMESPACE="coko-${COKO_ENVIRONMENT}"

# Kubernetes
export KUBECONFIG="${HOME}/.kube/config"
export KUBECTL_TIMEOUT="600s"

# Logging
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARN, ERROR
export LOG_FILE="/var/log/coko/automation.log"
export LOG_FORMAT="standard"  # standard, json, structured

# Notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export EMAIL_SMTP_SERVER="smtp.gmail.com"
export EMAIL_FROM="noreply@coko.africa"
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/..."

# Base de données
export DB_BACKUP_RETENTION_DAYS="30"
export DB_BACKUP_S3_BUCKET="coko-backups"

# Monitoring
export HEALTH_CHECK_TIMEOUT="30"
export PERFORMANCE_TEST_DURATION="5m"
export LOAD_TEST_USERS="100"

# Sécurité
export SECURITY_SCAN_ENABLED="true"
export VULNERABILITY_THRESHOLD="high"
```

### Fichier de Configuration

**Fichier :** `scripts/config/automation.conf`

```bash
# Configuration des scripts d'automatisation Coko

# Environnements supportés
SUPPORTED_ENVIRONMENTS=("development" "staging" "production")

# Services Coko
COKO_SERVICES=(
    "api-gateway"
    "auth-service"
    "catalog-service"
    "reading-service"
    "payment-service"
    "gamification-service"
    "community-service"
    "admin-service"
    "notification-service"
)

# Services d'infrastructure
INFRA_SERVICES=(
    "postgres"
    "redis"
    "elasticsearch"
    "minio"
    "rabbitmq"
)

# Timeouts (en secondes)
DEPLOYMENT_TIMEOUT=600
HEALTH_CHECK_TIMEOUT=30
ROLLBACK_TIMEOUT=300
BACKUP_TIMEOUT=1800

# Seuils d'alerte
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
ERROR_RATE_THRESHOLD=5

# Rétention
LOG_RETENTION_DAYS=30
BACKUP_RETENTION_DAYS=90
METRICS_RETENTION_DAYS=365

# URLs par environnement
declare -A ENVIRONMENT_URLS
ENVIRONMENT_URLS["development"]="http://localhost:3000"
ENVIRONMENT_URLS["staging"]="https://api-staging.coko.africa"
ENVIRONMENT_URLS["production"]="https://api.coko.africa"

# Canaux de notification par environnement
declare -A NOTIFICATION_CHANNELS
NOTIFICATION_CHANNELS["development"]="slack"
NOTIFICATION_CHANNELS["staging"]="slack,email"
NOTIFICATION_CHANNELS["production"]="slack,email,teams"
```

---

## Utilisation des Scripts

### Exemples d'Utilisation

```bash
# Déploiement
./scripts/deployment/deploy.sh staging v1.2.3
./scripts/deployment/blue-green-deploy.sh production v1.2.3

# Maintenance
./scripts/maintenance/database-maintenance.sh production full
./scripts/maintenance/cleanup.sh staging all

# Monitoring
./scripts/monitoring/health-check.sh production
./scripts/monitoring/performance-test.sh staging

# Backup
./scripts/backup/backup-databases.sh production
./scripts/backup/restore-database.sh staging coko_catalog

# Urgence
./scripts/emergency/emergency-rollback.sh production
./scripts/emergency/scale-services.sh production api-gateway 10
```

### Intégration CI/CD

Les scripts peuvent être intégrés dans les pipelines GitHub Actions :

```yaml
- name: Deploy to Staging
  run: |
    chmod +x scripts/deployment/deploy.sh
    ./scripts/deployment/deploy.sh staging ${{ github.sha }}

- name: Health Check
  run: |
    chmod +x scripts/monitoring/health-check.sh
    ./scripts/monitoring/health-check.sh staging
```

### Automatisation avec Cron

```bash
# Maintenance quotidienne
0 2 * * * /path/to/scripts/maintenance/cleanup.sh production logs

# Backup quotidien
0 3 * * * /path/to/scripts/backup/backup-databases.sh production

# Health check toutes les 5 minutes
*/5 * * * * /path/to/scripts/monitoring/health-check.sh production
```

---

## Bonnes Pratiques

1. **Sécurité**
   - Stocker les secrets dans des variables d'environnement
   - Utiliser des rôles RBAC appropriés
   - Auditer les accès aux scripts

2. **Monitoring**
   - Logger toutes les opérations
   - Envoyer des notifications pour les événements critiques
   - Surveiller les performances des scripts

3. **Maintenance**
   - Tester les scripts régulièrement
   - Maintenir la documentation à jour
   - Versionner les scripts avec le code

4. **Récupération**
   - Toujours avoir un plan de rollback
   - Tester les procédures de récupération
   - Documenter les procédures d'urgence