"""Middleware personnalisés pour l'application Coko"""

import logging
import time
import traceback
from django.http import JsonResponse
from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ValidationError
from rest_framework import status

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Middleware pour la gestion centralisée des erreurs"""
    
    def process_exception(self, request, exception):
        """Gère les exceptions non capturées"""
        
        # Log de l'erreur avec le traceback complet
        error_id = f"error_{int(time.time())}"
        logger.error(
            f"Erreur non gérée [{error_id}]: {str(exception)}",
            extra={
                'error_id': error_id,
                'path': request.path,
                'method': request.method,
                'user': getattr(request, 'user', None),
                'traceback': traceback.format_exc()
            }
        )
        
        # En mode debug, laisser Django gérer l'erreur
        if settings.DEBUG:
            return None
        
        # Réponse d'erreur standardisée pour l'API
        if request.path.startswith('/api/'):
            error_response = {
                'error': 'Une erreur interne s\'est produite',
                'error_id': error_id,
                'status': 'error'
            }
            
            # Ajouter des détails spécifiques selon le type d'erreur
            if isinstance(exception, ValidationError):
                error_response['error'] = 'Données invalides'
                return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)
            
            return JsonResponse(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Pour les autres requêtes, laisser Django gérer
        return None


class DatabaseConnectionMiddleware(MiddlewareMixin):
    """Middleware pour surveiller les connexions à la base de données"""
    
    def process_request(self, request):
        """Vérifie la santé des connexions DB avant traitement"""
        try:
            # Test simple de connexion
            connection.ensure_connection()
        except Exception as e:
            logger.error(f"Problème de connexion à la base de données: {e}")
            
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Service temporairement indisponible',
                    'status': 'error'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware pour logger les requêtes importantes"""
    
    def process_request(self, request):
        """Log des requêtes sensibles"""
        request.start_time = time.time()
        
        # Logger les requêtes d'authentification et d'administration
        if any(path in request.path for path in ['/api/auth/', '/admin/', '/api/users/']):
            logger.info(
                f"Requête sensible: {request.method} {request.path}",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'user': getattr(request, 'user', None),
                    'ip': self.get_client_ip(request)
                }
            )
    
    def process_response(self, request, response):
        """Log du temps de réponse pour les requêtes lentes"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Logger les requêtes lentes (> 2 secondes)
            if duration > 2.0:
                logger.warning(
                    f"Requête lente: {request.method} {request.path} - {duration:.2f}s",
                    extra={
                        'method': request.method,
                        'path': request.path,
                        'duration': duration,
                        'status_code': response.status_code
                    }
                )
        
        return response
    
    def get_client_ip(self, request):
        """Récupère l'IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware pour ajouter des en-têtes de sécurité"""
    
    def process_response(self, request, response):
        """Ajoute des en-têtes de sécurité"""
        if not settings.DEBUG:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response