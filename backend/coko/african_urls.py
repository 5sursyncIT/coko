# URLs pour les fonctionnalités africaines
# Intègre toutes les nouvelles APIs et vues créées

from django.urls import path, include
from django.views.generic import TemplateView
from . import african_middleware, african_payments, african_geolocation
from . import african_monitoring, african_pwa, african_languages, african_performance

# URLs pour les paiements africains
payment_patterns = [
    path('orange-money/', african_payments.orange_money_view, name='orange_money'),
    path('mtn-momo/', african_payments.mtn_momo_view, name='mtn_momo'),
    path('wave/', african_payments.wave_view, name='wave'),
    path('status/<str:transaction_id>/', african_payments.payment_status_view, name='payment_status'),
    path('webhook/', african_payments.payment_webhook_view, name='payment_webhook'),
]

# URLs pour la géolocalisation
geolocation_patterns = [
    path('location/', african_geolocation.location_api_view, name='location_api'),
    path('country-info/', african_geolocation.country_info_view, name='country_info'),
    path('network-recommendations/', african_geolocation.network_recommendations_view, name='network_recommendations'),
]

# URLs pour le monitoring
monitoring_patterns = [
    path('metrics/', african_monitoring.metrics_api_view, name='metrics_api'),
    path('dashboard/', african_monitoring.dashboard_view, name='monitoring_dashboard'),
    path('health/', african_monitoring.health_check_view, name='health_check'),
    path('alerts/', african_monitoring.alerts_view, name='alerts'),
]

# URLs pour PWA
pwa_patterns = [
    path('manifest.json', african_pwa.manifest_view, name='pwa_manifest'),
    path('sw.js', african_pwa.service_worker_view, name='service_worker'),
    path('offline/', african_pwa.offline_page_view, name='offline_page'),
    path('sync/', african_pwa.sync_api_view, name='sync_api'),
    path('install-prompt/', african_pwa.pwa_install_prompt_view, name='install_prompt'),
]

# URLs pour les langues
language_patterns = [
    path('api/', african_languages.language_api_view, name='language_api'),
    path('css/<str:lang_code>/', african_languages.language_css_view, name='language_css'),
    path('keyboard/<str:lang_code>/', african_languages.keyboard_layout_view, name='keyboard_layout'),
]

# URLs pour les performances
performance_patterns = [
    path('metrics/', african_performance.performance_metrics_view, name='performance_metrics'),
    path('cache-status/', african_performance.cache_status_view, name='cache_status'),
    path('optimize-assets/', african_performance.optimize_assets_view, name='optimize_assets'),
]

# URLs principales
urlpatterns = [
    # APIs africaines
    path('api/african/payments/', include(payment_patterns)),
    path('api/african/geolocation/', include(geolocation_patterns)),
    path('api/african/monitoring/', include(monitoring_patterns)),
    path('api/african/languages/', include(language_patterns)),
    path('api/african/performance/', include(performance_patterns)),
    
    # PWA (racine pour compatibilité)
    path('', include(pwa_patterns)),
    
    # Pages spéciales
    path('african-dashboard/', TemplateView.as_view(template_name='african/dashboard.html'), name='african_dashboard'),
    path('network-status/', TemplateView.as_view(template_name='african/network_status.html'), name='network_status'),
    path('payment-methods/', TemplateView.as_view(template_name='african/payment_methods.html'), name='payment_methods'),
]

# URLs pour les tests et développement
if getattr(settings, 'DEBUG', False):
    test_patterns = [
        path('test/network-quality/', african_middleware.test_network_quality_view, name='test_network_quality'),
        path('test/geolocation/', african_geolocation.test_geolocation_view, name='test_geolocation'),
        path('test/payments/', african_payments.test_payments_view, name='test_payments'),
        path('test/performance/', african_performance.test_performance_view, name='test_performance'),
    ]
    
    urlpatterns += [
        path('test/african/', include(test_patterns)),
    ]