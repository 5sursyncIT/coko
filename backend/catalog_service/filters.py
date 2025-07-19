import django_filters
from django.db.models import Q
from .models import Book, Author, Publisher, Category, Series


class BookFilter(django_filters.FilterSet):
    """Filtres pour les livres"""
    
    # Filtres de recherche
    title = django_filters.CharFilter(lookup_expr='icontains')
    author = django_filters.ModelChoiceFilter(
        queryset=Author.objects.all(),
        field_name='authors'
    )
    publisher = django_filters.ModelChoiceFilter(
        queryset=Publisher.objects.all()
    )
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True),
        field_name='categories'
    )
    series = django_filters.ModelChoiceFilter(
        queryset=Series.objects.all()
    )
    
    # Filtres par langue
    language = django_filters.ChoiceFilter(
        choices=Book.LANGUAGE_CHOICES
    )
    
    # Filtres booléens
    is_free = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()
    is_premium_only = django_filters.BooleanFilter()
    
    # Filtres de date
    publication_date_after = django_filters.DateFilter(
        field_name='publication_date',
        lookup_expr='gte'
    )
    publication_date_before = django_filters.DateFilter(
        field_name='publication_date',
        lookup_expr='lte'
    )
    
    # Filtres de plage
    page_count_min = django_filters.NumberFilter(
        field_name='page_count',
        lookup_expr='gte'
    )
    page_count_max = django_filters.NumberFilter(
        field_name='page_count',
        lookup_expr='lte'
    )
    
    # Filtre de recherche globale
    search = django_filters.CharFilter(
        method='filter_search',
        label='Recherche globale'
    )
    
    # Filtre par tags
    tags = django_filters.CharFilter(
        method='filter_tags',
        label='Tags (séparés par des virgules)'
    )
    
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'publisher', 'category', 'series',
            'language', 'is_free', 'is_featured', 'is_premium_only',
            'publication_date_after', 'publication_date_before',
            'page_count_min', 'page_count_max', 'search', 'tags'
        ]
    
    def filter_search(self, queryset, name, value):
        """Filtre de recherche globale"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(subtitle__icontains=value) |
            Q(description__icontains=value) |
            Q(summary__icontains=value) |
            Q(authors__first_name__icontains=value) |
            Q(authors__last_name__icontains=value) |
            Q(publisher__name__icontains=value) |
            Q(categories__name__icontains=value) |
            Q(series__title__icontains=value)
        ).distinct()
    
    def filter_tags(self, queryset, name, value):
        """Filtre par tags"""
        if not value:
            return queryset
        
        tags = [tag.strip() for tag in value.split(',') if tag.strip()]
        if not tags:
            return queryset
        
        for tag in tags:
            queryset = queryset.filter(
                tag_assignments__tag__name__icontains=tag
            )
        
        return queryset.distinct()


class AuthorFilter(django_filters.FilterSet):
    """Filtres pour les auteurs"""
    
    name = django_filters.CharFilter(
        method='filter_name',
        label='Nom complet'
    )
    nationality = django_filters.CharFilter(lookup_expr='icontains')
    birth_year = django_filters.NumberFilter(
        field_name='birth_date',
        lookup_expr='year'
    )
    
    class Meta:
        model = Author
        fields = ['name', 'nationality', 'birth_year']
    
    def filter_name(self, queryset, name, value):
        """Filtre par nom complet"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value)
        )


class PublisherFilter(django_filters.FilterSet):
    """Filtres pour les éditeurs"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    country = django_filters.CharFilter(lookup_expr='icontains')
    founded_year = django_filters.NumberFilter()
    founded_after = django_filters.NumberFilter(
        field_name='founded_year',
        lookup_expr='gte'
    )
    founded_before = django_filters.NumberFilter(
        field_name='founded_year',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Publisher
        fields = ['name', 'country', 'founded_year', 'founded_after', 'founded_before']


class CategoryFilter(django_filters.FilterSet):
    """Filtres pour les catégories"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True)
    )
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = Category
        fields = ['name', 'parent', 'is_active']


class SeriesFilter(django_filters.FilterSet):
    """Filtres pour les séries"""
    
    title = django_filters.CharFilter(lookup_expr='icontains')
    is_completed = django_filters.BooleanFilter()
    total_books_min = django_filters.NumberFilter(
        field_name='total_books',
        lookup_expr='gte'
    )
    total_books_max = django_filters.NumberFilter(
        field_name='total_books',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Series
        fields = ['title', 'is_completed', 'total_books_min', 'total_books_max']