from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Avg, Q, F, Sum
from django.core.cache import cache
import logging
from datetime import timedelta
from typing import Dict, List, Any
import json

from recommendation_service.models import (
    RecommendationSet, Recommendation, UserInteraction, 
    RecommendationFeedback, UserProfile
)
from recommendation_service.utils import (
    calculate_diversity_score, calculate_novelty_score
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Analyser les performances des recommandations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'all'],
            default='weekly',
            help='Période d\'analyse (défaut: weekly)'
        )
        
        parser.add_argument(
            '--algorithm',
            type=str,
            choices=['content_based', 'collaborative', 'popularity', 'hybrid', 'all'],
            default='all',
            help='Algorithme à analyser (défaut: all)'
        )
        
        parser.add_argument(
            '--user-id',
            type=int,
            help='Analyser les recommandations pour un utilisateur spécifique'
        )
        
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Affichage détaillé des métriques'
        )
        
        parser.add_argument(
            '--export',
            type=str,
            help='Exporter les résultats vers un fichier JSON'
        )
        
        parser.add_argument(
            '--compare-algorithms',
            action='store_true',
            help='Comparer les performances des différents algorithmes'
        )
        
        parser.add_argument(
            '--user-segments',
            action='store_true',
            help='Analyser par segments d\'utilisateurs'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé des opérations'
        )
    
    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        
        try:
            # Calculer la période d'analyse
            end_date = timezone.now()
            start_date = self._get_start_date(options['period'], end_date)
            
            self._log(f"Analyse des recommandations du {start_date.strftime('%Y-%m-%d')} au {end_date.strftime('%Y-%m-%d')}")
            
            # Collecter les données d'analyse
            analysis_data = {
                'period': options['period'],
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'overall_metrics': self._calculate_overall_metrics(start_date, end_date),
                'algorithm_performance': {},
                'user_segments': {},
                'recommendations_by_day': self._get_recommendations_by_day(start_date, end_date)
            }
            
            # Analyser par algorithme
            algorithms = [options['algorithm']] if options['algorithm'] != 'all' else [
                'content_based', 'collaborative', 'popularity', 'hybrid'
            ]
            
            for algorithm in algorithms:
                analysis_data['algorithm_performance'][algorithm] = self._analyze_algorithm(
                    algorithm, start_date, end_date, options
                )
            
            # Analyser par segments d'utilisateurs
            if options['user_segments']:
                analysis_data['user_segments'] = self._analyze_user_segments(
                    start_date, end_date, options
                )
            
            # Analyser un utilisateur spécifique
            if options['user_id']:
                analysis_data['user_analysis'] = self._analyze_user(
                    options['user_id'], start_date, end_date, options
                )
            
            # Afficher les résultats
            self._display_results(analysis_data, options)
            
            # Exporter si demandé
            if options['export']:
                self._export_results(analysis_data, options['export'])
            
            # Comparer les algorithmes
            if options['compare_algorithms']:
                self._compare_algorithms(analysis_data['algorithm_performance'])
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {str(e)}")
            raise CommandError(f"Erreur: {str(e)}")
    
    def _get_start_date(self, period: str, end_date):
        """Calculer la date de début selon la période"""
        if period == 'daily':
            return end_date - timedelta(days=1)
        elif period == 'weekly':
            return end_date - timedelta(weeks=1)
        elif period == 'monthly':
            return end_date - timedelta(days=30)
        elif period == 'all':
            return end_date - timedelta(days=365)  # 1 an max
        else:
            raise CommandError(f"Période inconnue: {period}")
    
    def _calculate_overall_metrics(self, start_date, end_date) -> Dict[str, Any]:
        """Calculer les métriques globales"""
        # Recommandations générées
        total_recommendations = RecommendationSet.objects.filter(
            created_at__range=[start_date, end_date]
        ).count()
        
        total_individual_recs = Recommendation.objects.filter(
            recommendation_set__created_at__range=[start_date, end_date]
        ).count()
        
        # Interactions avec les recommandations
        recommendation_interactions = UserInteraction.objects.filter(
            created_at__range=[start_date, end_date],
            recommendation__isnull=False
        )
        
        clicks = recommendation_interactions.filter(interaction_type='view').count()
        downloads = recommendation_interactions.filter(interaction_type='download').count()
        ratings = recommendation_interactions.filter(interaction_type='rating').count()
        
        # Taux de conversion
        ctr = (clicks / total_individual_recs * 100) if total_individual_recs > 0 else 0
        download_rate = (downloads / total_individual_recs * 100) if total_individual_recs > 0 else 0
        rating_rate = (ratings / total_individual_recs * 100) if total_individual_recs > 0 else 0
        
        # Feedback
        feedback_stats = RecommendationFeedback.objects.filter(
            created_at__range=[start_date, end_date]
        ).aggregate(
            total_feedback=Count('id'),
            positive_feedback=Count('id', filter=Q(rating__gte=4)),
            negative_feedback=Count('id', filter=Q(rating__lt=3)),
            avg_rating=Avg('rating')
        )
        
        # Utilisateurs actifs
        active_users = UserProfile.objects.filter(
            user__userinteraction__created_at__range=[start_date, end_date]
        ).distinct().count()
        
        return {
            'total_recommendation_sets': total_recommendations,
            'total_individual_recommendations': total_individual_recs,
            'total_clicks': clicks,
            'total_downloads': downloads,
            'total_ratings': ratings,
            'click_through_rate': round(ctr, 2),
            'download_rate': round(download_rate, 2),
            'rating_rate': round(rating_rate, 2),
            'total_feedback': feedback_stats['total_feedback'] or 0,
            'positive_feedback': feedback_stats['positive_feedback'] or 0,
            'negative_feedback': feedback_stats['negative_feedback'] or 0,
            'avg_feedback_rating': round(feedback_stats['avg_rating'] or 0, 2),
            'active_users': active_users
        }
    
    def _analyze_algorithm(self, algorithm: str, start_date, end_date, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyser les performances d'un algorithme spécifique"""
        # Recommandations de cet algorithme
        algorithm_recs = RecommendationSet.objects.filter(
            algorithm=algorithm,
            created_at__range=[start_date, end_date]
        )
        
        total_sets = algorithm_recs.count()
        if total_sets == 0:
            return {
                'total_sets': 0,
                'total_recommendations': 0,
                'performance_metrics': {}
            }
        
        # Recommandations individuelles
        individual_recs = Recommendation.objects.filter(
            recommendation_set__in=algorithm_recs
        )
        
        total_individual = individual_recs.count()
        
        # Interactions
        interactions = UserInteraction.objects.filter(
            recommendation__in=individual_recs,
            created_at__range=[start_date, end_date]
        )
        
        clicks = interactions.filter(interaction_type='view').count()
        downloads = interactions.filter(interaction_type='download').count()
        ratings = interactions.filter(interaction_type='rating').count()
        
        # Métriques de performance
        ctr = (clicks / total_individual * 100) if total_individual > 0 else 0
        download_rate = (downloads / total_individual * 100) if total_individual > 0 else 0
        rating_rate = (ratings / total_individual * 100) if total_individual > 0 else 0
        
        # Feedback spécifique à cet algorithme
        feedback_stats = RecommendationFeedback.objects.filter(
            recommendation__recommendation_set__algorithm=algorithm,
            created_at__range=[start_date, end_date]
        ).aggregate(
            total_feedback=Count('id'),
            avg_rating=Avg('rating'),
            positive_feedback=Count('id', filter=Q(rating__gte=4))
        )
        
        # Métriques de qualité (diversité, nouveauté)
        quality_metrics = self._calculate_quality_metrics(individual_recs)
        
        return {
            'total_sets': total_sets,
            'total_recommendations': total_individual,
            'performance_metrics': {
                'clicks': clicks,
                'downloads': downloads,
                'ratings': ratings,
                'click_through_rate': round(ctr, 2),
                'download_rate': round(download_rate, 2),
                'rating_rate': round(rating_rate, 2),
                'avg_feedback_rating': round(feedback_stats['avg_rating'] or 0, 2),
                'total_feedback': feedback_stats['total_feedback'] or 0,
                'positive_feedback_rate': round(
                    (feedback_stats['positive_feedback'] or 0) / max(feedback_stats['total_feedback'] or 1, 1) * 100, 2
                )
            },
            'quality_metrics': quality_metrics
        }
    
    def _calculate_quality_metrics(self, recommendations) -> Dict[str, float]:
        """Calculer les métriques de qualité des recommandations"""
        if not recommendations.exists():
            return {'diversity': 0.0, 'novelty': 0.0, 'coverage': 0.0}
        
        # Échantillon pour éviter les calculs trop longs
        sample_recs = recommendations.select_related('book')[:1000]
        
        try:
            # Diversité (variété des genres/auteurs)
            books = [rec.book for rec in sample_recs if rec.book]
            if not books:
                return {'diversity': 0.0, 'novelty': 0.0, 'coverage': 0.0}
            
            diversity = calculate_diversity_score(books)
            novelty = calculate_novelty_score(books)
            
            # Couverture (nombre de livres uniques recommandés)
            unique_books = recommendations.values('book').distinct().count()
            total_books = recommendations.count()
            coverage = (unique_books / total_books * 100) if total_books > 0 else 0
            
            return {
                'diversity': round(diversity, 2),
                'novelty': round(novelty, 2),
                'coverage': round(coverage, 2)
            }
            
        except Exception as e:
            logger.warning(f"Erreur lors du calcul des métriques de qualité: {str(e)}")
            return {'diversity': 0.0, 'novelty': 0.0, 'coverage': 0.0}
    
    def _analyze_user_segments(self, start_date, end_date, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyser par segments d'utilisateurs"""
        segments = {
            'new_users': UserProfile.objects.filter(
                user__date_joined__gte=start_date - timedelta(days=30)
            ),
            'active_users': UserProfile.objects.filter(
                user__userinteraction__created_at__range=[start_date, end_date]
            ).distinct(),
            'premium_users': UserProfile.objects.filter(
                preferences__get('premium', False)
            )
        }
        
        segment_analysis = {}
        
        for segment_name, users in segments.items():
            user_ids = list(users.values_list('user_id', flat=True))
            
            if not user_ids:
                segment_analysis[segment_name] = {
                    'user_count': 0,
                    'recommendations': 0,
                    'engagement': {}
                }
                continue
            
            # Recommandations pour ce segment
            segment_recs = RecommendationSet.objects.filter(
                user_id__in=user_ids,
                created_at__range=[start_date, end_date]
            )
            
            # Interactions de ce segment
            segment_interactions = UserInteraction.objects.filter(
                user_id__in=user_ids,
                created_at__range=[start_date, end_date],
                recommendation__isnull=False
            )
            
            clicks = segment_interactions.filter(interaction_type='view').count()
            downloads = segment_interactions.filter(interaction_type='download').count()
            
            total_recs = Recommendation.objects.filter(
                recommendation_set__in=segment_recs
            ).count()
            
            segment_analysis[segment_name] = {
                'user_count': len(user_ids),
                'recommendations': segment_recs.count(),
                'total_individual_recs': total_recs,
                'engagement': {
                    'clicks': clicks,
                    'downloads': downloads,
                    'ctr': round((clicks / total_recs * 100) if total_recs > 0 else 0, 2),
                    'download_rate': round((downloads / total_recs * 100) if total_recs > 0 else 0, 2)
                }
            }
        
        return segment_analysis
    
    def _analyze_user(self, user_id: int, start_date, end_date, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyser les recommandations pour un utilisateur spécifique"""
        try:
            user_profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            raise CommandError(f"Utilisateur {user_id} introuvable")
        
        # Recommandations de l'utilisateur
        user_recs = RecommendationSet.objects.filter(
            user_id=user_id,
            created_at__range=[start_date, end_date]
        )
        
        # Interactions de l'utilisateur avec les recommandations
        user_interactions = UserInteraction.objects.filter(
            user_id=user_id,
            created_at__range=[start_date, end_date],
            recommendation__isnull=False
        )
        
        # Feedback de l'utilisateur
        user_feedback = RecommendationFeedback.objects.filter(
            user_id=user_id,
            created_at__range=[start_date, end_date]
        )
        
        return {
            'user_id': user_id,
            'username': user_profile.user.username,
            'recommendation_sets': user_recs.count(),
            'total_recommendations': Recommendation.objects.filter(
                recommendation_set__in=user_recs
            ).count(),
            'interactions': {
                'total': user_interactions.count(),
                'views': user_interactions.filter(interaction_type='view').count(),
                'downloads': user_interactions.filter(interaction_type='download').count(),
                'ratings': user_interactions.filter(interaction_type='rating').count()
            },
            'feedback': {
                'total': user_feedback.count(),
                'avg_rating': user_feedback.aggregate(avg=Avg('rating'))['avg'] or 0
            },
            'preferences': user_profile.preferences
        }
    
    def _get_recommendations_by_day(self, start_date, end_date) -> List[Dict[str, Any]]:
        """Obtenir les recommandations par jour"""
        daily_stats = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            day_start = timezone.make_aware(timezone.datetime.combine(current_date, timezone.datetime.min.time()))
            day_end = day_start + timedelta(days=1)
            
            day_recs = RecommendationSet.objects.filter(
                created_at__range=[day_start, day_end]
            ).count()
            
            day_interactions = UserInteraction.objects.filter(
                created_at__range=[day_start, day_end],
                recommendation__isnull=False
            ).count()
            
            daily_stats.append({
                'date': current_date.isoformat(),
                'recommendations': day_recs,
                'interactions': day_interactions
            })
            
            current_date += timedelta(days=1)
        
        return daily_stats
    
    def _display_results(self, analysis_data: Dict[str, Any], options: Dict[str, Any]):
        """Afficher les résultats de l'analyse"""
        self._log("\n" + "="*60)
        self._log("RAPPORT D'ANALYSE DES RECOMMANDATIONS")
        self._log("="*60)
        
        # Métriques globales
        overall = analysis_data['overall_metrics']
        self._log("\nMÉTRIQUES GLOBALES:")
        self._log("-" * 20)
        self._log(f"Ensembles de recommandations: {overall['total_recommendation_sets']}")
        self._log(f"Recommandations individuelles: {overall['total_individual_recommendations']}")
        self._log(f"Taux de clic: {overall['click_through_rate']}%")
        self._log(f"Taux de téléchargement: {overall['download_rate']}%")
        self._log(f"Note moyenne feedback: {overall['avg_feedback_rating']}/5")
        self._log(f"Utilisateurs actifs: {overall['active_users']}")
        
        # Performance par algorithme
        if analysis_data['algorithm_performance']:
            self._log("\nPERFORMANCE PAR ALGORITHME:")
            self._log("-" * 30)
            
            for algo, perf in analysis_data['algorithm_performance'].items():
                if perf['total_sets'] > 0:
                    self._log(f"\n{algo.upper()}:")
                    self._log(f"  Ensembles: {perf['total_sets']}")
                    self._log(f"  CTR: {perf['performance_metrics']['click_through_rate']}%")
                    self._log(f"  Téléchargements: {perf['performance_metrics']['download_rate']}%")
                    self._log(f"  Diversité: {perf['quality_metrics']['diversity']}")
                    self._log(f"  Nouveauté: {perf['quality_metrics']['novelty']}")
        
        # Segments d'utilisateurs
        if analysis_data['user_segments']:
            self._log("\nANALYSE PAR SEGMENTS:")
            self._log("-" * 25)
            
            for segment, data in analysis_data['user_segments'].items():
                if data['user_count'] > 0:
                    self._log(f"\n{segment.upper()}:")
                    self._log(f"  Utilisateurs: {data['user_count']}")
                    self._log(f"  CTR: {data['engagement']['ctr']}%")
                    self._log(f"  Téléchargements: {data['engagement']['download_rate']}%")
    
    def _compare_algorithms(self, algorithm_performance: Dict[str, Any]):
        """Comparer les performances des algorithmes"""
        self._log("\n" + "="*60)
        self._log("COMPARAISON DES ALGORITHMES")
        self._log("="*60)
        
        # Trier par CTR
        sorted_algos = sorted(
            algorithm_performance.items(),
            key=lambda x: x[1]['performance_metrics'].get('click_through_rate', 0),
            reverse=True
        )
        
        self._log("\nClassement par taux de clic:")
        for i, (algo, perf) in enumerate(sorted_algos, 1):
            if perf['total_sets'] > 0:
                ctr = perf['performance_metrics']['click_through_rate']
                self._log(f"{i}. {algo}: {ctr}%")
        
        # Recommandations
        best_ctr = sorted_algos[0] if sorted_algos else None
        if best_ctr and best_ctr[1]['total_sets'] > 0:
            self._log(f"\n🏆 Meilleur algorithme (CTR): {best_ctr[0]}")
            self._log("Recommandation: Privilégier cet algorithme pour l'engagement")
    
    def _export_results(self, analysis_data: Dict[str, Any], export_path: str):
        """Exporter les résultats vers un fichier JSON"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False, default=str)
            
            self._log_success(f"Résultats exportés vers: {export_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export: {str(e)}")
            self._log_error(f"Erreur lors de l'export: {str(e)}")
    
    def _log(self, message: str):
        """Logger un message selon le niveau de verbosité"""
        if self.verbosity >= 1:
            self.stdout.write(message)
        
        logger.info(message)
    
    def _log_success(self, message: str):
        """Logger un message de succès"""
        if self.verbosity >= 1:
            self.stdout.write(self.style.SUCCESS(message))
        
        logger.info(message)
    
    def _log_error(self, message: str):
        """Logger un message d'erreur"""
        if self.verbosity >= 1:
            self.stdout.write(self.style.ERROR(message))
        
        logger.error(message)