from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
import uuid

User = get_user_model()


class UserProfile(models.Model):
    """Profil utilisateur pour les recommandations"""
    
    READING_LEVEL_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert')
    ]
    
    READING_FREQUENCY_CHOICES = [
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('occasional', 'Occasionnel')
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='recommendation_profile'
    )
    
    # Préférences de lecture
    preferred_genres = models.JSONField(
        default=list,
        help_text="Liste des genres préférés"
    )
    preferred_authors = models.JSONField(
        default=list,
        help_text="Liste des auteurs préférés"
    )
    preferred_languages = models.JSONField(
        default=list,
        help_text="Langues préférées pour la lecture"
    )
    
    # Niveau et habitudes de lecture
    reading_level = models.CharField(
        max_length=20,
        choices=READING_LEVEL_CHOICES,
        default='intermediate'
    )
    reading_frequency = models.CharField(
        max_length=20,
        choices=READING_FREQUENCY_CHOICES,
        default='weekly'
    )
    average_reading_time = models.DurationField(
        default=timedelta(minutes=30),
        help_text="Temps de lecture moyen par session"
    )
    
    # Préférences de contenu
    preferred_content_types = models.JSONField(
        default=list,
        help_text="Types de contenu préférés (ebook, audiobook, etc.)"
    )
    preferred_book_length = models.CharField(
        max_length=20,
        choices=[
            ('short', 'Court (< 200 pages)'),
            ('medium', 'Moyen (200-400 pages)'),
            ('long', 'Long (> 400 pages)'),
            ('any', 'Peu importe')
        ],
        default='any'
    )
    
    # Paramètres de recommandation
    enable_recommendations = models.BooleanField(
        default=True,
        help_text="Activer les recommandations personnalisées"
    )
    recommendation_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Quotidien'),
            ('weekly', 'Hebdomadaire'),
            ('monthly', 'Mensuel')
        ],
        default='weekly'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recommendation_user_profiles'
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'
    
    def __str__(self):
        return f"Profil de {self.user.username}"
    
    @property
    def recommendation_score_base(self):
        """Score de base pour les recommandations"""
        score = 1.0
        
        # Bonus selon la fréquence de lecture
        frequency_bonus = {
            'daily': 1.5,
            'weekly': 1.2,
            'monthly': 1.0,
            'occasional': 0.8
        }
        score *= frequency_bonus.get(self.reading_frequency, 1.0)
        
        # Bonus selon le niveau
        level_bonus = {
            'expert': 1.3,
            'advanced': 1.2,
            'intermediate': 1.0,
            'beginner': 0.9
        }
        score *= level_bonus.get(self.reading_level, 1.0)
        
        return score


class BookVector(models.Model):
    """Représentation vectorielle des livres pour les recommandations"""
    
    # Référence UUID vers le livre dans catalog_service
    book_uuid = models.UUIDField(
        unique=True,
        help_text="UUID du livre dans catalog_service"
    )
    book_title = models.CharField(
        max_length=500,
        help_text="Titre du livre (cache pour performance)"
    )
    
    # Vecteurs de caractéristiques
    content_vector = models.JSONField(
        help_text="Vecteur basé sur le contenu du livre"
    )
    genre_vector = models.JSONField(
        help_text="Vecteur basé sur les genres"
    )
    author_vector = models.JSONField(
        help_text="Vecteur basé sur l'auteur"
    )
    metadata_vector = models.JSONField(
        help_text="Vecteur basé sur les métadonnées"
    )
    
    # Scores de popularité
    popularity_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    quality_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    recency_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Statistiques d'engagement
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    rating_average = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    rating_count = models.PositiveIntegerField(default=0)
    
    # Métadonnées
    vector_version = models.CharField(
        max_length=10,
        default='1.0',
        help_text="Version de l'algorithme de vectorisation"
    )
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommendation_book_vectors'
        verbose_name = 'Vecteur de livre'
        verbose_name_plural = 'Vecteurs de livres'
        indexes = [
            models.Index(fields=['popularity_score']),
            models.Index(fields=['quality_score']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        return f"Vecteur - {self.book_title}"
    
    @property
    def combined_score(self):
        """Score combiné pour le classement"""
        return (
            self.popularity_score * 0.3 +
            self.quality_score * 0.4 +
            self.recency_score * 0.3
        )


class UserInteraction(models.Model):
    """Interactions utilisateur pour l'apprentissage des recommandations"""
    
    INTERACTION_TYPES = [
        ('view', 'Consultation'),
        ('download', 'Téléchargement'),
        ('read_start', 'Début de lecture'),
        ('read_progress', 'Progression de lecture'),
        ('read_complete', 'Lecture terminée'),
        ('bookmark', 'Signet ajouté'),
        ('rating', 'Note donnée'),
        ('share', 'Partage'),
        ('purchase', 'Achat'),
        ('wishlist', 'Ajout à la liste de souhaits'),
        ('search', 'Recherche'),
        ('recommendation_click', 'Clic sur recommandation')
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    # Référence UUID vers le livre dans catalog_service
    book_uuid = models.UUIDField(
        help_text="UUID du livre dans catalog_service"
    )
    book_title = models.CharField(
        max_length=500,
        help_text="Titre du livre (cache pour performance)"
    )
    
    interaction_type = models.CharField(
        max_length=30,
        choices=INTERACTION_TYPES
    )
    
    # Données contextuelles
    session_id = models.UUIDField(
        default=uuid.uuid4,
        help_text="ID de session pour grouper les interactions"
    )
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('mobile', 'Mobile'),
            ('tablet', 'Tablette'),
            ('desktop', 'Ordinateur'),
            ('ereader', 'Liseuse')
        ],
        null=True,
        blank=True
    )
    
    # Métadonnées d'interaction
    interaction_value = models.FloatField(
        null=True,
        blank=True,
        help_text="Valeur numérique de l'interaction (ex: note, pourcentage lu)"
    )
    interaction_metadata = models.JSONField(
        default=dict,
        help_text="Métadonnées supplémentaires de l'interaction"
    )
    
    # Contexte de recommandation
    from_recommendation = models.BooleanField(
        default=False,
        help_text="Interaction issue d'une recommandation"
    )
    recommendation_algorithm = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Algorithme de recommandation utilisé"
    )
    recommendation_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Score de la recommandation"
    )
    
    # Horodatage
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommendation_user_interactions'
        verbose_name = 'Interaction utilisateur'
        verbose_name_plural = 'Interactions utilisateurs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['book_uuid', 'interaction_type']),
            models.Index(fields=['session_id']),
            models.Index(fields=['from_recommendation']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} - {self.book_title}"
    
    @property
    def interaction_weight(self):
        """Poids de l'interaction pour les recommandations"""
        weights = {
            'view': 1.0,
            'download': 2.0,
            'read_start': 3.0,
            'read_progress': 2.0,
            'read_complete': 5.0,
            'bookmark': 3.0,
            'rating': 4.0,
            'share': 4.0,
            'purchase': 6.0,
            'wishlist': 2.0,
            'search': 0.5,
            'recommendation_click': 1.5
        }
        return weights.get(self.interaction_type, 1.0)


class RecommendationSet(models.Model):
    """Ensemble de recommandations générées pour un utilisateur"""
    
    ALGORITHM_TYPES = [
        ('collaborative', 'Filtrage collaboratif'),
        ('content_based', 'Basé sur le contenu'),
        ('hybrid', 'Hybride'),
        ('popularity', 'Popularité'),
        ('trending', 'Tendances'),
        ('personalized', 'Personnalisé'),
        ('cold_start', 'Démarrage à froid')
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendation_sets'
    )
    
    # Configuration de l'algorithme
    algorithm_type = models.CharField(
        max_length=30,
        choices=ALGORITHM_TYPES
    )
    algorithm_version = models.CharField(
        max_length=10,
        default='1.0'
    )
    
    # Contexte de génération
    context = models.JSONField(
        default=dict,
        help_text="Contexte de génération (page, recherche, etc.)"
    )
    parameters = models.JSONField(
        default=dict,
        help_text="Paramètres utilisés pour la génération"
    )
    
    # Métadonnées
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="Date d'expiration des recommandations"
    )
    
    # Statistiques
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    conversion_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'recommendation_sets'
        verbose_name = 'Ensemble de recommandations'
        verbose_name_plural = 'Ensembles de recommandations'
        indexes = [
            models.Index(fields=['user', 'generated_at']),
            models.Index(fields=['algorithm_type']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Recommandations {self.algorithm_type} pour {self.user.username}"
    
    @property
    def is_expired(self):
        """Vérifie si les recommandations ont expiré"""
        return timezone.now() > self.expires_at
    
    @property
    def click_through_rate(self):
        """Taux de clic sur les recommandations"""
        if self.view_count == 0:
            return 0.0
        return (self.click_count / self.view_count) * 100
    
    @property
    def conversion_rate(self):
        """Taux de conversion des recommandations"""
        if self.click_count == 0:
            return 0.0
        return (self.conversion_count / self.click_count) * 100


class Recommendation(models.Model):
    """Recommandation individuelle dans un ensemble"""
    
    recommendation_set = models.ForeignKey(
        RecommendationSet,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    # Référence UUID vers le livre dans catalog_service
    book_uuid = models.UUIDField(
        help_text="UUID du livre dans catalog_service"
    )
    book_title = models.CharField(
        max_length=500,
        help_text="Titre du livre (cache pour performance)"
    )
    
    # Score et position
    score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Score de recommandation (0-1)"
    )
    position = models.PositiveIntegerField(
        help_text="Position dans la liste de recommandations"
    )
    
    # Raisons de la recommandation
    reasons = models.JSONField(
        default=list,
        help_text="Raisons de la recommandation"
    )
    explanation = models.TextField(
        blank=True,
        help_text="Explication textuelle de la recommandation"
    )
    
    # Statistiques d'interaction
    viewed = models.BooleanField(default=False)
    clicked = models.BooleanField(default=False)
    converted = models.BooleanField(default=False)
    
    # Horodatage des interactions
    viewed_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'recommendations'
        verbose_name = 'Recommandation'
        verbose_name_plural = 'Recommandations'
        unique_together = ['recommendation_set', 'book_uuid']
        indexes = [
            models.Index(fields=['recommendation_set', 'position']),
            models.Index(fields=['score']),
            models.Index(fields=['clicked']),
            models.Index(fields=['converted']),
        ]
        ordering = ['position']
    
    def __str__(self):
        return f"Recommandation #{self.position}: {self.book_title}"
    
    def mark_viewed(self):
        """Marquer comme vue"""
        if not self.viewed:
            self.viewed = True
            self.viewed_at = timezone.now()
            self.save(update_fields=['viewed', 'viewed_at'])
            
            # Mettre à jour les statistiques du set
            self.recommendation_set.view_count += 1
            self.recommendation_set.save(update_fields=['view_count'])
    
    def mark_clicked(self):
        """Marquer comme cliquée"""
        if not self.clicked:
            self.clicked = True
            self.clicked_at = timezone.now()
            self.save(update_fields=['clicked', 'clicked_at'])
            
            # Mettre à jour les statistiques du set
            self.recommendation_set.click_count += 1
            self.recommendation_set.save(update_fields=['click_count'])
    
    def mark_converted(self):
        """Marquer comme convertie"""
        if not self.converted:
            self.converted = True
            self.converted_at = timezone.now()
            self.save(update_fields=['converted', 'converted_at'])
            
            # Mettre à jour les statistiques du set
            self.recommendation_set.conversion_count += 1
            self.recommendation_set.save(update_fields=['conversion_count'])


class SimilarityMatrix(models.Model):
    """Matrice de similarité entre livres"""
    
    # Références UUID vers les livres dans catalog_service
    book_a_uuid = models.UUIDField(
        help_text="UUID du premier livre dans catalog_service"
    )
    book_a_title = models.CharField(
        max_length=500,
        help_text="Titre du premier livre (cache)"
    )
    book_b_uuid = models.UUIDField(
        help_text="UUID du deuxième livre dans catalog_service"
    )
    book_b_title = models.CharField(
        max_length=500,
        help_text="Titre du deuxième livre (cache)"
    )
    
    # Scores de similarité
    content_similarity = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Similarité basée sur le contenu"
    )
    genre_similarity = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Similarité basée sur les genres"
    )
    author_similarity = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Similarité basée sur les auteurs"
    )
    user_similarity = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Similarité basée sur les interactions utilisateurs"
    )
    
    # Score global
    overall_similarity = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Score de similarité global"
    )
    
    # Métadonnées
    calculated_at = models.DateTimeField(auto_now=True)
    algorithm_version = models.CharField(
        max_length=10,
        default='1.0'
    )
    
    class Meta:
        db_table = 'recommendation_similarity_matrix'
        verbose_name = 'Similarité entre livres'
        verbose_name_plural = 'Similarités entre livres'
        unique_together = ['book_a_uuid', 'book_b_uuid']
        indexes = [
            models.Index(fields=['book_a_uuid', 'overall_similarity']),
            models.Index(fields=['book_b_uuid', 'overall_similarity']),
            models.Index(fields=['overall_similarity']),
        ]
    
    def __str__(self):
        return f"Similarité: {self.book_a_title} <-> {self.book_b_title} ({self.overall_similarity:.2f})"
    
    @classmethod
    def get_similar_books(cls, book_uuid, limit=10, min_similarity=0.3):
        """Obtenir les livres similaires à un livre donné par UUID"""
        from django.db import models as django_models
        
        similarities = cls.objects.filter(
            django_models.Q(book_a_uuid=book_uuid) | django_models.Q(book_b_uuid=book_uuid),
            overall_similarity__gte=min_similarity
        ).order_by('-overall_similarity')[:limit]
        
        similar_books = []
        for sim in similarities:
            if sim.book_a_uuid == book_uuid:
                similar_book_uuid = sim.book_b_uuid
                similar_book_title = sim.book_b_title
            else:
                similar_book_uuid = sim.book_a_uuid
                similar_book_title = sim.book_a_title
                
            similar_books.append({
                'book_uuid': similar_book_uuid,
                'book_title': similar_book_title,
                'similarity': sim.overall_similarity,
                'reasons': {
                    'content': sim.content_similarity,
                    'genre': sim.genre_similarity,
                    'author': sim.author_similarity,
                    'user': sim.user_similarity
                }
            })
        
        return similar_books


class TrendingBook(models.Model):
    """Livres en tendance pour les recommandations"""
    
    TREND_TYPES = [
        ('daily', 'Tendance du jour'),
        ('weekly', 'Tendance de la semaine'),
        ('monthly', 'Tendance du mois'),
        ('rising', 'En hausse'),
        ('viral', 'Viral'),
        ('seasonal', 'Saisonnier')
    ]
    
    # Référence UUID vers le livre dans catalog_service
    book_uuid = models.UUIDField(
        help_text="UUID du livre dans catalog_service"
    )
    book_title = models.CharField(
        max_length=500,
        help_text="Titre du livre (cache pour performance)"
    )
    
    trend_type = models.CharField(
        max_length=20,
        choices=TREND_TYPES
    )
    
    # Scores de tendance
    trend_score = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Score de tendance"
    )
    velocity = models.FloatField(
        default=0.0,
        help_text="Vitesse de croissance de la tendance"
    )
    
    # Métriques
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    # Période de tendance
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'recommendation_trending_books'
        verbose_name = 'Livre en tendance'
        verbose_name_plural = 'Livres en tendance'
        unique_together = ['book_uuid', 'trend_type', 'period_start']
        indexes = [
            models.Index(fields=['trend_type', 'trend_score']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['velocity']),
        ]
        ordering = ['-trend_score']
    
    def __str__(self):
        return f"{self.book_title} - {self.get_trend_type_display()} ({self.trend_score:.2f})"
    
    @property
    def is_active(self):
        """Vérifie si la tendance est encore active"""
        now = timezone.now()
        return self.period_start <= now <= self.period_end


class RecommendationFeedback(models.Model):
    """Feedback utilisateur sur les recommandations"""
    
    FEEDBACK_TYPES = [
        ('like', 'J\'aime'),
        ('dislike', 'Je n\'aime pas'),
        ('not_interested', 'Pas intéressé'),
        ('already_read', 'Déjà lu'),
        ('inappropriate', 'Inapproprié'),
        ('poor_quality', 'Mauvaise qualité'),
        ('good_recommendation', 'Bonne recommandation')
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendation_feedbacks'
    )
    recommendation = models.ForeignKey(
        Recommendation,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    
    feedback_type = models.CharField(
        max_length=30,
        choices=FEEDBACK_TYPES
    )
    
    # Feedback détaillé
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Note de 1 à 5 pour la recommandation"
    )
    comment = models.TextField(
        blank=True,
        help_text="Commentaire optionnel"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommendation_feedbacks'
        verbose_name = 'Feedback de recommandation'
        verbose_name_plural = 'Feedbacks de recommandations'
        unique_together = ['user', 'recommendation']
        indexes = [
            models.Index(fields=['feedback_type']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_feedback_type_display()} - {self.recommendation.book_title}"
    
    @property
    def is_positive(self):
        """Vérifie si le feedback est positif"""
        positive_types = ['like', 'good_recommendation']
        return self.feedback_type in positive_types
    
    @property
    def feedback_weight(self):
        """Poids du feedback pour l'apprentissage"""
        weights = {
            'like': 1.0,
            'dislike': -1.0,
            'not_interested': -0.5,
            'already_read': 0.0,
            'inappropriate': -1.5,
            'poor_quality': -1.2,
            'good_recommendation': 1.5
        }
        return weights.get(self.feedback_type, 0.0)