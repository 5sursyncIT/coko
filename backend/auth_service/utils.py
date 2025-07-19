from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import secrets
import string
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional


def generate_verification_token(user):
    """Génère un token de vérification pour l'utilisateur"""
    return default_token_generator.make_token(user)


def generate_secure_token(length: int = 32) -> str:
    """Génère un token sécurisé aléatoirement"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_password(length: int = 12) -> str:
    """Génère un mot de passe sécurisé"""
    # Au moins une majuscule, une minuscule, un chiffre et un caractère spécial
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*"
    
    # S'assurer qu'on a au moins un caractère de chaque type
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Compléter avec des caractères aléatoires
    all_chars = lowercase + uppercase + digits + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Mélanger la liste
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def send_verification_email(user, token: str):
    """Envoie un email de vérification à l'utilisateur"""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
    
    context = {
        'user': user,
        'verification_url': verification_url,
        'site_name': 'COKO',
        'frontend_url': settings.FRONTEND_URL
    }
    
    # Rendu du template HTML
    html_message = render_to_string('auth/verification_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Vérifiez votre adresse email - COKO',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_welcome_email(user):
    """Envoie un email de bienvenue après vérification"""
    context = {
        'user': user,
        'site_name': 'COKO',
        'frontend_url': settings.FRONTEND_URL,
        'support_email': settings.SUPPORT_EMAIL
    }
    
    html_message = render_to_string('auth/welcome_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Bienvenue sur COKO !',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,  # Ne pas faire échouer si l'email de bienvenue ne peut pas être envoyé
    )


def send_password_changed_notification(user):
    """Envoie une notification de changement de mot de passe"""
    context = {
        'user': user,
        'site_name': 'COKO',
        'frontend_url': settings.FRONTEND_URL,
        'support_email': settings.SUPPORT_EMAIL,
        'timestamp': datetime.now()
    }
    
    html_message = render_to_string('auth/password_changed_email.html', context)
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Votre mot de passe a été modifié - COKO',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )


def validate_password_strength(password: str) -> dict:
    """Valide la force d'un mot de passe"""
    errors = []
    score = 0
    
    # Longueur minimale
    if len(password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères")
    else:
        score += 1
    
    # Majuscules
    if not any(c.isupper() for c in password):
        errors.append("Le mot de passe doit contenir au moins une majuscule")
    else:
        score += 1
    
    # Minuscules
    if not any(c.islower() for c in password):
        errors.append("Le mot de passe doit contenir au moins une minuscule")
    else:
        score += 1
    
    # Chiffres
    if not any(c.isdigit() for c in password):
        errors.append("Le mot de passe doit contenir au moins un chiffre")
    else:
        score += 1
    
    # Caractères spéciaux
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("Le mot de passe doit contenir au moins un caractère spécial")
    else:
        score += 1
    
    # Longueur bonus
    if len(password) >= 12:
        score += 1
    
    # Déterminer le niveau de sécurité
    if score <= 2:
        strength = "Faible"
    elif score <= 4:
        strength = "Moyen"
    else:
        strength = "Fort"
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'score': score,
        'strength': strength
    }


def generate_api_key(user_id: str, secret_key: str) -> str:
    """Génère une clé API pour un utilisateur"""
    timestamp = str(int(datetime.now().timestamp()))
    data = f"{user_id}:{timestamp}"
    signature = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{data}:{signature}"


def validate_api_key(api_key: str, secret_key: str, max_age_hours: int = 24) -> Optional[str]:
    """Valide une clé API et retourne l'ID utilisateur si valide"""
    try:
        parts = api_key.split(':')
        if len(parts) != 3:
            return None
        
        user_id, timestamp, signature = parts
        
        # Vérifier l'âge de la clé
        key_time = datetime.fromtimestamp(int(timestamp))
        if datetime.now() - key_time > timedelta(hours=max_age_hours):
            return None
        
        # Vérifier la signature
        data = f"{user_id}:{timestamp}"
        expected_signature = hmac.new(
            secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(signature, expected_signature):
            return user_id
        
        return None
        
    except (ValueError, TypeError):
        return None


def mask_email(email: str) -> str:
    """Masque partiellement une adresse email pour l'affichage"""
    if '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Masque partiellement un numéro de téléphone"""
    if len(phone) <= 4:
        return phone
    
    return phone[:2] + '*' * (len(phone) - 4) + phone[-2:]


def get_client_ip(request) -> str:
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request) -> str:
    """Récupère le user agent du client"""
    return request.META.get('HTTP_USER_AGENT', '')


def is_suspicious_activity(user, request) -> bool:
    """Détecte une activité suspecte basée sur l'IP et le user agent"""
    from .models import UserSession
    
    current_ip = get_client_ip(request)
    current_ua = get_user_agent(request)
    
    # Vérifier les sessions récentes
    recent_sessions = UserSession.objects.filter(
        user=user,
        created_at__gte=datetime.now() - timedelta(hours=24)
    )
    
    # Si c'est une nouvelle IP et un nouveau user agent
    known_ips = set(session.ip_address for session in recent_sessions)
    known_uas = set(session.user_agent for session in recent_sessions)
    
    if current_ip not in known_ips and current_ua not in known_uas:
        return True
    
    return False


def log_security_event(user, event_type: str, details: dict, request=None):
    """Enregistre un événement de sécurité"""
    from .models import SecurityLog
    
    ip_address = get_client_ip(request) if request else None
    user_agent = get_user_agent(request) if request else None
    
    SecurityLog.objects.create(
        user=user,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )


def clean_expired_sessions():
    """Nettoie les sessions expirées (à utiliser dans une tâche Celery)"""
    from .models import UserSession
    from django.utils import timezone
    
    expired_count = UserSession.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()[0]
    
    return expired_count


def clean_expired_tokens():
    """Nettoie les tokens expirés (à utiliser dans une tâche Celery)"""
    from .models import User
    from django.utils import timezone
    
    # Nettoyer les tokens de réinitialisation expirés (plus de 24h)
    expired_reset_tokens = User.objects.filter(
        password_reset_requested_at__lt=timezone.now() - timedelta(hours=24),
        password_reset_token__isnull=False
    )
    
    count = expired_reset_tokens.count()
    expired_reset_tokens.update(
        password_reset_token=None,
        password_reset_requested_at=None
    )
    
    return count