# Guide d'Installation PostgreSQL (Optionnel)

## 🚀 Démarrage Rapide (SQLite)

Pour commencer immédiatement sans PostgreSQL :

```bash
# Dans le répertoire backend/
python start_dev.py
```

Ce script utilise SQLite et démarre automatiquement l'application.

## 📦 Installation PostgreSQL (Ubuntu/Debian)

Si vous souhaitez utiliser PostgreSQL plus tard :

### 1. Installation

```bash
# Mise à jour des paquets
sudo apt update

# Installation de PostgreSQL
sudo apt install postgresql postgresql-contrib

# Démarrage du service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Configuration

```bash
# Connexion en tant qu'utilisateur postgres
sudo -u postgres psql

# Dans psql, créer les bases de données :
CREATE DATABASE coko_main;
CREATE DATABASE coko_auth;
CREATE DATABASE coko_catalog;
CREATE DATABASE coko_reading;

# Créer un utilisateur (optionnel)
CREATE USER coko_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE coko_main TO coko_user;
GRANT ALL PRIVILEGES ON DATABASE coko_auth TO coko_user;
GRANT ALL PRIVILEGES ON DATABASE coko_catalog TO coko_user;
GRANT ALL PRIVILEGES ON DATABASE coko_reading TO coko_user;

# Quitter psql
\q
```

### 3. Configuration Django

Créer un fichier `.env` :

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec vos paramètres PostgreSQL
nano .env
```

Contenu du `.env` :

```env
# Base de données
DB_NAME=coko_main
AUTH_DB_NAME=coko_auth
CATALOG_DB_NAME=coko_catalog
READING_DB_NAME=coko_reading
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Django
DJANGO_SETTINGS_MODULE=coko.settings
SECRET_KEY=votre-clé-secrète-très-longue-et-sécurisée
DEBUG=True

# Redis (optionnel)
REDIS_URL=redis://localhost:6379/0
```

### 4. Démarrage avec PostgreSQL

```bash
# Utiliser les paramètres de production
export DJANGO_SETTINGS_MODULE=coko.settings

# Migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python create_superuser.py

# Démarrer le serveur
python manage.py runserver 0.0.0.0:8000
```

## 🔧 Services Additionnels

### Redis (pour le cache et Celery)

```bash
# Installation
sudo apt install redis-server

# Démarrage
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test
redis-cli ping
# Doit retourner: PONG
```

### Elasticsearch (pour la recherche)

```bash
# Installation Java (prérequis)
sudo apt install openjdk-11-jdk

# Télécharger et installer Elasticsearch 7.x
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.17.9-amd64.deb
sudo dpkg -i elasticsearch-7.17.9-amd64.deb

# Configuration
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch

# Test
curl -X GET "localhost:9200/"
```

## 🐳 Alternative Docker

Si vous préférez Docker plus tard :

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

## 🚨 Dépannage

### PostgreSQL ne démarre pas

```bash
# Vérifier le statut
sudo systemctl status postgresql

# Voir les logs
sudo journalctl -u postgresql

# Redémarrer
sudo systemctl restart postgresql
```

### Erreur de connexion Django

1. Vérifier que PostgreSQL fonctionne :
   ```bash
   sudo -u postgres psql -c "SELECT version();"
   ```

2. Vérifier les paramètres dans `.env`

3. Tester la connexion :
   ```bash
   python manage.py dbshell
   ```

### Permissions PostgreSQL

```bash
# Éditer la configuration
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Changer 'peer' en 'md5' pour l'authentification locale
# Redémarrer PostgreSQL
sudo systemctl restart postgresql
```

## 📝 Notes

- **SQLite** : Parfait pour le développement, simple et rapide
- **PostgreSQL** : Recommandé pour la production, plus de fonctionnalités
- **Docker** : Idéal pour un environnement isolé et reproductible

Choisissez la solution qui convient le mieux à votre workflow de développement !