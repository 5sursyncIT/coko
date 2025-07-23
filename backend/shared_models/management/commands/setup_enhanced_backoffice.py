"""
Commande Django pour configurer le back-office amélioré
Initialise les données nécessaires et configure les permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import json

from shared_models.financial_reports import PaymentTransaction
from shared_models.audit_trail import AuditLog, SecurityAlert
from auth_service.models import Role, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Configure le back-office amélioré avec dashboard unifié et nouvelles fonctionnalités'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Créer des données d\'exemple pour démonstration',
        )
        parser.add_argument(
            '--setup-permissions',
            action='store_true',
            help='Configurer les permissions et groupes',
        )
        parser.add_argument(
            '--create-demo-transactions',
            action='store_true',
            help='Créer des transactions de démonstration',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Configuration du back-office amélioré COKO'))
        
        with transaction.atomic():
            if options['setup_permissions']:
                self.setup_permissions()
            
            if options['create_sample_data']:
                self.create_sample_data()
            
            if options['create_demo_transactions']:
                self.create_demo_transactions()
        
        self.stdout.write(self.style.SUCCESS('✅ Configuration terminée avec succès!'))
        self.print_access_info()
    
    def setup_permissions(self):
        """Configure les permissions et groupes pour le back-office"""
        self.stdout.write('📋 Configuration des permissions...')
        
        # Créer les groupes
        groups_config = {
            'Dashboard Managers': [
                'view_auditlog', 'view_securityalert', 'view_paymenttransaction',
                'change_securityalert'
            ],
            'Financial Analysts': [
                'view_paymenttransaction', 'view_auditlog', 'export_financial_data'
            ],
            'Security Officers': [
                'view_auditlog', 'view_securityalert', 'change_securityalert',
                'add_securityalert', 'delete_securityalert'
            ],
            'Authors': [
                'export_author_data', 'view_own_books', 'view_own_analytics'
            ],
            'Publishers': [
                'export_publisher_data', 'view_catalog_data', 'view_author_performance'
            ],
            'African Operations': [
                'view_african_metrics', 'view_payment_providers', 'monitor_performance'
            ]
        }
        
        for group_name, permission_codenames in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'  ✓ Groupe créé: {group_name}')
            
            # Ajouter les permissions (certaines peuvent ne pas exister encore)
            for codename in permission_codenames:
                try:
                    permission = Permission.objects.get(codename=codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Permission non trouvée: {codename}')
                    )
        
        # Créer des rôles spécialisés
        specialized_roles = [
            {
                'name': 'dashboard_manager',
                'description': 'Gestionnaire du dashboard unifié',
                'permissions': ['view_dashboard', 'export_metrics', 'monitor_services']
            },
            {
                'name': 'african_operations',
                'description': 'Responsable des opérations africaines',
                'permissions': ['manage_african_features', 'view_payment_providers', 'optimize_network']
            },
            {
                'name': 'security_analyst',
                'description': 'Analyste sécurité',
                'permissions': ['manage_audit_logs', 'handle_security_alerts', 'investigate_incidents']
            }
        ]
        
        for role_data in specialized_roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'permissions': role_data['permissions']
                }
            )
            if created:
                self.stdout.write(f'  ✓ Rôle créé: {role_data["name"]}')
    
    def create_sample_data(self):
        """Crée des données d'exemple pour démonstration"""
        self.stdout.write('📊 Création de données d\'exemple...')
        
        # Créer quelques utilisateurs de test
        test_users = [
            {
                'username': 'author_demo',
                'email': 'author@coko.africa',
                'first_name': 'Amadou',
                'last_name': 'Diallo',
                'country': 'SN',
                'subscription_type': 'creator'
            },
            {
                'username': 'publisher_demo',
                'email': 'publisher@coko.africa',
                'first_name': 'Fatima',
                'last_name': 'Koné',
                'country': 'CI',
                'subscription_type': 'institutional'
            },
            {
                'username': 'reader_demo',
                'email': 'reader@coko.africa',
                'first_name': 'Ibrahim',
                'last_name': 'Traoré',
                'country': 'ML',
                'subscription_type': 'premium'
            }
        ]
        
        for user_data in test_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password('demo123')
                user.save()
                self.stdout.write(f'  ✓ Utilisateur créé: {user_data["username"]}')
                
                # Assigner des rôles
                if 'author' in user_data['username']:
                    author_role, _ = Role.objects.get_or_create(name='author')
                    UserRole.objects.get_or_create(user=user, role=author_role)
                elif 'publisher' in user_data['username']:
                    publisher_role, _ = Role.objects.get_or_create(name='publisher')
                    UserRole.objects.get_or_create(user=user, role=publisher_role)
        
        # Créer des logs d'audit d'exemple
        self.create_sample_audit_logs()
        
        # Créer des alertes de sécurité d'exemple
        self.create_sample_security_alerts()
    
    def create_sample_audit_logs(self):
        """Crée des logs d'audit d'exemple"""
        sample_logs = [
            {
                'action_type': 'LOGIN',
                'service': 'auth_service',
                'description': 'Connexion utilisateur depuis mobile',
                'risk_level': 'LOW',
                'ip_address': '196.168.1.100',
                'country': 'SN',
                'device_type': 'mobile',
                'success': True
            },
            {
                'action_type': 'BOOK_PUBLISH',
                'service': 'catalog_service',
                'description': 'Publication d\'un nouveau livre',
                'risk_level': 'LOW',
                'ip_address': '196.168.1.101',
                'country': 'CI',
                'device_type': 'desktop',
                'success': True
            },
            {
                'action_type': 'PAYMENT_SUCCESS',
                'service': 'payment_service',
                'description': 'Paiement Orange Money réussi',
                'risk_level': 'LOW',
                'ip_address': '196.168.1.102',
                'country': 'ML',
                'device_type': 'mobile',
                'success': True
            },
            {
                'action_type': 'LOGIN_FAILED',
                'service': 'auth_service',
                'description': 'Tentative de connexion échouée - mot de passe incorrect',
                'risk_level': 'MEDIUM',
                'ip_address': '185.220.101.42',  # IP suspecte
                'country': 'OTHER',
                'device_type': 'desktop',
                'success': False
            },
            {
                'action_type': 'ADMIN_ACCESS',
                'service': 'admin_service',
                'description': 'Accès à l\'interface d\'administration',
                'risk_level': 'MEDIUM',
                'ip_address': '196.168.1.103',
                'country': 'SN',
                'device_type': 'desktop',
                'success': True
            }
        ]
        
        for i, log_data in enumerate(sample_logs):
            # Décaler les timestamps pour avoir une progression
            timestamp = timezone.now() - timedelta(hours=24-i*4)
            
            AuditLog.objects.create(
                **log_data,
                timestamp=timestamp
            )
        
        self.stdout.write('  ✓ Logs d\'audit créés')
    
    def create_sample_security_alerts(self):
        """Crée des alertes de sécurité d'exemple"""
        sample_alerts = [
            {
                'alert_type': 'SUSPICIOUS_IP',
                'severity': 'WARNING',
                'status': 'OPEN',
                'title': 'Activité suspecte détectée',
                'description': 'IP 185.220.101.42 avec multiples tentatives de connexion échouées',
                'ip_address': '185.220.101.42',
                'risk_score': 75
            },
            {
                'alert_type': 'UNUSUAL_ACTIVITY',
                'severity': 'INFO',
                'status': 'RESOLVED',
                'title': 'Accès hors heures normales',
                'description': 'Accès administrateur à 3h du matin',
                'risk_score': 45
            }
        ]
        
        for alert_data in sample_alerts:
            SecurityAlert.objects.create(**alert_data)
        
        self.stdout.write('  ✓ Alertes de sécurité créées')
    
    def create_demo_transactions(self):
        """Crée des transactions de démonstration"""
        self.stdout.write('💳 Création de transactions de démonstration...')
        
        # Récupérer quelques utilisateurs
        users = User.objects.all()[:3]
        
        if not users:
            self.stdout.write(
                self.style.WARNING('  ⚠ Aucun utilisateur trouvé, créez d\'abord des utilisateurs')
            )
            return
        
        demo_transactions = [
            {
                'amount': 2000.00,
                'currency': 'XOF',
                'transaction_type': 'subscription',
                'status': 'completed',
                'payment_provider': 'orange_money',
                'phone_number': '+221701234567',
                'country_code': 'SN',
                'fees': 40.00,
                'net_amount': 1960.00,
                'metadata': {'subscription_plan': 'premium', 'duration': '1_month'}
            },
            {
                'amount': 500.00,
                'currency': 'XOF',
                'transaction_type': 'book_purchase',
                'status': 'completed',
                'payment_provider': 'wave',
                'phone_number': '+225701234567',
                'country_code': 'CI',
                'fees': 5.00,
                'net_amount': 495.00,
                'metadata': {'book_id': 'demo-book-1', 'title': 'Histoire du Sahel'}
            },
            {
                'amount': 1000.00,
                'currency': 'XOF',
                'transaction_type': 'tip',
                'status': 'processing',
                'payment_provider': 'mtn_momo',
                'phone_number': '+223701234567',
                'country_code': 'ML',
                'fees': 25.00,
                'net_amount': 975.00,
                'metadata': {'author_id': 'demo-author-1', 'book_id': 'demo-book-2'}
            },
            {
                'amount': 1500.00,
                'currency': 'XOF',
                'transaction_type': 'subscription',
                'status': 'failed',
                'payment_provider': 'orange_money',
                'phone_number': '+226701234567',
                'country_code': 'BF',
                'fees': 0.00,
                'net_amount': 0.00,
                'metadata': {'error_code': 'INSUFFICIENT_FUNDS', 'retry_count': 2}
            }
        ]
        
        for i, transaction_data in enumerate(demo_transactions):
            # Assigner à un utilisateur différent
            user = users[i % len(users)]
            
            # Décaler les dates
            created_at = timezone.now() - timedelta(days=i+1)
            
            transaction = PaymentTransaction.objects.create(
                user=user,
                created_at=created_at,
                **transaction_data
            )
            
            # Marquer comme terminée si c'est le statut
            if transaction.status == 'completed':
                transaction.completed_at = created_at + timedelta(minutes=2)
                transaction.save()
        
        self.stdout.write('  ✓ Transactions de démonstration créées')
    
    def print_access_info(self):
        """Affiche les informations d'accès"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎉 BACK-OFFICE AMÉLIORÉ CONFIGURÉ'))
        self.stdout.write('='*60)
        
        self.stdout.write('\n📱 Nouvelles fonctionnalités disponibles:')
        self.stdout.write('  • Dashboard unifié: /admin/dashboard/')
        self.stdout.write('  • Métriques africaines: /admin/dashboard/african-metrics/')
        self.stdout.write('  • Rapports financiers: /admin/dashboard/financial-reports/')
        self.stdout.write('  • Audit & sécurité: /admin/dashboard/security-overview/')
        
        self.stdout.write('\n🔗 APIs d\'export:')
        self.stdout.write('  • Auteurs: /api/export/author/*')
        self.stdout.write('  • Éditeurs: /api/export/publisher/*')
        self.stdout.write('  • Package complet: /api/export/complete-package/')
        
        self.stdout.write('\n👥 Groupes créés:')
        groups = Group.objects.all()
        for group in groups:
            self.stdout.write(f'  • {group.name}')
        
        self.stdout.write('\n🔐 Utilisateurs de démonstration:')
        demo_users = User.objects.filter(username__contains='demo')
        for user in demo_users:
            self.stdout.write(f'  • {user.username} ({user.email}) - mot de passe: demo123')
        
        self.stdout.write('\n📊 Données créées:')
        self.stdout.write(f'  • {AuditLog.objects.count()} logs d\'audit')
        self.stdout.write(f'  • {SecurityAlert.objects.count()} alertes de sécurité')
        self.stdout.write(f'  • {PaymentTransaction.objects.count()} transactions')
        
        self.stdout.write('\n🚀 Prochaines étapes:')
        self.stdout.write('  1. Connectez-vous à /admin/')
        self.stdout.write('  2. Explorez le dashboard unifié')
        self.stdout.write('  3. Testez les APIs d\'export')
        self.stdout.write('  4. Configurez les alertes temps réel')
        
        self.stdout.write('\n' + '='*60)