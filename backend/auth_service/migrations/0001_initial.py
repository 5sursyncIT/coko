# Generated by Django 4.2.7 on 2025-07-24 21:50

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="email address"
                    ),
                ),
                ("phone", models.CharField(blank=True, max_length=20, null=True)),
                (
                    "avatar",
                    models.ImageField(blank=True, null=True, upload_to="avatars/"),
                ),
                (
                    "country",
                    models.CharField(
                        choices=[
                            ("SN", "Sénégal"),
                            ("CI", "Côte d'Ivoire"),
                            ("ML", "Mali"),
                            ("BF", "Burkina Faso"),
                            ("MA", "Maroc"),
                            ("TN", "Tunisie"),
                            ("DZ", "Algérie"),
                            ("CM", "Cameroun"),
                            ("CD", "République Démocratique du Congo"),
                            ("FR", "France"),
                            ("CA", "Canada"),
                            ("OTHER", "Autre"),
                        ],
                        default="SN",
                        max_length=10,
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("fr", "Français"),
                            ("en", "English"),
                            ("wo", "Wolof"),
                            ("bm", "Bambara"),
                            ("ln", "Lingala"),
                        ],
                        default="fr",
                        max_length=5,
                    ),
                ),
                (
                    "subscription_type",
                    models.CharField(
                        choices=[
                            ("free", "Gratuit"),
                            ("premium", "Premium"),
                            ("creator", "Créateur"),
                            ("institutional", "Institutionnel"),
                        ],
                        default="free",
                        max_length=20,
                    ),
                ),
                (
                    "subscription_expires_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("is_verified", models.BooleanField(default=False)),
                (
                    "verification_token",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "reset_password_token",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("reset_password_expires", models.DateTimeField(blank=True, null=True)),
                ("last_login_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Utilisateur",
                "verbose_name_plural": "Utilisateurs",
                "db_table": "auth_users",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        choices=[
                            ("admin", "Administrateur"),
                            ("moderator", "Modérateur"),
                            ("author", "Auteur"),
                            ("publisher", "Éditeur"),
                            ("reader", "Lecteur"),
                        ],
                        max_length=50,
                        unique=True,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "permissions",
                    models.JSONField(
                        default=list, help_text="Liste des permissions accordées"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Rôle",
                "verbose_name_plural": "Rôles",
                "db_table": "auth_roles",
            },
        ),
        migrations.CreateModel(
            name="UserSession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("session_key", models.CharField(max_length=40, unique=True)),
                ("ip_address", models.GenericIPAddressField()),
                ("user_agent", models.TextField()),
                ("device_type", models.CharField(blank=True, max_length=20)),
                ("location", models.CharField(blank=True, max_length=100)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_activity", models.DateTimeField(auto_now=True)),
                ("expires_at", models.DateTimeField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Session utilisateur",
                "verbose_name_plural": "Sessions utilisateurs",
                "db_table": "auth_user_sessions",
                "ordering": ["-last_activity"],
            },
        ),
        migrations.CreateModel(
            name="UserPreferences",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "theme",
                    models.CharField(
                        choices=[
                            ("light", "Clair"),
                            ("dark", "Sombre"),
                            ("auto", "Automatique"),
                        ],
                        default="auto",
                        max_length=10,
                    ),
                ),
                (
                    "font_size",
                    models.CharField(
                        choices=[
                            ("small", "Petit"),
                            ("medium", "Moyen"),
                            ("large", "Grand"),
                            ("xlarge", "Très grand"),
                        ],
                        default="medium",
                        max_length=10,
                    ),
                ),
                ("notifications_email", models.BooleanField(default=True)),
                ("notifications_push", models.BooleanField(default=True)),
                ("notifications_sms", models.BooleanField(default=False)),
                ("auto_download", models.BooleanField(default=False)),
                ("reading_mode", models.CharField(default="paginated", max_length=20)),
                (
                    "language_interface",
                    models.CharField(
                        choices=[
                            ("fr", "Français"),
                            ("en", "English"),
                            ("wo", "Wolof"),
                            ("bm", "Bambara"),
                            ("ln", "Lingala"),
                        ],
                        default="fr",
                        max_length=5,
                    ),
                ),
                ("privacy_profile", models.CharField(default="public", max_length=20)),
                ("marketing_emails", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Préférences utilisateur",
                "verbose_name_plural": "Préférences utilisateurs",
                "db_table": "auth_user_preferences",
            },
        ),
        migrations.CreateModel(
            name="SecurityLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("LOGIN_SUCCESS", "Connexion réussie"),
                            ("LOGIN_FAILED", "Échec de connexion"),
                            ("LOGOUT", "Déconnexion"),
                            ("PASSWORD_CHANGED", "Mot de passe modifié"),
                            ("EMAIL_VERIFIED", "Email vérifié"),
                            ("ACCOUNT_CREATED", "Compte créé"),
                            ("SESSION_CREATED", "Session créée"),
                            ("SESSION_DELETED", "Session supprimée"),
                            ("SUSPICIOUS_LOGIN", "Connexion suspecte"),
                            ("MULTIPLE_FAILED_LOGINS", "Multiples échecs de connexion"),
                            (
                                "PASSWORD_BREACH_ATTEMPT",
                                "Tentative de violation de mot de passe",
                            ),
                            ("ACCOUNT_LOCKOUT", "Verrouillage de compte"),
                        ],
                        max_length=50,
                    ),
                ),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("details", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="security_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Journal de sécurité",
                "verbose_name_plural": "Journaux de sécurité",
                "db_table": "auth_security_logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="UserRole",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_roles",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="role_users",
                        to="auth_service.role",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_roles",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Rôle utilisateur",
                "verbose_name_plural": "Rôles utilisateurs",
                "db_table": "auth_user_roles",
                "unique_together": {("user", "role")},
            },
        ),
    ]
