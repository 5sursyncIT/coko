from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    ReadingSession, ReadingProgress, Bookmark, 
    ReadingGoal, ReadingStatistics
)


@admin.register(ReadingSession)
class ReadingSessionAdmin(admin.ModelAdmin):
    """Administration des sessions de lecture"""
    
    list_display = [
        'user', 'get_book_title', 'status', 'device_type', 
        'progress_percentage', 'total_reading_time', 
        'last_activity', 'created_at'
    ]
    
    list_filter = [
        'status', 'device_type', 'created_at', 'last_activity'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'book_title'
    ]
    
    readonly_fields = [
        'id', 'progress_percentage', 'is_completed', 
        'reading_speed_pages_per_hour', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'user', 'book_uuid', 'book_title', 'status')
        }),
        ('Progression', {
            'fields': (
                'current_page', 'current_position', 'total_pages_read',
                'progress_percentage', 'is_completed'
            )
        }),
        ('Temps de lecture', {
            'fields': (
                'start_time', 'last_activity', 'end_time', 
                'total_reading_time', 'reading_speed_pages_per_hour'
            )
        }),
        ('Appareil et paramètres', {
            'fields': (
                'device_type', 'device_info', 'ip_address', 'user_agent',
                'font_size', 'font_family', 'theme', 'line_height'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_completed', 'mark_as_abandoned', 'reset_progress']
    
    def get_book_title(self, obj):
        """Affiche le titre du livre"""
        return obj.book_title or '-'
    get_book_title.short_description = 'Livre'
    
    def progress_percentage(self, obj):
        """Affiche la progression en pourcentage"""
        progress = obj.progress_percentage
        color = 'green' if progress >= 90 else 'orange' if progress >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, progress
        )
    progress_percentage.short_description = 'Progression'
    
    def mark_as_completed(self, request, queryset):
        """Marque les sessions comme terminées"""
        updated = 0
        for session in queryset:
            if session.status != 'completed':
                session.mark_as_completed()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} session(s) marquée(s) comme terminée(s).'
        )
    mark_as_completed.short_description = 'Marquer comme terminées'
    
    def mark_as_abandoned(self, request, queryset):
        """Marque les sessions comme abandonnées"""
        updated = queryset.update(status='abandoned')
        self.message_user(
            request,
            f'{updated} session(s) marquée(s) comme abandonnée(s).'
        )
    mark_as_abandoned.short_description = 'Marquer comme abandonnées'
    
    def reset_progress(self, request, queryset):
        """Remet à zéro la progression"""
        updated = queryset.update(
            current_page=1,
            current_position=0.0,
            total_pages_read=0,
            total_reading_time=timezone.timedelta()
        )
        self.message_user(
            request,
            f'Progression remise à zéro pour {updated} session(s).'
        )
    reset_progress.short_description = 'Remettre à zéro la progression'


class ReadingProgressInline(admin.TabularInline):
    """Inline pour la progression de lecture"""
    model = ReadingProgress
    extra = 0
    readonly_fields = ['timestamp']
    fields = ['page_number', 'position_in_page', 'chapter_title', 'time_spent', 'timestamp']


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    """Administration de la progression de lecture"""
    
    list_display = [
        'session_user', 'session_book', 'page_number', 
        'chapter_title', 'time_spent', 'timestamp'
    ]
    
    list_filter = ['timestamp', 'session__status']
    
    search_fields = [
        'session__user__username', 'session__book_title', 'chapter_title'
    ]
    
    readonly_fields = ['id', 'timestamp']
    
    def session_user(self, obj):
        """Affiche l'utilisateur de la session"""
        return obj.session.user.username
    session_user.short_description = 'Utilisateur'
    
    def session_book(self, obj):
        """Affiche le livre de la session"""
        return obj.session.book_title
    session_book.short_description = 'Livre'


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    """Administration des signets"""
    
    list_display = [
        'user', 'get_book_title', 'type', 'page_number', 
        'is_favorite', 'is_private', 'created_at'
    ]
    
    list_filter = [
        'type', 'is_favorite', 'is_private', 'created_at'
    ]
    
    search_fields = [
        'user__username', 'book_title', 'title', 'content', 'note'
    ]
    
    readonly_fields = ['id', 'preview_text', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'user', 'book_uuid', 'book_title', 'type')
        }),
        ('Contenu', {
            'fields': ('title', 'content', 'note', 'preview_text')
        }),
        ('Position', {
            'fields': (
                'page_number', 'position_in_page', 'chapter_title',
                'start_offset', 'end_offset'
            )
        }),
        ('Paramètres', {
            'fields': (
                'highlight_color', 'is_private', 'is_favorite'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_favorite', 'mark_as_public', 'mark_as_private']
    
    def get_book_title(self, obj):
        """Affiche le titre du livre"""
        return obj.book_title
    get_book_title.short_description = 'Livre'
    
    def mark_as_favorite(self, request, queryset):
        """Marque les signets comme favoris"""
        updated = queryset.update(is_favorite=True)
        self.message_user(
            request,
            f'{updated} signet(s) marqué(s) comme favori(s).'
        )
    mark_as_favorite.short_description = 'Marquer comme favoris'
    
    def mark_as_public(self, request, queryset):
        """Rend les signets publics"""
        updated = queryset.update(is_private=False)
        self.message_user(
            request,
            f'{updated} signet(s) rendu(s) public(s).'
        )
    mark_as_public.short_description = 'Rendre publics'
    
    def mark_as_private(self, request, queryset):
        """Rend les signets privés"""
        updated = queryset.update(is_private=True)
        self.message_user(
            request,
            f'{updated} signet(s) rendu(s) privé(s).'
        )
    mark_as_private.short_description = 'Rendre privés'


@admin.register(ReadingGoal)
class ReadingGoalAdmin(admin.ModelAdmin):
    """Administration des objectifs de lecture"""
    
    list_display = [
        'user', 'title', 'goal_type', 'progress_display', 
        'status', 'days_remaining', 'created_at'
    ]
    
    list_filter = [
        'goal_type', 'status', 'is_public', 'send_reminders',
        'start_date', 'end_date', 'created_at'
    ]
    
    search_fields = [
        'user__username', 'title', 'description'
    ]
    
    readonly_fields = [
        'id', 'progress_percentage', 'is_completed', 
        'days_remaining', 'daily_target_remaining',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'user', 'title', 'description')
        }),
        ('Objectif', {
            'fields': (
                'goal_type', 'target_value', 'current_value',
                'progress_percentage', 'is_completed'
            )
        }),
        ('Période', {
            'fields': (
                'start_date', 'end_date', 'days_remaining',
                'daily_target_remaining'
            )
        }),
        ('Filtres', {
            'fields': ('category_uuid', 'author_uuid'),
            'classes': ('collapse',)
        }),
        ('Paramètres', {
            'fields': ('status', 'is_public', 'send_reminders')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['update_progress', 'mark_as_completed', 'mark_as_active']
    
    def progress_display(self, obj):
        """Affiche la progression avec barre de progression"""
        progress = obj.progress_percentage
        color = 'green' if progress >= 90 else 'orange' if progress >= 50 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">' +
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">' +
            '{:.1f}%</div></div>',
            progress, color, progress
        )
    progress_display.short_description = 'Progression'
    
    def update_progress(self, request, queryset):
        """Met à jour la progression des objectifs"""
        updated = 0
        for goal in queryset:
            goal.update_progress()
            updated += 1
        
        self.message_user(
            request,
            f'Progression mise à jour pour {updated} objectif(s).'
        )
    update_progress.short_description = 'Mettre à jour la progression'
    
    def mark_as_completed(self, request, queryset):
        """Marque les objectifs comme terminés"""
        updated = queryset.update(status='completed')
        self.message_user(
            request,
            f'{updated} objectif(s) marqué(s) comme terminé(s).'
        )
    mark_as_completed.short_description = 'Marquer comme terminés'
    
    def mark_as_active(self, request, queryset):
        """Marque les objectifs comme actifs"""
        updated = queryset.update(status='active')
        self.message_user(
            request,
            f'{updated} objectif(s) marqué(s) comme actif(s).'
        )
    mark_as_active.short_description = 'Marquer comme actifs'


@admin.register(ReadingStatistics)
class ReadingStatisticsAdmin(admin.ModelAdmin):
    """Administration des statistiques de lecture"""
    
    list_display = [
        'user', 'period_type', 'period_start', 'period_end',
        'books_completed', 'pages_read', 'reading_sessions_count'
    ]
    
    list_filter = [
        'period_type', 'period_start', 'preferred_device'
    ]
    
    search_fields = ['user__username']
    
    readonly_fields = [
        'id', 'average_pages_per_day', 'reading_consistency',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'user', 'period_type', 'period_start', 'period_end')
        }),
        ('Statistiques de lecture', {
            'fields': (
                'books_started', 'books_completed', 'pages_read',
                'total_reading_time', 'average_pages_per_day'
            )
        }),
        ('Statistiques de session', {
            'fields': (
                'reading_sessions_count', 'average_session_duration',
                'longest_session_duration', 'reading_consistency'
            )
        }),
        ('Préférences', {
            'fields': (
                'most_read_category_uuid', 'favorite_reading_time',
                'preferred_device'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Les statistiques sont générées automatiquement"""
        return False