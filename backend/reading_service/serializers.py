from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    ReadingSession, ReadingProgress, Bookmark, 
    ReadingGoal, ReadingStatistics
)

User = get_user_model()


class ReadingSessionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les sessions de lecture"""
    
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_cover = serializers.URLField(source='book.cover_image.url', read_only=True)
    book_author = serializers.StringRelatedField(source='book.authors', many=True, read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    reading_speed_pages_per_hour = serializers.ReadOnlyField()
    
    class Meta:
        model = ReadingSession
        fields = [
            'id', 'book', 'book_title', 'book_cover', 'book_author',
            'status', 'device_type', 'device_info',
            'current_page', 'current_position', 'total_pages_read',
            'start_time', 'last_activity', 'end_time', 'total_reading_time',
            'font_size', 'font_family', 'theme', 'line_height',
            'progress_percentage', 'is_completed', 'reading_speed_pages_per_hour',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'start_time', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReadingSessionCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour créer une session de lecture"""
    
    class Meta:
        model = ReadingSession
        fields = [
            'book', 'device_type', 'device_info',
            'font_size', 'font_family', 'theme', 'line_height'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReadingSessionUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour mettre à jour une session de lecture"""
    
    class Meta:
        model = ReadingSession
        fields = [
            'status', 'current_page', 'current_position', 'total_pages_read',
            'total_reading_time', 'font_size', 'font_family', 'theme', 'line_height'
        ]
    
    def update(self, instance, validated_data):
        # Mettre à jour last_activity automatiquement
        instance.last_activity = timezone.now()
        
        # Si le statut change vers 'completed', définir end_time
        if validated_data.get('status') == 'completed' and instance.status != 'completed':
            validated_data['end_time'] = timezone.now()
            validated_data['current_position'] = 100.0
        
        return super().update(instance, validated_data)


class ReadingProgressSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la progression de lecture"""
    
    class Meta:
        model = ReadingProgress
        fields = [
            'id', 'session', 'page_number', 'position_in_page',
            'chapter_title', 'time_spent', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class BookmarkSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les signets"""
    
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_cover = serializers.URLField(source='book.cover_image.url', read_only=True)
    preview_text = serializers.ReadOnlyField()
    
    class Meta:
        model = Bookmark
        fields = [
            'id', 'book', 'book_title', 'book_cover',
            'type', 'title', 'content', 'note',
            'page_number', 'position_in_page', 'chapter_title',
            'highlight_color', 'start_offset', 'end_offset',
            'is_private', 'is_favorite', 'preview_text',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BookmarkCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour créer un signet"""
    
    class Meta:
        model = Bookmark
        fields = [
            'book', 'type', 'title', 'content', 'note',
            'page_number', 'position_in_page', 'chapter_title',
            'highlight_color', 'start_offset', 'end_offset',
            'is_private', 'is_favorite'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReadingGoalSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les objectifs de lecture"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    daily_target_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = ReadingGoal
        fields = [
            'id', 'title', 'description', 'goal_type', 'target_value', 'current_value',
            'start_date', 'end_date', 'category', 'category_name', 'author', 'author_name',
            'status', 'is_public', 'send_reminders',
            'progress_percentage', 'is_completed', 'days_remaining', 'daily_target_remaining',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'current_value', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        """Validation des dates"""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        return data


class ReadingGoalCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour créer un objectif de lecture"""
    
    class Meta:
        model = ReadingGoal
        fields = [
            'title', 'description', 'goal_type', 'target_value',
            'start_date', 'end_date', 'category', 'author',
            'is_public', 'send_reminders'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        """Validation des données"""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        
        if data['target_value'] <= 0:
            raise serializers.ValidationError(
                "La valeur cible doit être positive."
            )
        
        return data


class ReadingStatisticsSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les statistiques de lecture"""
    
    most_read_category_name = serializers.CharField(source='most_read_category.name', read_only=True)
    average_pages_per_day = serializers.ReadOnlyField()
    reading_consistency = serializers.ReadOnlyField()
    
    class Meta:
        model = ReadingStatistics
        fields = [
            'id', 'period_type', 'period_start', 'period_end',
            'books_started', 'books_completed', 'pages_read', 'total_reading_time',
            'average_session_duration', 'longest_session_duration', 'reading_sessions_count',
            'most_read_category', 'most_read_category_name', 'favorite_reading_time', 'preferred_device',
            'average_pages_per_day', 'reading_consistency',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ReadingDashboardSerializer(serializers.Serializer):
    """Sérialiseur pour le tableau de bord de lecture"""
    
    # Sessions actives
    active_sessions = ReadingSessionSerializer(many=True, read_only=True)
    
    # Statistiques récentes
    books_read_this_month = serializers.IntegerField(read_only=True)
    pages_read_this_week = serializers.IntegerField(read_only=True)
    reading_time_this_week = serializers.DurationField(read_only=True)
    current_reading_streak = serializers.IntegerField(read_only=True)
    
    # Objectifs en cours
    active_goals = ReadingGoalSerializer(many=True, read_only=True)
    
    # Signets récents
    recent_bookmarks = BookmarkSerializer(many=True, read_only=True)
    
    # Recommandations
    recommended_books = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )


class ReadingSessionStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques de session"""
    
    total_sessions = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    completed_sessions = serializers.IntegerField()
    total_reading_time = serializers.DurationField()
    average_session_duration = serializers.DurationField()
    total_pages_read = serializers.IntegerField()
    books_completed = serializers.IntegerField()
    favorite_device = serializers.CharField()
    favorite_reading_time = serializers.TimeField()


class BookmarkStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques de signets"""
    
    total_bookmarks = serializers.IntegerField()
    bookmarks_by_type = serializers.DictField()
    favorite_bookmarks = serializers.IntegerField()
    most_bookmarked_book = serializers.CharField()
    recent_bookmarks_count = serializers.IntegerField()


class ReadingProgressStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques de progression"""
    
    books_in_progress = serializers.IntegerField()
    average_progress = serializers.FloatField()
    books_completed_this_month = serializers.IntegerField()
    pages_read_today = serializers.IntegerField()
    reading_consistency_percentage = serializers.FloatField()


class UserReadingPreferencesSerializer(serializers.Serializer):
    """Sérialiseur pour les préférences de lecture utilisateur"""
    
    # Préférences d'affichage
    default_font_size = serializers.IntegerField(min_value=8, max_value=72, default=16)
    default_font_family = serializers.CharField(max_length=50, default='Arial')
    default_theme = serializers.ChoiceField(
        choices=[('light', 'Clair'), ('dark', 'Sombre'), ('sepia', 'Sépia')],
        default='light'
    )
    default_line_height = serializers.FloatField(min_value=1.0, max_value=3.0, default=1.5)
    
    # Préférences de notification
    daily_reading_reminder = serializers.BooleanField(default=True)
    goal_progress_notifications = serializers.BooleanField(default=True)
    new_book_recommendations = serializers.BooleanField(default=True)
    
    # Préférences de confidentialité
    public_reading_stats = serializers.BooleanField(default=False)
    share_reading_goals = serializers.BooleanField(default=False)
    
    # Objectifs par défaut
    auto_create_yearly_goal = serializers.BooleanField(default=False)
    default_yearly_book_target = serializers.IntegerField(min_value=1, max_value=1000, default=12)


class ReadingRecommendationSerializer(serializers.Serializer):
    """Sérialiseur pour les recommandations de lecture"""
    
    book_id = serializers.UUIDField()
    title = serializers.CharField()
    authors = serializers.ListField(child=serializers.CharField())
    cover_image = serializers.URLField()
    rating = serializers.FloatField()
    category = serializers.CharField()
    reason = serializers.CharField()  # Raison de la recommandation
    confidence_score = serializers.FloatField()  # Score de confiance


class ReadingAnalyticsSerializer(serializers.Serializer):
    """Sérialiseur pour les analyses de lecture avancées"""
    
    # Tendances temporelles
    reading_trends = serializers.DictField()  # Données pour graphiques
    
    # Comparaisons
    compared_to_last_month = serializers.DictField()
    compared_to_average_user = serializers.DictField()
    
    # Insights
    reading_insights = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Prédictions
    yearly_projection = serializers.DictField()
    goal_achievement_probability = serializers.FloatField()