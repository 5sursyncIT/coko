#!/usr/bin/env python3
"""Script de configuration des dépendances pour l'application Coko"""

import os
import sys
import subprocess
import argparse

def run_command(command, description):
    """Exécute une commande et gère les erreurs"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Échec")
        print(f"Erreur: {e.stderr}")
        return False

def install_minimal_dependencies():
    """Installe les dépendances minimales (core requirements seulement)"""
    print("📦 Installation des dépendances minimales...")
    success = run_command(
        "pip install -r requirements.txt",
        "Installation des dépendances de base"
    )
    if success:
        print("💡 Note: Les dépendances ML/AI sont commentées. Décommentez-les dans requirements.txt si nécessaire.")
    return success

def install_ml_dependencies():
    """Active les dépendances ML/AI en les décommentant dans requirements.txt"""
    print("🤖 Activation des dépendances ML/AI...")
    
    try:
        # Lire requirements.txt
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        # Décommenter les packages ML/AI
        ml_packages = [
            'scikit-learn==1.3.2',
            'numpy==1.26.2', 
            'pandas==2.1.4',
            'scipy==1.11.4',
            'transformers==4.36.0',
            'nltk==3.8.1',
            'spacy==3.7.2',
            'langdetect==1.0.9'
        ]
        
        for package in ml_packages:
            content = content.replace(f'# {package}', package)
        
        # Réécrire requirements.txt
        with open('requirements.txt', 'w') as f:
            f.write(content)
        
        # Installer les dépendances
        return run_command(
            "pip install -r requirements.txt",
            "Installation des dépendances ML/AI"
        )
    except Exception as e:
        print(f"❌ Erreur lors de l'activation des dépendances ML/AI: {e}")
        return False

def install_full_dependencies():
    """Installe toutes les dépendances (décommente tout)"""
    print("📦 Installation de toutes les dépendances...")
    
    try:
        # Lire requirements.txt
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        # Décommenter tous les packages optionnels
        all_packages = [
            'scikit-learn==1.3.2',
            'numpy==1.26.2',
            'pandas==2.1.4', 
            'scipy==1.11.4',
            'tensorflow==2.15.0',
            'torch==2.1.2',
            'transformers==4.36.0',
            'nltk==3.8.1',
            'spacy==3.7.2',
            'langdetect==1.0.9',
            'opencv-python==4.8.1.78'
        ]
        
        for package in all_packages:
            content = content.replace(f'# {package}', package)
        
        # Réécrire requirements.txt
        with open('requirements.txt', 'w') as f:
            f.write(content)
        
        # Installer les dépendances
        return run_command(
            "pip install -r requirements.txt",
            "Installation complète des dépendances"
        )
    except Exception as e:
        print(f"❌ Erreur lors de l'installation complète: {e}")
        return False

def setup_database():
    """Configure la base de données"""
    print("\n🗄️ Configuration de la base de données...")
    
    commands = [
        ("python manage.py makemigrations", "Création des migrations"),
        ("python manage.py migrate --database=default", "Migration base par défaut"),
        ("python manage.py migrate --database=auth_db", "Migration base auth"),
        ("python manage.py migrate --database=catalog_db", "Migration base catalog"),
        ("python manage.py migrate --database=reading_db", "Migration base reading"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def collect_static():
    """Collecte les fichiers statiques"""
    return run_command(
        "python manage.py collectstatic --noinput",
        "Collecte des fichiers statiques"
    )

def check_environment():
    """Vérifie l'environnement"""
    print("🔍 Vérification de l'environnement...")
    
    # Vérifier Python
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python {python_version.major}.{python_version.minor} détecté. Python 3.8+ requis.")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Vérifier pip
    try:
        import pip
        print(f"✅ pip disponible")
    except ImportError:
        print("❌ pip non disponible")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Configuration des dépendances Coko")
    parser.add_argument(
        '--mode',
        choices=['minimal', 'ml', 'full'],
        default='minimal',
        help='Mode d\'installation: minimal (sans ML), ml (avec ML), full (tout)'
    )
    parser.add_argument(
        '--skip-db',
        action='store_true',
        help='Ignorer la configuration de la base de données'
    )
    parser.add_argument(
        '--skip-static',
        action='store_true',
        help='Ignorer la collecte des fichiers statiques'
    )
    
    args = parser.parse_args()
    
    print("🚀 Configuration de l'application Coko")
    print(f"Mode: {args.mode}")
    
    # Vérification de l'environnement
    if not check_environment():
        sys.exit(1)
    
    # Installation des dépendances
    success = False
    if args.mode == 'minimal':
        success = install_minimal_dependencies()
    elif args.mode == 'ml':
        success = install_minimal_dependencies() and install_ml_dependencies()
    elif args.mode == 'full':
        success = install_full_dependencies()
    
    if not success:
        print("❌ Échec de l'installation des dépendances")
        sys.exit(1)
    
    # Configuration de la base de données
    if not args.skip_db:
        if not setup_database():
            print("❌ Échec de la configuration de la base de données")
            sys.exit(1)
    
    # Collecte des fichiers statiques
    if not args.skip_static:
        if not collect_static():
            print("⚠️ Échec de la collecte des fichiers statiques (non critique)")
    
    print("\n🎉 Configuration terminée avec succès!")
    print("\n📋 Prochaines étapes:")
    print("   1. Configurer les variables d'environnement (.env)")
    print("   2. Créer un superutilisateur: python manage.py createsuperuser")
    print("   3. Démarrer le serveur: python manage.py runserver")
    
    if args.mode == 'minimal':
        print("\n💡 Pour activer les fonctionnalités ML/AI:")
        print("   python setup_dependencies.py --mode ml")

if __name__ == '__main__':
    main()