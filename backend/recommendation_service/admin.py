from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg
from django.contrib.admin import SimpleListFilter
from datetime import timedelta

from .models import (
    UserProfile, BookVector, UserInteraction, RecommendationSet,
    Recommendation, SimilarityMatrix, TrendingBook, RecommendationFeedback
)


class RecommendationInline(admin.TabularInline):
    """Inline pour les recommandations dans un ensemble"""
    model = Recommendation
    extra = 0
    readonly_fields = ['viewed', 'clicked', 'converted', 'viewed_at', 'clicked_at', 'converted_at']
    fields = [
        'book_uuid', 'book_title', 'score', 'position', 'reasons', 'explanation',
        'viewed', 'clicked', 'converted'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request)


class InteractionTypeFilter(SimpleListFilter):
    """Filtre par type d'interaction"""
    title = 'Type d\'interaction'
    parameter_name = 'interaction_type'
    
    def lookups(self, request, model_admin):
        return [
            ('view', 'Vue'),
            ('click', 'Clic'),
            ('read', 'Lecture'),
            ('rating', 'Note'),
            ('bookmark', 'Marque-page'),
            ('download', 'Téléchargement'),
            ('share', 'Partage'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(interaction_type=self.value())
        return queryset


class AlgorithmTypeFilter(SimpleListFilter):
    """Filtre par type d'algorithme"""
    title = 'Type d\'algorithme'
    parameter_name = 'algorithm_type'
    
    def lookups(self, request, model_admin):
        return [
            ('content_based', 'Basé sur le contenu'),
            ('collaborative', 'Filtrage collaboratif'),
            ('popularity', 'Popularité'),
            ('hybrid', 'Hybride'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(algorithm_type=self.value())
        return queryset


class ActiveRecommendationsFilter(SimpleListFilter):
    """Filtre pour les recommandations actives"""
    title = 'Statut'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return [
            ('active', 'Actives'),
            ('expired', 'Expirées'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(expires_at__gt=timezone.now())
        elif self.value() == 'expired':
            return queryset.filter(expires_at__lte=timezone.now())
        return queryset


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Administration des profils utilisateur"""
    
    list_display = [
        'user', 'user_email', 'reading_level', 'reading_frequency',
        'enable_recommendations', 'recommendation_frequency',
        'profile_completeness', 'created_at', 'updated_at'
    ]
    
    list_filter = [
        'reading_level', 'reading_frequency', 'enable_recommendations',
        'recommendation_frequency', 'created_at', 'updated_at'
    ]
    
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    
    readonly_fields = ['created_at', 'updated_at', 'recommendation_score_base']
    
    fieldsets = [
        ('Utilisateur', {
            'fields': ['user']
        }),
        ('Préférences de lecture', {
            'fields': [
                'preferred_genres', 'preferred_authors', 'preferred_languages',
                'reading_level', 'reading_frequency', 'average_reading_time',
                'preferred_content_types', 'preferred_book_length'
            ]
        }),
        ('Paramètres de recommandations', {
            'fields': [
                'enable_recommendations', 'recommendation_frequency',
                'recommendation_score_base'
            ]
        }),
        ('Métadonnées', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def profile_completeness(self, obj):
        """Calculer le pourcentage de complétude du profil"""
        completeness = 0
        total_fields = 6
        
        if obj.preferred_genres:
            completeness += 1
        if obj.preferred_authors:
            completeness += 1
        if obj.preferred_languages:
            completeness += 1
        if obj.reading_level:
            completeness += 1
        if obj.reading_frequency:
            completeness += 1
        if obj.average_reading_time:
            completeness += 1
        
        percentage = (completeness / total_fields) * 100
        
        if percentage >= 80:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.0f}%</span>',
            color, percentage
        )
    profile_completeness.short_description = 'Complétude'
    
    actions = ['enable_recommendations', 'disable_recommendations']
    
    def enable_recommendations(self, request, queryset):
        updated = queryset.update(enable_recommendations=True)
        self.message_user(
            request,
            f'{updated} profil(s) mis à jour - recommandations activées.'
        )
    enable_recommendations.short_description = 'Activer les recommandations'
    
    def disable_recommendations(self, request, queryset):
        updated = queryset.update(enable_recommendations=False)
        self.message_user(
            request,
            f'{updated} profil(s) mis à jour - recommandations désactivées.'
        )
    disable_recommendations.short_description = 'Désactiver les recommandations'


@admin.register(BookVector)
class BookVectorAdmin(admin.ModelAdmin):
    """Administration des vecteurs de livres"""
    
    list_display = [
        'get_book_title', 'combined_score', 'popularity_score',
        'quality_score', 'view_count', 'rating_average', 'last_updated'
    ]
    
    list_filter = ['vector_version', 'last_updated', 'created_at']
    
    search_fields = ['book_title']
    
    readonly_fields = [
        'combined_score', 'last_updated', 'created_at',
        'view_count', 'download_count', 'rating_average', 'rating_count'
    ]
    
    fieldsets = [
        ('Livre', {
            'fields': ['book']
        }),
        ('Vecteurs', {
            'fields': [
                'content_vector', 'genre_vector', 'author_vector', 'metadata_vector'
            ],
            'classes': ['collapse']
        }),
        ('Scores', {
            'fields': [
                'popularity_score', 'quality_score', 'recency_score', 'combined_score'
            ]
        }),
        ('Métriques', {
            'fields': [
                'view_count', 'download_count', 'rating_average', 'rating_count'
            ]
        }),
        ('Métadonnées', {
            'fields': ['vector_version', 'last_updated', 'created_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_book_title(self, obj):
        return obj.book_title or '-'
    get_book_title.short_description = 'Titre'
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    """Administration des interactions utilisateur"""
    
    list_display = [
        'user', 'book_title', 'interaction_type', 'interaction_value',
        'from_recommendation', 'recommendation_algorithm', 'timestamp'
    ]
    
    list_filter = [
        InteractionTypeFilter, 'from_recommendation',
        'recommendation_algorithm', 'device_type', 'timestamp'
    ]
    
    search_fields = [
        'user__username', 'book__title', 'session_id'
    ]
    
    readonly_fields = ['timestamp', 'interaction_weight']
    
    fieldsets = [
        ('Interaction', {
            'fields': [
                'user', 'book', 'interaction_type', 'interaction_value'
            ]
        }),
        ('Contexte', {
            'fields': [
                'session_id', 'device_type', 'interaction_metadata'
            ]
        }),
        ('Recommandation', {
            'fields': [
                'from_recommendation', 'recommendation_algorithm', 'recommendation_score'
            ]
        }),
        ('Métadonnées', {
            'fields': ['interaction_weight', 'timestamp'],
            'classes': ['collapse']
        })
    ]
    
    def get_book_title(self, obj):
        return obj.book_title or '-'
    get_book_title.short_description = 'Livre'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'book')


@admin.register(RecommendationSet)
class RecommendationSetAdmin(admin.ModelAdmin):
    """Administration des ensembles de recommandations"""
    
    list_display = [
        'id', 'user', 'algorithm_type', 'context',
        'recommendations_count', 'view_count', 'click_count', 'conversion_count',
        'click_through_rate', 'conversion_rate', 'is_expired', 'generated_at'
    ]
    
    list_filter = [
        AlgorithmTypeFilter, ActiveRecommendationsFilter,
        'context', 'generated_at', 'expires_at'
    ]
    
    search_fields = ['user__username', 'algorithm_type', 'context']
    
    readonly_fields = [
        'generated_at', 'view_count', 'click_count', 'conversion_count',
        'click_through_rate', 'conversion_rate', 'is_expired'
    ]
    
    inlines = [RecommendationInline]
    
    fieldsets = [
        ('Ensemble', {
            'fields': [
                'user', 'algorithm_type', 'algorithm_version', 'context'
            ]
        }),
        ('Paramètres', {
            'fields': ['parameters', 'expires_at']
        }),
        ('Métriques', {
            'fields': [
                'view_count', 'click_count', 'conversion_count',
                'click_through_rate', 'conversion_rate'
            ]
        }),
        ('Métadonnées', {
            'fields': ['generated_at', 'is_expired'],
            'classes': ['collapse']
        })
    ]
    
    def recommendations_count(self, obj):
        return obj.recommendations.count()
    recommendations_count.short_description = 'Nb recommandations'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('recommendations')


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """Administration des recommandations individuelles"""
    
    list_display = [
        'id', 'recommendation_set_user', 'book_title', 'score', 'position',
        'viewed', 'clicked', 'converted', 'viewed_at'
    ]
    
    list_filter = [
        'viewed', 'clicked', 'converted',
        'recommendation_set__algorithm_type',
        'viewed_at', 'clicked_at', 'converted_at'
    ]
    
    search_fields = [
        'book__title', 'recommendation_set__user__username'
    ]
    
    readonly_fields = [
        'viewed', 'clicked', 'converted',
        'viewed_at', 'clicked_at', 'converted_at'
    ]
    
    fieldsets = [
        ('Recommandation', {
            'fields': [
                'recommendation_set', 'book', 'score', 'position'
            ]
        }),
        ('Contenu', {
            'fields': ['reasons', 'explanation']
        }),
        ('Interactions', {
            'fields': [
                'viewed', 'clicked', 'converted',
                'viewed_at', 'clicked_at', 'converted_at'
            ]
        })
    ]
    
    def recommendation_set_user(self, obj):
        return obj.recommendation_set.user.username
    recommendation_set_user.short_description = 'Utilisateur'
    
    def get_book_title(self, obj):
        return obj.book_title or '-'
    get_book_title.short_description = 'Livre'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recommendation_set__user', 'book'
        )


@admin.register(SimilarityMatrix)
class SimilarityMatrixAdmin(admin.ModelAdmin):
    """Administration de la matrice de similarité"""
    
    list_display = [
        'book_a_title', 'book_b_title', 'overall_similarity',
        'content_similarity', 'genre_similarity', 'calculated_at'
    ]
    
    list_filter = ['algorithm_version', 'calculated_at']
    
    search_fields = ['book_a__title', 'book_b__title']
    
    readonly_fields = ['calculated_at']
    
    fieldsets = [
        ('Livres', {
            'fields': ['book_a', 'book_b']
        }),
        ('Similarités', {
            'fields': [
                'content_similarity', 'genre_similarity', 'author_similarity',
                'user_similarity', 'overall_similarity'
            ]
        }),
        ('Métadonnées', {
            'fields': ['calculated_at', 'algorithm_version'],
            'classes': ['collapse']
        })
    ]
    
    def book_a_title(self, obj):
        return obj.book_a.title
    book_a_title.short_description = 'Livre A'
    
    def book_b_title(self, obj):
        return obj.book_b.title
    book_b_title.short_description = 'Livre B'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book_a', 'book_b')


@admin.register(TrendingBook)
class TrendingBookAdmin(admin.ModelAdmin):
    """Administration des livres en tendance"""
    
    list_display = [
        'book_title', 'trend_type', 'trend_score', 'velocity',
        'view_count', 'download_count', 'is_active', 'period_start', 'period_end'
    ]
    
    list_filter = [
        'trend_type', 'period_start', 'period_end', 'created_at'
    ]
    
    search_fields = ['book__title']
    
    readonly_fields = ['created_at', 'updated_at', 'is_active']
    
    fieldsets = [
        ('Livre', {
            'fields': ['book', 'trend_type']
        }),
        ('Métriques', {
            'fields': [
                'trend_score', 'velocity',
                'view_count', 'download_count', 'share_count'
            ]
        }),
        ('Période', {
            'fields': ['period_start', 'period_end', 'is_active']
        }),
        ('Métadonnées', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_book_title(self, obj):
        return obj.book_title or '-'
    get_book_title.short_description = 'Livre'
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def mark_as_active(self, request, queryset):
        # Mettre à jour la période pour marquer comme actif
        updated = 0
        for obj in queryset:
            if obj.period_end > timezone.now():
                updated += 1
        
        self.message_user(
            request,
            f'{updated} livre(s) en tendance marqué(s) comme actif(s).'
        )
    mark_as_active.short_description = 'Marquer comme actif'
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(period_end=timezone.now())
        self.message_user(
            request,
            f'{updated} livre(s) en tendance marqué(s) comme inactif(s).'
        )
    mark_as_inactive.short_description = 'Marquer comme inactif'


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(admin.ModelAdmin):
    """Administration des feedbacks de recommandations"""
    
    list_display = [
        'user', 'recommendation_book', 'feedback_type', 'rating',
        'is_positive', 'feedback_weight', 'created_at'
    ]
    
    list_filter = [
        'feedback_type', 'rating', 'created_at'
    ]
    
    search_fields = [
        'user__username', 'recommendation__book__title', 'comment'
    ]
    
    readonly_fields = ['created_at', 'is_positive', 'feedback_weight']
    
    fieldsets = [
        ('Feedback', {
            'fields': [
                'user', 'recommendation', 'feedback_type', 'rating'
            ]
        }),
        ('Commentaire', {
            'fields': ['comment']
        }),
        ('Métadonnées', {
            'fields': ['is_positive', 'feedback_weight', 'created_at'],
            'classes': ['collapse']
        })
    ]
    
    def recommendation_book(self, obj):
        return obj.recommendation.book.title
    recommendation_book.short_description = 'Livre recommandé'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'recommendation__book'
        )
    
    # Empêcher l'ajout direct (les feedbacks sont créés via l'API)
    def has_add_permission(self, request):
        return False