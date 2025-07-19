from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, F, Prefetch
from django.utils import timezone
from django.core.cache import cache
from django.http import Http404
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
import logging

from .models import (
    Book, Author, Publisher, Category, Series, BookFile, 
    BookRating, BookTag, BookTagAssignment, BookCollection
)
from .serializers import (
    BookListSerializer, BookDetailSerializer, BookCreateUpdateSerializer,
    AuthorSerializer, PublisherSerializer, CategorySerializer, SeriesSerializer,
    BookFileSerializer, BookRatingSerializer, BookTagSerializer,
    BookCollectionSerializer, BookSearchSerializer, BookStatsSerializer
)
from .filters import BookFilter
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination standard pour les résultats"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BookListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des livres"""
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BookFilter
    search_fields = ['title', 'subtitle', 'description', 'authors__first_name', 'authors__last_name']
    ordering_fields = ['title', 'publication_date', 'created_at', 'view_count', 'average_rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourne la queryset optimisée"""
        return Book.objects.select_related(
            'publisher', 'series'
        ).prefetch_related(
            'authors', 'categories', 'book_files',
            Prefetch('ratings', queryset=BookRating.objects.select_related('user'))
        ).annotate(
            average_rating=Avg('ratings__score'),
            ratings_count=Count('ratings')
        ).filter(status='published')
    
    def get_serializer_class(self):
        """Retourne le serializer approprié"""
        if self.request.method == 'POST':
            return BookCreateUpdateSerializer
        return BookListSerializer
    
    def perform_create(self, serializer):
        """Sauvegarde avec l'utilisateur actuel"""
        serializer.save()
        logger.info(f"Nouveau livre créé: {serializer.instance.title} par {self.request.user}")


class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour les détails d'un livre"""
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Retourne la queryset optimisée"""
        return Book.objects.select_related(
            'publisher', 'series'
        ).prefetch_related(
            'authors', 'categories', 'book_files',
            Prefetch('ratings', queryset=BookRating.objects.select_related('user')),
            Prefetch('tag_assignments', queryset=BookTagAssignment.objects.select_related('tag'))
        ).annotate(
            average_rating=Avg('ratings__score'),
            ratings_count=Count('ratings')
        )
    
    def get_serializer_class(self):
        """Retourne le serializer approprié"""
        if self.request.method in ['PUT', 'PATCH']:
            return BookCreateUpdateSerializer
        return BookDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Récupère un livre et incrémente le compteur de vues"""
        instance = self.get_object()
        
        # Incrémenter le compteur de vues (avec cache pour éviter les requêtes multiples)
        cache_key = f"book_view_{instance.id}_{request.META.get('REMOTE_ADDR', 'unknown')}"
        if not cache.get(cache_key):
            Book.objects.filter(id=instance.id).update(view_count=F('view_count') + 1)
            cache.set(cache_key, True, 300)  # 5 minutes
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_update(self, serializer):
        """Sauvegarde avec log"""
        serializer.save()
        logger.info(f"Livre modifié: {serializer.instance.title} par {self.request.user}")
    
    def perform_destroy(self, instance):
        """Suppression avec log"""
        title = instance.title
        instance.delete()
        logger.info(f"Livre supprimé: {title} par {self.request.user}")


class BookSearchView(generics.ListAPIView):
    """Vue pour la recherche avancée de livres"""
    
    serializer_class = BookListSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retourne la queryset filtrée selon les paramètres de recherche"""
        serializer = BookSearchSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        
        queryset = Book.objects.select_related(
            'publisher', 'series'
        ).prefetch_related(
            'authors', 'categories'
        ).annotate(
            average_rating=Avg('ratings__score'),
            ratings_count=Count('ratings')
        ).filter(status='published')
        
        # Filtres de recherche
        filters = serializer.validated_data
        
        if filters.get('q'):
            query = filters['q']
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(subtitle__icontains=query) |
                Q(description__icontains=query) |
                Q(authors__first_name__icontains=query) |
                Q(authors__last_name__icontains=query)
            ).distinct()
        
        if filters.get('category'):
            queryset = queryset.filter(categories=filters['category'])
        
        if filters.get('author'):
            queryset = queryset.filter(authors=filters['author'])
        
        if filters.get('publisher'):
            queryset = queryset.filter(publisher=filters['publisher'])
        
        if filters.get('series'):
            queryset = queryset.filter(series=filters['series'])
        
        if filters.get('language'):
            queryset = queryset.filter(language=filters['language'])
        
        if filters.get('is_free') is not None:
            queryset = queryset.filter(is_free=filters['is_free'])
        
        if filters.get('is_featured') is not None:
            queryset = queryset.filter(is_featured=filters['is_featured'])
        
        if filters.get('min_rating'):
            queryset = queryset.filter(average_rating__gte=filters['min_rating'])
        
        if filters.get('tags'):
            for tag in filters['tags']:
                queryset = queryset.filter(tag_assignments__tag__name__icontains=tag)
        
        # Tri
        ordering = filters.get('ordering', '-created_at')
        if ordering == 'average_rating':
            queryset = queryset.order_by(F('average_rating').desc(nulls_last=True))
        elif ordering == '-average_rating':
            queryset = queryset.order_by(F('average_rating').asc(nulls_last=True))
        else:
            queryset = queryset.order_by(ordering)
        
        return queryset


class AuthorListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des auteurs"""
    
    queryset = Author.objects.annotate(
        books_count=Count('books')
    ).order_by('last_name', 'first_name')
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'biography']
    ordering_fields = ['first_name', 'last_name', 'birth_date', 'books_count']


class AuthorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour les détails d'un auteur"""
    
    queryset = Author.objects.annotate(
        books_count=Count('books')
    )
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class PublisherListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des éditeurs"""
    
    queryset = Publisher.objects.annotate(
        books_count=Count('books')
    ).order_by('name')
    serializer_class = PublisherSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'founded_year', 'books_count']


class PublisherDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour les détails d'un éditeur"""
    
    queryset = Publisher.objects.annotate(
        books_count=Count('books')
    )
    serializer_class = PublisherSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class CategoryListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des catégories"""
    
    queryset = Category.objects.filter(is_active=True).annotate(
        books_count=Count('books')
    ).order_by('sort_order', 'name')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour les détails d'une catégorie"""
    
    queryset = Category.objects.filter(is_active=True).annotate(
        books_count=Count('books')
    )
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class SeriesListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des séries"""
    
    queryset = Series.objects.annotate(
        books_count=Count('books')
    ).order_by('title')
    serializer_class = SeriesSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'total_books', 'books_count']


class SeriesDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour les détails d'une série"""
    
    queryset = Series.objects.annotate(
        books_count=Count('books')
    )
    serializer_class = SeriesSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'


class BookRatingListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des évaluations de livres"""
    
    serializer_class = BookRatingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Retourne les évaluations du livre"""
        book_slug = self.kwargs.get('book_slug')
        book = get_object_or_404(Book, slug=book_slug)
        return BookRating.objects.filter(book=book).select_related('user').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Sauvegarde avec l'utilisateur et le livre"""
        book_slug = self.kwargs.get('book_slug')
        book = get_object_or_404(Book, slug=book_slug)
        
        # Vérifier si l'utilisateur a déjà évalué ce livre
        existing_rating = BookRating.objects.filter(
            book=book, user=self.request.user
        ).first()
        
        if existing_rating:
            # Mettre à jour l'évaluation existante
            for attr, value in serializer.validated_data.items():
                setattr(existing_rating, attr, value)
            existing_rating.save()
            serializer.instance = existing_rating
        else:
            # Créer une nouvelle évaluation
            serializer.save(user=self.request.user, book=book)
        
        logger.info(f"Évaluation créée/mise à jour pour {book.title} par {self.request.user}")


class BookRatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour les détails d'une évaluation"""
    
    serializer_class = BookRatingSerializer
    permission_classes = [IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retourne les évaluations du livre"""
        book_slug = self.kwargs.get('book_slug')
        book = get_object_or_404(Book, slug=book_slug)
        return BookRating.objects.filter(book=book).select_related('user')


class BookCollectionListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des collections"""
    
    serializer_class = BookCollectionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at', 'books_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourne les collections publiques et celles de l'utilisateur"""
        if self.request.user.is_authenticated:
            return BookCollection.objects.filter(
                Q(is_public=True) | Q(created_by=self.request.user)
            ).annotate(
                books_count=Count('books')
            ).prefetch_related('books')
        else:
            return BookCollection.objects.filter(
                is_public=True
            ).annotate(
                books_count=Count('books')
            ).prefetch_related('books')
    
    def perform_create(self, serializer):
        """Sauvegarde avec l'utilisateur actuel"""
        serializer.save(created_by=self.request.user)


class BookCollectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour les détails d'une collection"""
    
    serializer_class = BookCollectionSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Retourne les collections accessibles"""
        if self.request.user.is_authenticated:
            return BookCollection.objects.filter(
                Q(is_public=True) | Q(created_by=self.request.user)
            ).annotate(
                books_count=Count('books')
            ).prefetch_related('books')
        else:
            return BookCollection.objects.filter(
                is_public=True
            ).annotate(
                books_count=Count('books')
            ).prefetch_related('books')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_book_to_collection(request, collection_slug, book_slug):
    """Ajoute un livre à une collection"""
    collection = get_object_or_404(
        BookCollection, 
        slug=collection_slug, 
        created_by=request.user
    )
    book = get_object_or_404(Book, slug=book_slug)
    
    collection.books.add(book)
    
    return Response(
        {'message': f'Livre "{book.title}" ajouté à la collection "{collection.title}"'},
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_book_from_collection(request, collection_slug, book_slug):
    """Retire un livre d'une collection"""
    collection = get_object_or_404(
        BookCollection, 
        slug=collection_slug, 
        created_by=request.user
    )
    book = get_object_or_404(Book, slug=book_slug)
    
    collection.books.remove(book)
    
    return Response(
        {'message': f'Livre "{book.title}" retiré de la collection "{collection.title}"'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
def book_stats(request):
    """Retourne les statistiques des livres"""
    cache_key = 'book_stats'
    stats = cache.get(cache_key)
    
    if not stats:
        # Calculer les statistiques
        total_books = Book.objects.count()
        published_books = Book.objects.filter(status='published').count()
        featured_books = Book.objects.filter(is_featured=True).count()
        free_books = Book.objects.filter(is_free=True).count()
        premium_books = Book.objects.filter(is_premium_only=True).count()
        
        total_authors = Author.objects.count()
        total_categories = Category.objects.filter(is_active=True).count()
        total_publishers = Publisher.objects.count()
        
        total_downloads = Book.objects.aggregate(
            total=models.Sum('download_count')
        )['total'] or 0
        
        total_views = Book.objects.aggregate(
            total=models.Sum('view_count')
        )['total'] or 0
        
        average_rating = BookRating.objects.aggregate(
            avg=Avg('score')
        )['avg'] or 0
        
        # Livres populaires
        most_popular_books = Book.objects.filter(
            status='published'
        ).order_by('-view_count')[:5]
        
        # Livres récents
        recent_books = Book.objects.filter(
            status='published'
        ).order_by('-created_at')[:5]
        
        # Livres les mieux notés
        top_rated_books = Book.objects.filter(
            status='published'
        ).annotate(
            avg_rating=Avg('ratings__score')
        ).order_by('-avg_rating')[:5]
        
        stats = {
            'total_books': total_books,
            'published_books': published_books,
            'featured_books': featured_books,
            'free_books': free_books,
            'premium_books': premium_books,
            'total_authors': total_authors,
            'total_categories': total_categories,
            'total_publishers': total_publishers,
            'total_downloads': total_downloads,
            'total_views': total_views,
            'average_rating': round(average_rating, 2),
            'most_popular_books': BookListSerializer(most_popular_books, many=True).data,
            'recent_books': BookListSerializer(recent_books, many=True).data,
            'top_rated_books': BookListSerializer(top_rated_books, many=True).data,
        }
        
        # Mettre en cache pour 1 heure
        cache.set(cache_key, stats, 3600)
    
    serializer = BookStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
def health_check(request):
    """Vérification de santé du service"""
    try:
        # Vérifier la base de données
        book_count = Book.objects.count()
        
        return Response({
            'status': 'healthy',
            'service': 'catalog_service',
            'timestamp': timezone.now(),
            'database': 'connected',
            'books_count': book_count
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'service': 'catalog_service',
            'timestamp': timezone.now(),
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)