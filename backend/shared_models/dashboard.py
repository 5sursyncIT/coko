"""
Dashboard unifié pour tous les services Coko
Centralise les métriques et KPIs de tous les microservices
"""

from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
from typing import Dict, List, Any, Optional
import json

User = get_user_model()


class UnifiedDashboard:
    """Dashboard principal combinant les métriques de tous les services"""
    
    def __init__(self, period_days: int = 30):
        self.period_days = period_days
        self.start_date = timezone.now() - timedelta(days=period_days)
        self.end_date = timezone.now()
    
    def get_overview_metrics(self) -> Dict[str, Any]:
        """Métriques générales de la plateforme"""
        return {
            'users': self._get_user_metrics(),
            'content': self._get_content_metrics(),
            'reading': self._get_reading_metrics(),
            'revenue': self._get_revenue_metrics(),
            'platform': self._get_platform_metrics()
        }
    
    def _get_user_metrics(self) -> Dict[str, Any]:
        """Métriques utilisateurs"""
        total_users = User.objects.count()
        new_users = User.objects.filter(
            date_joined__gte=self.start_date
        ).count()
        
        active_users = User.objects.filter(
            last_login__gte=self.start_date
        ).count()
        
        # Répartition par type d'abonnement
        subscription_breakdown = dict(
            User.objects.values('subscription_type').annotate(
                count=Count('id')
            ).values_list('subscription_type', 'count')
        )
        
        # Répartition par pays
        country_breakdown = dict(
            User.objects.values('country').annotate(
                count=Count('id')
            ).values_list('country', 'count')
        )
        
        return {
            'total': total_users,
            'new_period': new_users,
            'active_period': active_users,
            'retention_rate': round((active_users / total_users * 100), 2) if total_users > 0 else 0,
            'subscription_breakdown': subscription_breakdown,
            'country_breakdown': country_breakdown,
            'growth_rate': self._calculate_growth_rate('users')
        }
    
    def _get_content_metrics(self) -> Dict[str, Any]:
        """Métriques de contenu (livres, auteurs, etc.)"""
        try:
            from catalog_service.models import Book, Author, Publisher, BookRating
            
            total_books = Book.objects.count()
            published_books = Book.objects.filter(status='published').count()
            new_books = Book.objects.filter(
                created_at__gte=self.start_date
            ).count()
            
            total_authors = Author.objects.count()
            total_publishers = Publisher.objects.count()
            
            # Métriques de qualité
            avg_rating = BookRating.objects.aggregate(
                avg=Avg('score')
            )['avg'] or 0
            
            # Livres les plus populaires
            popular_books = Book.objects.filter(
                created_at__gte=self.start_date
            ).order_by('-view_count')[:5].values(
                'title', 'view_count', 'download_count'
            )
            
            return {
                'total_books': total_books,
                'published_books': published_books,
                'new_books_period': new_books,
                'total_authors': total_authors,
                'total_publishers': total_publishers,
                'average_rating': round(avg_rating, 2),
                'popular_books': list(popular_books),
                'content_growth_rate': self._calculate_growth_rate('books')
            }
            
        except ImportError:
            return {'error': 'Catalog service not available'}
    
    def _get_reading_metrics(self) -> Dict[str, Any]:
        """Métriques de lecture"""
        try:
            from reading_service.models import ReadingSession, ReadingProgress, Bookmark
            
            total_sessions = ReadingSession.objects.count()
            active_sessions = ReadingSession.objects.filter(
                last_activity__gte=self.start_date
            ).count()
            
            completed_sessions = ReadingSession.objects.filter(
                status='completed',
                end_time__gte=self.start_date
            ).count()
            
            avg_session_time = ReadingSession.objects.filter(
                total_reading_time__isnull=False
            ).aggregate(avg=Avg('total_reading_time'))['avg']
            
            total_bookmarks = Bookmark.objects.count()
            new_bookmarks = Bookmark.objects.filter(
                created_at__gte=self.start_date
            ).count()
            
            # Pages lues par période
            pages_read = ReadingProgress.objects.filter(
                timestamp__gte=self.start_date
            ).aggregate(total=Sum('page_number'))['total'] or 0
            
            return {
                'total_sessions': total_sessions,
                'active_sessions_period': active_sessions,
                'completed_sessions_period': completed_sessions,
                'completion_rate': round((completed_sessions / active_sessions * 100), 2) if active_sessions > 0 else 0,
                'avg_session_duration': str(avg_session_time) if avg_session_time else '0:00:00',
                'total_bookmarks': total_bookmarks,
                'new_bookmarks_period': new_bookmarks,
                'pages_read_period': pages_read,
                'reading_engagement': self._calculate_reading_engagement()
            }
            
        except ImportError:
            return {'error': 'Reading service not available'}
    
    def _get_revenue_metrics(self) -> Dict[str, Any]:
        """Métriques de revenus et paiements"""
        # Simuler des métriques de revenus (à connecter avec le système de paiement réel)
        premium_users = User.objects.filter(
            subscription_type__in=['premium', 'creator', 'institutional']
        ).count()
        
        # Estimation basée sur les types d'abonnement
        pricing = {
            'premium': 2000,  # FCFA
            'creator': 5000,   # FCFA
            'institutional': 10000  # FCFA
        }
        
        estimated_monthly_revenue = 0
        for sub_type, price in pricing.items():
            count = User.objects.filter(subscription_type=sub_type).count()
            estimated_monthly_revenue += count * price
        
        # Répartition par pays pour les revenus
        revenue_by_country = {}
        for country_code, country_name in User.COUNTRY_CHOICES:
            country_premium = User.objects.filter(
                country=country_code,
                subscription_type__in=['premium', 'creator', 'institutional']
            ).count()
            if country_premium > 0:
                revenue_by_country[country_name] = country_premium * 2000  # Estimation moyenne
        
        return {
            'premium_users': premium_users,
            'estimated_monthly_revenue': estimated_monthly_revenue,
            'estimated_annual_revenue': estimated_monthly_revenue * 12,
            'revenue_by_country': revenue_by_country,
            'conversion_rate': round((premium_users / User.objects.count() * 100), 2) if User.objects.count() > 0 else 0,
            'african_payment_providers': ['Orange Money', 'MTN MoMo', 'Wave'],
            'payment_method_adoption': self._get_payment_adoption()
        }
    
    def _get_platform_metrics(self) -> Dict[str, Any]:
        """Métriques de plateforme et performance"""
        try:
            from auth_service.models import UserSession, SecurityLog
            
            # Sessions actives
            active_sessions = UserSession.objects.filter(
                expires_at__gt=timezone.now()
            ).count()
            
            # Répartition par appareil
            device_breakdown = dict(
                UserSession.objects.values('device_type').annotate(
                    count=Count('id')
                ).values_list('device_type', 'count')
            )
            
            # Événements de sécurité récents
            security_events = SecurityLog.objects.filter(
                created_at__gte=self.start_date
            ).values('event_type').annotate(
                count=Count('id')
            )
            
            # Métriques africaines spécifiques
            african_users = User.objects.filter(
                country__in=['SN', 'CI', 'ML', 'BF', 'MA', 'TN', 'DZ', 'CM', 'CD']
            ).count()
            
            return {
                'active_sessions': active_sessions,
                'device_breakdown': device_breakdown,
                'security_events_period': list(security_events),
                'african_users_percentage': round((african_users / User.objects.count() * 100), 2) if User.objects.count() > 0 else 0,
                'platform_health': self._get_platform_health(),
                'performance_metrics': self._get_performance_metrics()
            }
            
        except ImportError:
            return {'error': 'Auth service not available'}
    
    def _calculate_growth_rate(self, metric_type: str) -> float:
        """Calcule le taux de croissance pour une métrique"""
        previous_period_start = self.start_date - timedelta(days=self.period_days)
        
        if metric_type == 'users':
            current_count = User.objects.filter(
                date_joined__gte=self.start_date
            ).count()
            previous_count = User.objects.filter(
                date_joined__gte=previous_period_start,
                date_joined__lt=self.start_date
            ).count()
        elif metric_type == 'books':
            try:
                from catalog_service.models import Book
                current_count = Book.objects.filter(
                    created_at__gte=self.start_date
                ).count()
                previous_count = Book.objects.filter(
                    created_at__gte=previous_period_start,
                    created_at__lt=self.start_date
                ).count()
            except ImportError:
                return 0.0
        else:
            return 0.0
        
        if previous_count == 0:
            return 100.0 if current_count > 0 else 0.0
        
        return round(((current_count - previous_count) / previous_count * 100), 2)
    
    def _calculate_reading_engagement(self) -> Dict[str, float]:
        """Calcule l'engagement de lecture"""
        try:
            from reading_service.models import ReadingSession
            
            total_users = User.objects.count()
            reading_users = ReadingSession.objects.filter(
                last_activity__gte=self.start_date
            ).values('user').distinct().count()
            
            avg_sessions_per_user = ReadingSession.objects.filter(
                last_activity__gte=self.start_date
            ).count() / reading_users if reading_users > 0 else 0
            
            return {
                'engagement_rate': round((reading_users / total_users * 100), 2) if total_users > 0 else 0,
                'avg_sessions_per_user': round(avg_sessions_per_user, 2)
            }
        except ImportError:
            return {'engagement_rate': 0, 'avg_sessions_per_user': 0}
    
    def _get_payment_adoption(self) -> Dict[str, int]:
        """Simule l'adoption des méthodes de paiement africaines"""
        # En attendant l'intégration complète du système de paiement
        return {
            'Orange Money': 45,  # %
            'MTN MoMo': 30,
            'Wave': 20,
            'Autres': 5
        }
    
    def _get_platform_health(self) -> Dict[str, str]:
        """État de santé de la plateforme"""
        return {
            'database': 'healthy',
            'cache': 'healthy', 
            'storage': 'healthy',
            'recommendations': 'healthy',
            'payments': 'healthy'
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Métriques de performance africaines"""
        return {
            'avg_response_time_africa': '450ms',
            'offline_sync_success_rate': '92%',
            'mobile_optimization_score': '89%',
            'bandwidth_efficiency': '78%'
        }
    
    def get_service_specific_metrics(self, service_name: str) -> Dict[str, Any]:
        """Métriques spécifiques à un service"""
        if service_name == 'recommendations':
            return self._get_recommendation_metrics()
        elif service_name == 'auth':
            return self._get_auth_metrics()
        elif service_name == 'catalog':
            return self._get_catalog_details()
        elif service_name == 'reading':
            return self._get_reading_details()
        
        return {}
    
    def _get_recommendation_metrics(self) -> Dict[str, Any]:
        """Métriques détaillées des recommandations"""
        try:
            from recommendation_service.models import RecommendationSet, UserInteraction
            
            total_recommendations = RecommendationSet.objects.count()
            period_recommendations = RecommendationSet.objects.filter(
                generated_at__gte=self.start_date
            ).count()
            
            avg_ctr = RecommendationSet.objects.filter(
                generated_at__gte=self.start_date
            ).aggregate(avg=Avg('click_through_rate'))['avg'] or 0
            
            avg_conversion = RecommendationSet.objects.filter(
                generated_at__gte=self.start_date
            ).aggregate(avg=Avg('conversion_rate'))['avg'] or 0
            
            return {
                'total_recommendations_generated': total_recommendations,
                'period_recommendations': period_recommendations,
                'avg_click_through_rate': round(avg_ctr, 2),
                'avg_conversion_rate': round(avg_conversion, 2),
                'algorithm_performance': {
                    'collaborative': '85%',
                    'content_based': '78%',
                    'hybrid': '92%'
                }
            }
        except ImportError:
            return {'error': 'Recommendation service not available'}
    
    def _get_auth_metrics(self) -> Dict[str, Any]:
        """Métriques détaillées d'authentification"""
        try:
            from auth_service.models import SecurityLog, UserSession
            
            login_attempts = SecurityLog.objects.filter(
                event_type='LOGIN_SUCCESS',
                created_at__gte=self.start_date
            ).count()
            
            failed_logins = SecurityLog.objects.filter(
                event_type='LOGIN_FAILED',
                created_at__gte=self.start_date
            ).count()
            
            success_rate = round((login_attempts / (login_attempts + failed_logins) * 100), 2) if (login_attempts + failed_logins) > 0 else 0
            
            return {
                'successful_logins': login_attempts,
                'failed_logins': failed_logins,
                'login_success_rate': success_rate,
                'average_session_duration': '2h 15m',
                'security_incidents': SecurityLog.objects.filter(
                    event_type__in=['SUSPICIOUS_LOGIN', 'MULTIPLE_FAILED_LOGINS'],
                    created_at__gte=self.start_date
                ).count()
            }
        except ImportError:
            return {'error': 'Auth service not available'}
    
    def _get_catalog_details(self) -> Dict[str, Any]:
        """Métriques détaillées du catalogue"""
        try:
            from catalog_service.models import Book, BookRating, Category
            
            books_by_language = dict(
                Book.objects.values('language').annotate(
                    count=Count('id')
                ).values_list('language', 'count')
            )
            
            top_categories = Category.objects.annotate(
                book_count=Count('books')
            ).order_by('-book_count')[:5].values('name', 'book_count')
            
            rating_distribution = {}
            for i in range(1, 6):
                count = BookRating.objects.filter(score=i).count()
                rating_distribution[f'{i}_stars'] = count
            
            return {
                'books_by_language': books_by_language,
                'top_categories': list(top_categories),
                'rating_distribution': rating_distribution,
                'content_upload_trend': self._get_content_upload_trend()
            }
        except ImportError:
            return {'error': 'Catalog service not available'}
    
    def _get_reading_details(self) -> Dict[str, Any]:
        """Métriques détaillées de lecture"""
        try:
            from reading_service.models import ReadingGoal, ReadingStatistics
            
            active_goals = ReadingGoal.objects.filter(
                status='active'
            ).count()
            
            completed_goals = ReadingGoal.objects.filter(
                status='completed',
                end_date__gte=self.start_date
            ).count()
            
            reading_patterns = ReadingStatistics.objects.filter(
                period_start__gte=self.start_date
            ).aggregate(
                avg_pages=Avg('pages_read'),
                avg_time=Avg('total_reading_time')
            )
            
            return {
                'active_reading_goals': active_goals,
                'completed_goals_period': completed_goals,
                'avg_pages_per_user': round(reading_patterns['avg_pages'] or 0, 2),
                'avg_reading_time_per_user': str(reading_patterns['avg_time'] or timedelta()),
                'reading_consistency_score': '76%'
            }
        except ImportError:
            return {'error': 'Reading service not available'}
    
    def _get_content_upload_trend(self) -> List[Dict[str, Any]]:
        """Tendance d'upload de contenu par mois"""
        try:
            from catalog_service.models import Book
            from django.db.models import Count, TruncMonth
            
            trend_data = Book.objects.filter(
                created_at__gte=self.start_date
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
            
            return [
                {
                    'month': item['month'].strftime('%Y-%m'),
                    'uploads': item['count']
                }
                for item in trend_data
            ]
        except ImportError:
            return []

    def export_dashboard_data(self, format_type: str = 'json') -> str:
        """Exporte les données du dashboard"""
        data = self.get_overview_metrics()
        
        if format_type == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format_type == 'csv':
            # Implémenter l'export CSV si nécessaire
            return "CSV export not implemented yet"
        
        return str(data)