from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Configuration des URLs pour le service de lecture
app_name = 'reading_service'

urlpatterns = [
    # Sessions de lecture
    path('sessions/', views.ReadingSessionListCreateView.as_view(), name='session-list'),
    path('sessions/<uuid:pk>/', views.ReadingSessionDetailView.as_view(), name='session-detail'),
    path('sessions/<uuid:session_id>/complete/', views.complete_reading_session, name='session-complete'),
    
    # Progression de lecture
    path('progress/', views.ReadingProgressListCreateView.as_view(), name='progress-list'),
    path('progress/update/', views.update_reading_position, name='progress-update'),
    
    # Signets
    path('bookmarks/', views.BookmarkListCreateView.as_view(), name='bookmark-list'),
    path('bookmarks/<uuid:pk>/', views.BookmarkDetailView.as_view(), name='bookmark-detail'),
    
    # Objectifs de lecture
    path('goals/', views.ReadingGoalListCreateView.as_view(), name='goal-list'),
    path('goals/<uuid:pk>/', views.ReadingGoalDetailView.as_view(), name='goal-detail'),
    
    # Tableau de bord et statistiques
    path('dashboard/', views.ReadingDashboardView.as_view(), name='dashboard'),
    path('statistics/', views.ReadingStatisticsView.as_view(), name='statistics'),
    path('analytics/', views.ReadingAnalyticsView.as_view(), name='analytics'),
    
    # Recommandations
    path('recommendations/', views.reading_recommendations, name='recommendations'),
    
    # Santé du service
    path('health/', views.health_check, name='health-check'),
]