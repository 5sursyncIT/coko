"""Commande Django pour gérer le système de facturation Coko"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import json

from shared_models.billing import (
    Invoice, AuthorRoyalty, RecurringBilling, BillingConfiguration
)
from shared_models.billing_services import (
    InvoiceService, RoyaltyService, RecurringBillingService,
    BillingAutomationService
)
from shared_models.billing_settings import (
    get_billing_config, validate_billing_config, init_billing_config
)


class Command(BaseCommand):
    help = 'Gère le système de facturation Coko'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=[
                'status', 'init', 'validate', 'process_daily', 'process_monthly',
                'calculate_royalties', 'process_recurring', 'send_overdue',
                'generate_reports', 'cleanup', 'stats', 'test_invoice',
                'test_royalty', 'reset_config'
            ],
            help='Action à exécuter'
        )
        
        parser.add_argument(
            '--author-id',
            type=int,
            help='ID de l\'auteur pour les actions spécifiques'
        )
        
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID de l\'utilisateur pour les actions spécifiques'
        )
        
        parser.add_argument(
            '--invoice-id',
            type=str,
            help='ID de la facture pour les actions spécifiques'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours pour certaines actions (défaut: 30)'
        )
        
        parser.add_argument(
            '--amount',
            type=float,
            help='Montant pour les tests'
        )
        
        parser.add_argument(
            '--currency',
            type=str,
            default='EUR',
            help='Devise pour les tests (défaut: EUR)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans modification des données'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force l\'exécution même en cas d\'avertissements'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'status':
                self.show_status(options)
            elif action == 'init':
                self.initialize_system(options)
            elif action == 'validate':
                self.validate_system(options)
            elif action == 'process_daily':
                self.process_daily_billing(options)
            elif action == 'process_monthly':
                self.process_monthly_billing(options)
            elif action == 'calculate_royalties':
                self.calculate_royalties(options)
            elif action == 'process_recurring':
                self.process_recurring_billing(options)
            elif action == 'send_overdue':
                self.send_overdue_notifications(options)
            elif action == 'generate_reports':
                self.generate_reports(options)
            elif action == 'cleanup':
                self.cleanup_old_data(options)
            elif action == 'stats':
                self.show_statistics(options)
            elif action == 'test_invoice':
                self.test_invoice_creation(options)
            elif action == 'test_royalty':
                self.test_royalty_calculation(options)
            elif action == 'reset_config':
                self.reset_configuration(options)
                
        except Exception as e:
            raise CommandError(f'Erreur lors de l\'exécution: {str(e)}')
    
    def show_status(self, options):
        """Affiche le statut du système de facturation"""
        self.stdout.write(self.style.HTTP_INFO('=== STATUT DU SYSTÈME DE FACTURATION ==='))
        
        # Vérifier la configuration
        errors = validate_billing_config()
        if errors:
            self.stdout.write(self.style.ERROR('❌ Configuration invalide:'))
            for error in errors:
                self.stdout.write(f'  - {error}')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Configuration valide'))
        
        # Statistiques des modèles
        try:
            invoice_count = Invoice.objects.count()
            royalty_count = AuthorRoyalty.objects.count()
            recurring_count = RecurringBilling.objects.count()
            config_count = BillingConfiguration.objects.count()
            
            self.stdout.write('\n📊 Statistiques:')
            self.stdout.write(f'  - Factures: {invoice_count}')
            self.stdout.write(f'  - Royalties: {royalty_count}')
            self.stdout.write(f'  - Abonnements récurrents: {recurring_count}')
            self.stdout.write(f'  - Configurations: {config_count}')
            
            # Factures en attente
            pending_invoices = Invoice.objects.filter(status__in=['pending', 'sent']).count()
            overdue_invoices = Invoice.objects.filter(status='overdue').count()
            
            if pending_invoices > 0:
                self.stdout.write(f'  - Factures en attente: {pending_invoices}')
            if overdue_invoices > 0:
                self.stdout.write(self.style.WARNING(f'  - Factures en retard: {overdue_invoices}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors de la récupération des statistiques: {str(e)}'))
    
    def initialize_system(self, options):
        """Initialise le système de facturation"""
        self.stdout.write(self.style.HTTP_INFO('=== INITIALISATION DU SYSTÈME ==='))
        
        if not options.get('force'):
            confirm = input('Voulez-vous vraiment initialiser le système? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Initialisation annulée.')
                return
        
        try:
            with transaction.atomic():
                # Initialiser la configuration
                init_billing_config()
                
                # Créer les configurations par défaut
                default_configs = [
                    {
                        'config_type': 'tax_rate',
                        'config_key': 'default_rate',
                        'config_value': {'rate': 0.20},
                        'description': 'Taux de taxe par défaut (20%)'
                    },
                    {
                        'config_type': 'royalty_rate',
                        'config_key': 'sale_rate',
                        'config_value': {'rate': 0.70},
                        'description': 'Taux de royalty pour les ventes (70%)'
                    },
                    {
                        'config_type': 'royalty_rate',
                        'config_key': 'subscription_rate',
                        'config_value': {'rate': 0.50},
                        'description': 'Taux de royalty pour les lectures d\'abonnement (50%)'
                    },
                    {
                        'config_type': 'payment_terms',
                        'config_key': 'default_due_days',
                        'config_value': {'days': 30},
                        'description': 'Délai de paiement par défaut (30 jours)'
                    },
                    {
                        'config_type': 'currency',
                        'config_key': 'default_currency',
                        'config_value': {'currency': 'EUR'},
                        'description': 'Devise par défaut'
                    }
                ]
                
                created_count = 0
                for config_data in default_configs:
                    config, created = BillingConfiguration.objects.get_or_create(
                        config_type=config_data['config_type'],
                        config_key=config_data['config_key'],
                        defaults={
                            'config_value': config_data['config_value'],
                            'description': config_data['description'],
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
                        if options.get('verbose'):
                            self.stdout.write(f'  ✅ Configuration créée: {config_data["description"]}')
                
                self.stdout.write(self.style.SUCCESS(f'✅ Système initialisé avec succès!'))
                self.stdout.write(f'📝 {created_count} nouvelles configurations créées.')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors de l\'initialisation: {str(e)}'))
    
    def validate_system(self, options):
        """Valide la configuration du système"""
        self.stdout.write(self.style.HTTP_INFO('=== VALIDATION DU SYSTÈME ==='))
        
        errors = validate_billing_config()
        if errors:
            self.stdout.write(self.style.ERROR('❌ Erreurs de configuration trouvées:'))
            for error in errors:
                self.stdout.write(f'  - {error}')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Configuration valide'))
        
        # Vérifier les dépendances
        try:
            import celery
            self.stdout.write('✅ Celery disponible')
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠️  Celery non disponible - tâches automatisées désactivées'))
        
        try:
            import reportlab
            self.stdout.write('✅ ReportLab disponible pour la génération PDF')
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠️  ReportLab non disponible - génération PDF désactivée'))
    
    def process_daily_billing(self, options):
        """Traite la facturation quotidienne"""
        self.stdout.write(self.style.HTTP_INFO('=== TRAITEMENT QUOTIDIEN ==='))
        
        if options.get('dry_run'):
            self.stdout.write(self.style.WARNING('🔍 Mode simulation activé'))
        
        try:
            automation_service = BillingAutomationService()
            
            if options.get('dry_run'):
                # Simulation
                pending_invoices = Invoice.objects.filter(status='pending').count()
                overdue_invoices = Invoice.objects.filter(
                    status='sent',
                    due_date__lt=timezone.now().date()
                ).count()
                
                self.stdout.write(f'📊 Simulation:')
                self.stdout.write(f'  - Factures à traiter: {pending_invoices}')
                self.stdout.write(f'  - Factures à marquer en retard: {overdue_invoices}')
            else:
                result = automation_service.run_daily_billing()
                
                self.stdout.write(f'✅ Traitement terminé:')
                self.stdout.write(f'  - Factures traitées: {result.get("invoices_processed", 0)}')
                self.stdout.write(f'  - Notifications envoyées: {result.get("notifications_sent", 0)}')
                self.stdout.write(f'  - Erreurs: {result.get("errors", 0)}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur: {str(e)}'))
    
    def process_monthly_billing(self, options):
        """Traite la facturation mensuelle"""
        self.stdout.write(self.style.HTTP_INFO('=== TRAITEMENT MENSUEL ==='))
        
        if options.get('dry_run'):
            self.stdout.write(self.style.WARNING('🔍 Mode simulation activé'))
        
        try:
            automation_service = BillingAutomationService()
            
            if options.get('dry_run'):
                # Simulation
                from auth_service.models import User
                authors_count = User.objects.filter(is_author=True).count()
                
                self.stdout.write(f'📊 Simulation:')
                self.stdout.write(f'  - Auteurs à traiter: {authors_count}')
            else:
                result = automation_service.run_monthly_billing()
                
                self.stdout.write(f'✅ Traitement terminé:')
                self.stdout.write(f'  - Royalties calculées: {result.get("royalties_calculated", 0)}')
                self.stdout.write(f'  - Rapports générés: {result.get("reports_generated", 0)}')
                self.stdout.write(f'  - Erreurs: {result.get("errors", 0)}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur: {str(e)}'))
    
    def calculate_royalties(self, options):
        """Calcule les royalties pour un auteur ou tous les auteurs"""
        author_id = options.get('author_id')
        
        if author_id:
            self.stdout.write(f'=== CALCUL ROYALTIES AUTEUR {author_id} ===')
        else:
            self.stdout.write('=== CALCUL ROYALTIES TOUS AUTEURS ===')
        
        try:
            royalty_service = RoyaltyService()
            
            if author_id:
                from auth_service.models import User
                author = User.objects.get(id=author_id, is_author=True)
                
                if options.get('dry_run'):
                    # Simulation pour un auteur
                    self.stdout.write(f'📊 Simulation pour {author.username}')
                else:
                    royalty = royalty_service.calculate_author_royalty(author)
                    if royalty:
                        self.stdout.write(f'✅ Royalty calculée: {royalty.royalty_amount} {royalty.currency}')
                    else:
                        self.stdout.write('ℹ️  Aucune royalty à calculer pour cette période')
            else:
                if options.get('dry_run'):
                    from auth_service.models import User
                    authors_count = User.objects.filter(is_author=True).count()
                    self.stdout.write(f'📊 Simulation pour {authors_count} auteurs')
                else:
                    results = royalty_service.calculate_all_royalties()
                    self.stdout.write(f'✅ {len(results)} royalties calculées')
                    
                    total_amount = sum(r.royalty_amount for r in results)
                    self.stdout.write(f'💰 Montant total: {total_amount} EUR')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur: {str(e)}'))
    
    def show_statistics(self, options):
        """Affiche les statistiques détaillées"""
        self.stdout.write(self.style.HTTP_INFO('=== STATISTIQUES DÉTAILLÉES ==='))
        
        try:
            from django.db.models import Sum, Count, Q
            
            # Période
            days = options.get('days', 30)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            self.stdout.write(f'📅 Période: {start_date.strftime("%Y-%m-%d")} - {end_date.strftime("%Y-%m-%d")}')
            
            # Statistiques des factures
            invoice_stats = Invoice.objects.aggregate(
                total_count=Count('id'),
                total_amount=Sum('total_amount'),
                paid_count=Count('id', filter=Q(status='paid')),
                paid_amount=Sum('total_amount', filter=Q(status='paid')),
                pending_count=Count('id', filter=Q(status__in=['pending', 'sent'])),
                overdue_count=Count('id', filter=Q(status='overdue')),
                recent_count=Count('id', filter=Q(created_at__gte=start_date))
            )
            
            self.stdout.write('\n💰 FACTURES:')
            self.stdout.write(f'  - Total: {invoice_stats["total_count"]} ({invoice_stats["total_amount"] or 0:.2f} EUR)')
            self.stdout.write(f'  - Payées: {invoice_stats["paid_count"]} ({invoice_stats["paid_amount"] or 0:.2f} EUR)')
            self.stdout.write(f'  - En attente: {invoice_stats["pending_count"]}')
            self.stdout.write(f'  - En retard: {invoice_stats["overdue_count"]}')
            self.stdout.write(f'  - Récentes ({days}j): {invoice_stats["recent_count"]}')
            
            # Statistiques des royalties
            royalty_stats = AuthorRoyalty.objects.aggregate(
                total_count=Count('id'),
                total_amount=Sum('royalty_amount'),
                paid_count=Count('id', filter=Q(status='paid')),
                paid_amount=Sum('royalty_amount', filter=Q(status='paid')),
                pending_count=Count('id', filter=Q(status='pending')),
                recent_count=Count('id', filter=Q(created_at__gte=start_date))
            )
            
            self.stdout.write('\n👨‍💼 ROYALTIES:')
            self.stdout.write(f'  - Total: {royalty_stats["total_count"]} ({royalty_stats["total_amount"] or 0:.2f} EUR)')
            self.stdout.write(f'  - Payées: {royalty_stats["paid_count"]} ({royalty_stats["paid_amount"] or 0:.2f} EUR)')
            self.stdout.write(f'  - En attente: {royalty_stats["pending_count"]}')
            self.stdout.write(f'  - Récentes ({days}j): {royalty_stats["recent_count"]}')
            
            # Statistiques des abonnements récurrents
            recurring_stats = RecurringBilling.objects.aggregate(
                total_count=Count('id'),
                active_count=Count('id', filter=Q(status='active')),
                paused_count=Count('id', filter=Q(status='paused')),
                cancelled_count=Count('id', filter=Q(status='cancelled'))
            )
            
            self.stdout.write('\n🔄 ABONNEMENTS RÉCURRENTS:')
            self.stdout.write(f'  - Total: {recurring_stats["total_count"]}')
            self.stdout.write(f'  - Actifs: {recurring_stats["active_count"]}')
            self.stdout.write(f'  - En pause: {recurring_stats["paused_count"]}')
            self.stdout.write(f'  - Annulés: {recurring_stats["cancelled_count"]}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur: {str(e)}'))
    
    def test_invoice_creation(self, options):
        """Teste la création d'une facture"""
        self.stdout.write(self.style.HTTP_INFO('=== TEST CRÉATION FACTURE ==='))
        
        user_id = options.get('user_id')
        amount = options.get('amount', 100.0)
        currency = options.get('currency', 'EUR')
        
        if not user_id:
            self.stdout.write(self.style.ERROR('❌ --user-id requis pour le test'))
            return
        
        try:
            from auth_service.models import User
            user = User.objects.get(id=user_id)
            
            if options.get('dry_run'):
                self.stdout.write(f'📊 Simulation:')
                self.stdout.write(f'  - Utilisateur: {user.username}')
                self.stdout.write(f'  - Montant: {amount} {currency}')
            else:
                invoice_service = InvoiceService()
                
                # Créer des items de test
                items = [
                    {
                        'description': 'Test - Abonnement Premium',
                        'quantity': 1,
                        'unit_price': amount,
                        'item_type': 'subscription'
                    }
                ]
                
                invoice = invoice_service.create_invoice(
                    user=user,
                    items=items,
                    currency=currency
                )
                
                self.stdout.write(f'✅ Facture créée: {invoice.invoice_number}')
                self.stdout.write(f'  - Montant: {invoice.total_amount} {invoice.currency}')
                self.stdout.write(f'  - Statut: {invoice.status}')
                self.stdout.write(f'  - Échéance: {invoice.due_date}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur: {str(e)}'))
    
    def cleanup_old_data(self, options):
        """Nettoie les anciennes données"""
        days = options.get('days', 365)  # Par défaut, supprimer les données de plus d'un an
        
        self.stdout.write(f'=== NETTOYAGE DONNÉES > {days} JOURS ===')
        
        if not options.get('force'):
            confirm = input(f'Supprimer les données de plus de {days} jours? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Nettoyage annulé.')
                return
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            if options.get('dry_run'):
                # Simulation
                old_invoices = Invoice.objects.filter(
                    created_at__lt=cutoff_date,
                    status__in=['paid', 'cancelled']
                ).count()
                
                old_royalties = AuthorRoyalty.objects.filter(
                    created_at__lt=cutoff_date,
                    status='paid'
                ).count()
                
                self.stdout.write(f'📊 Simulation:')
                self.stdout.write(f'  - Factures à supprimer: {old_invoices}')
                self.stdout.write(f'  - Royalties à supprimer: {old_royalties}')
            else:
                # Suppression réelle
                deleted_invoices = Invoice.objects.filter(
                    created_at__lt=cutoff_date,
                    status__in=['paid', 'cancelled']
                ).delete()[0]
                
                deleted_royalties = AuthorRoyalty.objects.filter(
                    created_at__lt=cutoff_date,
                    status='paid'
                ).delete()[0]
                
                self.stdout.write(f'✅ Nettoyage terminé:')
                self.stdout.write(f'  - Factures supprimées: {deleted_invoices}')
                self.stdout.write(f'  - Royalties supprimées: {deleted_royalties}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur: {str(e)}'))