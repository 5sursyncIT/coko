from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'catalog'

# URLs pour les livres
book_patterns = [
    path('', views.BookListCreateView.as_view(), name='book-list'),
    path('search/', views.BookSearchView.as_view(), name='book-search'),
    path('stats/', views.book_stats, name='book-stats'),
    path('<slug:slug>/', views.BookDetailView.as_view(), name='book-detail'),
    path('<slug:book_slug>/ratings/', views.BookRatingListCreateView.as_view(), name='book-rating-list'),
    path('<slug:book_slug>/ratings/<int:pk>/', views.BookRatingDetailView.as_view(), name='book-rating-detail'),
]

# URLs pour les auteurs
author_patterns = [
    path('', views.AuthorListCreateView.as_view(), name='author-list'),
    path('<slug:slug>/', views.AuthorDetailView.as_view(), name='author-detail'),
]

# URLs pour les éditeurs
publisher_patterns = [
    path('', views.PublisherListCreateView.as_view(), name='publisher-list'),
    path('<slug:slug>/', views.PublisherDetailView.as_view(), name='publisher-detail'),
]

# URLs pour les catégories
category_patterns = [
    path('', views.CategoryListCreateView.as_view(), name='category-list'),
    path('<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
]

# URLs pour les séries
series_patterns = [
    path('', views.SeriesListCreateView.as_view(), name='series-list'),
    path('<slug:slug>/', views.SeriesDetailView.as_view(), name='series-detail'),
]

# URLs pour les collections
collection_patterns = [
    path('', views.BookCollectionListCreateView.as_view(), name='collection-list'),
    path('<slug:slug>/', views.BookCollectionDetailView.as_view(), name='collection-detail'),
    path('<slug:collection_slug>/books/<slug:book_slug>/add/', 
         views.add_book_to_collection, name='collection-add-book'),
    path('<slug:collection_slug>/books/<slug:book_slug>/remove/', 
         views.remove_book_from_collection, name='collection-remove-book'),
]

# URLs principales
urlpatterns = [
    # Livres
    path('books/', include(book_patterns)),
    
    # Auteurs
    path('authors/', include(author_patterns)),
    
    # Éditeurs
    path('publishers/', include(publisher_patterns)),
    
    # Catégories
    path('categories/', include(category_patterns)),
    
    # Séries
    path('series/', include(series_patterns)),
    
    # Collections
    path('collections/', include(collection_patterns)),
    
    # Santé du service
    path('health/', views.health_check, name='health-check'),
]