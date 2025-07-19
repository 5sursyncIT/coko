from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class ReadingSession(models.Model):
    """Modèle pour les sessions de lecture"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'En pause'),
        ('completed', 'Terminée'),
        ('abandoned', 'Abandonnée'),
    ]
    
    DEVICE_CHOICES = [
        ('web', 'Navigateur Web'),
        ('mobile', 'Application Mobile'),
        ('tablet', 'Tablette'),
        ('ereader', 'Liseuse'),
        ('desktop', 'Application Desktop'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_sessions')
    # Référence UUID vers le livre dans catalog_service
    book_uuid = models.UUIDField(
        help_text="UUID du livre dans catalog_service"
    )
    book_title = models.CharField(
        max_length=500,
        help_text="Titre du livre (cache pour performance)"
    )
    
    # Informations de session
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    device_type = models.CharField(max_length=20, choices=DEVICE_CHOICES, default='web')
    device_info = models.JSONField(default=dict, blank=True)  # Infos détaillées sur l'appareil
    
    # Progression de lecture
    current_page = models.PositiveIntegerField(default=1)
    current_position = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    total_pages_read = models.PositiveIntegerField(default=0)
    
    # Temps de lecture
    start_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_reading_time = models.DurationField(default=timezone.timedelta)
    
    # Métadonnées
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Paramètres de lecture
    font_size = models.PositiveIntegerField(default=16, validators=[MinValueValidator(8), MaxValueValidator(72)])
    font_family = models.CharField(max_length=50, default='Arial')
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Clair'),
        ('dark', 'Sombre'),
        ('sepia', 'Sépia'),
    ])
    line_height = models.FloatField(default=1.5, validators=[MinValueValidator(1.0), MaxValueValidator(3.0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reading_sessions'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'book_uuid']),
            models.Index(fields=['status']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.book_title} ({self.status})"
    
    @property
    def progress_percentage(self):
        """Pourcentage de progression"""
        # Pour calculer le pourcentage, nous devons récupérer les infos du livre
        # via l'API catalog_service ou utiliser current_position
        return self.current_position
    
    @property
    def is_completed(self):
        """Vérifie si la lecture est terminée"""
        return self.status == 'completed' or self.progress_percentage >= 95
    
    @property
    def reading_speed_pages_per_hour(self):
        """Vitesse de lecture en pages par heure"""
        if self.total_reading_time.total_seconds() > 0:
            hours = self.total_reading_time.total_seconds() / 3600
            return self.total_pages_read / hours
        return 0
    
    def mark_as_completed(self):
        """Marque la session comme terminée"""
        self.status = 'completed'
        self.end_time = timezone.now()
        self.current_position = 100.0
        self.save()


class ReadingProgress(models.Model):
    """Modèle pour suivre la progression de lecture détaillée"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ReadingSession, on_delete=models.CASCADE, related_name='progress_entries')
    
    # Position dans le livre
    page_number = models.PositiveIntegerField()
    position_in_page = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    chapter_title = models.CharField(max_length=200, blank=True)
    
    # Temps passé sur cette page
    time_spent = models.DurationField(default=timezone.timedelta)
    
    # Métadonnées
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reading_progress'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session', 'page_number']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.session} - Page {self.page_number}"


class Bookmark(models.Model):
    """Modèle pour les signets de lecture"""
    
    TYPE_CHOICES = [
        ('bookmark', 'Signet'),
        ('highlight', 'Surlignage'),
        ('note', 'Note'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    # Référence UUID vers le livre dans catalog_service
    book_uuid = models.UUIDField(
        help_text="UUID du livre dans catalog_service"
    )
    book_title = models.CharField(
        max_length=500,
        help_text="Titre du livre (cache pour performance)"
    )
    
    # Type et contenu
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='bookmark')
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)  # Texte surligné ou note
    note = models.TextField(blank=True)  # Note personnelle
    
    # Position dans le livre
    page_number = models.PositiveIntegerField()
    position_in_page = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    chapter_title = models.CharField(max_length=200, blank=True)
    
    # Métadonnées pour le surlignage
    highlight_color = models.CharField(max_length=7, default='#ffff00')  # Couleur hex
    start_offset = models.PositiveIntegerField(null=True, blank=True)  # Position de début du texte
    end_offset = models.PositiveIntegerField(null=True, blank=True)  # Position de fin du texte
    
    # Paramètres
    is_private = models.BooleanField(default=True)
    is_favorite = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bookmarks'
        ordering = ['page_number', 'position_in_page']
        indexes = [
            models.Index(fields=['user', 'book_uuid']),
            models.Index(fields=['type']),
            models.Index(fields=['page_number']),
            models.Index(fields=['is_favorite']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.book_title} - Page {self.page_number}"
    
    @property
    def preview_text(self):
        """Aperçu du contenu"""
        if self.content:
            return self.content[:100] + '...' if len(self.content) > 100 else self.content
        return self.title or f"Signet page {self.page_number}"


class ReadingGoal(models.Model):
    """Modèle pour les objectifs de lecture"""
    
    GOAL_TYPE_CHOICES = [
        ('books_per_year', 'Livres par an'),
        ('books_per_month', 'Livres par mois'),
        ('pages_per_day', 'Pages par jour'),
        ('minutes_per_day', 'Minutes par jour'),
        ('books_in_category', 'Livres dans une catégorie'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('completed', 'Terminé'),
        ('paused', 'En pause'),
        ('failed', 'Échoué'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_goals')
    
    # Détails de l'objectif
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal_type = models.CharField(max_length=30, choices=GOAL_TYPE_CHOICES)
    target_value = models.PositiveIntegerField()  # Valeur cible
    current_value = models.PositiveIntegerField(default=0)  # Valeur actuelle
    
    # Période
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Filtres optionnels
    # Références UUID optionnelles pour les filtres
    category_uuid = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID de la catégorie dans catalog_service"
    )
    author_uuid = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID de l'auteur dans catalog_service"
    )
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Paramètres
    is_public = models.BooleanField(default=False)
    send_reminders = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reading_goals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['goal_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    @property
    def progress_percentage(self):
        """Pourcentage de progression vers l'objectif"""
        if self.target_value > 0:
            return min((self.current_value / self.target_value) * 100, 100)
        return 0
    
    @property
    def is_completed(self):
        """Vérifie si l'objectif est atteint"""
        return self.current_value >= self.target_value
    
    @property
    def days_remaining(self):
        """Nombre de jours restants"""
        today = timezone.now().date()
        if self.end_date > today:
            return (self.end_date - today).days
        return 0
    
    @property
    def daily_target_remaining(self):
        """Cible quotidienne pour atteindre l'objectif"""
        if self.days_remaining > 0 and self.goal_type in ['pages_per_day', 'minutes_per_day']:
            remaining = self.target_value - self.current_value
            return max(remaining / self.days_remaining, 0)
        return 0
    
    def update_progress(self):
        """Met à jour la progression de l'objectif"""
        today = timezone.now().date()
        
        if self.goal_type == 'books_per_year':
            # Compter les livres terminés cette année
            year_start = today.replace(month=1, day=1)
            completed_books = ReadingSession.objects.filter(
                user=self.user,
                status='completed',
                end_time__date__gte=year_start,
                end_time__date__lte=today
            ).count()
            self.current_value = completed_books
            
        elif self.goal_type == 'books_per_month':
            # Compter les livres terminés ce mois
            month_start = today.replace(day=1)
            completed_books = ReadingSession.objects.filter(
                user=self.user,
                status='completed',
                end_time__date__gte=month_start,
                end_time__date__lte=today
            ).count()
            self.current_value = completed_books
            
        elif self.goal_type == 'pages_per_day':
            # Compter les pages lues aujourd'hui
            pages_today = ReadingProgress.objects.filter(
                session__user=self.user,
                timestamp__date=today
            ).count()
            self.current_value = pages_today
            
        elif self.goal_type == 'minutes_per_day':
            # Calculer le temps de lecture aujourd'hui
            sessions_today = ReadingSession.objects.filter(
                user=self.user,
                last_activity__date=today
            )
            total_minutes = sum(
                session.total_reading_time.total_seconds() / 60 
                for session in sessions_today
            )
            self.current_value = int(total_minutes)
        
        # Vérifier si l'objectif est atteint
        if self.is_completed and self.status == 'active':
            self.status = 'completed'
        
        self.save()


class ReadingStatistics(models.Model):
    """Modèle pour les statistiques de lecture agrégées"""
    
    PERIOD_CHOICES = [
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('yearly', 'Annuel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_statistics')
    
    # Période
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Statistiques de lecture
    books_started = models.PositiveIntegerField(default=0)
    books_completed = models.PositiveIntegerField(default=0)
    pages_read = models.PositiveIntegerField(default=0)
    total_reading_time = models.DurationField(default=timezone.timedelta)
    
    # Statistiques détaillées
    average_session_duration = models.DurationField(default=timezone.timedelta)
    longest_session_duration = models.DurationField(default=timezone.timedelta)
    reading_sessions_count = models.PositiveIntegerField(default=0)
    
    # Préférences de lecture
    # Référence UUID vers la catégorie la plus lue
    most_read_category_uuid = models.UUIDField(
        null=True,
        blank=True,
        help_text="UUID de la catégorie la plus lue"
    )
    favorite_reading_time = models.TimeField(null=True, blank=True)  # Heure préférée
    preferred_device = models.CharField(max_length=20, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reading_statistics'
        unique_together = ['user', 'period_type', 'period_start']
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['user', 'period_type']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.period_type} - {self.period_start}"
    
    @property
    def average_pages_per_day(self):
        """Moyenne de pages par jour"""
        days = (self.period_end - self.period_start).days + 1
        return self.pages_read / days if days > 0 else 0
    
    @property
    def reading_consistency(self):
        """Pourcentage de jours avec lecture"""
        days = (self.period_end - self.period_start).days + 1
        reading_days = ReadingSession.objects.filter(
            user=self.user,
            last_activity__date__gte=self.period_start,
            last_activity__date__lte=self.period_end
        ).values('last_activity__date').distinct().count()
        
        return (reading_days / days) * 100 if days > 0 else 0