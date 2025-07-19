from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.utils import timezone
from django.conf import settings
from .models import User, UserPreferences, UserSession
from .utils import send_welcome_email, send_password_changed_notification, log_security_event, get_client_ip, get_user_agent
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Crée automatiquement les préférences utilisateur lors de la création d'un compte"""
    if created and not hasattr(instance, '_preferences_created'):
        try:
            UserPreferences.objects.get_or_create(user=instance)
            instance._preferences_created = True
            logger.info(f"Préférences créées pour l'utilisateur {instance.username}")
        except Exception as e:
            logger.error(f"Erreur lors de la création des préférences pour {instance.username}: {e}")


@receiver(post_save, sender=User)
def send_welcome_email_on_verification(sender, instance, **kwargs):
    """Envoie un email de bienvenue quand l'utilisateur vérifie son email"""
    if (instance.is_verified and 
        hasattr(instance, 'email_verified_at') and 
        instance.email_verified_at and 
        not hasattr(instance, '_welcome_email_sent')):
        # Vérifier si c'est une nouvelle vérification (dans les dernières minutes)
        if (timezone.now() - instance.email_verified_at).total_seconds() < 300:  # 5 minutes
            try:
                send_welcome_email(instance)
                instance._welcome_email_sent = True
                logger.info(f"Email de bienvenue envoyé à {instance.email}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email de bienvenue à {instance.email}: {e}")


@receiver(pre_save, sender=User)
def detect_password_change(sender, instance, **kwargs):
    """Détecte les changements de mot de passe et envoie une notification"""
    if instance.pk:  # L'utilisateur existe déjà
        try:
            old_instance = User.objects.get(pk=instance.pk)
            # Si le mot de passe a changé
            if old_instance.password != instance.password:
                # Marquer pour envoyer une notification après la sauvegarde
                instance._password_changed = True
                logger.info(f"Changement de mot de passe détecté pour {instance.username}")
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def send_password_change_notification(sender, instance, **kwargs):
    """Envoie une notification après changement de mot de passe"""
    if hasattr(instance, '_password_changed') and instance._password_changed:
        try:
            send_password_changed_notification(instance)
            logger.info(f"Notification de changement de mot de passe envoyée à {instance.email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification de changement de mot de passe: {e}")
        finally:
            # Nettoyer l'attribut temporaire
            if hasattr(instance, '_password_changed'):
                delattr(instance, '_password_changed')


@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """Enregistre les connexions réussies"""
    try:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        # Mettre à jour les informations de dernière connexion
        if hasattr(user, 'last_login_ip'):
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login_ip'])
        
        # Enregistrer l'événement de sécurité
        log_security_event(
            user=user,
            event_type='LOGIN_SUCCESS',
            details={
                'ip_address': ip_address,
                'user_agent': user_agent,
                'timestamp': timezone.now().isoformat()
            },
            request=request
        )
        
        logger.info(f"Connexion réussie pour {user.username} depuis {ip_address}")
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de la connexion pour {user.username}: {e}")


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Enregistre les tentatives de connexion échouées"""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    email = credentials.get('username', 'unknown')
    
    # Essayer de trouver l'utilisateur pour l'événement de sécurité
    user = None
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        pass
    
    # Enregistrer l'événement de sécurité
    log_security_event(
        user=user,
        event_type='LOGIN_FAILED',
        details={
            'attempted_email': email,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timezone.now().isoformat()
        },
        request=request
    )
    
    logger.warning(f"Tentative de connexion échouée pour {email} depuis {ip_address}")


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    """Enregistre les déconnexions"""
    if user:
        ip_address = get_client_ip(request)
        
        # Enregistrer l'événement de sécurité
        log_security_event(
            user=user,
            event_type='LOGOUT',
            details={
                'ip_address': ip_address,
                'timestamp': timezone.now().isoformat()
            },
            request=request
        )
        
        # Supprimer la session utilisateur
        if hasattr(request, 'session') and request.session.session_key:
            UserSession.objects.filter(
                user=user,
                session_key=request.session.session_key
            ).delete()
        
        logger.info(f"Déconnexion de {user.username} depuis {ip_address}")


@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """Enregistre la création de nouveaux comptes"""
    if created and not hasattr(instance, '_creation_logged'):
        try:
            log_security_event(
                user=instance,
                event_type='ACCOUNT_CREATED',
                details={
                    'email': instance.email,
                    'username': instance.username,
                    'country': getattr(instance, 'country', 'Unknown'),
                    'language': getattr(instance, 'language', 'Unknown'),
                    'timestamp': timezone.now().isoformat()
                }
            )
            instance._creation_logged = True
            logger.info(f"Nouveau compte créé: {instance.username} ({instance.email})")
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la création du compte {instance.username}: {e}")


@receiver(post_save, sender=User)
def log_email_verification(sender, instance, **kwargs):
    """Enregistre la vérification d'email"""
    if (instance.is_verified and 
        hasattr(instance, 'email_verified_at') and 
        instance.email_verified_at and 
        not hasattr(instance, '_verification_logged')):
        # Vérifier si c'est une nouvelle vérification
        if (timezone.now() - instance.email_verified_at).total_seconds() < 300:  # 5 minutes
            try:
                log_security_event(
                    user=instance,
                    event_type='EMAIL_VERIFIED',
                    details={
                        'email': instance.email,
                        'verified_at': instance.email_verified_at.isoformat(),
                        'timestamp': timezone.now().isoformat()
                    }
                )
                instance._verification_logged = True
                logger.info(f"Email vérifié pour {instance.username}")
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement de la vérification email pour {instance.username}: {e}")


@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """Enregistre la suppression de comptes"""
    # Note: On ne peut pas utiliser log_security_event ici car l'utilisateur n'existe plus
    logger.warning(f"Compte supprimé: {instance.username} ({instance.email})")


@receiver(post_save, sender=UserSession)
def log_session_creation(sender, instance, created, **kwargs):
    """Enregistre la création de nouvelles sessions"""
    if created:
        log_security_event(
            user=instance.user,
            event_type='SESSION_CREATED',
            details={
                'session_id': str(instance.id),
                'ip_address': instance.ip_address,
                'user_agent': instance.user_agent,
                'expires_at': instance.expires_at.isoformat(),
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.info(f"Nouvelle session créée pour {instance.user.username}")


@receiver(post_delete, sender=UserSession)
def log_session_deletion(sender, instance, **kwargs):
    """Enregistre la suppression de sessions"""
    log_security_event(
        user=instance.user,
        event_type='SESSION_DELETED',
        details={
            'session_id': str(instance.id),
            'ip_address': instance.ip_address,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    logger.info(f"Session supprimée pour {instance.user.username}")


# Signal personnalisé pour les événements de sécurité critiques
from django.dispatch import Signal

security_event = Signal()


@receiver(security_event)
def handle_security_event(sender, user, event_type, details, **kwargs):
    """Gestionnaire pour les événements de sécurité critiques"""
    critical_events = [
        'SUSPICIOUS_LOGIN',
        'MULTIPLE_FAILED_LOGINS',
        'PASSWORD_BREACH_ATTEMPT',
        'ACCOUNT_LOCKOUT'
    ]
    
    if event_type in critical_events:
        # Envoyer une alerte par email à l'équipe de sécurité
        if hasattr(settings, 'SECURITY_TEAM_EMAIL'):
            from django.core.mail import send_mail
            
            try:
                send_mail(
                    subject=f'[COKO SECURITY] {event_type}',
                    message=f'Événement de sécurité détecté:\n\nUtilisateur: {user.username if user else "Inconnu"}\nType: {event_type}\nDétails: {details}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.SECURITY_TEAM_EMAIL],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'alerte de sécurité: {e}")
        
        logger.critical(f"Événement de sécurité critique: {event_type} pour {user.username if user else 'Inconnu'}")