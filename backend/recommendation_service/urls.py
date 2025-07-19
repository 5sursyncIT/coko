from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'recommendation_service'

# Router pour les ViewSets (si nécessaire)
router = DefaultRouter()

urlpatterns = [
    # Profils utilisateur
    path(
        'profiles/',
        views.UserProfileListCreateView.as_view(),
        name='user-profile-list'
    ),
    path(
        'profiles/<int:pk>/',
        views.UserProfileDetailView.as_view(),
        name='user-profile-detail'
    ),
    
    # Interactions utilisateur
    path(
        'interactions/',
        views.UserInteractionListCreateView.as_view(),
        name='user-interaction-list'
    ),
    
    # Ensembles de recommandations
    path(
        'recommendation-sets/',
        views.RecommendationSetListView.as_view(),
        name='recommendation-set-list'
    ),
    path(
        'recommendation-sets/<int:pk>/',
        views.RecommendationSetDetailView.as_view(),
        name='recommendation-set-detail'
    ),
    
    # Recommandations personnalisées
    path(
        'recommendations/',
        views.PersonalizedRecommendationsView.as_view(),
        name='personalized-recommendations'
    ),
    
    # Livres similaires
    path(
        'books/<int:book_id>/similar/',
        views.SimilarBooksView.as_view(),
        name='similar-books'
    ),
    
    # Livres en tendance
    path(
        'trending/',
        views.TrendingBooksView.as_view(),
        name='trending-books'
    ),
    
    # Feedbacks de recommandations
    path(
        'feedback/',
        views.RecommendationFeedbackListCreateView.as_view(),
        name='recommendation-feedback-list'
    ),
    
    # Interactions avec les recommandations
    path(
        'recommendations/<int:recommendation_id>/interact/',
        views.RecommendationInteractionView.as_view(),
        name='recommendation-interaction'
    ),
    
    # Statistiques et analytics
    path(
        'stats/',
        views.RecommendationStatsView.as_view(),
        name='recommendation-stats'
    ),
    path(
        'analytics/',
        views.RecommendationAnalyticsView.as_view(),
        name='recommendation-analytics'
    ),
    
    # Configuration du moteur (admin)
    path(
        'config/',
        views.RecommendationEngineConfigView.as_view(),
        name='recommendation-engine-config'
    ),
    
    # Contrôle de santé
    path(
        'health/',
        views.health_check,
        name='health-check'
    ),
    
    # Inclure les routes du router
    path('', include(router.urls)),
]