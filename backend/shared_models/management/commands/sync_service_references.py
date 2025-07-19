"""
Commande de gestion pour synchroniser les références entre services.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from typing import List, Optional
import uuid

from shared_models.services import reference_manager, service_communication
from shared_models.api_client import service_clients


class Command(BaseCommand):
    """
    Commande pour synchroniser les références entre services.
    
    Usage:
        python manage.py sync_service_references
        python manage.py sync_service_references --service catalog
        python manage.py sync_service_references --full-sync
    """
    
    help = 'Synchronise les références entre les microservices'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--service',
            type=str,
            choices=['catalog', 'auth', 'reading', 'recommendation'],
            help='Service spécifique à synchroniser'
        )
        
        parser.add_argument(
            '--full-sync',
            action='store_true',
            help='Effectue une synchronisation complète'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les actions qui seraient effectuées sans les exécuter'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=1000,
            help='Limite le nombre d\'objets à synchroniser'
        )
    
    def handle(self, *args, **options):
        """
        Point d'entrée principal de la commande.
        """
        self.dry_run = options['dry_run']
        self.limit = options['limit']
        
        start_time = timezone.now()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('Mode DRY-RUN activé - aucune modification ne sera effectuée')
            )
        
        try:
            if options['full_sync']:
                self.full_sync()
            elif options['service']:
                self.sync_service(options['service'])
            else:
                self.sync_pending_events()
            
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Synchronisation terminée en {duration:.2f} secondes'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Erreur lors de la synchronisation: {e}')
    
    def full_sync(self):
        """
        Effectue une synchronisation complète de tous les services.
        """
        self.stdout.write('Démarrage de la synchronisation complète...')
        
        services = ['catalog', 'auth']
        
        for service in services:
            self.stdout.write(f'Synchronisation du service {service}...')
            self.sync_service(service)
    
    def sync_service(self, service_name: str):
        """
        Synchronise un service spécifique.
        """
        if service_name == 'catalog':
            self.sync_catalog_service()
        elif service_name == 'auth':
            self.sync_auth_service()
        else:
            self.stdout.write(
                self.style.WARNING(f'Synchronisation du service {service_name} non implémentée')
            )
    
    def sync_catalog_service(self):
        """
        Synchronise les données du service catalog.
        """
        self.stdout.write('Synchronisation des livres...')
        self.sync_books()
        
        self.stdout.write('Synchronisation des auteurs...')
        self.sync_authors()
        
        self.stdout.write('Synchronisation des catégories...')
        self.sync_categories()
    
    def sync_books(self):
        """
        Synchronise les livres depuis catalog_service.
        """
        try:
            catalog_client = service_clients.get_client('catalog')
            
            # Récupérer la liste des livres
            response = catalog_client.get('books/', params={'limit': self.limit})
            books = response.get('results', [])
            
            count = 0
            for book_data in books:
                if self.dry_run:
                    self.stdout.write(f'  [DRY-RUN] Sync book: {book_data.get("title", "N/A")}')
                else:
                    reference_manager.create_book_reference({
                        'uuid': book_data['id'],
                        'title': book_data.get('title', ''),
                        'slug': book_data.get('slug', ''),
                        'isbn': book_data.get('isbn', ''),
                        'is_active': book_data.get('is_active', True),
                    })
                count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'  {count} livres synchronisés')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  Erreur lors de la synchronisation des livres: {e}')
            )
    
    def sync_authors(self):
        """
        Synchronise les auteurs depuis catalog_service.
        """
        try:
            catalog_client = service_clients.get_client('catalog')
            
            # Récupérer la liste des auteurs
            response = catalog_client.get('authors/', params={'limit': self.limit})
            authors = response.get('results', [])
            
            count = 0
            for author_data in authors:
                if self.dry_run:
                    self.stdout.write(f'  [DRY-RUN] Sync author: {author_data.get("name", "N/A")}')
                else:
                    reference_manager.create_author_reference({
                        'uuid': author_data['id'],
                        'name': author_data.get('name', ''),
                        'slug': author_data.get('slug', ''),
                        'is_active': author_data.get('is_active', True),
                    })
                count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'  {count} auteurs synchronisés')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  Erreur lors de la synchronisation des auteurs: {e}')
            )
    
    def sync_categories(self):
        """
        Synchronise les catégories depuis catalog_service.
        """
        try:
            catalog_client = service_clients.get_client('catalog')
            
            # Récupérer la liste des catégories
            response = catalog_client.get('categories/', params={'limit': self.limit})
            categories = response.get('results', [])
            
            count = 0
            for category_data in categories:
                if self.dry_run:
                    self.stdout.write(f'  [DRY-RUN] Sync category: {category_data.get("name", "N/A")}')
                else:
                    reference_manager.create_category_reference({
                        'uuid': category_data['id'],
                        'name': category_data.get('name', ''),
                        'slug': category_data.get('slug', ''),
                        'parent_uuid': category_data.get('parent_id'),
                        'is_active': category_data.get('is_active', True),
                    })
                count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'  {count} catégories synchronisées')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  Erreur lors de la synchronisation des catégories: {e}')
            )
    
    def sync_auth_service(self):
        """
        Synchronise les données du service auth.
        """
        self.stdout.write('Synchronisation des utilisateurs...')
        self.sync_users()
    
    def sync_users(self):
        """
        Synchronise les utilisateurs depuis auth_service.
        """
        try:
            auth_client = service_clients.get_client('auth')
            
            # Récupérer la liste des utilisateurs
            response = auth_client.get('users/', params={'limit': self.limit})
            users = response.get('results', [])
            
            count = 0
            for user_data in users:
                if self.dry_run:
                    self.stdout.write(f'  [DRY-RUN] Sync user: {user_data.get("username", "N/A")}')
                else:
                    reference_manager.create_user_reference({
                        'uuid': user_data['id'],
                        'username': user_data.get('username', ''),
                        'display_name': user_data.get('display_name', ''),
                        'is_active': user_data.get('is_active', True),
                    })
                count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'  {count} utilisateurs synchronisés')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  Erreur lors de la synchronisation des utilisateurs: {e}')
            )
    
    def sync_pending_events(self):
        """
        Traite les événements en attente.
        """
        self.stdout.write('Traitement des événements en attente...')
        
        if self.dry_run:
            from shared_models.models import CrossServiceEvent
            
            pending_events = CrossServiceEvent.objects.filter(
                status='pending'
            )[:self.limit]
            
            self.stdout.write(f'  [DRY-RUN] {pending_events.count()} événements en attente')
            
            for event in pending_events:
                self.stdout.write(
                    f'    [DRY-RUN] Process event: {event.event_type} from {event.source_service}'
                )
        else:
            # Traiter les événements réels
            service_communication.process_pending_syncs(limit=self.limit)
            
            self.stdout.write(
                self.style.SUCCESS('Événements en attente traités')
            )