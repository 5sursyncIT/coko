"""
APIs d'export spécialisées pour auteurs et éditeurs
Facilite l'extraction de données pour les créateurs de contenu
"""

from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.serializers import serialize
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import csv
import json
# import xlsxwriter
from io import BytesIO, StringIO
from datetime import datetime, timedelta
from typing import Dict, List, Any
import zipfile

User = get_user_model()


class AuthorExportAPI:
    """API d'export pour les auteurs"""
    
    def __init__(self, user):
        self.user = user
        self.is_author = self._check_author_permissions()
    
    def _check_author_permissions(self):
        """Vérifie si l'utilisateur est un auteur"""
        try:
            # Vérifier les rôles
            user_roles = self.user.user_roles.values_list('role__name', flat=True)
            return 'author' in user_roles or self.user.is_staff
        except:
            return False
    
    def get_author_books_data(self, format_type='json', period_days=None):
        """Exporte les données des livres de l'auteur"""
        if not self.is_author:
            return {'error': 'Permissions insuffisantes'}
        
        try:
            from catalog_service.models import Book, BookRating
            
            # Filtrer les livres de l'auteur
            books_query = Book.objects.filter(
                authors__user=self.user
            ).prefetch_related('ratings', 'categories', 'authors')
            
            if period_days:
                cutoff_date = timezone.now() - timedelta(days=period_days)
                books_query = books_query.filter(created_at__gte=cutoff_date)
            
            books_data = []
            for book in books_query:
                # Statistiques du livre
                ratings = book.ratings.all()
                avg_rating = ratings.aggregate(avg=Avg('score'))['avg'] or 0
                total_ratings = ratings.count()
                
                book_data = {
                    'id': str(book.id),
                    'title': book.title,
                    'subtitle': book.subtitle,
                    'isbn': book.isbn,
                    'status': book.status,
                    'language': book.language,
                    'page_count': book.page_count,
                    'publication_date': book.publication_date.isoformat() if book.publication_date else None,
                    'created_at': book.created_at.isoformat(),
                    'is_featured': book.is_featured,
                    'is_free': book.is_free,
                    'is_premium_only': book.is_premium_only,
                    'view_count': book.view_count,
                    'download_count': book.download_count,
                    'average_rating': round(avg_rating, 2),
                    'total_ratings': total_ratings,
                    'categories': [cat.name for cat in book.categories.all()],
                    'co_authors': [author.full_name for author in book.authors.exclude(user=self.user)]
                }
                
                # Répartition des notes
                rating_distribution = {}
                for i in range(1, 6):
                    count = ratings.filter(score=i).count()
                    rating_distribution[f'{i}_stars'] = count
                book_data['rating_distribution'] = rating_distribution
                
                books_data.append(book_data)
            
            if format_type == 'json':
                return {
                    'success': True,
                    'data': books_data,
                    'metadata': {
                        'total_books': len(books_data),
                        'export_date': timezone.now().isoformat(),
                        'author': self.user.get_full_name(),
                        'period_days': period_days
                    }
                }
            elif format_type == 'csv':
                return self._export_books_csv(books_data)
            elif format_type == 'xlsx':
                return self._export_books_xlsx(books_data)
            
        except Exception as e:
            return {'error': f'Erreur lors de l\'export: {str(e)}'}
    
    def get_reading_analytics(self, format_type='json', period_days=30):
        """Analytics de lecture pour les livres de l'auteur"""
        if not self.is_author:
            return {'error': 'Permissions insuffisantes'}
        
        try:
            from catalog_service.models import Book
            from reading_service.models import ReadingSession, ReadingProgress
            
            # Livres de l'auteur
            author_books = Book.objects.filter(authors__user=self.user)
            book_ids = [str(book.id) for book in author_books]
            
            cutoff_date = timezone.now() - timedelta(days=period_days)
            
            # Sessions de lecture
            reading_sessions = ReadingSession.objects.filter(
                book_uuid__in=book_ids,
                created_at__gte=cutoff_date
            )
            
            analytics_data = []
            for book in author_books:
                book_sessions = reading_sessions.filter(book_uuid=str(book.id))
                
                # Métriques par livre
                total_sessions = book_sessions.count()
                completed_sessions = book_sessions.filter(status='completed').count()
                active_readers = book_sessions.values('user').distinct().count()
                
                # Temps de lecture moyen
                avg_reading_time = book_sessions.aggregate(
                    avg=Avg('total_reading_time')
                )['avg'] or timedelta()
                
                # Progression moyenne
                avg_progress = book_sessions.aggregate(
                    avg=Avg('current_page')
                )['avg'] or 0
                
                completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
                
                book_analytics = {
                    'book_id': str(book.id),
                    'book_title': book.title,
                    'total_reading_sessions': total_sessions,
                    'completed_sessions': completed_sessions,
                    'completion_rate': round(completion_rate, 2),
                    'unique_readers': active_readers,
                    'avg_reading_time_minutes': int(avg_reading_time.total_seconds() / 60),
                    'avg_progress_pages': round(avg_progress, 2),
                    'engagement_score': self._calculate_engagement_score(book_sessions)
                }
                
                analytics_data.append(book_analytics)
            
            if format_type == 'json':
                return {
                    'success': True,
                    'data': analytics_data,
                    'summary': {
                        'total_books_analyzed': len(analytics_data),
                        'period_days': period_days,
                        'total_unique_readers': reading_sessions.values('user').distinct().count(),
                        'total_reading_sessions': reading_sessions.count(),
                        'avg_completion_rate': round(
                            sum(item['completion_rate'] for item in analytics_data) / len(analytics_data), 2
                        ) if analytics_data else 0
                    }
                }
            
        except Exception as e:
            return {'error': f'Erreur lors de l\'analyse: {str(e)}'}
    
    def get_revenue_report(self, format_type='json', period_days=30):
        """Rapport de revenus pour l'auteur"""
        if not self.is_author:
            return {'error': 'Permissions insuffisantes'}
        
        try:
            from shared_models.financial_reports import PaymentTransaction
            from catalog_service.models import Book
            
            # Livres de l'auteur
            author_books = Book.objects.filter(authors__user=self.user)
            
            cutoff_date = timezone.now() - timedelta(days=period_days)
            
            # Simuler les revenus par livre (à adapter selon le modèle réel)
            revenue_data = []
            total_revenue = 0
            
            for book in author_books:
                # Simulation basée sur les téléchargements et le type de livre
                if book.is_free:
                    book_revenue = 0
                else:
                    # Revenus estimés basés sur les vues et téléchargements
                    base_price = 500 if book.is_premium_only else 200  # FCFA
                    estimated_sales = book.download_count * 0.1  # 10% de conversion
                    book_revenue = estimated_sales * base_price
                
                revenue_data.append({
                    'book_id': str(book.id),
                    'book_title': book.title,
                    'book_type': 'Premium' if book.is_premium_only else 'Gratuit' if book.is_free else 'Standard',
                    'estimated_revenue': book_revenue,
                    'downloads': book.download_count,
                    'views': book.view_count,
                    'conversion_rate': '10%'  # Estimation
                })
                
                total_revenue += book_revenue
            
            return {
                'success': True,
                'data': revenue_data,
                'summary': {
                    'total_estimated_revenue': total_revenue,
                    'currency': 'XOF',
                    'period_days': period_days,
                    'total_books': len(revenue_data),
                    'avg_revenue_per_book': round(total_revenue / len(revenue_data), 2) if revenue_data else 0
                }
            }
            
        except Exception as e:
            return {'error': f'Erreur lors du calcul des revenus: {str(e)}'}
    
    def _calculate_engagement_score(self, sessions):
        """Calcule un score d'engagement pour un livre"""
        if not sessions.exists():
            return 0
        
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(status='completed').count()
        avg_progress = sessions.aggregate(avg=Avg('current_page'))['avg'] or 0
        
        # Score basé sur taux de complétion et progression moyenne
        completion_score = (completed_sessions / total_sessions) * 50
        progress_score = min(avg_progress / 100, 1) * 50  # Normalisé sur 50
        
        return round(completion_score + progress_score, 2)
    
    def _export_books_csv(self, books_data):
        """Exporte les données des livres au format CSV"""
        output = StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        headers = [
            'ID', 'Titre', 'Sous-titre', 'ISBN', 'Statut', 'Langue',
            'Pages', 'Date de publication', 'Date de création', 'Mis en avant',
            'Gratuit', 'Premium seulement', 'Vues', 'Téléchargements',
            'Note moyenne', 'Nombre d\'évaluations', 'Catégories', 'Co-auteurs'
        ]
        writer.writerow(headers)
        
        # Données
        for book in books_data:
            row = [
                book['id'], book['title'], book['subtitle'], book['isbn'],
                book['status'], book['language'], book['page_count'],
                book['publication_date'], book['created_at'], book['is_featured'],
                book['is_free'], book['is_premium_only'], book['view_count'],
                book['download_count'], book['average_rating'], book['total_ratings'],
                ', '.join(book['categories']), ', '.join(book['co_authors'])
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def _export_books_xlsx(self, books_data):
        """Exporte les données des livres au format Excel"""
        # Temporarily disabled - xlsxwriter not installed
        return {'error': 'Excel export temporarily unavailable'}
        worksheet = workbook.add_worksheet('Mes Livres')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white'
        })
        
        # En-têtes
        headers = [
            'ID', 'Titre', 'Sous-titre', 'ISBN', 'Statut', 'Langue',
            'Pages', 'Date de publication', 'Vues', 'Téléchargements',
            'Note moyenne', 'Évaluations'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Données
        for row, book in enumerate(books_data, 1):
            worksheet.write(row, 0, book['id'])
            worksheet.write(row, 1, book['title'])
            worksheet.write(row, 2, book['subtitle'] or '')
            worksheet.write(row, 3, book['isbn'] or '')
            worksheet.write(row, 4, book['status'])
            worksheet.write(row, 5, book['language'])
            worksheet.write(row, 6, book['page_count'] or 0)
            worksheet.write(row, 7, book['publication_date'] or '')
            worksheet.write(row, 8, book['view_count'])
            worksheet.write(row, 9, book['download_count'])
            worksheet.write(row, 10, book['average_rating'])
            worksheet.write(row, 11, book['total_ratings'])
        
        workbook.close()
        output.seek(0)
        
        return output.getvalue()


class PublisherExportAPI:
    """API d'export pour les éditeurs"""
    
    def __init__(self, user):
        self.user = user
        self.is_publisher = self._check_publisher_permissions()
    
    def _check_publisher_permissions(self):
        """Vérifie si l'utilisateur est un éditeur"""
        try:
            user_roles = self.user.user_roles.values_list('role__name', flat=True)
            return 'publisher' in user_roles or self.user.is_staff
        except:
            return False
    
    def get_catalog_overview(self, format_type='json'):
        """Vue d'ensemble du catalogue de l'éditeur"""
        if not self.is_publisher:
            return {'error': 'Permissions insuffisantes'}
        
        try:
            from catalog_service.models import Book, Publisher, Author
            
            # Trouver l'éditeur associé à l'utilisateur
            publisher = Publisher.objects.filter(
                # Supposons qu'il y ait un lien user dans Publisher
                name__icontains=self.user.get_full_name()
            ).first()
            
            if not publisher:
                return {'error': 'Aucun éditeur associé à ce compte'}
            
            # Livres de l'éditeur
            books = Book.objects.filter(publisher=publisher)
            
            catalog_data = {
                'publisher_info': {
                    'name': publisher.name,
                    'country': publisher.country,
                    'founded_year': publisher.founded_year,
                    'website': publisher.website
                },
                'catalog_stats': {
                    'total_books': books.count(),
                    'published_books': books.filter(status='published').count(),
                    'draft_books': books.filter(status='draft').count(),
                    'featured_books': books.filter(is_featured=True).count(),
                    'free_books': books.filter(is_free=True).count(),
                    'premium_books': books.filter(is_premium_only=True).count()
                },
                'performance_metrics': {
                    'total_views': books.aggregate(total=Sum('view_count'))['total'] or 0,
                    'total_downloads': books.aggregate(total=Sum('download_count'))['total'] or 0,
                    'avg_rating': books.aggregate(avg=Avg('ratings__score'))['avg'] or 0
                },
                'top_performing_books': list(
                    books.order_by('-view_count')[:10].values(
                        'title', 'view_count', 'download_count'
                    )
                )
            }
            
            return {
                'success': True,
                'data': catalog_data,
                'export_date': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Erreur lors de l\'export: {str(e)}'}
    
    def get_authors_performance(self, format_type='json', period_days=90):
        """Performance des auteurs de l'éditeur"""
        if not self.is_publisher:
            return {'error': 'Permissions insuffisantes'}
        
        try:
            from catalog_service.models import Book, Publisher, Author
            
            publisher = Publisher.objects.filter(
                name__icontains=self.user.get_full_name()
            ).first()
            
            if not publisher:
                return {'error': 'Aucun éditeur associé à ce compte'}
            
            # Auteurs qui ont publié avec cet éditeur
            books = Book.objects.filter(publisher=publisher)
            authors = Author.objects.filter(books__in=books).distinct()
            
            cutoff_date = timezone.now() - timedelta(days=period_days)
            
            authors_data = []
            for author in authors:
                author_books = books.filter(authors=author)
                recent_books = author_books.filter(created_at__gte=cutoff_date)
                
                author_stats = {
                    'author_name': author.full_name,
                    'author_nationality': author.nationality,
                    'total_books_with_publisher': author_books.count(),
                    'recent_books': recent_books.count(),
                    'total_views': author_books.aggregate(total=Sum('view_count'))['total'] or 0,
                    'total_downloads': author_books.aggregate(total=Sum('download_count'))['total'] or 0,
                    'avg_rating': author_books.aggregate(avg=Avg('ratings__score'))['avg'] or 0,
                    'most_popular_book': author_books.order_by('-view_count').first().title if author_books.exists() else None,
                    'productivity_score': self._calculate_productivity_score(author_books, recent_books)
                }
                
                authors_data.append(author_stats)
            
            # Trier par performance
            authors_data.sort(key=lambda x: x['total_views'], reverse=True)
            
            return {
                'success': True,
                'data': authors_data,
                'summary': {
                    'total_authors': len(authors_data),
                    'period_days': period_days,
                    'top_performer': authors_data[0]['author_name'] if authors_data else None
                }
            }
            
        except Exception as e:
            return {'error': f'Erreur lors de l\'analyse: {str(e)}'}
    
    def _calculate_productivity_score(self, all_books, recent_books):
        """Calcule un score de productivité pour un auteur"""
        total_books = all_books.count()
        recent_count = recent_books.count()
        avg_views = all_books.aggregate(avg=Avg('view_count'))['avg'] or 0
        
        # Score basé sur la productivité récente et la popularité
        productivity = (recent_count / max(total_books, 1)) * 50
        popularity = min(avg_views / 1000, 1) * 50
        
        return round(productivity + popularity, 2)


# Vues d'API REST
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_author_books(request):
    """Export des livres d'un auteur"""
    format_type = request.GET.get('format', 'json')
    period_days = request.GET.get('period_days')
    
    if period_days:
        try:
            period_days = int(period_days)
        except ValueError:
            period_days = None
    
    exporter = AuthorExportAPI(request.user)
    data = exporter.get_author_books_data(format_type, period_days)
    
    if format_type == 'csv':
        response = HttpResponse(data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="mes_livres_{timezone.now().strftime("%Y%m%d")}.csv"'
        return response
    elif format_type == 'xlsx':
        response = HttpResponse(
            data,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="mes_livres_{timezone.now().strftime("%Y%m%d")}.xlsx"'
        return response
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_author_analytics(request):
    """Export des analytics de lecture pour un auteur"""
    format_type = request.GET.get('format', 'json')
    period_days = int(request.GET.get('period_days', 30))
    
    exporter = AuthorExportAPI(request.user)
    data = exporter.get_reading_analytics(format_type, period_days)
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_author_revenue(request):
    """Export du rapport de revenus pour un auteur"""
    format_type = request.GET.get('format', 'json')
    period_days = int(request.GET.get('period_days', 30))
    
    exporter = AuthorExportAPI(request.user)
    data = exporter.get_revenue_report(format_type, period_days)
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_publisher_catalog(request):
    """Export du catalogue d'un éditeur"""
    format_type = request.GET.get('format', 'json')
    
    exporter = PublisherExportAPI(request.user)
    data = exporter.get_catalog_overview(format_type)
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_publisher_authors(request):
    """Export de la performance des auteurs d'un éditeur"""
    format_type = request.GET.get('format', 'json')
    period_days = int(request.GET.get('period_days', 90))
    
    exporter = PublisherExportAPI(request.user)
    data = exporter.get_authors_performance(format_type, period_days)
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_complete_package(request):
    """Export complet pour auteurs et éditeurs"""
    user_roles = request.user.user_roles.values_list('role__name', flat=True)
    
    # Créer un package ZIP avec tous les exports disponibles
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        
        if 'author' in user_roles or request.user.is_staff:
            author_exporter = AuthorExportAPI(request.user)
            
            # Export des livres
            books_data = author_exporter.get_author_books_data('json')
            if books_data.get('success'):
                zip_file.writestr(
                    'auteur_livres.json',
                    json.dumps(books_data, indent=2, ensure_ascii=False)
                )
            
            # Export des analytics
            analytics_data = author_exporter.get_reading_analytics('json')
            if analytics_data.get('success'):
                zip_file.writestr(
                    'auteur_analytics.json',
                    json.dumps(analytics_data, indent=2, ensure_ascii=False)
                )
            
            # Export des revenus
            revenue_data = author_exporter.get_revenue_report('json')
            if revenue_data.get('success'):
                zip_file.writestr(
                    'auteur_revenus.json',
                    json.dumps(revenue_data, indent=2, ensure_ascii=False)
                )
        
        if 'publisher' in user_roles or request.user.is_staff:
            publisher_exporter = PublisherExportAPI(request.user)
            
            # Export du catalogue
            catalog_data = publisher_exporter.get_catalog_overview('json')
            if catalog_data.get('success'):
                zip_file.writestr(
                    'editeur_catalogue.json',
                    json.dumps(catalog_data, indent=2, ensure_ascii=False)
                )
            
            # Export des auteurs
            authors_data = publisher_exporter.get_authors_performance('json')
            if authors_data.get('success'):
                zip_file.writestr(
                    'editeur_auteurs.json',
                    json.dumps(authors_data, indent=2, ensure_ascii=False)
                )
        
        # Ajouter un fichier README
        readme_content = f"""
# Export Coko - {request.user.get_full_name()}

Date d'export: {timezone.now().strftime('%d/%m/%Y %H:%M')}

## Contenu du package:

"""
        if 'author' in user_roles:
            readme_content += """
### Données Auteur:
- auteur_livres.json: Liste de vos livres avec statistiques
- auteur_analytics.json: Analytics de lecture de vos livres  
- auteur_revenus.json: Rapport de revenus estimés

"""
        
        if 'publisher' in user_roles:
            readme_content += """
### Données Éditeur:
- editeur_catalogue.json: Vue d'ensemble de votre catalogue
- editeur_auteurs.json: Performance de vos auteurs

"""
        
        readme_content += """
## Support:
Pour toute question sur ces données, contactez support@coko.africa
"""
        
        zip_file.writestr('README.txt', readme_content)
    
    zip_buffer.seek(0)
    
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="export_coko_{request.user.username}_{timezone.now().strftime("%Y%m%d")}.zip"'
    
    return response