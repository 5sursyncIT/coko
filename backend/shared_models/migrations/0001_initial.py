# Generated migration for shared_models initial setup

from django.conf import settings
import django.contrib.contenttypes.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='XOF', max_length=3)),
                ('transaction_type', models.CharField(choices=[('subscription', 'Abonnement'), ('book_purchase', 'Achat de livre'), ('premium_upgrade', 'Mise à niveau premium'), ('refund', 'Remboursement'), ('tip', 'Pourboire auteur')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('processing', 'En cours'), ('completed', 'Terminée'), ('failed', 'Échouée'), ('cancelled', 'Annulée'), ('refunded', 'Remboursée')], default='pending', max_length=20)),
                ('payment_provider', models.CharField(choices=[('orange_money', 'Orange Money'), ('mtn_momo', 'MTN Mobile Money'), ('wave', 'Wave'), ('stripe', 'Stripe'), ('paypal', 'PayPal'), ('other', 'Autre')], max_length=20)),
                ('provider_transaction_id', models.CharField(blank=True, max_length=255)),
                ('provider_reference', models.CharField(blank=True, max_length=255)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('country_code', models.CharField(blank=True, max_length=5)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('fees', models.DecimalField(decimal_places=2, default=0.0, max_digits=8)),
                ('net_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'payment_transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action_type', models.CharField(choices=[('CREATE', 'Création'), ('UPDATE', 'Modification'), ('DELETE', 'Suppression'), ('VIEW', 'Consultation'), ('DOWNLOAD', 'Téléchargement'), ('EXPORT', 'Export'), ('LOGIN', 'Connexion'), ('LOGOUT', 'Déconnexion'), ('LOGIN_FAILED', 'Échec connexion'), ('PASSWORD_CHANGE', 'Changement mot de passe'), ('ACCOUNT_LOCK', 'Verrouillage compte'), ('BOOK_PUBLISH', 'Publication livre'), ('BOOK_UNPUBLISH', 'Dépublication livre'), ('CONTENT_MODERATE', 'Modération contenu'), ('REVIEW_SUBMIT', 'Soumission avis'), ('REVIEW_MODERATE', 'Modération avis'), ('READING_START', 'Début lecture'), ('READING_PAUSE', 'Pause lecture'), ('READING_FINISH', 'Fin lecture'), ('BOOKMARK_ADD', 'Ajout signet'), ('GOAL_CREATE', 'Création objectif'), ('RECOMMENDATION_GENERATE', 'Génération recommandations'), ('RECOMMENDATION_CLICK', 'Clic recommandation'), ('FEEDBACK_SUBMIT', 'Soumission feedback'), ('PAYMENT_INITIATE', 'Initiation paiement'), ('PAYMENT_SUCCESS', 'Paiement réussi'), ('PAYMENT_FAILURE', 'Échec paiement'), ('SUBSCRIPTION_CHANGE', 'Changement abonnement'), ('REFUND_PROCESS', 'Traitement remboursement'), ('ADMIN_ACCESS', 'Accès administration'), ('USER_ROLE_CHANGE', 'Changement rôle utilisateur'), ('PERMISSION_GRANT', 'Attribution permission'), ('PERMISSION_REVOKE', 'Révocation permission'), ('SYSTEM_CONFIG', 'Configuration système'), ('DATA_BACKUP', 'Sauvegarde données'), ('DATA_RESTORE', 'Restauration données'), ('SUSPICIOUS_ACTIVITY', 'Activité suspecte'), ('SECURITY_VIOLATION', 'Violation sécurité'), ('ACCESS_DENIED', 'Accès refusé'), ('API_RATE_LIMIT', 'Limite API atteinte'), ('MALICIOUS_REQUEST', 'Requête malveillante')], max_length=50)),
                ('service', models.CharField(choices=[('auth_service', "Service d'authentification"), ('catalog_service', 'Service de catalogue'), ('reading_service', 'Service de lecture'), ('recommendation_service', 'Service de recommandations'), ('payment_service', 'Service de paiement'), ('admin_service', "Service d'administration"), ('api_service', 'Service API'), ('system', 'Système')], max_length=30)),
                ('risk_level', models.CharField(choices=[('LOW', 'Faible'), ('MEDIUM', 'Moyen'), ('HIGH', 'Élevé'), ('CRITICAL', 'Critique')], default='LOW', max_length=10)),
                ('session_key', models.CharField(blank=True, max_length=40)),
                ('object_id', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField()),
                ('changes', models.JSONField(blank=True, default=dict)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('referer', models.URLField(blank=True)),
                ('request_method', models.CharField(blank=True, max_length=10)),
                ('request_url', models.TextField(blank=True)),
                ('country', models.CharField(blank=True, max_length=10)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('device_type', models.CharField(blank=True, max_length=20)),
                ('success', models.BooleanField(default=True)),
                ('error_message', models.TextField(blank=True)),
                ('impact_assessment', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('correlation_id', models.UUIDField(blank=True, null=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('parent_log', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='shared_models.auditlog')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'audit_logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='SecurityAlert',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('alert_type', models.CharField(choices=[('MULTIPLE_FAILED_LOGINS', 'Tentatives de connexion multiples'), ('SUSPICIOUS_IP', 'Adresse IP suspecte'), ('UNUSUAL_ACTIVITY', 'Activité inhabituelle'), ('PRIVILEGE_ESCALATION', 'Escalade de privilèges'), ('DATA_BREACH_ATTEMPT', 'Tentative de violation de données'), ('MALICIOUS_PATTERN', 'Motif malveillant détecté'), ('RATE_LIMIT_EXCEEDED', 'Limite de taux dépassée'), ('UNAUTHORIZED_ACCESS', 'Accès non autorisé')], max_length=50)),
                ('severity', models.CharField(choices=[('INFO', 'Information'), ('WARNING', 'Avertissement'), ('ERROR', 'Erreur'), ('CRITICAL', 'Critique')], max_length=10)),
                ('status', models.CharField(choices=[('OPEN', 'Ouvert'), ('INVESTIGATING', "En cours d'investigation"), ('RESOLVED', 'Résolu'), ('FALSE_POSITIVE', 'Faux positif')], default='OPEN', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('detection_rules', models.JSONField(default=list)),
                ('risk_score', models.IntegerField(default=0)),
                ('investigation_notes', models.TextField(blank=True)),
                ('resolution_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_alerts', to=settings.AUTH_USER_MODEL)),
                ('related_logs', models.ManyToManyField(related_name='security_alerts', to='shared_models.auditlog')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'security_alerts',
                'ordering': ['-created_at'],
            },
        ),
        # Index creation
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS audit_logs_user_timestamp_idx ON audit_logs (user_id, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS audit_logs_user_timestamp_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS audit_logs_service_action_idx ON audit_logs (service, action_type);",
            reverse_sql="DROP INDEX IF EXISTS audit_logs_service_action_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS audit_logs_risk_timestamp_idx ON audit_logs (risk_level, timestamp);",
            reverse_sql="DROP INDEX IF EXISTS audit_logs_risk_timestamp_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS payment_transactions_user_status_idx ON payment_transactions (user_id, status);",
            reverse_sql="DROP INDEX IF EXISTS payment_transactions_user_status_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS payment_transactions_provider_created_idx ON payment_transactions (payment_provider, created_at);",
            reverse_sql="DROP INDEX IF EXISTS payment_transactions_provider_created_idx;"
        ),
    ]