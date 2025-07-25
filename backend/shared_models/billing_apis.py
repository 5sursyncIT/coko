"""APIs REST pour le système de facturation Coko"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv
import json

from .billing import (
    Invoice, InvoiceItem, AuthorRoyalty, BillingConfiguration, 
    RecurringBilling
)
from .billing_services import (
    InvoiceService, RoyaltyService, RecurringBillingService,
    BillingAutomationService
)
from .billing_serializers import (
    InvoiceSerializer, InvoiceItemSerializer, AuthorRoyaltySerializer,
    BillingConfigurationSerializer, RecurringBillingSerializer,
    InvoiceCreateSerializer, RoyaltyCalculationSerializer
)


class BillingPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des factures"""
    
    serializer_class = InvoiceSerializer
    pagination_class = BillingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'invoice_type', 'currency']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Invoice.objects.all().select_related('user').prefetch_related('items')
        else:
            return Invoice.objects.filter(user=user).prefetch_related('items')
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Marque une facture comme payée"""
        invoice = self.get_object()
        
        if invoice.status in ['paid', 'refunded']:
            return Response(
                {'error': 'Cette facture est déjà payée ou remboursée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_date = request.data.get('payment_date')
        if payment_date:
            payment_date = datetime.fromisoformat(payment_date)
        
        invoice.mark_as_paid(payment_date)
        
        return Response({
            'message': 'Facture marquée comme payée',
            'invoice': InvoiceSerializer(invoice).data
        })
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Télécharge la facture en PDF (simulation)"""
        invoice = self.get_object()
        
        # Dans un vrai système, on générerait un PDF
        # Ici, on retourne les données de la facture
        response_data = {
            'invoice_number': invoice.invoice_number,
            'billing_name': invoice.billing_name,
            'total_amount': str(invoice.total_amount),
            'currency': invoice.currency,
            'issue_date': invoice.issue_date.isoformat(),
            'due_date': invoice.due_date.isoformat(),
            'items': [
                {
                    'description': item.description,
                    'quantity': str(item.quantity),
                    'unit_price': str(item.unit_price),
                    'total_amount': str(item.total_amount)
                }
                for item in invoice.items.all()
            ]
        }
        
        response = HttpResponse(
            json.dumps(response_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="facture_{invoice.invoice_number}.json"'
        
        return response
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Récupère les statistiques des factures"""
        user = request.user if not request.user.is_staff else None
        stats = InvoiceService.get_invoice_statistics(user)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Liste les factures en retard"""
        queryset = self.get_queryset().filter(status='overdue')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_mark_paid(self, request):
        """Marque plusieurs factures comme payées (admin seulement)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice_ids = request.data.get('invoice_ids', [])
        payment_date = request.data.get('payment_date')
        
        if payment_date:
            payment_date = datetime.fromisoformat(payment_date)
        
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            status__in=['pending', 'sent', 'overdue']
        )
        
        updated_count = 0
        for invoice in invoices:
            invoice.mark_as_paid(payment_date)
            updated_count += 1
        
        return Response({
            'message': f'{updated_count} factures marquées comme payées',
            'updated_count': updated_count
        })


class AuthorRoyaltyViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des royalties d'auteurs"""
    
    serializer_class = AuthorRoyaltySerializer
    pagination_class = BillingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'royalty_type', 'currency']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return AuthorRoyalty.objects.all().select_related('author', 'invoice')
        else:
            return AuthorRoyalty.objects.filter(author=user).select_related('invoice')
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['post'])
    def calculate_period(self, request):
        """Calcule les royalties pour une période donnée"""
        serializer = RoyaltyCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        author_id = serializer.validated_data.get('author_id')
        period_start = serializer.validated_data['period_start']
        period_end = serializer.validated_data['period_end']
        
        # Si pas d'auteur spécifié et utilisateur non admin, utiliser l'utilisateur actuel
        if not author_id and not request.user.is_staff:
            author = request.user
        elif author_id:
            try:
                author = request.user.__class__.objects.get(id=author_id)
            except request.user.__class__.DoesNotExist:
                return Response(
                    {'error': 'Auteur non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {'error': 'ID auteur requis pour les administrateurs'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier les permissions
        if not request.user.is_staff and author != request.user:
            return Response(
                {'error': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            royalties = RoyaltyService.calculate_author_royalties(author, period_start, period_end)
            
            if royalties:
                invoice = RoyaltyService.generate_royalty_invoices(author, royalties)
                
                return Response({
                    'message': 'Royalties calculées avec succès',
                    'royalties_count': len(royalties),
                    'total_amount': sum(r.royalty_amount for r in royalties),
                    'invoice_id': str(invoice.id) if invoice else None,
                    'royalties': AuthorRoyaltySerializer(royalties, many=True).data
                })
            else:
                return Response({
                    'message': 'Aucune royalty à calculer pour cette période',
                    'royalties_count': 0,
                    'total_amount': 0,
                    'invoice_id': None
                })
                
        except Exception as e:
            return Response(
                {'error': f'Erreur lors du calcul des royalties: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé des royalties de l'utilisateur"""
        user = request.user
        if request.user.is_staff and request.query_params.get('author_id'):
            try:
                user = request.user.__class__.objects.get(id=request.query_params['author_id'])
            except request.user.__class__.DoesNotExist:
                return Response(
                    {'error': 'Auteur non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        royalties = AuthorRoyalty.objects.filter(author=user)
        
        summary = {
            'total_royalties': royalties.aggregate(Sum('royalty_amount'))['royalty_amount__sum'] or 0,
            'pending_royalties': royalties.filter(status='pending').aggregate(Sum('royalty_amount'))['royalty_amount__sum'] or 0,
            'paid_royalties': royalties.filter(status='paid').aggregate(Sum('royalty_amount'))['royalty_amount__sum'] or 0,
            'royalties_by_type': {
                royalty_type: royalties.filter(royalty_type=royalty_type).aggregate(Sum('royalty_amount'))['royalty_amount__sum'] or 0
                for royalty_type, _ in AuthorRoyalty.ROYALTY_TYPES
            },
            'last_calculation': royalties.order_by('-calculated_at').first().calculated_at if royalties.exists() else None
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Exporte les royalties en CSV"""
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="royalties.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Auteur', 'Type', 'Livre', 'Montant de base', 'Taux', 
            'Montant royalty', 'Devise', 'Statut', 'Période début', 'Période fin'
        ])
        
        for royalty in queryset:
            writer.writerow([
                str(royalty.id),
                royalty.author.get_full_name(),
                royalty.get_royalty_type_display(),
                royalty.book_title or '',
                str(royalty.base_amount),
                str(royalty.royalty_rate),
                str(royalty.royalty_amount),
                royalty.currency,
                royalty.get_status_display(),
                royalty.period_start.strftime('%Y-%m-%d'),
                royalty.period_end.strftime('%Y-%m-%d')
            ])
        
        return response


class RecurringBillingViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion de la facturation récurrente"""
    
    serializer_class = RecurringBillingSerializer
    pagination_class = BillingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'frequency', 'subscription_type']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return RecurringBilling.objects.all().select_related('user')
        else:
            return RecurringBilling.objects.filter(user=user)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Met en pause une facturation récurrente"""
        billing = self.get_object()
        
        if billing.status != 'active':
            return Response(
                {'error': 'Seules les facturations actives peuvent être mises en pause'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        billing.status = 'paused'
        billing.save()
        
        return Response({
            'message': 'Facturation récurrente mise en pause',
            'billing': RecurringBillingSerializer(billing).data
        })
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Reprend une facturation récurrente"""
        billing = self.get_object()
        
        if billing.status != 'paused':
            return Response(
                {'error': 'Seules les facturations en pause peuvent être reprises'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        billing.status = 'active'
        # Recalculer la prochaine date de facturation
        billing.next_billing_date = billing.calculate_next_billing_date()
        billing.save()
        
        return Response({
            'message': 'Facturation récurrente reprise',
            'billing': RecurringBillingSerializer(billing).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annule une facturation récurrente"""
        billing = self.get_object()
        
        if billing.status == 'cancelled':
            return Response(
                {'error': 'Cette facturation est déjà annulée'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        
        billing.status = 'cancelled'
        billing.end_date = timezone.now()
        billing.metadata.update({
            'cancellation_reason': reason,
            'cancelled_at': timezone.now().isoformat()
        })
        billing.save()
        
        return Response({
            'message': 'Facturation récurrente annulée',
            'billing': RecurringBillingSerializer(billing).data
        })
    
    @action(detail=False, methods=['post'])
    def process_due(self, request):
        """Traite les facturations récurrentes dues (admin seulement)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoices = RecurringBillingService.process_due_billings()
        
        return Response({
            'message': f'{len(invoices)} facturations récurrentes traitées',
            'processed_count': len(invoices),
            'invoice_ids': [str(inv.id) for inv in invoices]
        })


class BillingConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion de la configuration de facturation (admin seulement)"""
    
    queryset = BillingConfiguration.objects.all()
    serializer_class = BillingConfigurationSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = BillingPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['config_type', 'is_active', 'country_code', 'user_type']
    
    @action(detail=False, methods=['get'])
    def get_config(self, request):
        """Récupère une configuration spécifique"""
        config_type = request.query_params.get('config_type')
        config_key = request.query_params.get('config_key')
        country_code = request.query_params.get('country_code', '')
        user_type = request.query_params.get('user_type', '')
        
        if not config_type or not config_key:
            return Response(
                {'error': 'config_type et config_key sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config_value = BillingConfiguration.get_config(
            config_type, config_key, country_code, user_type
        )
        
        if config_value is not None:
            return Response({
                'config_type': config_type,
                'config_key': config_key,
                'config_value': config_value,
                'country_code': country_code,
                'user_type': user_type
            })
        else:
            return Response(
                {'error': 'Configuration non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )


class BillingDashboardViewSet(viewsets.ViewSet):
    """ViewSet pour le tableau de bord de facturation"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Vue d'ensemble du système de facturation"""
        user = request.user
        
        if user.is_staff:
            # Vue administrateur
            data = {
                'invoice_stats': InvoiceService.get_invoice_statistics(),
                'recent_invoices': InvoiceSerializer(
                    Invoice.objects.order_by('-created_at')[:5],
                    many=True
                ).data,
                'pending_royalties': AuthorRoyalty.objects.filter(
                    status__in=['pending', 'calculated']
                ).count(),
                'active_recurring_billings': RecurringBilling.objects.filter(
                    status='active'
                ).count(),
                'overdue_invoices': Invoice.objects.filter(status='overdue').count()
            }
        else:
            # Vue utilisateur
            user_invoices = Invoice.objects.filter(user=user)
            user_royalties = AuthorRoyalty.objects.filter(author=user)
            
            data = {
                'my_invoices': {
                    'total': user_invoices.count(),
                    'pending': user_invoices.filter(status__in=['pending', 'sent']).count(),
                    'paid': user_invoices.filter(status='paid').count(),
                    'overdue': user_invoices.filter(status='overdue').count()
                },
                'my_royalties': {
                    'total_amount': user_royalties.aggregate(Sum('royalty_amount'))['royalty_amount__sum'] or 0,
                    'pending_amount': user_royalties.filter(status='pending').aggregate(Sum('royalty_amount'))['royalty_amount__sum'] or 0,
                    'paid_amount': user_royalties.filter(status='paid').aggregate(Sum('royalty_amount'))['royalty_amount__sum'] or 0
                },
                'recent_invoices': InvoiceSerializer(
                    user_invoices.order_by('-created_at')[:3],
                    many=True
                ).data,
                'recent_royalties': AuthorRoyaltySerializer(
                    user_royalties.order_by('-created_at')[:3],
                    many=True
                ).data
            }
        
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def run_automation(self, request):
        """Lance les tâches d'automatisation (admin seulement)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission refusée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        task_type = request.data.get('task_type')
        
        if task_type == 'daily':
            result = BillingAutomationService.run_daily_billing_tasks()
        elif task_type == 'monthly_royalties':
            result = BillingAutomationService.run_monthly_royalty_calculation()
        else:
            return Response(
                {'error': 'Type de tâche non valide. Utilisez "daily" ou "monthly_royalties"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': f'Tâche {task_type} exécutée avec succès',
            'result': result
        })