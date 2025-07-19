"""
Utils refactorisés pour utiliser les services découplés
"""
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

from coko.services import get_book_service, get_reading_service
from coko.events import publish_event, EventType
from .service_adapters import recommendation_adapter
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
    """Générer des recommandations personnalisées via les services découplés"""
    
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
        
        # Obtenir les livres déjà lus via le service de lecture
        reading_history = get_reading_service().get_user_reading_history(user.id)
        read_book_ids = set(session['book_id'] for session in reading_history)
        
        # Générer les recommandations selon l'algorithme
        if algorithm == 'content_based':
            recommendations = recommendation_adapter.generate_content_based_recommendations(
                user, user_profile, read_book_ids, count, context
            )
        elif algorithm == 'collaborative':
            recommendations = recommendation_adapter.generate_collaborative_recommendations(
                user, user_profile, read_book_ids, count, context
            )
        elif algorithm == 'popularity':
            recommendations = generate_popularity_based_recommendations_via_service(
                user, user_profile, read_book_ids, count, context
            )
        elif algorithm == 'hybrid':
            recommendations = generate_hybrid_recommendations_via_service(
                user, user_profile, read_book_ids, count, context
            )
        else:
            recommendations = generate_hybrid_recommendations_via_service(
                user, user_profile, read_book_ids, count, context
            )
        
        # Calculer les scores de diversité et nouveauté
        diversity_score = calculate_diversity_score_via_service(recommendations)
        novelty_score = calculate_novelty_score_via_service(recommendations, user)
        
        # Préparer la réponse
        response_data = {
            'books': [{
                'id': book_data['id'],
                'title': book_data['title'],
                'slug': book_data.get('slug', ''),
                'authors': book_data.get('authors', []),
                'categories': book_data.get('categories', []),
                'cover_image': book_data.get('cover_image'),
                'average_rating': book_data.get('average_rating', 0),
                'publication_date': book_data.get('publication_date'),
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
        save_recommendation_set_via_service(user, algorithm, recommendations, context)
        
        # Publier l'événement
        publish_event(
            EventType.RECOMMENDATION_GENERATED,
            {
                'algorithm': algorithm,
                'count': len(recommendations),
                'context': context,
                'confidence_score': response_data['confidence_score']
            },
            user_id=user.id,
            source_service='recommendation_service'
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {str(e)}")
        raise


def generate_popularity_based_recommendations_via_service(
    user: User,
    user_profile: UserProfile,
    read_book_ids: set,
    count: int,
    context: str
) -> List[Tuple[Dict[str, Any], float, List[str]]]:
    """Générer des recommandations basées sur la popularité via les services"""
    
    book_service = get_book_service()
    popular_books = book_service.get_popular_books(
        limit=count * 2,  # Obtenir plus pour filtrer
        exclude_ids=list(read_book_ids)
    )
    
    recommendations = []
    for book_data in popular_books[:count]:
        score = min(book_data.get('average_rating', 0) / 5.0, 1.0)
        reasons = ['Livre populaire', f'Note moyenne: {book_data.get("average_rating", 0):.1f}']
        recommendations.append((book_data, score, reasons))
    
    return recommendations


def generate_hybrid_recommendations_via_service(
    user: User,
    user_profile: UserProfile,
    read_book_ids: set,
    count: int,
    context: str
) -> List[Tuple[Dict[str, Any], float, List[str]]]:
    """Générer des recommandations hybrides via les services"""
    
    # Obtenir la configuration des poids
    config = cache.get('recommendation_engine_config', {})
    content_weight = config.get('algorithm_weights', {}).get('content_based', 0.4)
    collaborative_weight = config.get('algorithm_weights', {}).get('collaborative', 0.4)
    popularity_weight = config.get('algorithm_weights', {}).get('popularity', 0.2)
    
    # Générer des recommandations avec chaque algorithme
    content_recs = recommendation_adapter.generate_content_based_recommendations(
        user, user_profile, read_book_ids, count * 2, context
    )
    
    collaborative_recs = recommendation_adapter.generate_collaborative_recommendations(
        user, user_profile, read_book_ids, count * 2, context
    )
    
    popularity_recs = generate_popularity_based_recommendations_via_service(
        user, user_profile, read_book_ids, count * 2, context
    )
    
    # Combiner les recommandations
    book_scores = defaultdict(lambda: {'score': 0, 'reasons': set(), 'count': 0})
    
    # Ajouter les scores pondérés
    for book_data, score, reasons in content_recs:
        book_id = book_data['id']
        book_scores[book_id]['book_data'] = book_data
        book_scores[book_id]['score'] += score * content_weight
        book_scores[book_id]['reasons'].update(reasons)
        book_scores[book_id]['count'] += 1
    
    for book_data, score, reasons in collaborative_recs:
        book_id = book_data['id']
        if 'book_data' not in book_scores[book_id]:
            book_scores[book_id]['book_data'] = book_data
        book_scores[book_id]['score'] += score * collaborative_weight
        book_scores[book_id]['reasons'].update(reasons)
        book_scores[book_id]['count'] += 1
    
    for book_data, score, reasons in popularity_recs:
        book_id = book_data['id']
        if 'book_data' not in book_scores[book_id]:
            book_scores[book_id]['book_data'] = book_data
        book_scores[book_id]['score'] += score * popularity_weight
        book_scores[book_id]['reasons'].update(reasons)
        book_scores[book_id]['count'] += 1
    
    # Normaliser les scores et créer la liste finale
    final_recommendations = []
    for book_id, data in book_scores.items():
        if 'book_data' in data:
            # Bonus pour les livres recommandés par plusieurs algorithmes
            diversity_bonus = min(data['count'] * 0.1, 0.3)
            final_score = min(data['score'] + diversity_bonus, 1.0)
            
            final_recommendations.append((
                data['book_data'],
                final_score,
                list(data['reasons'])
            ))
    
    # Trier par score et retourner les meilleurs
    final_recommendations.sort(key=lambda x: x[1], reverse=True)
    
    return final_recommendations[:count]


def calculate_diversity_score_via_service(recommendations: List[Tuple[Dict[str, Any], float, List[str]]]) -> float:
    """Calculer le score de diversité via les services"""
    
    if not recommendations:
        return 0.0
    
    # Obtenir les genres et auteurs
    all_genres = set()
    all_authors = set()
    
    for book_data, _, _ in recommendations:
        # Les catégories et auteurs sont déjà dans book_data grâce aux services
        all_genres.update(book_data.get('categories', []))
        all_authors.update(book_data.get('authors', []))
    
    # Calculer la diversité
    genre_diversity = len(all_genres) / len(recommendations)
    author_diversity = len(all_authors) / len(recommendations)
    
    return (genre_diversity + author_diversity) / 2


def calculate_novelty_score_via_service(recommendations: List[Tuple[Dict[str, Any], float, List[str]]], user: User) -> float:
    """Calculer le score de nouveauté via les services"""
    
    if not recommendations:
        return 0.0
    
    # Obtenir les genres/auteurs déjà connus via le service de lecture
    reading_service = get_reading_service()
    book_service = get_book_service()
    
    reading_history = reading_service.get_user_reading_history(user.id)
    
    known_genres = set()
    known_authors = set()
    
    for session in reading_history:
        book_data = book_service.get_book_by_id(session['book_id'])
        if book_data:
            known_genres.update(book_data.get('categories', []))
            known_authors.update(book_data.get('authors', []))
    
    # Calculer la nouveauté
    novel_items = 0
    
    for book_data, _, _ in recommendations:
        book_genres = set(book_data.get('categories', []))
        book_authors = set(book_data.get('authors', []))
        
        # Vérifier si le livre introduit de nouveaux genres/auteurs
        if not book_genres.issubset(known_genres) or not book_authors.issubset(known_authors):
            novel_items += 1
    
    return novel_items / len(recommendations)


def save_recommendation_set_via_service(
    user: User,
    algorithm: str,
    recommendations: List[Tuple[Dict[str, Any], float, List[str]]],
    context: str
) -> RecommendationSet:
    """Sauvegarder un ensemble de recommandations via les services"""
    
    # Créer l'ensemble de recommandations
    recommendation_set = RecommendationSet.objects.create(
        user=user,
        algorithm_type=algorithm,
        algorithm_version='2.0',  # Version avec services découplés
        context=context,
        parameters={'count': len(recommendations), 'via_services': True},
        expires_at=timezone.now() + timedelta(hours=24)
    )
    
    # Créer les recommandations individuelles
    for position, (book_data, score, reasons) in enumerate(recommendations):
        # Nous ne pouvons pas stocker directement l'objet Book puisque nous utilisons des services
        # Stockons l'ID et récupérons le livre à la demande
        try:
            from catalog_service.models import Book
            book = Book.objects.get(id=book_data['id'])
            
            Recommendation.objects.create(
                recommendation_set=recommendation_set,
                book=book,
                score=score,
                position=position + 1,
                reasons=reasons,
                explanation=f'Recommandé par l\'algorithme {algorithm} (services découplés)'
            )
        except Exception as e:
            logger.warning(f"Impossible de créer la recommandation pour le livre {book_data['id']}: {str(e)}")
    
    return recommendation_set


def get_trending_books_via_service(period: str = 'week', trend_type: str = 'overall', limit: int = 20) -> List[Dict[str, Any]]:
    """Obtenir les livres en tendance via les services"""
    
    book_service = get_book_service()
    
    # Pour l'instant, utiliser les livres populaires comme approximation
    # Dans une implémentation complète, on aurait un service dédié aux tendances
    popular_books = book_service.get_popular_books(limit=limit)
    
    # Ajouter des informations de tendance simulées
    trending_books = []
    for book_data in popular_books:
        trending_books.append({
            **book_data,
            'trend_score': random.uniform(0.5, 1.0),  # Simulation
            'trend_type': trend_type,
            'period': period
        })
    
    return trending_books


def calculate_recommendation_stats_via_service(user_id: int, period: str = 'month') -> Dict[str, Any]:
    """Calculer les statistiques de recommandations via les services"""
    
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
    
    # Calculer les métriques de base
    total_recommendations = recommendation_sets.count()
    total_views = sum(rs.view_count for rs in recommendation_sets)
    total_clicks = sum(rs.click_count for rs in recommendation_sets)
    total_conversions = sum(rs.conversion_count for rs in recommendation_sets)
    
    # Calculer les taux
    average_ctr = (total_clicks / total_views) if total_views > 0 else 0
    average_conversion_rate = (total_conversions / total_clicks) if total_clicks > 0 else 0
    
    # Obtenir les statistiques de lecture via le service
    reading_service = get_reading_service()
    reading_stats = reading_service.get_reading_statistics(user_id, period)
    
    return {
        'total_recommendations': total_recommendations,
        'total_views': total_views,
        'total_clicks': total_clicks,
        'total_conversions': total_conversions,
        'average_ctr': average_ctr,
        'average_conversion_rate': average_conversion_rate,
        'reading_integration': {
            'books_completed': reading_stats.get('session_stats', {}).get('completed_sessions', 0),
            'reading_time': reading_stats.get('session_stats', {}).get('total_reading_time', timedelta()),
            'consistency': reading_stats.get('progress_stats', {}).get('reading_consistency', 0)
        },
        'period_start': start_date,
        'period_end': end_date,
        'via_services': True
    }


def update_recommendation_metrics_via_service(
    user: User,
    book_id: int,
    interaction_type: str,
    algorithm: str
) -> None:
    """Mettre à jour les métriques de recommandation via les services"""
    
    # Utiliser l'adaptateur pour enregistrer l'interaction
    recommendation_adapter.record_interaction_via_service(
        user.id,
        book_id,
        interaction_type,
        {'algorithm': algorithm}
    )
    
    # Publier l'événement approprié
    if interaction_type in ['click', 'view']:
        event_type = EventType.RECOMMENDATION_CLICKED
    elif interaction_type in ['read', 'download', 'bookmark']:
        event_type = EventType.RECOMMENDATION_CONVERTED
    else:
        event_type = EventType.USER_INTERACTION_RECORDED
    
    publish_event(
        event_type,
        {
            'book_id': book_id,
            'interaction_type': interaction_type,
            'algorithm': algorithm
        },
        user_id=user.id,
        source_service='recommendation_service'
    )


# Fonctions utilitaires (inchangées car elles ne dépendent pas des autres services)

def calculate_confidence_score(recommendations: List[Tuple[Dict[str, Any], float, List[str]]], user_profile: UserProfile) -> float:
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
            'Combinaison de plusieurs algorithmes via services découplés',
            'Approche équilibrée pour des recommandations optimales'
        ]
    }
    
    return explanations.get(algorithm, ['Algorithme de recommandation personnalisé'])