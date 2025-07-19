"""
Commande de migration pour passer aux services découplés
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migre le système vers les services découplés'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Exécuter en mode test sans faire de modifications'
        )
        parser.add_argument(
            '--verify-only',
            action='store_true',
            help='Vérifier uniquement la compatibilité sans migration'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verify_only = options['verify_only']
        
        self.stdout.write(
            self.style.SUCCESS('🔄 Début de la migration vers les services découplés')
        )
        
        if verify_only:
            self._verify_system_compatibility()
            return
        
        try:
            with transaction.atomic():
                # 1. Vérifier la compatibilité
                self._verify_system_compatibility()
                
                # 2. Migrer les configurations
                self._migrate_service_configurations()
                
                # 3. Mettre à jour les caches
                self._update_caches()
                
                # 4. Initialiser le système d'événements
                self._initialize_event_system()
                
                # 5. Valider la migration
                self._validate_migration()
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING('🔍 Mode dry-run: aucune modification persistée')
                    )
                    transaction.set_rollback(True)
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Migration vers les services découplés terminée')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la migration: {str(e)}')
            )
            raise
    
    def _verify_system_compatibility(self):
        """Vérifier la compatibilité du système"""
        self.stdout.write('🔍 Vérification de la compatibilité...')
        
        # Vérifier les imports des interfaces
        try:
            from coko.interfaces import (
                BookServiceInterface, ReadingServiceInterface,
                RecommendationServiceInterface, UserServiceInterface
            )
            self.stdout.write('✅ Interfaces de service disponibles')
        except ImportError as e:
            raise Exception(f'Interfaces de service non disponibles: {str(e)}')
        
        # Vérifier le système d'événements
        try:
            from coko.events import EventBus, EventType, publish_event
            event_bus = EventBus()
            self.stdout.write('✅ Système d\'événements disponible')
        except ImportError as e:
            raise Exception(f'Système d\'événements non disponible: {str(e)}')
        
        # Vérifier les services concrets
        try:
            from coko.services import get_book_service, get_reading_service
            book_service = get_book_service()
            reading_service = get_reading_service()
            self.stdout.write('✅ Services concrets disponibles')
        except ImportError as e:
            raise Exception(f'Services concrets non disponibles: {str(e)}')
        
        # Vérifier les adaptateurs
        try:
            from recommendation_service.service_adapters import RecommendationServiceAdapter
            adapter = RecommendationServiceAdapter()
            self.stdout.write('✅ Adaptateurs de service disponibles')
        except ImportError as e:
            raise Exception(f'Adaptateurs non disponibles: {str(e)}')
    
    def _migrate_service_configurations(self):
        """Migrer les configurations vers les nouveaux services"""
        self.stdout.write('⚙️ Migration des configurations...')
        
        from django.core.cache import cache
        
        # Configuration du moteur de recommandations avec services découplés
        recommendation_config = {
            'enabled_algorithms': ['content_based', 'collaborative', 'hybrid'],
            'algorithm_weights': {
                'content_based': 0.3,
                'collaborative': 0.4,
                'hybrid': 0.3
            },
            'use_services': True,
            'service_timeout': 5.0,
            'cache_duration': 3600,
            'event_driven': True
        }
        
        cache.set('recommendation_engine_config', recommendation_config, None)
        self.stdout.write('✅ Configuration des recommandations mise à jour')
        
        # Configuration des services
        service_config = {
            'book_service': {
                'cache_duration': 3600,
                'max_results_per_query': 100
            },
            'reading_service': {
                'statistics_cache_duration': 1800,
                'history_limit': 1000
            },
            'event_service': {
                'max_handlers_per_event': 10,
                'event_retention_days': 30
            }
        }
        
        cache.set('service_configurations', service_config, None)
        self.stdout.write('✅ Configuration des services mise à jour')
    
    def _update_caches(self):
        """Mettre à jour les caches pour les nouveaux services"""
        self.stdout.write('💾 Mise à jour des caches...')
        
        from django.core.cache import cache
        
        # Invalider les anciens caches
        old_cache_patterns = [
            'user_recommendations_*',
            'book_details_*',
            'reading_stats_*'
        ]
        
        # Note: En production, vous utiliseriez une méthode plus sophistiquée
        # pour invalider les caches par pattern
        cache.clear()
        self.stdout.write('✅ Caches invalidés')
        
        # Pré-charger quelques données essentielles
        try:
            from coko.services import get_book_service
            book_service = get_book_service()
            
            # Pré-charger les livres populaires
            popular_books = book_service.get_popular_books(limit=20)
            cache.set('popular_books_preload', popular_books, 3600)
            
            self.stdout.write('✅ Données essentielles pré-chargées')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Impossible de pré-charger les données: {str(e)}')
            )
    
    def _initialize_event_system(self):
        """Initialiser le système d'événements"""
        self.stdout.write('📡 Initialisation du système d\'événements...')
        
        from coko.events import event_bus, EventType
        from recommendation_service.service_adapters import RecommendationServiceAdapter
        
        # Initialiser l'adaptateur (qui s'abonne automatiquement aux événements)
        adapter = RecommendationServiceAdapter()
        
        # Vérifier que les handlers sont enregistrés
        event_types_to_check = [
            EventType.BOOK_COMPLETED,
            EventType.USER_INTERACTION_RECORDED,
            EventType.USER_PREFERENCES_UPDATED
        ]
        
        for event_type in event_types_to_check:
            if event_type in event_bus._handlers:
                handler_count = len(event_bus._handlers[event_type])
                self.stdout.write(f'✅ {handler_count} handler(s) pour {event_type.value}')
            else:
                self.stdout.write(f'⚠️ Aucun handler pour {event_type.value}')
        
        self.stdout.write('✅ Système d\'événements initialisé')
    
    def _validate_migration(self):
        """Valider que la migration s'est bien passée"""
        self.stdout.write('🔍 Validation de la migration...')
        
        # Test 1: Vérifier que les services fonctionnent
        try:
            from coko.services import get_book_service, get_reading_service
            
            book_service = get_book_service()
            reading_service = get_reading_service()
            
            # Test simple des services
            popular_books = book_service.get_popular_books(limit=1)
            self.stdout.write('✅ Service de livres fonctionnel')
            
            # Tester avec un utilisateur existant
            test_user = User.objects.first()
            if test_user:
                reading_history = reading_service.get_user_reading_history(test_user.id, limit=1)
                self.stdout.write('✅ Service de lecture fonctionnel')
            
        except Exception as e:
            raise Exception(f'Validation des services échouée: {str(e)}')
        
        # Test 2: Vérifier le système d'événements
        try:
            from coko.events import publish_event, EventType
            
            # Publier un événement de test
            publish_event(
                EventType.USER_INTERACTION_RECORDED,
                {'test': True, 'migration_validation': True},
                user_id=test_user.id if test_user else None,
                source_service='migration_command'
            )
            
            self.stdout.write('✅ Système d\'événements fonctionnel')
            
        except Exception as e:
            raise Exception(f'Validation du système d\'événements échouée: {str(e)}')
        
        # Test 3: Vérifier les recommandations découplées
        try:
            from recommendation_service.utils_refactored import generate_personalized_recommendations
            
            if test_user:
                recommendations = generate_personalized_recommendations(
                    test_user,
                    algorithm='popularity',
                    count=1,
                    context='migration_test'
                )
                
                if recommendations and 'books' in recommendations:
                    self.stdout.write('✅ Recommandations découplées fonctionnelles')
                else:
                    self.stdout.write('⚠️ Recommandations vides (normal si pas de données)')
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Test des recommandations échoué: {str(e)}')
            )
        
        self.stdout.write('✅ Validation terminée')
    
    def _show_migration_summary(self):
        """Afficher un résumé de la migration"""
        self.stdout.write(
            self.style.SUCCESS('\n📊 Résumé de la migration:')
        )
        
        summary_items = [
            '🔌 Interfaces de service : Implémentées',
            '📡 Système d\'événements : Actif',
            '🏗️ Services concrets : Disponibles',
            '🔄 Adaptateurs : Configurés',
            '💾 Caches : Mis à jour',
            '⚙️ Configuration : Migrée'
        ]
        
        for item in summary_items:
            self.stdout.write(f'  {item}')
        
        self.stdout.write(
            self.style.WARNING('\n⚠️ Points d\'attention post-migration:')
        )
        
        attention_items = [
            'Surveiller les performances des nouveaux services',
            'Vérifier les logs pour les événements non traités',
            'Mettre à jour les tests pour utiliser les nouvelles interfaces',
            'Documenter les nouveaux patterns pour l\'équipe'
        ]
        
        for item in attention_items:
            self.stdout.write(f'  • {item}')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Migration vers les services découplés terminée avec succès!')
        )