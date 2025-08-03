from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Dashboard unifié et back-office amélioré
    path('dashboard/', include('shared_models.urls')),
    
    # API endpoints
    path('api/v1/auth/', include('auth_service.urls')),
    path('api/v1/catalog/', include('catalog_service.urls')),
    path('api/v1/reading/', include('reading_service.urls')),
    path('api/v1/recommendations/', include('recommendation_service.urls')),
    
    # GraphQL endpoint
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    
    # Health check
    path('health/', include('coko.health_urls')),
    
    # African-specific features (temporarily disabled)
    # path('african/', include('coko.african_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)