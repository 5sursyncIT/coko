from rest_framework import serializers
from django.db.models import Avg, Count
from .models import (
    Book, Author, Publisher, Category, Series, BookFile, 
    BookRating, BookTag, BookTagAssignment, BookCollection
)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer pour les catégories"""
    
    books_count = serializers.ReadOnlyField()
    full_path = serializers.ReadOnlyField()
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'icon', 'color',
            'is_active', 'sort_order', 'books_count', 'full_path', 'subcategories',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subcategories(self, obj):
        """Retourne les sous-catégories"""
        if hasattr(obj, 'subcategories'):
            return CategorySerializer(obj.subcategories.filter(is_active=True), many=True).data
        return []


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer pour les auteurs"""
    
    full_name = serializers.ReadOnlyField()
    books_count = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Author
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'slug', 'biography',
            'birth_date', 'death_date', 'nationality', 'photo', 'website',
            'books_count', 'age', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer pour les éditeurs"""
    
    books_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Publisher
        fields = [
            'id', 'name', 'slug', 'description', 'founded_year', 'country',
            'website', 'logo', 'books_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SeriesSerializer(serializers.ModelSerializer):
    """Serializer pour les séries"""
    
    books_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Series
        fields = [
            'id', 'title', 'slug', 'description', 'total_books', 'is_completed',
            'books_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BookFileSerializer(serializers.ModelSerializer):
    """Serializer pour les fichiers de livres"""
    
    file_size_mb = serializers.ReadOnlyField()
    
    class Meta:
        model = BookFile
        fields = [
            'id', 'format', 'file', 'file_size', 'file_size_mb', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_size', 'created_at', 'updated_at']


class BookRatingSerializer(serializers.ModelSerializer):
    """Serializer pour les évaluations de livres"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = BookRating
        fields = [
            'id', 'book', 'user', 'user_username', 'user_full_name', 'score', 
            'review', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_score(self, value):
        """Validation de la note"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("La note doit être comprise entre 1 et 5")
        return value


class BookTagSerializer(serializers.ModelSerializer):
    """Serializer pour les tags"""
    
    books_count = serializers.ReadOnlyField()
    
    class Meta:
        model = BookTag
        fields = [
            'id', 'name', 'slug', 'color', 'books_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BookListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des livres (vue simplifiée)"""
    
    authors_list = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    ratings_count = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    categories = CategorySerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'slug', 'subtitle', 'summary', 'authors_list',
            'publisher', 'categories', 'language', 'publication_date',
            'cover_image', 'status', 'is_featured', 'is_free', 'is_premium_only',
            'average_rating', 'ratings_count', 'view_count', 'is_available',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'view_count', 'created_at', 'updated_at'
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un livre"""
    
    authors = AuthorSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    series = SeriesSerializer(read_only=True)
    book_files = BookFileSerializer(many=True, read_only=True)
    ratings = BookRatingSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()
    
    # Propriétés calculées
    full_title = serializers.ReadOnlyField()
    authors_list = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    ratings_count = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    
    # Statistiques
    rating_distribution = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'slug', 'subtitle', 'description', 'summary',
            'full_title', 'authors', 'authors_list', 'publisher', 'categories',
            'series', 'isbn', 'language', 'page_count', 'publication_date',
            'series_number', 'cover_image', 'status', 'is_featured', 'is_free',
            'is_premium_only', 'view_count', 'download_count', 'book_files',
            'ratings', 'tags', 'average_rating', 'ratings_count', 'is_available',
            'rating_distribution', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'view_count', 'download_count', 'created_at', 'updated_at'
        ]
    
    def get_tags(self, obj):
        """Retourne les tags du livre"""
        tag_assignments = obj.tag_assignments.select_related('tag')
        return BookTagSerializer([ta.tag for ta in tag_assignments], many=True).data
    
    def get_rating_distribution(self, obj):
        """Retourne la distribution des notes"""
        ratings = obj.ratings.values('score').annotate(count=Count('score')).order_by('score')
        distribution = {str(i): 0 for i in range(1, 6)}
        for rating in ratings:
            distribution[str(rating['score'])] = rating['count']
        return distribution


class BookCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la création et modification de livres"""
    
    author_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True
    )
    category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True
    )
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Book
        fields = [
            'title', 'slug', 'subtitle', 'description', 'summary',
            'publisher', 'series', 'isbn', 'language', 'page_count',
            'publication_date', 'series_number', 'cover_image', 'status',
            'is_featured', 'is_free', 'is_premium_only', 'author_ids',
            'category_ids', 'tag_names'
        ]
    
    def validate_author_ids(self, value):
        """Validation des IDs d'auteurs"""
        if not value:
            raise serializers.ValidationError("Au moins un auteur est requis")
        
        existing_authors = Author.objects.filter(id__in=value)
        if len(existing_authors) != len(value):
            raise serializers.ValidationError("Un ou plusieurs auteurs n'existent pas")
        
        return value
    
    def validate_category_ids(self, value):
        """Validation des IDs de catégories"""
        if not value:
            raise serializers.ValidationError("Au moins une catégorie est requise")
        
        existing_categories = Category.objects.filter(id__in=value, is_active=True)
        if len(existing_categories) != len(value):
            raise serializers.ValidationError("Une ou plusieurs catégories n'existent pas ou sont inactives")
        
        return value
    
    def create(self, validated_data):
        """Création d'un livre avec relations"""
        author_ids = validated_data.pop('author_ids')
        category_ids = validated_data.pop('category_ids')
        tag_names = validated_data.pop('tag_names', [])
        
        book = Book.objects.create(**validated_data)
        
        # Assigner les auteurs
        book.authors.set(author_ids)
        
        # Assigner les catégories
        book.categories.set(category_ids)
        
        # Créer et assigner les tags
        if tag_names:
            self._assign_tags(book, tag_names)
        
        return book
    
    def update(self, instance, validated_data):
        """Mise à jour d'un livre avec relations"""
        author_ids = validated_data.pop('author_ids', None)
        category_ids = validated_data.pop('category_ids', None)
        tag_names = validated_data.pop('tag_names', None)
        
        # Mettre à jour les champs du livre
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mettre à jour les relations
        if author_ids is not None:
            instance.authors.set(author_ids)
        
        if category_ids is not None:
            instance.categories.set(category_ids)
        
        if tag_names is not None:
            # Supprimer les anciens tags et assigner les nouveaux
            instance.tag_assignments.all().delete()
            self._assign_tags(instance, tag_names)
        
        return instance
    
    def _assign_tags(self, book, tag_names):
        """Assigne les tags au livre"""
        for tag_name in tag_names:
            tag, created = BookTag.objects.get_or_create(
                name=tag_name.strip().lower(),
                defaults={'slug': tag_name.strip().lower().replace(' ', '-')}
            )
            BookTagAssignment.objects.get_or_create(
                book=book,
                tag=tag,
                defaults={'assigned_by': self.context.get('request').user if self.context.get('request') else None}
            )


class BookCollectionSerializer(serializers.ModelSerializer):
    """Serializer pour les collections de livres"""
    
    books_count = serializers.ReadOnlyField()
    books = BookListSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = BookCollection
        fields = [
            'id', 'title', 'slug', 'description', 'books', 'books_count',
            'is_featured', 'is_public', 'sort_order', 'created_by',
            'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class BookSearchSerializer(serializers.Serializer):
    """Serializer pour les paramètres de recherche de livres"""
    
    q = serializers.CharField(required=False, help_text="Terme de recherche")
    category = serializers.UUIDField(required=False, help_text="ID de catégorie")
    author = serializers.UUIDField(required=False, help_text="ID d'auteur")
    publisher = serializers.UUIDField(required=False, help_text="ID d'éditeur")
    series = serializers.UUIDField(required=False, help_text="ID de série")
    language = serializers.CharField(required=False, help_text="Code de langue")
    is_free = serializers.BooleanField(required=False, help_text="Livres gratuits uniquement")
    is_featured = serializers.BooleanField(required=False, help_text="Livres mis en avant uniquement")
    min_rating = serializers.FloatField(required=False, min_value=0, max_value=5, help_text="Note minimale")
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Liste de tags"
    )
    ordering = serializers.ChoiceField(
        choices=[
            'title', '-title', 'publication_date', '-publication_date',
            'created_at', '-created_at', 'view_count', '-view_count',
            'average_rating', '-average_rating'
        ],
        required=False,
        default='-created_at',
        help_text="Ordre de tri"
    )


class BookStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de livres"""
    
    total_books = serializers.IntegerField()
    published_books = serializers.IntegerField()
    featured_books = serializers.IntegerField()
    free_books = serializers.IntegerField()
    premium_books = serializers.IntegerField()
    total_authors = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    total_publishers = serializers.IntegerField()
    total_downloads = serializers.IntegerField()
    total_views = serializers.IntegerField()
    average_rating = serializers.FloatField()
    most_popular_books = BookListSerializer(many=True)
    recent_books = BookListSerializer(many=True)
    top_rated_books = BookListSerializer(many=True)