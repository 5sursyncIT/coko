#!/usr/bin/env python
"""
Script de démarrage pour le développement avec fonctionnalités africaines
Optimisé pour les conditions de développement en Afrique
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_african_environment():
    """
    Configure l'environnement pour les fonctionnalités africaines
    """
    logger.info("🌍 Configuration de l'environnement africain...")
    
    # Variables d'environnement par défaut pour le développement
    default_env = {
        'DJANGO_SETTINGS_MODULE': 'coko.settings_local',
        'PYTHONPATH': os.path.dirname(os.path.abspath(__file__)),
        
        # Optimisations africaines
        'ENABLE_AFRICAN_OPTIMIZATIONS': 'true',
        'AGGRESSIVE_CACHING': 'true',
        'COMPRESSION_LEVEL': 'balanced',
        'LOW_BANDWIDTH_MODE': 'true',
        
        # Géolocalisation (mode développement)
        'AFRICAN_GEOLOCATION_FALLBACK_COUNTRY': 'SN',  # Sénégal
        'AFRICAN_GEOLOCATION_CACHE_TIMEOUT': '3600',
        
        # Paiements (mode sandbox)
        'ORANGE_MONEY_SANDBOX': 'true',
        'MTN_MOMO_SANDBOX': 'true',
        'WAVE_SANDBOX': 'true',
        
        # Performance
        'PWA_CACHE_VERSION': '1.0.0-dev',
        'AFRICAN_CDN_ENABLED': 'false',  # Désactivé en dev
        
        # Monitoring
        'AFRICAN_MONITORING_ENABLED': 'true',
        'AFRICAN_MONITORING_DEBUG': 'true',
        
        # Langues
        'AFRICAN_LANGUAGES_AUTO_DETECT': 'true',
        'AFRICAN_LANGUAGES_FALLBACK': 'fr',
    }
    
    # Appliquer les variables d'environnement
    for key, value in default_env.items():
        if key not in os.environ:
            os.environ[key] = value
            logger.info(f"✓ {key} = {value}")

def check_african_dependencies():
    """
    Vérifie que toutes les dépendances africaines sont disponibles
    """
    logger.info("🔍 Vérification des dépendances africaines...")
    
    required_packages = [
        'django',
        'requests',
        'PIL',  # Pour l'optimisation d'images (Pillow)
    ]
    
    optional_packages = {
        'brotli': 'Compression Brotli (recommandé pour l\'Afrique)',
        'redis': 'Cache Redis (optionnel)',
        'celery': 'Tâches asynchrones (optionnel)',
    }
    
    # Vérifier les packages requis
    missing_required = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} disponible")
        except ImportError:
            missing_required.append(package)
            logger.error(f"✗ {package} manquant")
    
    if missing_required:
        logger.error(f"Packages manquants: {', '.join(missing_required)}")
        logger.error("Installez avec: pip install " + ' '.join(missing_required))
        return False
    
    # Vérifier les packages optionnels
    for package, description in optional_packages.items():
        try:
            __import__(package)
            logger.info(f"✓ {package} disponible - {description}")
        except ImportError:
            logger.warning(f"⚠ {package} non disponible - {description}")
    
    return True

def setup_african_database():
    """
    Configure la base de données avec les optimisations africaines
    """
    logger.info("🗄️ Configuration de la base de données...")
    
    try:
        # Importer Django après configuration de l'environnement
        django.setup()
        
        from django.core.management import call_command
        from django.db import connection
        
        # Vérifier la connexion à la base de données
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            logger.info("✓ Connexion à la base de données OK")
        
        # Appliquer les migrations
        logger.info("Applying migrations...")
        call_command('migrate', verbosity=0)
        logger.info("✓ Migrations appliquées")
        
        # Créer un superutilisateur si nécessaire
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            logger.info("Création d'un superutilisateur...")
            User.objects.create_superuser(
                username='admin',
                email='admin@coko.africa',
                password='admin123'
            )
            logger.info("✓ Superutilisateur créé (admin/admin123)")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur de configuration de la base de données: {e}")
        return False

def test_african_features():
    """
    Teste les fonctionnalités africaines de base
    """
    logger.info("🧪 Test des fonctionnalités africaines...")
    
    try:
        # Test de géolocalisation
        from coko.african_geolocation import AfricanGeolocationManager
        geo_manager = AfricanGeolocationManager()
        logger.info("✓ Géolocalisation africaine initialisée")
        
        # Test des paiements
        from coko.african_payments import AfricanPaymentManager
        payment_manager = AfricanPaymentManager()
        logger.info("✓ Gestionnaire de paiements africains initialisé")
        
        # Test des langues
        from coko.african_languages import AfricanLanguageManager
        lang_manager = AfricanLanguageManager()
        available_langs = len(lang_manager.african_languages)
        logger.info(f"✓ Support multilingue: {available_langs} langues africaines")
        
        # Test du monitoring
        from coko.african_monitoring import AfricanMetricsCollector
        metrics_collector = AfricanMetricsCollector()
        logger.info("✓ Monitoring africain initialisé")
        
        # Test PWA
        from coko.african_pwa import AfricanPWAManager
        pwa_manager = AfricanPWAManager()
        logger.info("✓ PWA africaine initialisée")
        
        # Test des performances
        from coko.african_performance import AfricanPerformanceOptimizer
        perf_optimizer = AfricanPerformanceOptimizer()
        logger.info("✓ Optimiseur de performances initialisé")
        
        logger.info("🎉 Toutes les fonctionnalités africaines sont opérationnelles!")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors du test des fonctionnalités: {e}")
        return False

def display_african_info():
    """
    Affiche les informations sur les fonctionnalités africaines
    """
    print("\n" + "="*60)
    print("🌍 COKO - PLATEFORME OPTIMISÉE POUR L'AFRIQUE")
    print("="*60)
    print("\n📋 Fonctionnalités activées:")
    print("   ✓ Optimisation réseau adaptative")
    print("   ✓ Support de 12 langues africaines")
    print("   ✓ Paiements mobiles (Orange Money, MTN MoMo, Wave)")
    print("   ✓ Mode hors-ligne avec PWA")
    print("   ✓ Géolocalisation africaine")
    print("   ✓ Monitoring spécialisé")
    print("   ✓ Compression et cache agressifs")
    
    print("\n🌐 URLs importantes:")
    print("   • Dashboard africain: http://localhost:8000/african-dashboard/")
    print("   • Monitoring: http://localhost:8000/api/african/monitoring/dashboard/")
    print("   • Statut réseau: http://localhost:8000/network-status/")
    print("   • Méthodes de paiement: http://localhost:8000/payment-methods/")
    print("   • Admin: http://localhost:8000/admin/ (admin/admin123)")
    
    print("\n📱 APIs africaines:")
    print("   • Paiements: /api/african/payments/")
    print("   • Géolocalisation: /api/african/geolocation/")
    print("   • Langues: /api/african/languages/")
    print("   • Performance: /api/african/performance/")
    
    print("\n🔧 Configuration:")
    print(f"   • Mode: Développement avec optimisations africaines")
    print(f"   • Base de données: SQLite (optimisée)")
    print(f"   • Cache: Agressif pour simulation connexion lente")
    print(f"   • Compression: Activée (Gzip/Brotli)")
    print(f"   • PWA: Activée avec cache offline")
    
    print("\n📚 Documentation:")
    print("   • Fonctionnalités: /root/coko/backend/AFRICAN_FEATURES.md")
    print("   • Recommandations: /root/coko/RECOMMENDATIONS.md")
    
    print("\n" + "="*60)
    print("🚀 Serveur prêt pour le développement africain!")
    print("="*60 + "\n")

def main():
    """
    Fonction principale de démarrage
    """
    logger.info("🚀 Démarrage du serveur de développement africain...")
    
    # 1. Configuration de l'environnement
    setup_african_environment()
    
    # 2. Vérification des dépendances
    if not check_african_dependencies():
        sys.exit(1)
    
    # 3. Configuration de la base de données
    if not setup_african_database():
        sys.exit(1)
    
    # 4. Test des fonctionnalités
    if not test_african_features():
        logger.warning("Certaines fonctionnalités africaines ne sont pas disponibles")
    
    # 5. Affichage des informations
    display_african_info()
    
    # 6. Démarrage du serveur
    logger.info("Démarrage du serveur Django...")
    
    # Arguments par défaut pour le serveur
    default_args = ['manage.py', 'runserver', '0.0.0.0:8000']
    
    # Utiliser les arguments de la ligne de commande s'ils sont fournis
    if len(sys.argv) > 1:
        args = sys.argv
    else:
        args = default_args
    
    try:
        execute_from_command_line(args)
    except KeyboardInterrupt:
        logger.info("\n👋 Arrêt du serveur. Au revoir!")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()