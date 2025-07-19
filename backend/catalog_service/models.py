from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
import uuid
import os

User = get_user_model()


def book_cover_upload_path(instance, filename):
    """Génère le chemin de téléchargement pour les couvertures de livres"""
    ext = filename.split('.')[-1]
    filename = f"{instance.id}.{ext}"
    return os.path.join('books', 'covers', filename)


def book_file_upload_path(instance, filename):
    """Génère le chemin de téléchargement pour les fichiers de livres"""
    ext = filename.split('.')[-1]
    filename = f"{instance.book.id}_{instance.format}.{ext}"
    return os.path.join('books', 'files', filename)


class Category(models.Model):
    """Modèle pour les catégories de livres"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    slug = models.SlugField(max_length=120, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='subcategories',
        verbose_name="Catégorie parente"
    )
    icon = models.CharField(max_length=50, blank=True, verbose_name="Icône")
    color = models.CharField(max_length=7, default='#007bff', verbose_name="Couleur")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordre de tri")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})
    
    @property
    def full_path(self):
        """Retourne le chemin complet de la catégorie"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
    
    @property
    def books_count(self):
        """Retourne le nombre de livres dans cette catégorie et ses sous-catégories"""
        from django.db.models import Q
        return Book.objects.filter(
            Q(categories=self) | Q(categories__parent=self)
        ).distinct().count()


class Author(models.Model):
    """Modèle pour les auteurs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(max_length=220, unique=True, verbose_name="Slug")
    biography = models.TextField(blank=True, verbose_name="Biographie")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    death_date = models.DateField(null=True, blank=True, verbose_name="Date de décès")
    nationality = models.CharField(max_length=100, blank=True, verbose_name="Nationalité")
    photo = models.ImageField(
        upload_to='authors/photos/', 
        null=True, 
        blank=True, 
        verbose_name="Photo"
    )
    website = models.URLField(blank=True, verbose_name="Site web")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return self.full_name
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_absolute_url(self):
        return reverse('catalog:author_detail', kwargs={'slug': self.slug})
    
    @property
    def books_count(self):
        """Retourne le nombre de livres de cet auteur"""
        return self.books.count()
    
    @property
    def age(self):
        """Retourne l'âge de l'auteur ou None s'il est décédé"""
        if self.birth_date:
            end_date = self.death_date or timezone.now().date()
            return (end_date - self.birth_date).days // 365
        return None


class Publisher(models.Model):
    """Modèle pour les éditeurs"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True, verbose_name="Nom")
    slug = models.SlugField(max_length=220, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    founded_year = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Année de fondation"
    )
    country = models.CharField(max_length=100, blank=True, verbose_name="Pays")
    website = models.URLField(blank=True, verbose_name="Site web")
    logo = models.ImageField(
        upload_to='publishers/logos/', 
        null=True, 
        blank=True, 
        verbose_name="Logo"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Éditeur"
        verbose_name_plural = "Éditeurs"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('catalog:publisher_detail', kwargs={'slug': self.slug})
    
    @property
    def books_count(self):
        """Retourne le nombre de livres de cet éditeur"""
        return self.books.count()


class Series(models.Model):
    """Modèle pour les séries de livres"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=220, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    total_books = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Nombre total de livres"
    )
    is_completed = models.BooleanField(default=False, verbose_name="Série terminée")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Série"
        verbose_name_plural = "Séries"
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('catalog:series_detail', kwargs={'slug': self.slug})
    
    @property
    def books_count(self):
        """Retourne le nombre de livres actuels dans la série"""
        return self.books.count()


class Book(models.Model):
    """Modèle principal pour les livres"""
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
        ('coming_soon', 'Bientôt disponible'),
    ]
    
    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'Anglais'),
        ('es', 'Espagnol'),
        ('de', 'Allemand'),
        ('it', 'Italien'),
        ('pt', 'Portugais'),
        ('other', 'Autre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300, verbose_name="Titre")
    slug = models.SlugField(max_length=320, unique=True, verbose_name="Slug")
    subtitle = models.CharField(max_length=300, blank=True, verbose_name="Sous-titre")
    description = models.TextField(verbose_name="Description")
    summary = models.TextField(blank=True, verbose_name="Résumé court")
    
    # Relations
    authors = models.ManyToManyField(
        Author, 
        related_name='books', 
        verbose_name="Auteurs"
    )
    publisher = models.ForeignKey(
        Publisher, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='books',
        verbose_name="Éditeur"
    )
    categories = models.ManyToManyField(
        Category, 
        related_name='books', 
        verbose_name="Catégories"
    )
    series = models.ForeignKey(
        Series, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='books',
        verbose_name="Série"
    )
    
    # Métadonnées
    isbn = models.CharField(max_length=17, unique=True, null=True, blank=True, verbose_name="ISBN")
    language = models.CharField(
        max_length=10, 
        choices=LANGUAGE_CHOICES, 
        default='fr', 
        verbose_name="Langue"
    )
    page_count = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Nombre de pages"
    )
    publication_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Date de publication"
    )
    series_number = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Numéro dans la série"
    )
    
    # Contenu
    cover_image = models.ImageField(
        upload_to=book_cover_upload_path, 
        null=True, 
        blank=True, 
        verbose_name="Couverture"
    )
    
    # Statut et visibilité
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft', 
        verbose_name="Statut"
    )
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    is_free = models.BooleanField(default=False, verbose_name="Gratuit")
    is_premium_only = models.BooleanField(default=False, verbose_name="Premium uniquement")
    
    # Statistiques
    view_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de vues")
    download_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de téléchargements")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Publié le")
    
    class Meta:
        verbose_name = "Livre"
        verbose_name_plural = "Livres"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['publication_date']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('catalog:book_detail', kwargs={'slug': self.slug})
    
    @property
    def full_title(self):
        """Retourne le titre complet avec sous-titre"""
        if self.subtitle:
            return f"{self.title}: {self.subtitle}"
        return self.title
    
    @property
    def authors_list(self):
        """Retourne la liste des auteurs sous forme de chaîne"""
        return ", ".join([author.full_name for author in self.authors.all()])
    
    @property
    def average_rating(self):
        """Retourne la note moyenne du livre"""
        ratings = self.ratings.all()
        if ratings:
            return sum(rating.score for rating in ratings) / len(ratings)
        return 0
    
    @property
    def ratings_count(self):
        """Retourne le nombre d'évaluations"""
        return self.ratings.count()
    
    @property
    def is_available(self):
        """Vérifie si le livre est disponible"""
        return self.status == 'published' and self.book_files.exists()
    
    def increment_view_count(self):
        """Incrémente le compteur de vues"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_download_count(self):
        """Incrémente le compteur de téléchargements"""
        self.download_count += 1
        self.save(update_fields=['download_count'])


class BookFile(models.Model):
    """Modèle pour les fichiers de livres dans différents formats"""
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('epub', 'EPUB'),
        ('mobi', 'MOBI'),
        ('azw3', 'AZW3'),
        ('txt', 'TXT'),
        ('html', 'HTML'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(
        Book, 
        on_delete=models.CASCADE, 
        related_name='book_files',
        verbose_name="Livre"
    )
    format = models.CharField(
        max_length=10, 
        choices=FORMAT_CHOICES, 
        verbose_name="Format"
    )
    file = models.FileField(
        upload_to=book_file_upload_path, 
        verbose_name="Fichier"
    )
    file_size = models.PositiveBigIntegerField(
        null=True, 
        blank=True, 
        verbose_name="Taille du fichier (bytes)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Fichier de livre"
        verbose_name_plural = "Fichiers de livres"
        unique_together = ['book', 'format']
        ordering = ['format']
    
    def __str__(self):
        return f"{self.book.title} - {self.format.upper()}"
    
    @property
    def file_size_mb(self):
        """Retourne la taille du fichier en MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec calcul automatique de la taille"""
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class BookRating(models.Model):
    """Modèle pour les évaluations de livres"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(
        Book, 
        on_delete=models.CASCADE, 
        related_name='ratings',
        verbose_name="Livre"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='book_ratings',
        verbose_name="Utilisateur"
    )
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note"
    )
    review = models.TextField(blank=True, verbose_name="Commentaire")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        unique_together = ['book', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.book.title} - {self.score}/5 par {self.user.username}"


class BookTag(models.Model):
    """Modèle pour les tags de livres"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom")
    slug = models.SlugField(max_length=60, unique=True, verbose_name="Slug")
    color = models.CharField(max_length=7, default='#6c757d', verbose_name="Couleur")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def books_count(self):
        """Retourne le nombre de livres avec ce tag"""
        return self.books.count()


class BookTagAssignment(models.Model):
    """Modèle pour l'assignation de tags aux livres"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(
        Book, 
        on_delete=models.CASCADE, 
        related_name='tag_assignments',
        verbose_name="Livre"
    )
    tag = models.ForeignKey(
        BookTag, 
        on_delete=models.CASCADE, 
        related_name='books',
        verbose_name="Tag"
    )
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Assigné par"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Assignation de tag"
        verbose_name_plural = "Assignations de tags"
        unique_together = ['book', 'tag']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.book.title} - {self.tag.name}"


class BookCollection(models.Model):
    """Modèle pour les collections de livres"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=220, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    books = models.ManyToManyField(
        Book, 
        related_name='collections', 
        verbose_name="Livres"
    )
    is_featured = models.BooleanField(default=False, verbose_name="Mis en avant")
    is_public = models.BooleanField(default=True, verbose_name="Public")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Ordre de tri")
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_collections',
        verbose_name="Créé par"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        ordering = ['sort_order', 'title']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('catalog:collection_detail', kwargs={'slug': self.slug})
    
    @property
    def books_count(self):
        """Retourne le nombre de livres dans la collection"""
        return self.books.count()