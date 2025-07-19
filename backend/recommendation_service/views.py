from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta, datetime
import logging
import json

from catalog_service.models import Book
from .models import (
    UserProfile, BookVector, UserInteraction, RecommendationSet,
    Recommendation, SimilarityMatrix, TrendingBook, RecommendationFeedback
)
from .serializers import (
    UserProfileSerializer, UserProfileCreateSerializer,
    BookVectorSerializer, UserInteractionSerializer, UserInteractionCreateSerializer,
    RecommendationSetSerializer, RecommendationSetCreateSerializer,
    RecommendationSerializer, RecommendationDetailSerializer,
    SimilarityMatrixSerializer, TrendingBookSerializer,
    RecommendationFeedbackSerializer, RecommendationStatsSerializer,
    PersonalizedRecommendationSerializer, RecommendationEngineConfigSerializer,
    RecommendationAnalyticsSerializer
)
from .permissions import (
    IsOwnerOrReadOnly, CanAccessRecommendations, CanManageRecommendations,
    CanViewRecommendationAnalytics, IsAdminOrOwner
)
# from .utils import (
#     generate_personalized_recommendations, calculate_recommendation_stats,
#     update_recommendation_metrics, get_trending_books,
#     calculate_user_similarity, generate_content_based_recommendations,
#     generate_collaborative_recommendations, get_recommendation_analytics
# )

User = get_user_model()
logger = logging.getLogger(__name__)


class UserProfileListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des profils utilisateur"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserProfileCreateSerializer
        return UserProfileSerializer
    
    def perform_create(self, serializer):
        # Vérifier qu'un profil n'existe pas déjà
        if UserProfile.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError(
                "Un profil de recommandations existe déjà pour cet utilisateur."
            )
        
        serializer.save(user=self.request.user)
        
        # Invalider le cache des recommandations
        cache_key = f"user_recommendations_{self.request.user.id}"
        cache.delete(cache_key)
        
        logger.info(f"Profil de recommandations créé pour l'utilisateur {self.request.user.username}")


class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour récupérer, modifier et supprimer un profil utilisateur"""
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save()
        
        # Invalider le cache des recommandations
        cache_key = f"user_recommendations_{self.request.user.id}"
        cache.delete(cache_key)
        
        logger.info(f"Profil de recommandations mis à jour pour l'utilisateur {self.request.user.username}")
    
    def perform_destroy(self, instance):
        user_id = instance.user.id
        instance.delete()
        
        # Nettoyer le cache
        cache_key = f"user_recommendations_{user_id}"
        cache.delete(cache_key)
        
        logger.info(f"Profil de recommandations supprimé pour l'utilisateur {instance.user.username}")


class UserInteractionListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des interactions utilisateur"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = UserInteraction.objects.filter(user=self.request.user)
        
        # Filtres
        book_id = self.request.query_params.get('book')
        interaction_type = self.request.query_params.get('type')
        from_recommendation = self.request.query_params.get('from_recommendation')
        
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        
        if interaction_type:
            queryset = queryset.filter(interaction_type=interaction_type)
        
        if from_recommendation is not None:
            queryset = queryset.filter(from_recommendation=from_recommendation.lower() == 'true')
        
        return queryset.order_by('-timestamp')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserInteractionCreateSerializer
        return UserInteractionSerializer
    
    def perform_create(self, serializer):
        interaction = serializer.save(user=self.request.user)
        
        # Mettre à jour les métriques de recommandation si applicable
        # if interaction.from_recommendation and interaction.recommendation_algorithm:
        #     update_recommendation_metrics(
        #         user=self.request.user,
        #         book=interaction.book,
        #         interaction_type=interaction.interaction_type,
        #         algorithm=interaction.recommendation_algorithm
        #     )
        
        # Invalider le cache des recommandations
        cache_key = f"user_recommendations_{self.request.user.id}"
        cache.delete(cache_key)
        
        logger.info(
            f"Interaction {interaction.interaction_type} enregistrée pour "
            f"l'utilisateur {self.request.user.username} et le livre {interaction.book.title}"
        )


class RecommendationSetListView(generics.ListAPIView):
    """Vue pour lister les ensembles de recommandations"""
    
    serializer_class = RecommendationSetSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = RecommendationSet.objects.filter(user=self.request.user)
        
        # Filtres
        algorithm_type = self.request.query_params.get('algorithm')
        active_only = self.request.query_params.get('active_only', 'false').lower() == 'true'
        
        if algorithm_type:
            queryset = queryset.filter(algorithm_type=algorithm_type)
        
        if active_only:
            queryset = queryset.filter(expires_at__gt=timezone.now())
        
        return queryset.order_by('-generated_at')


class RecommendationSetDetailView(generics.RetrieveAPIView):
    """Vue pour récupérer un ensemble de recommandations"""
    
    serializer_class = RecommendationSetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return RecommendationSet.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Incrémenter le compteur de vues
        instance.view_count = F('view_count') + 1
        instance.save(update_fields=['view_count'])
        
        # Marquer les recommandations comme vues
        instance.recommendations.filter(viewed=False).update(
            viewed=True,
            viewed_at=timezone.now()
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PersonalizedRecommendationsView(APIView):
    """Vue pour obtenir des recommandations personnalisées"""
    
    permission_classes = [permissions.IsAuthenticated, CanAccessRecommendations]
    
    def get(self, request):
        """Obtenir des recommandations personnalisées"""
        user = request.user
        
        # Paramètres de la requête
        algorithm = request.query_params.get('algorithm', 'hybrid')
        count = min(int(request.query_params.get('count', 10)), 50)
        context = request.query_params.get('context', 'general')
        force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'
        
        # Vérifier le cache
        cache_key = f"user_recommendations_{user.id}_{algorithm}_{count}_{context}"
        
        if not force_refresh:
            cached_recommendations = cache.get(cache_key)
            if cached_recommendations:
                return Response(cached_recommendations)
        
        try:
            # Générer les recommandations
            # recommendations_data = generate_personalized_recommendations(
            #     user=user,
            #     algorithm=algorithm,
            #     count=count,
            #     context=context
            # )
            recommendations_data = {'recommendations': [], 'message': 'Service temporairement indisponible'}
            
            # Mettre en cache pour 1 heure
            cache.set(cache_key, recommendations_data, 3600)
            
            logger.info(
                f"Recommandations générées pour l'utilisateur {user.username} "
                f"(algorithme: {algorithm}, contexte: {context})"
            )
            
            return Response(recommendations_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des recommandations: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la génération des recommandations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SimilarBooksView(APIView):
    """Vue pour obtenir des livres similaires"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, book_id):
        """Obtenir des livres similaires à un livre donné"""
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response(
                {'error': 'Livre non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        count = min(int(request.query_params.get('count', 10)), 20)
        
        # Vérifier le cache
        cache_key = f"similar_books_{book_id}_{count}"
        cached_similar = cache.get(cache_key)
        
        if cached_similar:
            return Response(cached_similar)
        
        try:
            # Obtenir les livres similaires via la matrice de similarité
            similar_books = SimilarityMatrix.objects.filter(
                Q(book_a=book) | Q(book_b=book)
            ).order_by('-overall_similarity')[:count]
            
            similar_data = []
            for similarity in similar_books:
                similar_book = similarity.book_b if similarity.book_a == book else similarity.book_a
                similar_data.append({
                    'book': {
                        'id': similar_book.id,
                        'title': similar_book.title,
                        'slug': similar_book.slug,
                        'cover_image': similar_book.cover_image.url if similar_book.cover_image else None
                    },
                    'similarity_score': similarity.overall_similarity,
                    'reasons': {
                        'content': similarity.content_similarity,
                        'genre': similarity.genre_similarity,
                        'author': similarity.author_similarity,
                        'user_behavior': similarity.user_similarity
                    }
                })
            
            response_data = {
                'book': {
                    'id': book.id,
                    'title': book.title,
                    'slug': book.slug
                },
                'similar_books': similar_data,
                'algorithm': 'similarity_matrix',
                'generated_at': timezone.now()
            }
            
            # Mettre en cache pour 6 heures
            cache.set(cache_key, response_data, 21600)
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de livres similaires: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la recherche de livres similaires'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrendingBooksView(generics.ListAPIView):
    """Vue pour obtenir les livres en tendance"""
    
    serializer_class = TrendingBookSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        trend_type = self.request.query_params.get('type', 'overall')
        period = self.request.query_params.get('period', 'week')
        
        queryset = TrendingBook.objects.filter(
            trend_type=trend_type,
            is_active=True
        )
        
        # Filtrer par période
        if period == 'day':
            start_date = timezone.now() - timedelta(days=1)
        elif period == 'week':
            start_date = timezone.now() - timedelta(weeks=1)
        elif period == 'month':
            start_date = timezone.now() - timedelta(days=30)
        else:
            start_date = timezone.now() - timedelta(weeks=1)
        
        queryset = queryset.filter(period_start__gte=start_date)
        
        return queryset.order_by('-trend_score')[:20]


class RecommendationFeedbackListCreateView(generics.ListCreateAPIView):
    """Vue pour lister et créer des feedbacks de recommandations"""
    
    serializer_class = RecommendationFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RecommendationFeedback.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        feedback = serializer.save(user=self.request.user)
        
        logger.info(
            f"Feedback de recommandation créé par l'utilisateur {self.request.user.username} "
            f"pour la recommandation {feedback.recommendation.id}"
        )


class RecommendationStatsView(APIView):
    """Vue pour obtenir les statistiques de recommandations"""
    
    permission_classes = [permissions.IsAuthenticated, CanViewRecommendationAnalytics]
    
    def get(self, request):
        """Obtenir les statistiques de recommandations"""
        period = request.query_params.get('period', 'month')
        user_id = request.query_params.get('user_id')
        
        # Seuls les admins peuvent voir les stats d'autres utilisateurs
        if user_id and not request.user.is_staff:
            user_id = request.user.id
        elif not user_id:
            user_id = request.user.id
        
        try:
            stats = calculate_recommendation_stats(
                user_id=user_id,
                period=period
            )
            
            serializer = RecommendationStatsSerializer(stats)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return Response(
                {'error': 'Erreur lors du calcul des statistiques'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecommendationAnalyticsView(APIView):
    """Vue pour obtenir les analytics de recommandations (admin)"""
    
    permission_classes = [permissions.IsAuthenticated, CanViewRecommendationAnalytics]
    
    def get(self, request):
        """Obtenir les analytics de recommandations"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Accès non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        period = request.query_params.get('period', 'month')
        
        try:
            analytics = get_recommendation_analytics(period=period)
            serializer = RecommendationAnalyticsSerializer(analytics)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des analytics: {str(e)}")
            return Response(
                {'error': 'Erreur lors du calcul des analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecommendationEngineConfigView(APIView):
    """Vue pour gérer la configuration du moteur de recommandations (admin)"""
    
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get(self, request):
        """Obtenir la configuration actuelle"""
        config = cache.get('recommendation_engine_config', {})
        
        # Configuration par défaut
        default_config = {
            'enabled_algorithms': ['content_based', 'collaborative', 'hybrid'],
            'algorithm_weights': {
                'content_based': 0.3,
                'collaborative': 0.4,
                'hybrid': 0.3
            },
            'diversity_factor': 0.3,
            'novelty_factor': 0.2,
            'popularity_boost': 1.0,
            'min_rating': 0.0,
            'exclude_read_books': True,
            'max_recommendations': 10,
            'cache_duration': 3600
        }
        
        config = {**default_config, **config}
        serializer = RecommendationEngineConfigSerializer(config)
        return Response(serializer.data)
    
    def post(self, request):
        """Mettre à jour la configuration"""
        serializer = RecommendationEngineConfigSerializer(data=request.data)
        
        if serializer.is_valid():
            # Sauvegarder la configuration en cache
            cache.set('recommendation_engine_config', serializer.validated_data, None)
            
            # Invalider tous les caches de recommandations
            cache.delete_many([key for key in cache._cache.keys() if 'recommendations' in key])
            
            logger.info(f"Configuration du moteur de recommandations mise à jour par {request.user.username}")
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecommendationInteractionView(APIView):
    """Vue pour enregistrer les interactions avec les recommandations"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, recommendation_id):
        """Enregistrer une interaction avec une recommandation"""
        try:
            recommendation = Recommendation.objects.get(
                id=recommendation_id,
                recommendation_set__user=request.user
            )
        except Recommendation.DoesNotExist:
            return Response(
                {'error': 'Recommandation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        interaction_type = request.data.get('type')
        
        if interaction_type == 'click':
            if not recommendation.clicked:
                recommendation.clicked = True
                recommendation.clicked_at = timezone.now()
                recommendation.save()
                
                # Incrémenter le compteur de clics de l'ensemble
                recommendation.recommendation_set.click_count = F('click_count') + 1
                recommendation.recommendation_set.save(update_fields=['click_count'])
        
        elif interaction_type == 'convert':
            if not recommendation.converted:
                recommendation.converted = True
                recommendation.converted_at = timezone.now()
                recommendation.save()
                
                # Incrémenter le compteur de conversions de l'ensemble
                recommendation.recommendation_set.conversion_count = F('conversion_count') + 1
                recommendation.recommendation_set.save(update_fields=['conversion_count'])
        
        # Enregistrer l'interaction utilisateur
        UserInteraction.objects.create(
            user=request.user,
            book=recommendation.book,
            interaction_type=interaction_type,
            from_recommendation=True,
            recommendation_algorithm=recommendation.recommendation_set.algorithm_type,
            recommendation_score=recommendation.score
        )
        
        return Response({'status': 'success'})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """Point de contrôle de santé pour le service de recommandations"""
    try:
        # Vérifier la base de données
        user_profiles_count = UserProfile.objects.count()
        recommendations_count = RecommendationSet.objects.count()
        
        # Vérifier le cache
        cache_test_key = 'health_check_test'
        cache.set(cache_test_key, 'ok', 60)
        cache_status = cache.get(cache_test_key) == 'ok'
        cache.delete(cache_test_key)
        
        return Response({
            'status': 'healthy',
            'service': 'recommendation_service',
            'timestamp': timezone.now(),
            'database': {
                'status': 'connected',
                'user_profiles': user_profiles_count,
                'recommendation_sets': recommendations_count
            },
            'cache': {
                'status': 'connected' if cache_status else 'error'
            },
            'version': '1.0.0'
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du contrôle de santé: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'service': 'recommendation_service',
            'timestamp': timezone.now(),
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)