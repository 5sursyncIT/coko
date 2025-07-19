from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from .models import (
    Book, Author, Publisher, Category, Series, BookFile, 
    BookRating, BookTag, BookTagAssignment, BookCollection
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Administration des catégories"""
    
    list_display = ['name', 'parent', 'books_count', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Apparence', {
            'fields': ('icon', 'color')
        }),
        ('Paramètres', {
            'fields': ('is_active', 'sort_order')
        }),
    )
    
    def books_count(self, obj):
        """Nombre de livres dans la catégorie"""
        return obj.books.count()
    books_count.short_description = 'Livres'
    books_count.admin_order_field = 'books__count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            books_count=Count('books')
        )


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Administration des auteurs"""
    
    list_display = ['full_name', 'nationality', 'birth_date', 'books_count', 'created_at']
    list_filter = ['nationality', 'birth_date', 'created_at']
    search_fields = ['first_name', 'last_name', 'biography']
    prepopulated_fields = {'slug': ('first_name', 'last_name')}
    date_hierarchy = 'birth_date'
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'slug', 'biography')
        }),
        ('Dates', {
            'fields': ('birth_date', 'death_date')
        }),
        ('Autres informations', {
            'fields': ('nationality', 'photo', 'website')
        }),
    )
    
    def books_count(self, obj):
        """Nombre de livres de l'auteur"""
        return obj.books.count()
    books_count.short_description = 'Livres'
    books_count.admin_order_field = 'books__count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            books_count=Count('books')
        )


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Administration des éditeurs"""
    
    list_display = ['name', 'country', 'founded_year', 'books_count', 'created_at']
    list_filter = ['country', 'founded_year', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Localisation', {
            'fields': ('country', 'founded_year')
        }),
        ('Contact', {
            'fields': ('website', 'logo')
        }),
    )
    
    def books_count(self, obj):
        """Nombre de livres de l'éditeur"""
        return obj.books.count()
    books_count.short_description = 'Livres'
    books_count.admin_order_field = 'books__count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            books_count=Count('books')
        )


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    """Administration des séries"""
    
    list_display = ['title', 'total_books', 'books_count', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_completed']
    
    def books_count(self, obj):
        """Nombre de livres dans la série"""
        return obj.books.count()
    books_count.short_description = 'Livres publiés'
    books_count.admin_order_field = 'books__count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            books_count=Count('books')
        )


class BookFileInline(admin.TabularInline):
    """Inline pour les fichiers de livres"""
    model = BookFile
    extra = 1
    fields = ['format', 'file', 'file_size', 'is_active']
    readonly_fields = ['file_size']


class BookRatingInline(admin.TabularInline):
    """Inline pour les évaluations de livres"""
    model = BookRating
    extra = 0
    fields = ['user', 'score', 'review', 'created_at']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


class BookTagAssignmentInline(admin.TabularInline):
    """Inline pour les tags de livres"""
    model = BookTagAssignment
    extra = 1
    fields = ['tag', 'assigned_by', 'created_at']
    readonly_fields = ['assigned_by', 'created_at']
    
    def save_model(self, request, obj, form, change):
        if not obj.assigned_by:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Administration des livres"""
    
    list_display = [
        'title', 'authors_list', 'publisher', 'language', 'status', 
        'is_featured', 'is_free', 'average_rating', 'view_count', 'created_at'
    ]
    list_filter = [
        'status', 'language', 'is_featured', 'is_free', 'is_premium_only',
        'categories', 'publisher', 'created_at', 'publication_date'
    ]
    search_fields = ['title', 'subtitle', 'description', 'isbn', 'authors__first_name', 'authors__last_name']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['status', 'is_featured', 'is_free']
    date_hierarchy = 'publication_date'
    filter_horizontal = ['authors', 'categories']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'slug', 'subtitle', 'description', 'summary')
        }),
        ('Relations', {
            'fields': ('authors', 'publisher', 'categories', 'series', 'series_number')
        }),
        ('Détails du livre', {
            'fields': ('isbn', 'language', 'page_count', 'publication_date')
        }),
        ('Média', {
            'fields': ('cover_image',)
        }),
        ('Paramètres', {
            'fields': ('status', 'is_featured', 'is_free', 'is_premium_only')
        }),
        ('Statistiques', {
            'fields': ('view_count', 'download_count'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['view_count', 'download_count']
    inlines = [BookFileInline, BookRatingInline, BookTagAssignmentInline]
    
    actions = ['mark_as_published', 'mark_as_featured', 'mark_as_free']
    
    def authors_list(self, obj):
        """Liste des auteurs"""
        return ', '.join([author.full_name for author in obj.authors.all()])
    authors_list.short_description = 'Auteurs'
    
    def average_rating(self, obj):
        """Note moyenne"""
        avg = obj.ratings.aggregate(avg=Avg('score'))['avg']
        if avg:
            return f"{avg:.1f}/5"
        return "Pas de note"
    average_rating.short_description = 'Note moyenne'
    
    def cover_image_preview(self, obj):
        """Aperçu de la couverture"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.cover_image.url
            )
        return "Pas d'image"
    cover_image_preview.short_description = 'Aperçu'
    
    def mark_as_published(self, request, queryset):
        """Marquer comme publié"""
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} livre(s) marqué(s) comme publié(s).')
    mark_as_published.short_description = "Marquer comme publié"
    
    def mark_as_featured(self, request, queryset):
        """Marquer comme mis en avant"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} livre(s) marqué(s) comme mis en avant.')
    mark_as_featured.short_description = "Marquer comme mis en avant"
    
    def mark_as_free(self, request, queryset):
        """Marquer comme gratuit"""
        updated = queryset.update(is_free=True)
        self.message_user(request, f'{updated} livre(s) marqué(s) comme gratuit(s).')
    mark_as_free.short_description = "Marquer comme gratuit"
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'authors', 'categories', 'ratings'
        )


@admin.register(BookFile)
class BookFileAdmin(admin.ModelAdmin):
    """Administration des fichiers de livres"""
    
    list_display = ['book', 'format', 'file_size_mb', 'is_active', 'created_at']
    list_filter = ['format', 'is_active', 'created_at']
    search_fields = ['book__title']
    list_editable = ['is_active']
    
    def file_size_mb(self, obj):
        """Taille du fichier en MB"""
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "Inconnue"
    file_size_mb.short_description = 'Taille'


@admin.register(BookRating)
class BookRatingAdmin(admin.ModelAdmin):
    """Administration des évaluations"""
    
    list_display = ['book', 'user', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['book__title', 'user__username', 'review']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False


@admin.register(BookTag)
class BookTagAdmin(admin.ModelAdmin):
    """Administration des tags"""
    
    list_display = ['name', 'color', 'books_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['color']
    
    def books_count(self, obj):
        """Nombre de livres avec ce tag"""
        return obj.book_assignments.count()
    books_count.short_description = 'Livres'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('book_assignments')


@admin.register(BookCollection)
class BookCollectionAdmin(admin.ModelAdmin):
    """Administration des collections"""
    
    list_display = ['title', 'created_by', 'books_count', 'is_featured', 'is_public', 'created_at']
    list_filter = ['is_featured', 'is_public', 'created_at']
    search_fields = ['title', 'description', 'created_by__username']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_featured', 'is_public']
    filter_horizontal = ['books']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'slug', 'description', 'created_by')
        }),
        ('Livres', {
            'fields': ('books',)
        }),
        ('Paramètres', {
            'fields': ('is_featured', 'is_public', 'sort_order')
        }),
    )
    
    def books_count(self, obj):
        """Nombre de livres dans la collection"""
        return obj.books.count()
    books_count.short_description = 'Livres'
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Configuration de l'interface d'administration
admin.site.site_header = "Administration COKO - Catalogue"
admin.site.site_title = "COKO Catalogue"
admin.site.index_title = "Gestion du catalogue de livres"