from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg, Max
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import uuid

from .models import (
    ReadingSession, ReadingProgress, Bookmark, 
    ReadingGoal, ReadingStatistics
)
from .serializers import (
    ReadingSessionSerializer, ReadingSessionCreateSerializer, ReadingSessionUpdateSerializer,
    ReadingProgressSerializer, BookmarkSerializer, BookmarkCreateSerializer,
    ReadingGoalSerializer, ReadingGoalCreateSerializer, ReadingStatisticsSerializer,
    ReadingDashboardSerializer, ReadingSessionStatsSerializer, BookmarkStatsSerializer,
    ReadingProgressStatsSerializer, UserReadingPreferencesSerializer,
    ReadingRecommendationSerializer, ReadingAnalyticsSerializer
)
from .permissions import IsOwnerOrReadOnly, CanAccessReadingData
from .utils import (
    calculate_reading_statistics, get_reading_recommendations,
    update_reading_goals, generate_reading_insights
)

User = get_user_model()


class ReadingSessionListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des sessions de lecture"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ReadingSession.objects.filter(user=self.request.user)
        
        # Filtres
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        device_type = self.request.query_params.get('device_type')
        if device_type:
            queryset = queryset.filter(device_type=device_type)
        
        return queryset.select_related('book').order_by('-last_activity')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReadingSessionCreateSerializer
        return ReadingSessionSerializer
    
    def perform_create(self, serializer):
        # Vérifier s'il existe déjà une session active pour ce livre
        book = serializer.validated_data['book']
        existing_session = ReadingSession.objects.filter(
            user=self.request.user,
            book=book,
            status='active'
        ).first()
        
        if existing_session:
            # Reprendre la session existante
            existing_session.last_activity = timezone.now()
            existing_session.save()
            return existing_session
        
        # Créer une nouvelle session
        session = serializer.save(
            user=self.request.user,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Mettre à jour les statistiques
        update_reading_goals(self.request.user)
        
        return session


class ReadingSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour récupérer, modifier et supprimer une session de lecture"""
    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return ReadingSession.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ReadingSessionUpdateSerializer
        return ReadingSessionSerializer
    
    def perform_update(self, serializer):
        session = serializer.save()
        
        # Mettre à jour les objectifs de lecture
        update_reading_goals(self.request.user)
        
        # Invalider le cache des statistiques
        cache_key = f"reading_stats_{self.request.user.id}"
        cache.delete(cache_key)


class ReadingProgressListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des entrées de progression"""
    
    serializer_class = ReadingProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        session_id = self.request.query_params.get('session')
        if session_id:
            return ReadingProgress.objects.filter(
                session_id=session_id,
                session__user=self.request.user
            ).order_by('-timestamp')
        
        return ReadingProgress.objects.filter(
            session__user=self.request.user
        ).order_by('-timestamp')
    
    def perform_create(self, serializer):
        # Vérifier que la session appartient à l'utilisateur
        session = serializer.validated_data['session']
        if session.user != self.request.user:
            raise permissions.PermissionDenied("Vous ne pouvez pas modifier cette session.")
        
        progress = serializer.save()
        
        # Mettre à jour la session
        session.current_page = progress.page_number
        session.last_activity = timezone.now()
        session.save()


class BookmarkListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des signets"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Bookmark.objects.filter(user=self.request.user)
        
        # Filtres
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        bookmark_type = self.request.query_params.get('type')
        if bookmark_type:
            queryset = queryset.filter(type=bookmark_type)
        
        is_favorite = self.request.query_params.get('favorite')
        if is_favorite is not None:
            queryset = queryset.filter(is_favorite=is_favorite.lower() == 'true')
        
        return queryset.select_related('book').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookmarkCreateSerializer
        return BookmarkSerializer


class BookmarkDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour récupérer, modifier et supprimer un signet"""
    
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)


class ReadingGoalListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des objectifs de lecture"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ReadingGoal.objects.filter(user=self.request.user)
        
        # Filtres
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        goal_type = self.request.query_params.get('type')
        if goal_type:
            queryset = queryset.filter(goal_type=goal_type)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReadingGoalCreateSerializer
        return ReadingGoalSerializer
    
    def perform_create(self, serializer):
        goal = serializer.save(user=self.request.user)
        
        # Mettre à jour immédiatement la progression
        goal.update_progress()


class ReadingGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour récupérer, modifier et supprimer un objectif de lecture"""
    
    serializer_class = ReadingGoalSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return ReadingGoal.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        goal = serializer.save()
        goal.update_progress()


class ReadingDashboardView(APIView):
    """Vue pour le tableau de bord de lecture"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Sessions actives
        active_sessions = ReadingSession.objects.filter(
            user=user,
            status='active'
        ).select_related('book')[:5]
        
        # Statistiques récentes
        books_read_this_month = ReadingSession.objects.filter(
            user=user,
            status='completed',
            end_time__date__gte=month_start
        ).count()
        
        pages_read_this_week = ReadingProgress.objects.filter(
            session__user=user,
            timestamp__date__gte=week_start
        ).count()
        
        reading_time_this_week = ReadingSession.objects.filter(
            user=user,
            last_activity__date__gte=week_start
        ).aggregate(total=Sum('total_reading_time'))['total'] or timedelta()
        
        # Streak de lecture
        current_streak = self._calculate_reading_streak(user)
        
        # Objectifs actifs
        active_goals = ReadingGoal.objects.filter(
            user=user,
            status='active'
        )[:3]
        
        # Signets récents
        recent_bookmarks = Bookmark.objects.filter(
            user=user
        ).select_related('book')[:5]
        
        # Recommandations
        recommended_books = get_reading_recommendations(user)
        
        data = {
            'active_sessions': ReadingSessionSerializer(active_sessions, many=True).data,
            'books_read_this_month': books_read_this_month,
            'pages_read_this_week': pages_read_this_week,
            'reading_time_this_week': reading_time_this_week,
            'current_reading_streak': current_streak,
            'active_goals': ReadingGoalSerializer(active_goals, many=True).data,
            'recent_bookmarks': BookmarkSerializer(recent_bookmarks, many=True).data,
            'recommended_books': recommended_books
        }
        
        return Response(data)
    
    def _calculate_reading_streak(self, user):
        """Calcule la série de jours consécutifs avec lecture"""
        today = timezone.now().date()
        streak = 0
        current_date = today
        
        while True:
            has_reading = ReadingSession.objects.filter(
                user=user,
                last_activity__date=current_date
            ).exists()
            
            if has_reading:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
            
            # Limite pour éviter les boucles infinies
            if streak > 365:
                break
        
        return streak


class ReadingStatisticsView(APIView):
    """Vue pour les statistiques de lecture"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        period = request.query_params.get('period', 'monthly')  # daily, weekly, monthly, yearly
        
        # Vérifier le cache
        cache_key = f"reading_stats_{user.id}_{period}"
        cached_stats = cache.get(cache_key)
        if cached_stats:
            return Response(cached_stats)
        
        # Calculer les statistiques
        stats = calculate_reading_statistics(user, period)
        
        # Mettre en cache pour 1 heure
        cache.set(cache_key, stats, 3600)
        
        return Response(stats)


class ReadingAnalyticsView(APIView):
    """Vue pour les analyses avancées de lecture"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Générer les analyses
        analytics = {
            'reading_trends': self._get_reading_trends(user),
            'compared_to_last_month': self._compare_to_last_month(user),
            'compared_to_average_user': self._compare_to_average_user(user),
            'reading_insights': generate_reading_insights(user),
            'yearly_projection': self._calculate_yearly_projection(user),
            'goal_achievement_probability': self._calculate_goal_probability(user)
        }
        
        return Response(analytics)
    
    def _get_reading_trends(self, user):
        """Obtient les tendances de lecture sur les 12 derniers mois"""
        today = timezone.now().date()
        trends = []
        
        for i in range(12):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            stats = ReadingSession.objects.filter(
                user=user,
                last_activity__date__gte=month_start,
                last_activity__date__lte=month_end
            ).aggregate(
                books_completed=Count('id', filter=Q(status='completed')),
                total_time=Sum('total_reading_time'),
                pages_read=Sum('total_pages_read')
            )
            
            trends.append({
                'month': month_start.strftime('%Y-%m'),
                'books_completed': stats['books_completed'] or 0,
                'total_time_hours': (stats['total_time'].total_seconds() / 3600) if stats['total_time'] else 0,
                'pages_read': stats['pages_read'] or 0
            })
        
        return list(reversed(trends))
    
    def _compare_to_last_month(self, user):
        """Compare les statistiques avec le mois précédent"""
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)
        
        this_month_stats = ReadingSession.objects.filter(
            user=user,
            last_activity__date__gte=this_month_start
        ).aggregate(
            books=Count('id', filter=Q(status='completed')),
            time=Sum('total_reading_time'),
            pages=Sum('total_pages_read')
        )
        
        last_month_stats = ReadingSession.objects.filter(
            user=user,
            last_activity__date__gte=last_month_start,
            last_activity__date__lte=last_month_end
        ).aggregate(
            books=Count('id', filter=Q(status='completed')),
            time=Sum('total_reading_time'),
            pages=Sum('total_pages_read')
        )
        
        def calculate_change(current, previous):
            if previous and previous > 0:
                return ((current - previous) / previous) * 100
            return 0 if current == 0 else 100
        
        return {
            'books_change': calculate_change(
                this_month_stats['books'] or 0,
                last_month_stats['books'] or 0
            ),
            'time_change': calculate_change(
                (this_month_stats['time'].total_seconds() / 3600) if this_month_stats['time'] else 0,
                (last_month_stats['time'].total_seconds() / 3600) if last_month_stats['time'] else 0
            ),
            'pages_change': calculate_change(
                this_month_stats['pages'] or 0,
                last_month_stats['pages'] or 0
            )
        }
    
    def _compare_to_average_user(self, user):
        """Compare avec la moyenne des utilisateurs"""
        # Statistiques de l'utilisateur ce mois
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        user_stats = ReadingSession.objects.filter(
            user=user,
            last_activity__date__gte=month_start
        ).aggregate(
            books=Count('id', filter=Q(status='completed')),
            time=Sum('total_reading_time'),
            pages=Sum('total_pages_read')
        )
        
        # Moyenne de tous les utilisateurs
        avg_stats = ReadingSession.objects.filter(
            last_activity__date__gte=month_start
        ).aggregate(
            avg_books=Avg('user__reading_sessions__id'),
            avg_time=Avg('total_reading_time'),
            avg_pages=Avg('total_pages_read')
        )
        
        return {
            'books_vs_average': (user_stats['books'] or 0) - (avg_stats['avg_books'] or 0),
            'time_vs_average': ((user_stats['time'].total_seconds() / 3600) if user_stats['time'] else 0) - 
                             ((avg_stats['avg_time'].total_seconds() / 3600) if avg_stats['avg_time'] else 0),
            'pages_vs_average': (user_stats['pages'] or 0) - (avg_stats['avg_pages'] or 0)
        }
    
    def _calculate_yearly_projection(self, user):
        """Calcule la projection annuelle basée sur les tendances actuelles"""
        today = timezone.now().date()
        year_start = today.replace(month=1, day=1)
        days_passed = (today - year_start).days + 1
        days_remaining = (today.replace(year=today.year + 1) - today).days
        
        year_stats = ReadingSession.objects.filter(
            user=user,
            last_activity__date__gte=year_start
        ).aggregate(
            books=Count('id', filter=Q(status='completed')),
            pages=Sum('total_pages_read')
        )
        
        books_per_day = (year_stats['books'] or 0) / days_passed
        pages_per_day = (year_stats['pages'] or 0) / days_passed
        
        return {
            'projected_books': (year_stats['books'] or 0) + (books_per_day * days_remaining),
            'projected_pages': (year_stats['pages'] or 0) + (pages_per_day * days_remaining),
            'current_books': year_stats['books'] or 0,
            'current_pages': year_stats['pages'] or 0
        }
    
    def _calculate_goal_probability(self, user):
        """Calcule la probabilité d'atteindre les objectifs actifs"""
        active_goals = ReadingGoal.objects.filter(
            user=user,
            status='active'
        )
        
        if not active_goals.exists():
            return 0
        
        total_probability = 0
        for goal in active_goals:
            if goal.days_remaining > 0:
                required_daily_rate = (goal.target_value - goal.current_value) / goal.days_remaining
                current_daily_rate = goal.daily_target_remaining
                
                if required_daily_rate <= current_daily_rate:
                    probability = min(100, (current_daily_rate / required_daily_rate) * 100)
                else:
                    probability = max(0, 100 - ((required_daily_rate - current_daily_rate) / required_daily_rate) * 100)
                
                total_probability += probability
        
        return total_probability / active_goals.count()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_reading_position(request):
    """Met à jour la position de lecture"""
    session_id = request.data.get('session_id')
    page_number = request.data.get('page_number')
    position_in_page = request.data.get('position_in_page', 0.0)
    time_spent = request.data.get('time_spent', 0)  # en secondes
    
    try:
        session = ReadingSession.objects.get(
            id=session_id,
            user=request.user
        )
        
        # Mettre à jour la session
        session.current_page = page_number
        session.current_position = (page_number / session.book.page_count) * 100 if session.book.page_count else 0
        session.last_activity = timezone.now()
        
        if time_spent > 0:
            session.total_reading_time += timedelta(seconds=time_spent)
        
        session.save()
        
        # Créer une entrée de progression
        ReadingProgress.objects.create(
            session=session,
            page_number=page_number,
            position_in_page=position_in_page,
            time_spent=timedelta(seconds=time_spent)
        )
        
        # Mettre à jour les objectifs
        update_reading_goals(request.user)
        
        return Response({
            'status': 'success',
            'progress_percentage': session.progress_percentage
        })
        
    except ReadingSession.DoesNotExist:
        return Response(
            {'error': 'Session de lecture non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_reading_session(request, session_id):
    """Marque une session de lecture comme terminée"""
    try:
        session = ReadingSession.objects.get(
            id=session_id,
            user=request.user
        )
        
        session.mark_as_completed()
        
        # Mettre à jour les objectifs
        update_reading_goals(request.user)
        
        return Response({
            'status': 'success',
            'message': 'Session de lecture terminée'
        })
        
    except ReadingSession.DoesNotExist:
        return Response(
            {'error': 'Session de lecture non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def reading_recommendations(request):
    """Obtient des recommandations de lecture personnalisées"""
    user = request.user
    limit = int(request.query_params.get('limit', 10))
    
    recommendations = get_reading_recommendations(user, limit=limit)
    
    return Response({
        'recommendations': recommendations,
        'count': len(recommendations)
    })


@api_view(['GET'])
def health_check(request):
    """Vérification de l'état du service de lecture"""
    return Response({
        'status': 'healthy',
        'service': 'reading_service',
        'timestamp': timezone.now().isoformat()
    })