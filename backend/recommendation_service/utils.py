import numpy as np
import pandas as pd
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg, F, Sum
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta, datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
import random
from collections import defaultdict

# Suppression des imports directs - utilisation des services
from coko.services import get_book_service, get_reading_service
from coko.interfaces import BookServiceInterface, ReadingServiceInterface
from .models import (
    UserProfile, BookVector, UserInteraction, RecommendationSet,
    Recommendation, SimilarityMatrix, TrendingBook, RecommendationFeedback
)

User = get_user_model()
logger = logging.getLogger(__name__)


def generate_personalized_recommendations(
    user: User,
    algorithm: str = 'hybrid',
    count: int = 10,
    context: str = 'general'
) -> Dict[str, Any]:
    """Générer des recommandations personnalisées pour un utilisateur"""
    
    try:
        # Obtenir ou créer le profil utilisateur
        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'preferred_genres': [],
                'preferred_authors': [],
                'preferred_languages': ['fr'],
                'enable_recommendations': True
            }
        )
        
        if not user_profile.enable_recommendations:
            return {
                'books': [],
                'algorithm_used': algorithm,
                'confidence_score': 0.0,
                'reasons': ['Recommandations désactivées par l\'utilisateur'],
                'generated_at': timezone.now(),
                'expires_at': timezone.now() + timedelta(hours=24),
                'context': context,
                'user_preferences': {},
                'diversity_score': 0.0,
                'novelty_score': 0.0
            }
        
        # Obtenir les livres déjà lus/interagis
        read_books = set(
            UserInteraction.objects.filter(
                user=user,
                interaction_type__in=['read', 'completed', 'rating']
            ).values_list('book_id', flat=True)
        )
        
        # Générer les recommandations selon l'algorithme
        if algorithm == 'content_based':
            recommendations = generate_content_based_recommendations(
                user, user_profile, read_books, count, context
            )
        elif algorithm == 'collaborative':
            recommendations = generate_collaborative_recommendations(
                user, user_profile, read_books, count, context
            )
        elif algorithm == 'popularity':
            recommendations = generate_popularity_based_recommendations(
                user, user_profile, read_books, count, context
            )
        elif algorithm == 'hybrid':
            recommendations = generate_hybrid_recommendations(
                user, user_profile, read_books, count, context
            )
        else:
            recommendations = generate_hybrid_recommendations(
                user, user_profile, read_books, count, context
            )
        
        # Calculer les scores de diversité et nouveauté
        diversity_score = calculate_diversity_score(recommendations)
        novelty_score = calculate_novelty_score(recommendations, user)
        
        # Préparer la réponse
        response_data = {
            'books': [{
                'id': book_data['id'] if isinstance(book_data, dict) else book_data.id,
                'title': book_data['title'] if isinstance(book_data, dict) else book_data.title,
                'slug': book_data['slug'] if isinstance(book_data, dict) else book_data.slug,
                'authors': [author['name'] if isinstance(author, dict) else author for author in book_data.get('authors', [])] if isinstance(book_data, dict) else [author.name for author in book_data.authors.all()],
                'categories': [cat['name'] if isinstance(cat, dict) else cat for cat in book_data.get('categories', [])] if isinstance(book_data, dict) else [cat.name for cat in book_data.categories.all()],
                'cover_image': book_data.get('cover_image') if isinstance(book_data, dict) else (book_data.cover_image.url if book_data.cover_image else None),
                'average_rating': book_data.get('average_rating') if isinstance(book_data, dict) else book_data.average_rating,
                'publication_date': book_data.get('publication_date') if isinstance(book_data, dict) else book_data.publication_date,
                'score': score,
                'reasons': reasons
            } for book_data, score, reasons in recommendations],
            'algorithm_used': algorithm,
            'confidence_score': calculate_confidence_score(recommendations, user_profile),
            'reasons': get_algorithm_explanation(algorithm),
            'generated_at': timezone.now(),
            'expires_at': timezone.now() + timedelta(hours=24),
            'context': context,
            'user_preferences': {
                'preferred_genres': user_profile.preferred_genres,
                'preferred_authors': user_profile.preferred_authors,
                'reading_level': user_profile.reading_level,
                'reading_frequency': user_profile.reading_frequency
            },
            'diversity_score': diversity_score,
            'novelty_score': novelty_score
        }
        
        # Sauvegarder l'ensemble de recommandations
        save_recommendation_set(user, algorithm, recommendations, context)
        
        return response_data
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {str(e)}")
        raise


def generate_content_based_recommendations(
    user: User,
    user_profile: UserProfile,
    read_books: set,
    count: int,
    context: str
) -> List[Tuple[Book, float, List[str]]]:
    """Générer des recommandations basées sur le contenu"""
    
    recommendations = []
    
    # Obtenir les préférences utilisateur
    preferred_genres = user_profile.preferred_genres or []
    preferred_authors = user_profile.preferred_authors or []
    
    # Si pas de préférences, utiliser l'historique de lecture via le service
    if not preferred_genres and not preferred_authors:
        reading_service = get_reading_service()
        book_service = get_book_service()
        
        recent_sessions = reading_service.get_user_reading_history(user.id, limit=10)
        
        for session_data in recent_sessions:
            book_data = book_service.get_book_by_id(session_data['book_id'])
            if book_data:
                preferred_genres.extend([cat['name'] for cat in book_data.get('categories', [])])
                preferred_authors.extend([author['name'] for author in book_data.get('authors', [])])
    
    book_service = get_book_service()
    
    # Obtenir des livres par auteurs préférés
    if preferred_authors:
        author_books = book_service.get_books_by_author(
            preferred_authors,
            limit=count//2
        )
        for book_data in author_books:
            if book_data['id'] not in read_books:
                recommendations.append((book_data, 0.9, ['Auteur préféré']))
    
    # Ajouter des livres par genre
    if preferred_genres and len(recommendations) < count:
        genre_books = book_service.get_books_by_category(
            preferred_genres,
            limit=count - len(recommendations)
        )
        
        existing_book_ids = {rec[0]['id'] for rec in recommendations}
        
        for book_data in genre_books:
            if book_data['id'] not in read_books and book_data['id'] not in existing_book_ids:
                recommendations.append((book_data, 0.7, ['Genre préféré']))
    
    # Compléter avec des livres populaires si nécessaire
    if len(recommendations) < count:
        exclude_ids = list(read_books) + [rec[0]['id'] for rec in recommendations]
        popular_books = book_service.get_popular_books(
            limit=count - len(recommendations),
            exclude_ids=exclude_ids
        )
        
        for book_data in popular_books:
            recommendations.append((book_data, 0.5, ['Livre populaire']))
    
    return recommendations[:count]


def generate_collaborative_recommendations(
    user: User,
    user_profile: UserProfile,
    read_books: set,
    count: int,
    context: str
) -> List[Tuple[Book, float, List[str]]]:
    """Générer des recommandations basées sur le filtrage collaboratif"""
    
    recommendations = []
    
    # Trouver des utilisateurs similaires
    similar_users = find_similar_users(user, limit=20)
    
    if not similar_users:
        # Fallback vers les recommandations basées sur le contenu
        return generate_content_based_recommendations(
            user, user_profile, read_books, count, context
        )
    
    # Obtenir les livres aimés par les utilisateurs similaires
    similar_user_books = defaultdict(list)
    
    for similar_user, similarity_score in similar_users:
        # Obtenir les livres bien notés par cet utilisateur
        liked_books = UserInteraction.objects.filter(
            user=similar_user,
            interaction_type='rating',
            interaction_value__gte=4
        ).exclude(
            book_id__in=read_books
        ).select_related('book')
        
        for interaction in liked_books:
            similar_user_books[interaction.book].append(
                (similarity_score, interaction.interaction_value)
            )
    
    # Calculer les scores de recommandation
    book_scores = []
    for book, user_ratings in similar_user_books.items():
        if not book.is_active:
            continue
            
        # Calculer le score pondéré
        total_weight = sum(sim_score for sim_score, _ in user_ratings)
        weighted_rating = sum(
            sim_score * rating for sim_score, rating in user_ratings
        ) / total_weight if total_weight > 0 else 0
        
        # Normaliser le score
        final_score = min(weighted_rating / 5.0, 1.0)
        
        reasons = [f'Aimé par {len(user_ratings)} utilisateurs similaires']
        book_scores.append((book, final_score, reasons))
    
    # Trier par score et retourner les meilleurs
    book_scores.sort(key=lambda x: x[1], reverse=True)
    recommendations = book_scores[:count]
    
    # Compléter si nécessaire
    if len(recommendations) < count:
        content_recs = generate_content_based_recommendations(
            user, user_profile, read_books, count - len(recommendations), context
        )
        recommendations.extend(content_recs)
    
    return recommendations[:count]


def generate_popularity_based_recommendations(
    user: User,
    user_profile: UserProfile,
    read_books: set,
    count: int,
    context: str
) -> List[Tuple[Book, float, List[str]]]:
    """Générer des recommandations basées sur la popularité"""
    
    # Obtenir les livres populaires
    popular_books = Book.objects.exclude(
        id__in=read_books
    ).filter(
        is_active=True,
        average_rating__gte=3.5
    ).annotate(
        popularity_score=(
            F('view_count') * 0.3 +
            F('download_count') * 0.4 +
            F('average_rating') * F('rating_count') * 0.3
        )
    ).order_by('-popularity_score')[:count]
    
    recommendations = []
    for book in popular_books:
        score = min(book.popularity_score / 1000, 1.0) if book.popularity_score else 0.5
        reasons = ['Livre populaire', f'Note moyenne: {book.average_rating:.1f}']
        recommendations.append((book, score, reasons))
    
    return recommendations


def generate_hybrid_recommendations(
    user: User,
    user_profile: UserProfile,
    read_books: set,
    count: int,
    context: str
) -> List[Tuple[Book, float, List[str]]]:
    """Générer des recommandations hybrides (combinaison d'algorithmes)"""
    
    # Obtenir la configuration des poids
    config = cache.get('recommendation_engine_config', {})
    content_weight = config.get('algorithm_weights', {}).get('content_based', 0.4)
    collaborative_weight = config.get('algorithm_weights', {}).get('collaborative', 0.4)
    popularity_weight = config.get('algorithm_weights', {}).get('popularity', 0.2)
    
    # Générer des recommandations avec chaque algorithme
    content_recs = generate_content_based_recommendations(
        user, user_profile, read_books, count * 2, context
    )
    
    collaborative_recs = generate_collaborative_recommendations(
        user, user_profile, read_books, count * 2, context
    )
    
    popularity_recs = generate_popularity_based_recommendations(
        user, user_profile, read_books, count * 2, context
    )
    
    # Combiner les recommandations
    book_scores = defaultdict(lambda: {'score': 0, 'reasons': set(), 'count': 0})
    
    # Ajouter les scores pondérés
    for book, score, reasons in content_recs:
        book_scores[book]['score'] += score * content_weight
        book_scores[book]['reasons'].update(reasons)
        book_scores[book]['count'] += 1
    
    for book, score, reasons in collaborative_recs:
        book_scores[book]['score'] += score * collaborative_weight
        book_scores[book]['reasons'].update(reasons)
        book_scores[book]['count'] += 1
    
    for book, score, reasons in popularity_recs:
        book_scores[book]['score'] += score * popularity_weight
        book_scores[book]['reasons'].update(reasons)
        book_scores[book]['count'] += 1
    
    # Normaliser les scores et créer la liste finale
    final_recommendations = []
    for book, data in book_scores.items():
        # Bonus pour les livres recommandés par plusieurs algorithmes
        diversity_bonus = min(data['count'] * 0.1, 0.3)
        final_score = min(data['score'] + diversity_bonus, 1.0)
        
        final_recommendations.append((
            book,
            final_score,
            list(data['reasons'])
        ))
    
    # Trier par score et retourner les meilleurs
    final_recommendations.sort(key=lambda x: x[1], reverse=True)
    
    return final_recommendations[:count]


def find_similar_users(user: User, limit: int = 20) -> List[Tuple[User, float]]:
    """Trouver des utilisateurs similaires basés sur les interactions"""
    
    # Obtenir les interactions de l'utilisateur
    user_interactions = UserInteraction.objects.filter(
        user=user,
        interaction_type='rating'
    ).values('book_id', 'interaction_value')
    
    if not user_interactions:
        return []
    
    user_ratings = {item['book_id']: item['interaction_value'] for item in user_interactions}
    
    # Trouver d'autres utilisateurs qui ont noté les mêmes livres
    other_users = User.objects.filter(
        userinteraction__book_id__in=user_ratings.keys(),
        userinteraction__interaction_type='rating'
    ).exclude(id=user.id).distinct()
    
    similar_users = []
    
    for other_user in other_users:
        other_interactions = UserInteraction.objects.filter(
            user=other_user,
            interaction_type='rating',
            book_id__in=user_ratings.keys()
        ).values('book_id', 'interaction_value')
        
        other_ratings = {item['book_id']: item['interaction_value'] for item in other_interactions}
        
        # Calculer la similarité cosinus
        similarity = calculate_cosine_similarity(user_ratings, other_ratings)
        
        if similarity > 0.1:  # Seuil minimum de similarité
            similar_users.append((other_user, similarity))
    
    # Trier par similarité décroissante
    similar_users.sort(key=lambda x: x[1], reverse=True)
    
    return similar_users[:limit]


def calculate_cosine_similarity(ratings1: Dict[int, float], ratings2: Dict[int, float]) -> float:
    """Calculer la similarité cosinus entre deux ensembles de notes"""
    
    # Obtenir les livres en commun
    common_books = set(ratings1.keys()) & set(ratings2.keys())
    
    if len(common_books) < 2:
        return 0.0
    
    # Créer les vecteurs
    vec1 = [ratings1[book] for book in common_books]
    vec2 = [ratings2[book] for book in common_books]
    
    # Calculer la similarité cosinus
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def calculate_diversity_score(recommendations: List[Tuple[Book, float, List[str]]]) -> float:
    """Calculer le score de diversité des recommandations"""
    
    if not recommendations:
        return 0.0
    
    # Obtenir les genres et auteurs
    all_genres = set()
    all_authors = set()
    
    for book, _, _ in recommendations:
        all_genres.update(cat.name for cat in book.categories.all())
        all_authors.update(author.name for author in book.authors.all())
    
    # Calculer la diversité (nombre d'éléments uniques / nombre total)
    genre_diversity = len(all_genres) / len(recommendations)
    author_diversity = len(all_authors) / len(recommendations)
    
    return (genre_diversity + author_diversity) / 2


def calculate_novelty_score(recommendations: List[Tuple[Book, float, List[str]]], user: User) -> float:
    """Calculer le score de nouveauté des recommandations"""
    
    if not recommendations:
        return 0.0
    
    # Obtenir les genres/auteurs déjà connus par l'utilisateur
    known_genres = set()
    known_authors = set()
    
    user_interactions = UserInteraction.objects.filter(
        user=user,
        interaction_type__in=['read', 'rating', 'bookmark']
    ).select_related('book')
    
    for interaction in user_interactions:
        book = interaction.book
        known_genres.update(cat.name for cat in book.categories.all())
        known_authors.update(author.name for author in book.authors.all())
    
    # Calculer la nouveauté
    novel_items = 0
    
    for book, _, _ in recommendations:
        book_genres = set(cat.name for cat in book.categories.all())
        book_authors = set(author.name for author in book.authors.all())
        
        # Vérifier si le livre introduit de nouveaux genres/auteurs
        if not book_genres.issubset(known_genres) or not book_authors.issubset(known_authors):
            novel_items += 1
    
    return novel_items / len(recommendations)


def calculate_confidence_score(recommendations: List[Tuple[Book, float, List[str]]], user_profile: UserProfile) -> float:
    """Calculer le score de confiance des recommandations"""
    
    if not recommendations:
        return 0.0
    
    # Facteurs de confiance
    profile_completeness = calculate_profile_completeness(user_profile)
    avg_recommendation_score = sum(score for _, score, _ in recommendations) / len(recommendations)
    
    # Score de confiance combiné
    confidence = (profile_completeness * 0.4 + avg_recommendation_score * 0.6)
    
    return min(confidence, 1.0)


def calculate_profile_completeness(user_profile: UserProfile) -> float:
    """Calculer le pourcentage de complétude du profil utilisateur"""
    
    completeness = 0.0
    total_fields = 6
    
    if user_profile.preferred_genres:
        completeness += 1
    if user_profile.preferred_authors:
        completeness += 1
    if user_profile.preferred_languages:
        completeness += 1
    if user_profile.reading_level:
        completeness += 1
    if user_profile.reading_frequency:
        completeness += 1
    if user_profile.average_reading_time:
        completeness += 1
    
    return completeness / total_fields


def get_algorithm_explanation(algorithm: str) -> List[str]:
    """Obtenir l'explication d'un algorithme de recommandation"""
    
    explanations = {
        'content_based': [
            'Basé sur vos préférences de genres et d\'auteurs',
            'Analyse du contenu des livres que vous avez aimés'
        ],
        'collaborative': [
            'Basé sur les goûts d\'utilisateurs similaires',
            'Recommandations de personnes ayant des goûts similaires'
        ],
        'popularity': [
            'Basé sur la popularité générale',
            'Livres les plus appréciés par la communauté'
        ],
        'hybrid': [
            'Combinaison de plusieurs algorithmes',
            'Approche équilibrée pour des recommandations optimales'
        ]
    }
    
    return explanations.get(algorithm, ['Algorithme de recommandation personnalisé'])


def save_recommendation_set(
    user: User,
    algorithm: str,
    recommendations: List[Tuple[Book, float, List[str]]],
    context: str
) -> RecommendationSet:
    """Sauvegarder un ensemble de recommandations"""
    
    # Créer l'ensemble de recommandations
    recommendation_set = RecommendationSet.objects.create(
        user=user,
        algorithm_type=algorithm,
        algorithm_version='1.0',
        context=context,
        parameters={'count': len(recommendations)},
        expires_at=timezone.now() + timedelta(hours=24)
    )
    
    # Créer les recommandations individuelles
    for position, (book, score, reasons) in enumerate(recommendations):
        Recommendation.objects.create(
            recommendation_set=recommendation_set,
            book=book,
            score=score,
            position=position + 1,
            reasons=reasons,
            explanation=f'Recommandé par l\'algorithme {algorithm}'
        )
    
    return recommendation_set


def calculate_recommendation_stats(user_id: int, period: str = 'month') -> Dict[str, Any]:
    """Calculer les statistiques de recommandations pour un utilisateur"""
    
    # Définir la période
    if period == 'day':
        start_date = timezone.now() - timedelta(days=1)
    elif period == 'week':
        start_date = timezone.now() - timedelta(weeks=1)
    elif period == 'month':
        start_date = timezone.now() - timedelta(days=30)
    elif period == 'year':
        start_date = timezone.now() - timedelta(days=365)
    else:
        start_date = timezone.now() - timedelta(days=30)
    
    end_date = timezone.now()
    
    # Obtenir les ensembles de recommandations
    recommendation_sets = RecommendationSet.objects.filter(
        user_id=user_id,
        generated_at__range=[start_date, end_date]
    )
    
    # Calculer les métriques
    total_recommendations = recommendation_sets.count()
    total_views = sum(rs.view_count for rs in recommendation_sets)
    total_clicks = sum(rs.click_count for rs in recommendation_sets)
    total_conversions = sum(rs.conversion_count for rs in recommendation_sets)
    
    # Calculer les taux
    average_ctr = (total_clicks / total_views) if total_views > 0 else 0
    average_conversion_rate = (total_conversions / total_clicks) if total_clicks > 0 else 0
    
    # Performance par algorithme
    algorithm_performance = {}
    for algorithm in ['content_based', 'collaborative', 'popularity', 'hybrid']:
        algo_sets = recommendation_sets.filter(algorithm_type=algorithm)
        if algo_sets.exists():
            algo_views = sum(rs.view_count for rs in algo_sets)
            algo_clicks = sum(rs.click_count for rs in algo_sets)
            algo_conversions = sum(rs.conversion_count for rs in algo_sets)
            
            algorithm_performance[algorithm] = {
                'sets': algo_sets.count(),
                'views': algo_views,
                'clicks': algo_clicks,
                'conversions': algo_conversions,
                'ctr': (algo_clicks / algo_views) if algo_views > 0 else 0,
                'conversion_rate': (algo_conversions / algo_clicks) if algo_clicks > 0 else 0
            }
    
    # Algorithmes tendance
    trending_algorithms = sorted(
        algorithm_performance.items(),
        key=lambda x: x[1]['ctr'],
        reverse=True
    )[:3]
    
    return {
        'total_recommendations': total_recommendations,
        'total_views': total_views,
        'total_clicks': total_clicks,
        'total_conversions': total_conversions,
        'average_ctr': average_ctr,
        'average_conversion_rate': average_conversion_rate,
        'algorithm_performance': algorithm_performance,
        'trending_algorithms': [algo for algo, _ in trending_algorithms],
        'user_engagement': {
            'active_days': recommendation_sets.values('generated_at__date').distinct().count(),
            'avg_recommendations_per_day': total_recommendations / max(
                (end_date - start_date).days, 1
            )
        },
        'popular_genres': [],  # À implémenter selon les besoins
        'period_start': start_date,
        'period_end': end_date
    }


def update_recommendation_metrics(
    user: User,
    book: Book,
    interaction_type: str,
    algorithm: str
) -> None:
    """Mettre à jour les métriques de recommandation"""
    
    try:
        # Trouver la recommandation correspondante
        recent_recommendations = Recommendation.objects.filter(
            recommendation_set__user=user,
            book=book,
            recommendation_set__algorithm_type=algorithm,
            recommendation_set__generated_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-recommendation_set__generated_at')
        
        if recent_recommendations.exists():
            recommendation = recent_recommendations.first()
            
            if interaction_type in ['click', 'view']:
                if not recommendation.clicked:
                    recommendation.clicked = True
                    recommendation.clicked_at = timezone.now()
                    recommendation.save()
            
            elif interaction_type in ['read', 'download', 'bookmark']:
                if not recommendation.converted:
                    recommendation.converted = True
                    recommendation.converted_at = timezone.now()
                    recommendation.save()
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des métriques: {str(e)}")


def get_trending_books(period: str = 'week', trend_type: str = 'overall', limit: int = 20) -> List[Book]:
    """Obtenir les livres en tendance"""
    
    # Définir la période
    if period == 'day':
        start_date = timezone.now() - timedelta(days=1)
    elif period == 'week':
        start_date = timezone.now() - timedelta(weeks=1)
    elif period == 'month':
        start_date = timezone.now() - timedelta(days=30)
    else:
        start_date = timezone.now() - timedelta(weeks=1)
    
    # Obtenir les livres en tendance
    trending_books = TrendingBook.objects.filter(
        trend_type=trend_type,
        period_start__gte=start_date,
        is_active=True
    ).select_related('book').order_by('-trend_score')[:limit]
    
    return [tb.book for tb in trending_books]


def get_recommendation_analytics(period: str = 'month') -> Dict[str, Any]:
    """Obtenir les analytics globales de recommandations (admin)"""
    
    # Définir la période
    if period == 'day':
        start_date = timezone.now() - timedelta(days=1)
    elif period == 'week':
        start_date = timezone.now() - timedelta(weeks=1)
    elif period == 'month':
        start_date = timezone.now() - timedelta(days=30)
    elif period == 'year':
        start_date = timezone.now() - timedelta(days=365)
    else:
        start_date = timezone.now() - timedelta(days=30)
    
    end_date = timezone.now()
    
    # Métriques globales
    total_users = User.objects.filter(is_active=True).count()
    active_users = UserProfile.objects.filter(
        enable_recommendations=True,
        updated_at__gte=start_date
    ).count()
    
    recommendations_generated = RecommendationSet.objects.filter(
        generated_at__range=[start_date, end_date]
    ).count()
    
    # Métriques d'engagement
    all_sets = RecommendationSet.objects.filter(
        generated_at__range=[start_date, end_date]
    )
    
    total_views = sum(rs.view_count for rs in all_sets)
    total_clicks = sum(rs.click_count for rs in all_sets)
    total_conversions = sum(rs.conversion_count for rs in all_sets)
    
    average_ctr = (total_clicks / total_views) if total_views > 0 else 0
    average_conversion_rate = (total_conversions / total_clicks) if total_clicks > 0 else 0
    
    # Score de satisfaction utilisateur (basé sur les feedbacks)
    feedbacks = RecommendationFeedback.objects.filter(
        created_at__range=[start_date, end_date]
    )
    
    if feedbacks.exists():
        avg_rating = feedbacks.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        user_satisfaction_score = avg_rating / 5.0
    else:
        user_satisfaction_score = 0.0
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'recommendations_generated': recommendations_generated,
        'average_ctr': average_ctr,
        'average_conversion_rate': average_conversion_rate,
        'user_satisfaction_score': user_satisfaction_score,
        'algorithm_performance': {},  # À implémenter
        'daily_metrics': [],  # À implémenter
        'weekly_metrics': [],  # À implémenter
        'monthly_metrics': [],  # À implémenter
        'user_segments': {},  # À implémenter
        'top_recommended_books': [],  # À implémenter
        'trending_genres': [],  # À implémenter
        'report_generated_at': timezone.now(),
        'period_start': start_date,
        'period_end': end_date
    }


def clean_old_recommendation_data(days_to_keep: int = 90) -> Dict[str, int]:
    """Nettoyer les anciennes données de recommandations"""
    
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    # Supprimer les anciens ensembles de recommandations
    old_sets = RecommendationSet.objects.filter(
        generated_at__lt=cutoff_date
    )
    sets_count = old_sets.count()
    old_sets.delete()
    
    # Supprimer les anciennes interactions
    old_interactions = UserInteraction.objects.filter(
        timestamp__lt=cutoff_date
    )
    interactions_count = old_interactions.count()
    old_interactions.delete()
    
    # Supprimer les anciens feedbacks
    old_feedbacks = RecommendationFeedback.objects.filter(
        created_at__lt=cutoff_date
    )
    feedbacks_count = old_feedbacks.count()
    old_feedbacks.delete()
    
    logger.info(
        f"Nettoyage des données de recommandations terminé: "
        f"{sets_count} ensembles, {interactions_count} interactions, "
        f"{feedbacks_count} feedbacks supprimés"
    )
    
    return {
        'recommendation_sets_deleted': sets_count,
        'interactions_deleted': interactions_count,
        'feedbacks_deleted': feedbacks_count
    }