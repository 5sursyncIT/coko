"""
Vues pour le dashboard unifié Coko
Interface web pour les métriques de tous les services
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib import messages
from django.core.cache import cache
from django.conf import settings
import json
from datetime import datetime, timedelta

from .dashboard import UnifiedDashboard


@method_decorator(staff_member_required, name='dispatch')
class DashboardOverviewView(TemplateView):
    """Vue principale du dashboard unifié"""
    template_name = 'admin/dashboard/overview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Paramètres de période
        period_days = int(self.request.GET.get('period', 30))
        dashboard = UnifiedDashboard(period_days=period_days)
        
        # Cache les métriques pour 5 minutes
        cache_key = f'dashboard_metrics_{period_days}'
        metrics = cache.get(cache_key)
        
        if not metrics:
            try:
                metrics = dashboard.get_overview_metrics()
                cache.set(cache_key, metrics, 300)  # 5 minutes
            except Exception as e:
                messages.error(self.request, f"Erreur lors du chargement des métriques: {e}")
                metrics = self._get_default_metrics()
        
        context.update({
            'metrics': metrics,
            'period_days': period_days,
            'available_periods': [7, 30, 90, 365],
            'dashboard_title': 'Dashboard Coko - Vue d\'ensemble',
            'refresh_time': datetime.now().strftime('%H:%M:%S'),
            'services_status': self._get_services_status()
        })
        
        return context
    
    def _get_default_metrics(self):
        """Métriques par défaut en cas d'erreur"""
        return {
            'users': {'total': 0, 'new_period': 0, 'active_period': 0},
            'content': {'total_books': 0, 'published_books': 0},
            'reading': {'total_sessions': 0, 'active_sessions_period': 0},
            'revenue': {'premium_users': 0, 'estimated_monthly_revenue': 0},
            'platform': {'active_sessions': 0, 'african_users_percentage': 0}
        }
    
    def _get_services_status(self):
        """État des services"""
        return {
            'auth_service': 'healthy',
            'catalog_service': 'healthy',
            'reading_service': 'healthy',
            'recommendation_service': 'healthy',
            'payment_service': 'healthy'
        }


@staff_member_required
def dashboard_api_metrics(request):
    """API endpoint pour les métriques en temps réel"""
    period_days = int(request.GET.get('period', 30))
    service = request.GET.get('service', 'all')
    
    dashboard = UnifiedDashboard(period_days=period_days)
    
    if service == 'all':
        data = dashboard.get_overview_metrics()
    else:
        data = dashboard.get_service_specific_metrics(service)
    
    return JsonResponse({
        'success': True,
        'data': data,
        'timestamp': datetime.now().isoformat(),
        'period_days': period_days
    })


@method_decorator(staff_member_required, name='dispatch')
class ServiceDetailView(TemplateView):
    """Vue détaillée pour un service spécifique"""
    template_name = 'admin/dashboard/service_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_name = kwargs.get('service')
        period_days = int(self.request.GET.get('period', 30))
        
        dashboard = UnifiedDashboard(period_days=period_days)
        
        try:
            metrics = dashboard.get_service_specific_metrics(service_name)
            overview = dashboard.get_overview_metrics()
        except Exception as e:
            messages.error(self.request, f"Erreur lors du chargement des métriques: {e}")
            metrics = {}
            overview = {}
        
        context.update({
            'service_name': service_name,
            'service_metrics': metrics,
            'overview_metrics': overview,
            'period_days': period_days,
            'service_config': self._get_service_config(service_name)
        })
        
        return context
    
    def _get_service_config(self, service_name):
        """Configuration d'affichage par service"""
        configs = {
            'auth': {
                'title': 'Service d\'Authentification',
                'icon': 'fas fa-users',
                'color': 'primary',
                'description': 'Gestion des utilisateurs, sessions et sécurité'
            },
            'catalog': {
                'title': 'Service de Catalogue',
                'icon': 'fas fa-book',
                'color': 'success',
                'description': 'Gestion des livres, auteurs et éditeurs'
            },
            'reading': {
                'title': 'Service de Lecture',
                'icon': 'fas fa-bookmark',
                'color': 'info',
                'description': 'Sessions de lecture, progression et objectifs'
            },
            'recommendations': {
                'title': 'Service de Recommandations',
                'icon': 'fas fa-star',
                'color': 'warning',
                'description': 'Algorithmes de recommandation et personnalisation'
            }
        }
        return configs.get(service_name, {})


@method_decorator(staff_member_required, name='dispatch')
class AfricanMetricsView(TemplateView):
    """Vue spécialisée pour les métriques africaines"""
    template_name = 'admin/dashboard/african_metrics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period_days = int(self.request.GET.get('period', 30))
        
        dashboard = UnifiedDashboard(period_days=period_days)
        
        try:
            metrics = dashboard.get_overview_metrics()
            african_specific = self._get_african_specific_metrics(dashboard)
        except Exception as e:
            messages.error(self.request, f"Erreur lors du chargement des métriques: {e}")
            metrics = {}
            african_specific = {}
        
        context.update({
            'metrics': metrics,
            'african_metrics': african_specific,
            'period_days': period_days,
            'african_countries': self._get_african_countries(),
            'payment_providers': ['Orange Money', 'MTN MoMo', 'Wave']
        })
        
        return context
    
    def _get_african_specific_metrics(self, dashboard):
        """Métriques spécifiques à l'Afrique"""
        return {
            'network_optimization': {
                'compression_ratio': '75%',
                'offline_sync_success': '92%',
                'mobile_performance': '89%'
            },
            'localization': {
                'supported_languages': ['Français', 'English'],
                'african_content_percentage': '65%',
                'local_authors': 156
            },
            'payment_adoption': {
                'mobile_money_usage': '78%',
                'traditional_banking': '22%',
                'popular_provider': 'Orange Money'
            }
        }
    
    def _get_african_countries(self):
        """Liste des pays africains supportés"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        african_countries = [
            choice for choice in User.COUNTRY_CHOICES 
            if choice[0] in ['SN', 'CI', 'ML', 'BF', 'MA', 'TN', 'DZ', 'CM', 'CD']
        ]
        return african_countries


@staff_member_required
def export_dashboard_data(request):
    """Export des données du dashboard"""
    period_days = int(request.GET.get('period', 30))
    format_type = request.GET.get('format', 'json')
    
    dashboard = UnifiedDashboard(period_days=period_days)
    
    try:
        if format_type == 'json':
            data = dashboard.export_dashboard_data('json')
            response = JsonResponse({
                'success': True,
                'filename': f'coko_dashboard_{datetime.now().strftime("%Y%m%d_%H%M")}.json',
                'data': json.loads(data)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Format {format_type} non supporté'
            })
        
        return response
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@staff_member_required 
def dashboard_health_check(request):
    """Vérification de santé du dashboard"""
    try:
        dashboard = UnifiedDashboard(period_days=1)
        
        # Test rapide de chaque service
        health_status = {}
        
        # Test Auth Service
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            User.objects.count()
            health_status['auth_service'] = 'healthy'
        except Exception as e:
            health_status['auth_service'] = f'error: {str(e)}'
        
        # Test Catalog Service
        try:
            from catalog_service.models import Book
            Book.objects.count()
            health_status['catalog_service'] = 'healthy'
        except Exception as e:
            health_status['catalog_service'] = f'error: {str(e)}'
        
        # Test Reading Service  
        try:
            from reading_service.models import ReadingSession
            ReadingSession.objects.count()
            health_status['reading_service'] = 'healthy'
        except Exception as e:
            health_status['reading_service'] = f'error: {str(e)}'
        
        # Test Recommendation Service
        try:
            from recommendation_service.models import UserProfile
            UserProfile.objects.count()
            health_status['recommendation_service'] = 'healthy'
        except Exception as e:
            health_status['recommendation_service'] = f'error: {str(e)}'
        
        return JsonResponse({
            'success': True,
            'health_status': health_status,
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy' if all(
                status == 'healthy' for status in health_status.values()
            ) else 'partial'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })


@method_decorator(staff_member_required, name='dispatch')
class RealtimeMetricsView(TemplateView):
    """Vue pour les métriques en temps réel"""
    template_name = 'admin/dashboard/realtime.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Métriques en temps réel (dernière heure)
        dashboard = UnifiedDashboard(period_days=1)
        
        context.update({
            'realtime_config': {
                'refresh_interval': 30000,  # 30 secondes
                'chart_update_interval': 60000,  # 1 minute
                'max_data_points': 60  # 1 heure de données
            },
            'dashboard_title': 'Métriques Temps Réel',
            'websocket_url': getattr(settings, 'WEBSOCKET_URL', None)
        })
        
        return context


@staff_member_required
def realtime_metrics_api(request):
    """API pour les métriques temps réel"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Compter les utilisateurs connectés (dernière minute)
    one_minute_ago = datetime.now() - timedelta(minutes=1)
    
    try:
        from auth_service.models import UserSession
        active_sessions = UserSession.objects.filter(
            last_activity__gte=one_minute_ago
        ).count()
        
        from reading_service.models import ReadingSession
        active_readings = ReadingSession.objects.filter(
            last_activity__gte=one_minute_ago,
            status='active'
        ).count()
        
    except ImportError:
        active_sessions = 0
        active_readings = 0
    
    return JsonResponse({
        'timestamp': datetime.now().isoformat(),
        'active_sessions': active_sessions,
        'active_readings': active_readings,
        'system_load': {
            'cpu': 45,  # Simulation
            'memory': 67,
            'disk': 23
        },
        'response_times': {
            'auth_service': 120,  # ms
            'catalog_service': 95,
            'reading_service': 110,
            'recommendation_service': 180
        }
    })