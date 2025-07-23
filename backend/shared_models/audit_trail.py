"""
Système d'audit trail unifié pour tous les services Coko
Extension des logs de sécurité à l'ensemble de la plateforme
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
import json
import uuid
from typing import Dict, Any, Optional

User = get_user_model()


class AuditLog(models.Model):
    """Modèle principal pour l'audit trail unifié"""
    
    ACTION_TYPES = [
        # Actions générales
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('VIEW', 'Consultation'),
        ('DOWNLOAD', 'Téléchargement'),
        ('EXPORT', 'Export'),
        
        # Actions d'authentification
        ('LOGIN', 'Connexion'),
        ('LOGOUT', 'Déconnexion'),
        ('LOGIN_FAILED', 'Échec connexion'),
        ('PASSWORD_CHANGE', 'Changement mot de passe'),
        ('ACCOUNT_LOCK', 'Verrouillage compte'),
        
        # Actions sur le contenu
        ('BOOK_PUBLISH', 'Publication livre'),
        ('BOOK_UNPUBLISH', 'Dépublication livre'),
        ('CONTENT_MODERATE', 'Modération contenu'),
        ('REVIEW_SUBMIT', 'Soumission avis'),
        ('REVIEW_MODERATE', 'Modération avis'),
        
        # Actions de lecture
        ('READING_START', 'Début lecture'),
        ('READING_PAUSE', 'Pause lecture'),
        ('READING_FINISH', 'Fin lecture'),
        ('BOOKMARK_ADD', 'Ajout signet'),
        ('GOAL_CREATE', 'Création objectif'),
        
        # Actions de recommandation
        ('RECOMMENDATION_GENERATE', 'Génération recommandations'),
        ('RECOMMENDATION_CLICK', 'Clic recommandation'),
        ('FEEDBACK_SUBMIT', 'Soumission feedback'),
        
        # Actions financières
        ('PAYMENT_INITIATE', 'Initiation paiement'),
        ('PAYMENT_SUCCESS', 'Paiement réussi'),
        ('PAYMENT_FAILURE', 'Échec paiement'),
        ('SUBSCRIPTION_CHANGE', 'Changement abonnement'),
        ('REFUND_PROCESS', 'Traitement remboursement'),
        
        # Actions administratives
        ('ADMIN_ACCESS', 'Accès administration'),
        ('USER_ROLE_CHANGE', 'Changement rôle utilisateur'),
        ('PERMISSION_GRANT', 'Attribution permission'),
        ('PERMISSION_REVOKE', 'Révocation permission'),
        ('SYSTEM_CONFIG', 'Configuration système'),
        ('DATA_BACKUP', 'Sauvegarde données'),
        ('DATA_RESTORE', 'Restauration données'),
        
        # Actions de sécurité
        ('SUSPICIOUS_ACTIVITY', 'Activité suspecte'),
        ('SECURITY_VIOLATION', 'Violation sécurité'),
        ('ACCESS_DENIED', 'Accès refusé'),
        ('API_RATE_LIMIT', 'Limite API atteinte'),
        ('MALICIOUS_REQUEST', 'Requête malveillante'),
    ]
    
    RISK_LEVELS = [
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyen'),
        ('HIGH', 'Élevé'),
        ('CRITICAL', 'Critique'),
    ]
    
    SERVICES = [
        ('auth_service', 'Service d\'authentification'),
        ('catalog_service', 'Service de catalogue'),
        ('reading_service', 'Service de lecture'),
        ('recommendation_service', 'Service de recommandations'),
        ('payment_service', 'Service de paiement'),
        ('admin_service', 'Service d\'administration'),
        ('api_service', 'Service API'),
        ('system', 'Système'),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Action et contexte
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    service = models.CharField(max_length=30, choices=SERVICES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='LOW')
    
    # Utilisateur et session
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs'
    )
    session_key = models.CharField(max_length=40, blank=True)
    
    # Objet concerné (relation générique)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Détails de l'action
    description = models.TextField()
    changes = models.JSONField(default=dict, blank=True)  # Avant/après pour les modifications
    metadata = models.JSONField(default=dict, blank=True)  # Données supplémentaires
    
    # Informations techniques
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referer = models.URLField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_url = models.TextField(blank=True)
    
    # Géolocalisation et contexte
    country = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=20, blank=True)  # mobile, desktop, tablet
    
    # Résultat et impact
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    impact_assessment = models.TextField(blank=True)
    
    # Horodatage
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Corrélation (pour grouper des événements liés)
    correlation_id = models.UUIDField(null=True, blank=True)
    parent_log = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['service', 'action_type']),
            models.Index(fields=['risk_level', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['correlation_id']),
        ]
    
    def __str__(self):
        user_info = f"{self.user.username}" if self.user else "Anonyme"
        return f"{self.get_action_type_display()} - {user_info} - {self.timestamp}"
    
    @classmethod
    def log_action(cls, action_type: str, user=None, description: str = "", 
                   service: str = "system", risk_level: str = "LOW", 
                   request=None, target_object=None, changes: Dict = None, 
                   metadata: Dict = None, correlation_id=None, **kwargs):
        """Méthode utilitaire pour créer un log d'audit"""
        
        log_data = {
            'action_type': action_type,
            'service': service,
            'risk_level': risk_level,
            'user': user,
            'description': description,
            'changes': changes or {},
            'metadata': metadata or {},
            'correlation_id': correlation_id,
        }
        
        # Extraire les informations de la requête si fournie
        if request:
            log_data.update({
                'ip_address': cls._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referer': request.META.get('HTTP_REFERER', ''),
                'request_method': request.method,
                'request_url': request.get_full_path(),
                'session_key': request.session.session_key,
            })
            
            # Détection du type d'appareil
            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            if 'mobile' in user_agent:
                log_data['device_type'] = 'mobile'
            elif 'tablet' in user_agent:
                log_data['device_type'] = 'tablet'
            else:
                log_data['device_type'] = 'desktop'
        
        # Objet cible
        if target_object:
            log_data.update({
                'content_object': target_object,
            })
        
        # Ajouter les champs supplémentaires
        log_data.update(kwargs)
        
        return cls.objects.create(**log_data)
    
    @staticmethod
    def _get_client_ip(request):
        """Récupère l'IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def mark_as_resolved(self, resolution_note: str = ""):
        """Marque un incident comme résolu"""
        self.metadata['resolved'] = True
        self.metadata['resolution_timestamp'] = timezone.now().isoformat()
        self.metadata['resolution_note'] = resolution_note
        self.save()
    
    def add_follow_up(self, description: str, user=None):
        """Ajoute un suivi à ce log"""
        return AuditLog.objects.create(
            action_type='FOLLOW_UP',
            service=self.service,
            user=user,
            description=description,
            parent_log=self,
            correlation_id=self.correlation_id,
            risk_level=self.risk_level
        )


class SecurityAlert(models.Model):
    """Alertes de sécurité basées sur les logs d'audit"""
    
    ALERT_TYPES = [
        ('MULTIPLE_FAILED_LOGINS', 'Tentatives de connexion multiples'),
        ('SUSPICIOUS_IP', 'Adresse IP suspecte'),
        ('UNUSUAL_ACTIVITY', 'Activité inhabituelle'),
        ('PRIVILEGE_ESCALATION', 'Escalade de privilèges'),
        ('DATA_BREACH_ATTEMPT', 'Tentative de violation de données'),
        ('MALICIOUS_PATTERN', 'Motif malveillant détecté'),
        ('RATE_LIMIT_EXCEEDED', 'Limite de taux dépassée'),
        ('UNAUTHORIZED_ACCESS', 'Accès non autorisé'),
    ]
    
    SEVERITY_LEVELS = [
        ('INFO', 'Information'),
        ('WARNING', 'Avertissement'),
        ('ERROR', 'Erreur'),
        ('CRITICAL', 'Critique'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Ouvert'),
        ('INVESTIGATING', 'En cours d\'investigation'),
        ('RESOLVED', 'Résolu'),
        ('FALSE_POSITIVE', 'Faux positif'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Type et sévérité
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # Description et contexte
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Logs d'audit liés
    related_logs = models.ManyToManyField(AuditLog, related_name='security_alerts')
    
    # Utilisateur et IP concernés
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Métadonnées de l'alerte
    detection_rules = models.JSONField(default=list)  # Règles qui ont déclenché l'alerte
    risk_score = models.IntegerField(default=0)  # Score de risque 0-100
    
    # Traitement
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_alerts'
    )
    investigation_notes = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Horodatage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'security_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.get_severity_display()}"
    
    def resolve(self, resolution_note: str = "", user=None):
        """Résout l'alerte"""
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        self.resolution_notes = resolution_note
        if user:
            self.assigned_to = user
        self.save()
    
    def escalate(self):
        """Escalade l'alerte au niveau supérieur"""
        severity_map = {
            'INFO': 'WARNING',
            'WARNING': 'ERROR',
            'ERROR': 'CRITICAL'
        }
        if self.severity in severity_map:
            self.severity = severity_map[self.severity]
            self.save()


class AuditLogAnalyzer:
    """Analyseur de logs d'audit pour détecter les anomalies"""
    
    def __init__(self):
        self.detection_rules = [
            self._detect_multiple_failed_logins,
            self._detect_suspicious_ip_activity,
            self._detect_unusual_access_patterns,
            self._detect_privilege_escalation,
            self._detect_data_access_anomalies,
        ]
    
    def analyze_recent_logs(self, hours: int = 1):
        """Analyse les logs récents pour détecter des anomalies"""
        cutoff_time = timezone.now() - timezone.timedelta(hours=hours)
        recent_logs = AuditLog.objects.filter(timestamp__gte=cutoff_time)
        
        alerts_created = []
        
        for rule in self.detection_rules:
            try:
                detected_issues = rule(recent_logs)
                for issue in detected_issues:
                    alert = self._create_security_alert(issue, recent_logs)
                    if alert:
                        alerts_created.append(alert)
            except Exception as e:
                # Logger l'erreur mais continuer l'analyse
                AuditLog.log_action(
                    action_type='SYSTEM_ERROR',
                    service='system',
                    description=f"Erreur dans l'analyse de sécurité: {str(e)}",
                    risk_level='MEDIUM'
                )
        
        return alerts_created
    
    def _detect_multiple_failed_logins(self, logs):
        """Détecte les tentatives de connexion multiples échouées"""
        failed_logins = logs.filter(
            action_type='LOGIN_FAILED'
        ).values('ip_address', 'user').annotate(
            count=models.Count('id')
        ).filter(count__gte=5)  # 5 échecs ou plus
        
        issues = []
        for login_data in failed_logins:
            issues.append({
                'type': 'MULTIPLE_FAILED_LOGINS',
                'severity': 'WARNING',
                'title': 'Tentatives de connexion multiples échouées',
                'description': f"Détection de {login_data['count']} tentatives de connexion échouées",
                'ip_address': login_data['ip_address'],
                'user_id': login_data['user'],
                'risk_score': min(login_data['count'] * 10, 100)
            })
        
        return issues
    
    def _detect_suspicious_ip_activity(self, logs):
        """Détecte l'activité suspecte d'IP"""
        # IPs avec beaucoup d'activité différente
        suspicious_ips = logs.values('ip_address').annotate(
            unique_users=models.Count('user', distinct=True),
            total_actions=models.Count('id'),
            unique_actions=models.Count('action_type', distinct=True)
        ).filter(
            unique_users__gte=10,  # Plus de 10 utilisateurs différents
            unique_actions__gte=5   # Plus de 5 types d'actions différentes
        )
        
        issues = []
        for ip_data in suspicious_ips:
            issues.append({
                'type': 'SUSPICIOUS_IP',
                'severity': 'ERROR',
                'title': 'Activité IP suspecte',
                'description': f"IP avec activité anormale: {ip_data['unique_users']} utilisateurs, {ip_data['total_actions']} actions",
                'ip_address': ip_data['ip_address'],
                'risk_score': min((ip_data['unique_users'] + ip_data['total_actions']) * 2, 100)
            })
        
        return issues
    
    def _detect_unusual_access_patterns(self, logs):
        """Détecte les motifs d'accès inhabituels"""
        # Accès en dehors des heures normales (ex: 2h-6h du matin)
        unusual_hours = logs.filter(
            timestamp__hour__in=[2, 3, 4, 5, 6],
            action_type__in=['ADMIN_ACCESS', 'DATA_EXPORT', 'SYSTEM_CONFIG']
        )
        
        issues = []
        if unusual_hours.exists():
            issues.append({
                'type': 'UNUSUAL_ACTIVITY',
                'severity': 'WARNING',
                'title': 'Accès en dehors des heures normales',
                'description': f"Détection de {unusual_hours.count()} accès sensibles hors heures normales",
                'risk_score': min(unusual_hours.count() * 15, 100)
            })
        
        return issues
    
    def _detect_privilege_escalation(self, logs):
        """Détecte les tentatives d'escalade de privilèges"""
        privilege_changes = logs.filter(
            action_type__in=['USER_ROLE_CHANGE', 'PERMISSION_GRANT']
        )
        
        issues = []
        for log in privilege_changes:
            # Vérifier si l'utilisateur qui fait le changement a les droits appropriés
            if log.user and not log.user.is_staff:
                issues.append({
                    'type': 'PRIVILEGE_ESCALATION',
                    'severity': 'CRITICAL',
                    'title': 'Tentative d\'escalade de privilèges',
                    'description': f"Utilisateur non-admin tentant de modifier les privilèges",
                    'user_id': log.user.id,
                    'risk_score': 90
                })
        
        return issues
    
    def _detect_data_access_anomalies(self, logs):
        """Détecte les anomalies d'accès aux données"""
        # Téléchargements massifs
        mass_downloads = logs.filter(
            action_type='DOWNLOAD'
        ).values('user').annotate(
            count=models.Count('id')
        ).filter(count__gte=50)  # Plus de 50 téléchargements
        
        issues = []
        for download_data in mass_downloads:
            issues.append({
                'type': 'DATA_BREACH_ATTEMPT',
                'severity': 'ERROR',
                'title': 'Téléchargements massifs détectés',
                'description': f"Utilisateur avec {download_data['count']} téléchargements",
                'user_id': download_data['user'],
                'risk_score': min(download_data['count'] * 2, 100)
            })
        
        return issues
    
    def _create_security_alert(self, issue_data, related_logs):
        """Crée une alerte de sécurité basée sur les données détectées"""
        try:
            # Vérifier si une alerte similaire existe déjà
            existing_alert = SecurityAlert.objects.filter(
                alert_type=issue_data['type'],
                ip_address=issue_data.get('ip_address'),
                user_id=issue_data.get('user_id'),
                status__in=['OPEN', 'INVESTIGATING'],
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).first()
            
            if existing_alert:
                # Mettre à jour l'alerte existante
                existing_alert.risk_score = max(existing_alert.risk_score, issue_data['risk_score'])
                existing_alert.save()
                return existing_alert
            
            # Créer une nouvelle alerte
            alert = SecurityAlert.objects.create(
                alert_type=issue_data['type'],
                severity=issue_data['severity'],
                title=issue_data['title'],
                description=issue_data['description'],
                ip_address=issue_data.get('ip_address'),
                user_id=issue_data.get('user_id'),
                risk_score=issue_data['risk_score']
            )
            
            # Associer les logs liés
            relevant_logs = related_logs.filter(
                ip_address=issue_data.get('ip_address'),
                user_id=issue_data.get('user_id')
            )[:20]  # Limiter à 20 logs
            
            alert.related_logs.set(relevant_logs)
            
            return alert
            
        except Exception as e:
            # Logger l'erreur
            AuditLog.log_action(
                action_type='SYSTEM_ERROR',
                service='system',
                description=f"Erreur lors de la création d'alerte: {str(e)}",
                risk_level='MEDIUM'
            )
            return None


# Middleware pour l'audit automatique
class AuditTrailMiddleware:
    """Middleware pour capturer automatiquement les actions utilisateur"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Traitement avant la vue
        correlation_id = uuid.uuid4()
        request.correlation_id = correlation_id
        
        response = self.get_response(request)
        
        # Traitement après la vue (si nécessaire)
        # On peut logger ici les réponses importantes
        
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Log automatique des vues importantes"""
        sensitive_views = [
            'admin:',
            'api:users',
            'api:payments',
            'export',
            'dashboard'
        ]
        
        view_name = getattr(view_func, '__name__', '')
        
        # Vérifier si c'est une vue sensible
        if any(sensitive in view_name.lower() for sensitive in sensitive_views):
            AuditLog.log_action(
                action_type='VIEW',
                service='api_service',
                description=f"Accès à la vue: {view_name}",
                user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                request=request,
                correlation_id=request.correlation_id,
                risk_level='MEDIUM' if 'admin' in view_name.lower() else 'LOW'
            )