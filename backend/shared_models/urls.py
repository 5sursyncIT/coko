"""
URLs pour le système de dashboard unifié et les fonctionnalités back-office améliorées
"""

from django.urls import path, include
from django.contrib.admin.views.decorators import staff_member_required

from .dashboard_views import (
    DashboardOverviewView, ServiceDetailView, AfricanMetricsView,
    RealtimeMetricsView, dashboard_api_metrics, export_dashboard_data,
    dashboard_health_check, realtime_metrics_api
)
from .export_apis import (
    export_author_books, export_author_analytics, export_author_revenue,
    export_publisher_catalog, export_publisher_authors, export_complete_package
)

app_name = 'dashboard'

# URLs du dashboard principal
dashboard_patterns = [
    # Vues principales du dashboard
    path('', DashboardOverviewView.as_view(), name='overview'),
    path('service/<str:service>/', ServiceDetailView.as_view(), name='service_detail'),
    path('african-metrics/', AfricanMetricsView.as_view(), name='african_metrics'),
    path('realtime/', RealtimeMetricsView.as_view(), name='realtime'),
    
    # APIs du dashboard
    path('api/metrics/', dashboard_api_metrics, name='api_metrics'),
    path('api/realtime/', realtime_metrics_api, name='api_realtime'),
    path('api/health/', dashboard_health_check, name='api_health'),
    
    # Export des données
    path('export/', export_dashboard_data, name='export_data'),
]

# URLs des APIs d'export pour créateurs
export_patterns = [
    # Exports pour auteurs
    path('author/books/', export_author_books, name='export_author_books'),
    path('author/analytics/', export_author_analytics, name='export_author_analytics'),
    path('author/revenue/', export_author_revenue, name='export_author_revenue'),
    
    # Exports pour éditeurs
    path('publisher/catalog/', export_publisher_catalog, name='export_publisher_catalog'),
    path('publisher/authors/', export_publisher_authors, name='export_publisher_authors'),
    
    # Export complet
    path('complete-package/', export_complete_package, name='export_complete_package'),
]

# URLs principales
urlpatterns = [
    # Dashboard unifié
    path('dashboard/', include(dashboard_patterns)),
    
    # APIs d'export
    path('api/export/', include(export_patterns)),
]