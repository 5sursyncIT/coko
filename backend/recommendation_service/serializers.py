from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# Removed direct import - using service API calls instead
# from catalog_service.serializers import BookListSerializer, BookDetailSerializer

class BookDataSerializer(serializers.Serializer):
    """Sérialiseur pour les données de livre reçues des services"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    slug = serializers.CharField()
    authors = serializers.ListField(child=serializers.CharField())
    categories = serializers.ListField(child=serializers.CharField())
    cover_image = serializers.URLField(allow_null=True)
    average_rating = serializers.FloatField()
    publication_date = serializers.DateField()
    score = serializers.FloatField(required=False)
    reasons = serializers.ListField(child=serializers.CharField(), required=False)
from .models import (
    UserProfile, BookVector, UserInteraction, RecommendationSet,
    Recommendation, SimilarityMatrix, TrendingBook, RecommendationFeedback
)

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le profil utilisateur de recommandations"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    recommendation_score_base = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_username',
            'preferred_genres', 'preferred_authors', 'preferred_languages',
            'reading_level', 'reading_frequency', 'average_reading_time',
            'preferred_content_types', 'preferred_book_length',
            'enable_recommendations', 'recommendation_frequency',
            'recommendation_score_base',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def validate_preferred_genres(self, value):
        """Valider la liste des genres préférés"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Les genres préférés doivent être une liste.")
        
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 genres préférés autorisés.")
        
        return value
    
    def validate_preferred_authors(self, value):
        """Valider la liste des auteurs préférés"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Les auteurs préférés doivent être une liste.")
        
        if len(value) > 20:
            raise serializers.ValidationError("Maximum 20 auteurs préférés autorisés.")
        
        return value
    
    def validate_average_reading_time(self, value):
        """Valider le temps de lecture moyen"""
        if value.total_seconds() < 300:  # 5 minutes minimum
            raise serializers.ValidationError("Le temps de lecture moyen doit être d'au moins 5 minutes.")
        
        if value.total_seconds() > 14400:  # 4 heures maximum
            raise serializers.ValidationError("Le temps de lecture moyen ne peut pas dépasser 4 heures.")
        
        return value


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'un profil utilisateur"""
    
    class Meta:
        model = UserProfile
        fields = [
            'preferred_genres', 'preferred_authors', 'preferred_languages',
            'reading_level', 'reading_frequency', 'average_reading_time',
            'preferred_content_types', 'preferred_book_length',
            'enable_recommendations', 'recommendation_frequency'
        ]
    
    def create(self, validated_data):
        """Créer un profil utilisateur"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class BookVectorSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les vecteurs de livres"""
    
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_slug = serializers.CharField(source='book.slug', read_only=True)
    combined_score = serializers.ReadOnlyField()
    
    class Meta:
        model = BookVector
        fields = [
            'id', 'book', 'book_title', 'book_slug',
            'content_vector', 'genre_vector', 'author_vector', 'metadata_vector',
            'popularity_score', 'quality_score', 'recency_score', 'combined_score',
            'view_count', 'download_count', 'rating_average', 'rating_count',
            'vector_version', 'last_updated', 'created_at'
        ]
        read_only_fields = ['last_updated', 'created_at']


class UserInteractionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les interactions utilisateur"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    interaction_weight = serializers.ReadOnlyField()
    
    class Meta:
        model = UserInteraction
        fields = [
            'id', 'user', 'user_username', 'book', 'book_title',
            'interaction_type', 'session_id', 'device_type',
            'interaction_value', 'interaction_metadata',
            'from_recommendation', 'recommendation_algorithm', 'recommendation_score',
            'interaction_weight', 'timestamp'
        ]
        read_only_fields = ['user', 'timestamp']
    
    def validate_interaction_value(self, value):
        """Valider la valeur d'interaction"""
        if value is not None:
            if self.initial_data.get('interaction_type') == 'rating':
                if not (1 <= value <= 5):
                    raise serializers.ValidationError("La note doit être entre 1 et 5.")
            elif self.initial_data.get('interaction_type') == 'read_progress':
                if not (0 <= value <= 100):
                    raise serializers.ValidationError("Le pourcentage de progression doit être entre 0 et 100.")
        
        return value


class UserInteractionCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'interactions utilisateur"""
    
    class Meta:
        model = UserInteraction
        fields = [
            'book', 'interaction_type', 'session_id', 'device_type',
            'interaction_value', 'interaction_metadata',
            'from_recommendation', 'recommendation_algorithm', 'recommendation_score'
        ]
    
    def create(self, validated_data):
        """Créer une interaction utilisateur"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class RecommendationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les recommandations individuelles"""
    
    # Book details retrieved via service API
    book_details = serializers.SerializerMethodField()
    
    def get_book_details(self, obj):
        """Récupère les détails du livre via l'API catalog_service"""
        from shared_models.api_client import catalog_client
        return catalog_client.get_book(obj.book_uuid)
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'book_uuid', 'book_title', 'book_details', 'score', 'position',
            'reasons', 'explanation',
            'viewed', 'clicked', 'converted',
            'viewed_at', 'clicked_at', 'converted_at'
        ]
        read_only_fields = [
            'viewed', 'clicked', 'converted',
            'viewed_at', 'clicked_at', 'converted_at'
        ]


class RecommendationDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur détaillé pour les recommandations"""
    
    # Book details retrieved via service API
    book_details = serializers.SerializerMethodField()
    
    def get_book_details(self, obj):
        """Récupère les détails du livre via l'API catalog_service"""
        from shared_models.api_client import catalog_client
        return catalog_client.get_book(obj.book_uuid)
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'book_uuid', 'book_title', 'book_details', 'score', 'position',
            'reasons', 'explanation',
            'viewed', 'clicked', 'converted',
            'viewed_at', 'clicked_at', 'converted_at'
        ]
        read_only_fields = [
            'viewed', 'clicked', 'converted',
            'viewed_at', 'clicked_at', 'converted_at'
        ]


class RecommendationSetSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les ensembles de recommandations"""
    
    recommendations = RecommendationSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    is_expired = serializers.ReadOnlyField()
    click_through_rate = serializers.ReadOnlyField()
    conversion_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = RecommendationSet
        fields = [
            'id', 'user', 'user_username',
            'algorithm_type', 'algorithm_version',
            'context', 'parameters',
            'generated_at', 'expires_at', 'is_expired',
            'view_count', 'click_count', 'conversion_count',
            'click_through_rate', 'conversion_rate',
            'recommendations'
        ]
        read_only_fields = [
            'user', 'generated_at', 'view_count', 'click_count', 'conversion_count'
        ]


class RecommendationSetCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'ensembles de recommandations"""
    
    class Meta:
        model = RecommendationSet
        fields = [
            'algorithm_type', 'algorithm_version',
            'context', 'parameters', 'expires_at'
        ]
    
    def validate_expires_at(self, value):
        """Valider la date d'expiration"""
        if value <= timezone.now():
            raise serializers.ValidationError("La date d'expiration doit être dans le futur.")
        
        # Maximum 30 jours
        max_expiry = timezone.now() + timedelta(days=30)
        if value > max_expiry:
            raise serializers.ValidationError("La date d'expiration ne peut pas dépasser 30 jours.")
        
        return value
    
    def create(self, validated_data):
        """Créer un ensemble de recommandations"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class SimilarityMatrixSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la matrice de similarité"""
    
    book_a_title = serializers.CharField(source='book_a.title', read_only=True)
    book_b_title = serializers.CharField(source='book_b.title', read_only=True)
    
    class Meta:
        model = SimilarityMatrix
        fields = [
            'id', 'book_a', 'book_a_title', 'book_b', 'book_b_title',
            'content_similarity', 'genre_similarity', 'author_similarity',
            'user_similarity', 'overall_similarity',
            'calculated_at', 'algorithm_version'
        ]
        read_only_fields = ['calculated_at']


class TrendingBookSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les livres en tendance"""
    
    # Book details retrieved via service API
    book_details = serializers.SerializerMethodField()
    
    def get_book_details(self, obj):
        """Récupère les détails du livre via l'API catalog_service"""
        from shared_models.api_client import catalog_client
        return catalog_client.get_book(obj.book_uuid)
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = TrendingBook
        fields = [
            'id', 'book', 'trend_type',
            'trend_score', 'velocity',
            'view_count', 'download_count', 'share_count',
            'period_start', 'period_end', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RecommendationFeedbackSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les feedbacks de recommandations"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='recommendation.book.title', read_only=True)
    is_positive = serializers.ReadOnlyField()
    feedback_weight = serializers.ReadOnlyField()
    
    class Meta:
        model = RecommendationFeedback
        fields = [
            'id', 'user', 'user_username', 'recommendation', 'book_title',
            'feedback_type', 'rating', 'comment',
            'is_positive', 'feedback_weight', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']
    
    def validate_rating(self, value):
        """Valider la note"""
        if value is not None and not (1 <= value <= 5):
            raise serializers.ValidationError("La note doit être entre 1 et 5.")
        return value
    
    def validate(self, data):
        """Validation globale"""
        # Vérifier que l'utilisateur n'a pas déjà donné un feedback pour cette recommandation
        user = self.context['request'].user
        recommendation = data['recommendation']
        
        if self.instance is None:  # Création
            if RecommendationFeedback.objects.filter(
                user=user, 
                recommendation=recommendation
            ).exists():
                raise serializers.ValidationError(
                    "Vous avez déjà donné un feedback pour cette recommandation."
                )
        
        return data
    
    def create(self, validated_data):
        """Créer un feedback de recommandation"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class RecommendationStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques de recommandations"""
    
    total_recommendations = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    total_conversions = serializers.IntegerField()
    
    average_ctr = serializers.FloatField()
    average_conversion_rate = serializers.FloatField()
    
    algorithm_performance = serializers.DictField()
    trending_algorithms = serializers.ListField()
    
    user_engagement = serializers.DictField()
    popular_genres = serializers.ListField()
    
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()


class PersonalizedRecommendationSerializer(serializers.Serializer):
    """Sérialiseur pour les recommandations personnalisées"""
    
    books = BookDataSerializer(many=True, read_only=True)
    algorithm_used = serializers.CharField()
    confidence_score = serializers.FloatField()
    reasons = serializers.ListField()
    
    # Métadonnées de génération
    generated_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    context = serializers.DictField()
    
    # Paramètres de personnalisation
    user_preferences = serializers.DictField()
    diversity_score = serializers.FloatField()
    novelty_score = serializers.FloatField()


class RecommendationEngineConfigSerializer(serializers.Serializer):
    """Sérialiseur pour la configuration du moteur de recommandations"""
    
    # Algorithmes activés
    enabled_algorithms = serializers.ListField(
        child=serializers.CharField(),
        help_text="Liste des algorithmes activés"
    )
    
    # Poids des algorithmes
    algorithm_weights = serializers.DictField(
        child=serializers.FloatField(min_value=0.0, max_value=1.0),
        help_text="Poids de chaque algorithme"
    )
    
    # Paramètres de diversité
    diversity_factor = serializers.FloatField(
        min_value=0.0, max_value=1.0,
        default=0.3,
        help_text="Facteur de diversité des recommandations"
    )
    
    # Paramètres de nouveauté
    novelty_factor = serializers.FloatField(
        min_value=0.0, max_value=1.0,
        default=0.2,
        help_text="Facteur de nouveauté des recommandations"
    )
    
    # Paramètres de popularité
    popularity_boost = serializers.FloatField(
        min_value=0.0, max_value=2.0,
        default=1.0,
        help_text="Boost de popularité"
    )
    
    # Filtres
    min_rating = serializers.FloatField(
        min_value=0.0, max_value=5.0,
        default=0.0,
        help_text="Note minimale pour les recommandations"
    )
    
    exclude_read_books = serializers.BooleanField(
        default=True,
        help_text="Exclure les livres déjà lus"
    )
    
    max_recommendations = serializers.IntegerField(
        min_value=1, max_value=50,
        default=10,
        help_text="Nombre maximum de recommandations"
    )
    
    # Cache
    cache_duration = serializers.IntegerField(
        min_value=300, max_value=86400,
        default=3600,
        help_text="Durée de cache en secondes"
    )
    
    def validate_algorithm_weights(self, value):
        """Valider que la somme des poids fait 1.0"""
        if value:
            total_weight = sum(value.values())
            if abs(total_weight - 1.0) > 0.01:
                raise serializers.ValidationError(
                    "La somme des poids des algorithmes doit être égale à 1.0"
                )
        return value


class RecommendationAnalyticsSerializer(serializers.Serializer):
    """Sérialiseur pour les analytics de recommandations"""
    
    # Métriques globales
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    recommendations_generated = serializers.IntegerField()
    
    # Métriques d'engagement
    average_ctr = serializers.FloatField()
    average_conversion_rate = serializers.FloatField()
    user_satisfaction_score = serializers.FloatField()
    
    # Performance par algorithme
    algorithm_performance = serializers.DictField()
    
    # Tendances temporelles
    daily_metrics = serializers.ListField()
    weekly_metrics = serializers.ListField()
    monthly_metrics = serializers.ListField()
    
    # Segmentation utilisateurs
    user_segments = serializers.DictField()
    
    # Contenu populaire
    top_recommended_books = serializers.ListField()
    trending_genres = serializers.ListField()
    
    # Métadonnées
    report_generated_at = serializers.DateTimeField()
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()