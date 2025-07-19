#!/usr/bin/env python
"""
Script de démarrage rapide pour le développement local sans Docker
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Succès")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erreur")
        if e.stderr:
            print(f"Erreur: {e.stderr}")
        if e.stdout:
            print(f"Sortie: {e.stdout}")
        return False

def setup_environment():
    """Configure l'environnement de développement"""
    print("🚀 Configuration de l'environnement de développement Coko")
    print("📝 Mode: Développement local (sans Docker)")
    
    # Vérifier que nous sommes dans le bon répertoire
    if not Path('manage.py').exists():
        print("❌ Erreur: manage.py non trouvé. Exécutez ce script depuis le répertoire backend/")
        sys.exit(1)
    
    # Définir la variable d'environnement pour utiliser les paramètres de dev
    os.environ['DJANGO_SETTINGS_MODULE'] = 'coko.settings_dev'
    
    # Créer les répertoires nécessaires
    print("\n📁 Création des répertoires...")
    Path('logs').mkdir(exist_ok=True)
    Path('media').mkdir(exist_ok=True)
    Path('staticfiles').mkdir(exist_ok=True)
    print("✅ Répertoires créés")
    
    # Migrations
    if not run_command("python manage.py makemigrations", "Création des migrations"):
        print("⚠️  Erreur lors de la création des migrations, mais on continue...")
    
    if not run_command("python manage.py migrate", "Application des migrations"):
        print("❌ Erreur critique lors des migrations")
        return False
    
    # Collecte des fichiers statiques
    run_command("python manage.py collectstatic --noinput", "Collecte des fichiers statiques")
    
    return True

def create_superuser_if_needed():
    """Crée un superutilisateur si nécessaire"""
    print("\n👤 Vérification du superutilisateur...")
    
    # Vérifier s'il existe déjà un superutilisateur
    check_cmd = "python manage.py shell -c \"from auth_service.models import User; print('exists' if User.objects.filter(is_superuser=True).exists() else 'none')\""
    
    try:
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if 'exists' in result.stdout:
            print("✅ Superutilisateur déjà existant")
            return
    except:
        pass
    
    print("🔧 Création d'un superutilisateur de développement...")
    if run_command("python create_superuser.py", "Création du superutilisateur"):
        print("✅ Superutilisateur créé: superadmin / admin123")
        print("🌐 Admin: http://localhost:8000/admin/")

def start_server():
    """Démarre le serveur de développement"""
    print("\n🌐 Démarrage du serveur de développement...")
    print("📍 URL: http://localhost:8000/")
    print("🛑 Arrêt: Ctrl+C")
    print("-" * 50)
    
    try:
        subprocess.run("python manage.py runserver 0.0.0.0:8000", shell=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Serveur arrêté")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚀 COKO - Démarrage Développement Local")
    print("=" * 60)
    
    # Configuration de l'environnement
    if not setup_environment():
        print("\n❌ Échec de la configuration. Vérifiez les erreurs ci-dessus.")
        sys.exit(1)
    
    # Création du superutilisateur
    create_superuser_if_needed()
    
    # Démarrage du serveur
    start_server()

if __name__ == "__main__":
    main()