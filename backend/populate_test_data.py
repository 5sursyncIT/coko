#!/usr/bin/env python
"""
Script pour peupler la base de données avec des données de test
"""

import os
import sys
import django
from django.utils import timezone
from datetime import datetime, timedelta
import random
import uuid
from django.db import transaction

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coko.settings_local')
django.setup()

from django.contrib.auth import get_user_model
from catalog_service.models import (
    Category, Author, Publisher, Series, Book, BookFile, BookRating
)
from reading_service.models import (
    ReadingSession, ReadingProgress, Bookmark, ReadingGoal
)
from recommendation_service.models import (
    UserProfile, UserInteraction, BookVector
)

User = get_user_model()

def create_test_data():
    print("Création des données de test...")
    
    # Créer des utilisateurs de test
    print("Création des utilisateurs...")
    users = []
    
    # Disable signals temporarily to avoid SecurityLog creation issues
    from django.db.models.signals import post_save, pre_save
    from auth_service.signals import (
        create_user_preferences, 
        log_user_creation, 
        send_welcome_email_on_verification,
        detect_password_change,
        send_password_change_notification,
        log_email_verification
    )
    
    # Disconnect signals temporarily
    post_save.disconnect(create_user_preferences, sender=User)
    post_save.disconnect(log_user_creation, sender=User)
    post_save.disconnect(send_welcome_email_on_verification, sender=User)
    post_save.disconnect(send_password_change_notification, sender=User)
    post_save.disconnect(log_email_verification, sender=User)
    pre_save.disconnect(detect_password_change, sender=User)
    
    try:
        for i in range(1, 6):
             user, created = User.objects.get_or_create(
                 username=f'user{i}',
                 email=f'user{i}@example.com',
                 defaults={
                     'first_name': f'User{i}',
                     'last_name': f'Test{i}',
                     'is_verified': True,
                     'country': random.choice(['SN', 'CI', 'ML', 'BF', 'MA']),
                     'language': random.choice(['fr', 'en', 'wo']),
                     'subscription_type': random.choice(['free', 'premium', 'creator'])
                 }
             )
             if created:
                 user.set_password('password123')
                 user.save()
                 # Manually create user preferences
                 from auth_service.models import UserPreferences
                 UserPreferences.objects.get_or_create(user=user)
                 print(f"Préférences créées pour l'utilisateur {user.username}")
             users.append(user)
             print(f"Utilisateur {user.username} créé ou récupéré")
    finally:
         # Reconnect signals
         post_save.connect(create_user_preferences, sender=User)
         post_save.connect(log_user_creation, sender=User)
         post_save.connect(send_welcome_email_on_verification, sender=User)
         post_save.connect(send_password_change_notification, sender=User)
         post_save.connect(log_email_verification, sender=User)
         pre_save.connect(detect_password_change, sender=User)
    
    # Créer des catégories
    print("Création des catégories...")
    categories_data = [
        {'name': 'Fiction', 'slug': 'fiction', 'description': 'Romans et nouvelles', 'color': '#FF6B6B'},
        {'name': 'Science-Fiction', 'slug': 'science-fiction', 'description': 'Littérature de science-fiction', 'color': '#4ECDC4'},
        {'name': 'Fantasy', 'slug': 'fantasy', 'description': 'Littérature fantastique', 'color': '#45B7D1'},
        {'name': 'Romance', 'slug': 'romance', 'description': 'Romans d\'amour', 'color': '#F7DC6F'},
        {'name': 'Thriller', 'slug': 'thriller', 'description': 'Romans à suspense', 'color': '#BB8FCE'},
        {'name': 'Non-Fiction', 'slug': 'non-fiction', 'description': 'Livres documentaires', 'color': '#85C1E9'},
    ]
    
    categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        categories.append(category)
    
    # Créer des auteurs
    print("Création des auteurs...")
    authors_data = [
        {'first_name': 'Isaac', 'last_name': 'Asimov', 'birth_date': datetime(1920, 1, 2).date()},
        {'first_name': 'Ursula K.', 'last_name': 'Le Guin', 'birth_date': datetime(1929, 10, 21).date()},
        {'first_name': 'Philip K.', 'last_name': 'Dick', 'birth_date': datetime(1928, 12, 16).date()},
        {'first_name': 'J.R.R.', 'last_name': 'Tolkien', 'birth_date': datetime(1892, 1, 3).date()},
        {'first_name': 'George R.R.', 'last_name': 'Martin', 'birth_date': datetime(1948, 9, 20).date()},
        {'first_name': 'Agatha', 'last_name': 'Christie', 'birth_date': datetime(1890, 9, 15).date()},
        {'first_name': 'Stephen', 'last_name': 'King', 'birth_date': datetime(1947, 9, 21).date()},
        {'first_name': 'Jane', 'last_name': 'Austen', 'birth_date': datetime(1775, 12, 16).date()},
    ]
    
    authors = []
    for author_data in authors_data:
        slug = f"{author_data['first_name'].lower().replace(' ', '-').replace('.', '')}-{author_data['last_name'].lower().replace(' ', '-')}"
        author, created = Author.objects.get_or_create(
            slug=slug,
            defaults={
                **author_data,
                'slug': slug,
                'biography': f"Biographie de {author_data['first_name']} {author_data['last_name']}"
            }
        )
        authors.append(author)
    
    # Créer des éditeurs
    print("Création des éditeurs...")
    publishers_data = [
        {'name': 'Penguin Random House', 'founded_year': 1927, 'country': 'États-Unis'},
        {'name': 'HarperCollins', 'founded_year': 1989, 'country': 'États-Unis'},
        {'name': 'Macmillan Publishers', 'founded_year': 1843, 'country': 'Royaume-Uni'},
        {'name': 'Simon & Schuster', 'founded_year': 1924, 'country': 'États-Unis'},
        {'name': 'Hachette Book Group', 'founded_year': 1826, 'country': 'France'},
    ]
    
    publishers = []
    for pub_data in publishers_data:
        slug = pub_data['name'].lower().replace(' ', '-').replace('&', 'and')
        publisher, created = Publisher.objects.get_or_create(
            slug=slug,
            defaults={
                **pub_data,
                'slug': slug,
                'description': f"Description de {pub_data['name']}"
            }
        )
        publishers.append(publisher)
    
    # Créer des séries
    print("Création des séries...")
    series_data = [
        {'title': 'Foundation', 'total_books': 7, 'is_completed': True},
        {'title': 'The Lord of the Rings', 'total_books': 3, 'is_completed': True},
        {'title': 'A Song of Ice and Fire', 'total_books': 7, 'is_completed': False},
        {'title': 'Hercule Poirot', 'total_books': 39, 'is_completed': True},
    ]
    
    series_list = []
    for series_data in series_data:
        slug = series_data['title'].lower().replace(' ', '-')
        series, created = Series.objects.get_or_create(
            slug=slug,
            defaults={
                **series_data,
                'slug': slug,
                'description': f"Description de la série {series_data['title']}"
            }
        )
        series_list.append(series)
    
    # Créer des livres
    print("Création des livres...")
    books_data = [
        {
            'title': 'Foundation',
            'subtitle': 'The First Novel in the Foundation Series',
            'description': 'The first book in Isaac Asimov\'s Foundation series.',
            'isbn': '9780553293357',
            'language': 'en',
            'page_count': 244,
            'publication_date': datetime(1951, 5, 1).date(),
            'author_idx': 0,  # Isaac Asimov
            'publisher_idx': 0,
            'series_idx': 0,
            'category_indices': [1],  # Science-Fiction
            'is_free': True,
            'is_featured': True,
        },
        {
            'title': 'The Left Hand of Darkness',
            'description': 'A groundbreaking work of science fiction.',
            'isbn': '9780441478125',
            'language': 'en',
            'page_count': 304,
            'publication_date': datetime(1969, 3, 1).date(),
            'author_idx': 1,  # Ursula K. Le Guin
            'publisher_idx': 1,
            'category_indices': [1],  # Science-Fiction
            'is_free': False,
            'is_featured': True,
        },
        {
            'title': 'Do Androids Dream of Electric Sheep?',
            'description': 'The novel that inspired Blade Runner.',
            'isbn': '9780345404473',
            'language': 'en',
            'page_count': 210,
            'publication_date': datetime(1968, 1, 1).date(),
            'author_idx': 2,  # Philip K. Dick
            'publisher_idx': 2,
            'category_indices': [1],  # Science-Fiction
            'is_free': True,
            'is_featured': False,
        },
        {
            'title': 'The Fellowship of the Ring',
            'subtitle': 'The Lord of the Rings, Part One',
            'description': 'The first volume of The Lord of the Rings.',
            'isbn': '9780547928210',
            'language': 'en',
            'page_count': 423,
            'publication_date': datetime(1954, 7, 29).date(),
            'author_idx': 3,  # J.R.R. Tolkien
            'publisher_idx': 3,
            'series_idx': 1,
            'category_indices': [2],  # Fantasy
            'is_free': False,
            'is_featured': True,
        },
        {
            'title': 'A Game of Thrones',
            'subtitle': 'A Song of Ice and Fire, Book One',
            'description': 'The first book in the epic fantasy series.',
            'isbn': '9780553103540',
            'language': 'en',
            'page_count': 694,
            'publication_date': datetime(1996, 8, 1).date(),
            'author_idx': 4,  # George R.R. Martin
            'publisher_idx': 0,
            'series_idx': 2,
            'category_indices': [2],  # Fantasy
            'is_free': False,
            'is_featured': True,
        },
        {
            'title': 'Murder on the Orient Express',
            'description': 'A classic Hercule Poirot mystery.',
            'isbn': '9780062693662',
            'language': 'en',
            'page_count': 256,
            'publication_date': datetime(1934, 1, 1).date(),
            'author_idx': 5,  # Agatha Christie
            'publisher_idx': 1,
            'series_idx': 3,
            'category_indices': [4],  # Thriller
            'is_free': True,
            'is_featured': False,
        },
        {
            'title': 'The Shining',
            'description': 'A horror novel by Stephen King.',
            'isbn': '9780307743657',
            'language': 'en',
            'page_count': 447,
            'publication_date': datetime(1977, 1, 28).date(),
            'author_idx': 6,  # Stephen King
            'publisher_idx': 2,
            'category_indices': [4],  # Thriller
            'is_free': False,
            'is_featured': False,
        },
        {
            'title': 'Pride and Prejudice',
            'description': 'A romantic novel by Jane Austen.',
            'isbn': '9780141439518',
            'language': 'en',
            'page_count': 432,
            'publication_date': datetime(1813, 1, 28).date(),
            'author_idx': 7,  # Jane Austen
            'publisher_idx': 0,
            'category_indices': [0, 3],  # Fiction, Romance
            'is_free': True,
            'is_featured': True,
        },
    ]
    
    books = []
    for book_data in books_data:
        slug = book_data['title'].lower().replace(' ', '-').replace('?', '').replace('\'', '')
        
        # Extraire les données spécifiques
        author_idx = book_data.pop('author_idx')
        publisher_idx = book_data.pop('publisher_idx')
        series_idx = book_data.pop('series_idx', None)
        category_indices = book_data.pop('category_indices')
        
        book, created = Book.objects.get_or_create(
            slug=slug,
            defaults={
                **book_data,
                'slug': slug,
                'publisher': publishers[publisher_idx],
                'series': series_list[series_idx] if series_idx is not None else None,
                'status': 'published',
                'view_count': 0,
                'download_count': 0,
            }
        )
        
        if created:
            # Ajouter l'auteur
            book.authors.add(authors[author_idx])
            
            # Ajouter les catégories
            for cat_idx in category_indices:
                book.categories.add(categories[cat_idx])
        
        books.append(book)
    
    # Créer des évaluations
    print("Création des évaluations...")
    for user in users[:3]:  # Seulement les 3 premiers utilisateurs
        for book in books[:5]:  # Seulement les 5 premiers livres
            rating, created = BookRating.objects.get_or_create(
                user=user,
                book=book,
                defaults={
                    'score': (hash(f"{user.id}{book.id}") % 5) + 1,  # Score pseudo-aléatoire entre 1 et 5
                    'review': f"Excellent livre ! Recommandé par {user.username}."
                }
            )
    
    # Créer des sessions de lecture
    print("Création des sessions de lecture...")
    for user in users[:3]:
        for book in books[:3]:
            session, created = ReadingSession.objects.get_or_create(
                user=user,
                book=book,
                defaults={
                    'status': 'active',
                    'device_type': 'web',
                    'current_page': (hash(f"{user.id}{book.id}") % 50) + 1,
                    'current_position': ((hash(f"{user.id}{book.id}") % 100) / 100) * 100,
                    'total_pages_read': (hash(f"{user.id}{book.id}") % 30) + 1,
                    'total_reading_time': timedelta(minutes=(hash(f"{user.id}{book.id}") % 120) + 30),
                }
            )
    
    # Créer des signets
    print("Création des signets...")
    for user in users[:2]:
        for book in books[:4]:
            bookmark, created = Bookmark.objects.get_or_create(
                user=user,
                book=book,
                defaults={
                    'type': 'bookmark',
                    'title': f"Signet dans {book.title}",
                    'page_number': (hash(f"{user.id}{book.id}") % 100) + 1,
                    'position_in_page': 0.5,
                    'note': f"Note personnelle de {user.username} sur {book.title}",
                }
            )
    
    # Créer des profils de recommandation
    print("Création des profils de recommandation...")
    for user in users:
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'preferred_genres': ['science-fiction', 'fantasy'],
                'preferred_authors': [str(authors[0].id), str(authors[1].id)],
                'preferred_languages': ['en', 'fr'],
                'reading_level': 'intermediate',
                'reading_frequency': 'weekly',
                'preferred_book_length': 'medium',
                'enable_recommendations': True,
                'recommendation_frequency': 'weekly',
            }
        )
    
    # Créer des interactions utilisateur
    print("Création des interactions utilisateur...")
    interaction_types = ['view', 'download', 'read_start', 'rating', 'bookmark']
    for user in users[:3]:
        for book in books[:6]:
            for interaction_type in interaction_types[:2]:  # Seulement view et download
                interaction, created = UserInteraction.objects.get_or_create(
                    user=user,
                    book=book,
                    interaction_type=interaction_type,
                    defaults={
                        'session_id': str(uuid.uuid4()),
                        'device_type': 'desktop',
                        'interaction_value': 1.0 if interaction_type == 'view' else 5.0,
                        'from_recommendation': False,
                    }
                )
    
    # Créer des vecteurs de livres
    print("Création des vecteurs de livres...")
    for book in books:
        vector, created = BookVector.objects.get_or_create(
            book=book,
            defaults={
                'content_vector': [0.1, 0.2, 0.3, 0.4, 0.5] * 20,  # Vecteur factice de 100 dimensions
                'genre_vector': [0.8, 0.2, 0.0, 0.0, 0.0],
                'author_vector': [0.9, 0.1, 0.0, 0.0, 0.0],
                'metadata_vector': [0.5, 0.3, 0.2, 0.0, 0.0],
                'popularity_score': 0.7,
                'quality_score': 0.8,
                'recency_score': 0.6,
                'view_count': book.view_count,
                'download_count': book.download_count,
                'rating_average': 4.2,
                'rating_count': 15,
            }
        )
    
    print("Données de test créées avec succès !")
    print(f"- {len(users)} utilisateurs")
    print(f"- {len(categories)} catégories")
    print(f"- {len(authors)} auteurs")
    print(f"- {len(publishers)} éditeurs")
    print(f"- {len(series_list)} séries")
    print(f"- {len(books)} livres")
    print(f"- {BookRating.objects.count()} évaluations")
    print(f"- {ReadingSession.objects.count()} sessions de lecture")
    print(f"- {Bookmark.objects.count()} signets")
    print(f"- {UserProfile.objects.count()} profils de recommandation")
    print(f"- {UserInteraction.objects.count()} interactions")
    print(f"- {BookVector.objects.count()} vecteurs de livres")

if __name__ == '__main__':
    create_test_data()