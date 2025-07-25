"""
Système de rapports financiers pour les paiements mobiles africains
Analyse des revenus, transactions et performance des providers
"""

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
import json
import uuid


class PaymentTransaction(models.Model):
    """Modèle pour tracker les transactions de paiement"""
    
    TRANSACTION_STATUS = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminée'),
        ('failed', 'Échouée'),
        ('cancelled', 'Annulée'),
        ('refunded', 'Remboursée')
    ]
    
    PAYMENT_PROVIDERS = [
        ('orange_money', 'Orange Money'),
        ('mtn_momo', 'MTN Mobile Money'),
        ('wave', 'Wave'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('other', 'Autre')
    ]
    
    TRANSACTION_TYPES = [
        ('subscription', 'Abonnement'),
        ('book_purchase', 'Achat de livre'),
        ('premium_upgrade', 'Mise à niveau premium'),
        ('refund', 'Remboursement'),
        ('tip', 'Pourboire auteur')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    
    # Détails de la transaction
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XOF')  # XOF, NGN, GHS
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    
    # Informations du provider
    payment_provider = models.CharField(max_length=20, choices=PAYMENT_PROVIDERS)
    provider_transaction_id = models.CharField(max_length=255, blank=True)
    provider_reference = models.CharField(max_length=255, blank=True)
    
    # Détails client
    phone_number = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True)
    fees = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_provider', 'created_at']),
            models.Index(fields=['country_code', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} - {self.get_status_display()}"
    
    @property
    def is_african_payment(self):
        """Vérifie si c'est un paiement mobile africain"""
        return self.payment_provider in ['orange_money', 'mtn_momo', 'wave']
    
    def mark_completed(self):
        """Marque la transaction comme terminée"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def calculate_fees(self):
        """Calcule les frais de transaction"""
        fee_rates = {
            'orange_money': Decimal('0.02'),  # 2%
            'mtn_momo': Decimal('0.025'),     # 2.5%
            'wave': Decimal('0.01'),          # 1%
            'stripe': Decimal('0.029'),       # 2.9%
            'paypal': Decimal('0.035'),       # 3.5%
        }
        
        rate = fee_rates.get(self.payment_provider, Decimal('0.03'))
        self.fees = self.amount * rate
        self.net_amount = self.amount - self.fees
        return self.fees


class FinancialReport:
    """Générateur de rapports financiers"""
    
    def __init__(self, start_date: datetime = None, end_date: datetime = None):
        self.end_date = end_date or timezone.now()
        self.start_date = start_date or (self.end_date - timedelta(days=30))
    
    def get_revenue_overview(self) -> Dict[str, Any]:
        """Vue d'ensemble des revenus"""
        transactions = PaymentTransaction.objects.filter(
            created_at__gte=self.start_date,
            created_at__lte=self.end_date,
            status='completed'
        )
        
        total_revenue = transactions.aggregate(
            total=Sum('net_amount')
        )['total'] or Decimal('0.00')
        
        total_fees = transactions.aggregate(
            total=Sum('fees')
        )['total'] or Decimal('0.00')
        
        transaction_count = transactions.count()
        
        # Revenus par provider
        revenue_by_provider = {}
        for provider, name in PaymentTransaction.PAYMENT_PROVIDERS:
            provider_revenue = transactions.filter(
                payment_provider=provider
            ).aggregate(total=Sum('net_amount'))['total'] or Decimal('0.00')
            
            if provider_revenue > 0:
                revenue_by_provider[name] = float(provider_revenue)
        
        # Revenus par pays
        revenue_by_country = {}
        for country_code in ['SN', 'CI', 'ML', 'BF', 'NG', 'GH']:
            country_revenue = transactions.filter(
                country_code=country_code
            ).aggregate(total=Sum('net_amount'))['total'] or Decimal('0.00')
            
            if country_revenue > 0:
                revenue_by_country[country_code] = float(country_revenue)
        
        # Tendance quotidienne
        daily_revenue = self._get_daily_revenue_trend(transactions)
        
        return {
            'total_revenue': float(total_revenue),
            'total_fees': float(total_fees),
            'gross_revenue': float(total_revenue + total_fees),
            'transaction_count': transaction_count,
            'average_transaction': float(total_revenue / transaction_count) if transaction_count > 0 else 0,
            'revenue_by_provider': revenue_by_provider,
            'revenue_by_country': revenue_by_country,
            'daily_trend': daily_revenue,
            'period': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat(),
                'days': (self.end_date - self.start_date).days
            }
        }
    
    def get_provider_performance(self) -> Dict[str, Any]:
        """Performance des providers de paiement"""
        performance = {}
        
        for provider, provider_name in PaymentTransaction.PAYMENT_PROVIDERS:
            provider_transactions = PaymentTransaction.objects.filter(
                payment_provider=provider,
                created_at__gte=self.start_date,
                created_at__lte=self.end_date
            )
            
            if provider_transactions.exists():
                total_count = provider_transactions.count()
                completed_count = provider_transactions.filter(status='completed').count()
                failed_count = provider_transactions.filter(status='failed').count()
                
                success_rate = (completed_count / total_count * 100) if total_count > 0 else 0
                
                revenue = provider_transactions.filter(
                    status='completed'
                ).aggregate(total=Sum('net_amount'))['total'] or Decimal('0.00')
                
                avg_processing_time = self._calculate_avg_processing_time(provider_transactions)
                
                performance[provider_name] = {
                    'total_transactions': total_count,
                    'successful_transactions': completed_count,
                    'failed_transactions': failed_count,
                    'success_rate': round(success_rate, 2),
                    'total_revenue': float(revenue),
                    'avg_processing_time_minutes': avg_processing_time,
                    'market_share': round((total_count / PaymentTransaction.objects.filter(
                        created_at__gte=self.start_date,
                        created_at__lte=self.end_date
                    ).count() * 100), 2) if PaymentTransaction.objects.filter(
                        created_at__gte=self.start_date,
                        created_at__lte=self.end_date
                    ).count() > 0 else 0
                }
        
        return performance
    
    def get_african_payment_insights(self) -> Dict[str, Any]:
        """Insights spécifiques aux paiements mobiles africains"""
        african_transactions = PaymentTransaction.objects.filter(
            created_at__gte=self.start_date,
            created_at__lte=self.end_date,
            payment_provider__in=['orange_money', 'mtn_momo', 'wave']
        )
        
        total_african = african_transactions.count()
        total_all = PaymentTransaction.objects.filter(
            created_at__gte=self.start_date,
            created_at__lte=self.end_date
        ).count()
        
        african_adoption_rate = (total_african / total_all * 100) if total_all > 0 else 0
        
        # Analyse par heure pour optimiser les campagnes
        hourly_distribution = {}
        for hour in range(24):
            hour_count = african_transactions.filter(
                created_at__hour=hour
            ).count()
            hourly_distribution[hour] = hour_count
        
        # Taux de conversion par pays
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        conversion_by_country = {}
        for country_code in ['SN', 'CI', 'ML', 'BF', 'NG', 'GH']:
            country_users = User.objects.filter(country=country_code).count()
            country_transactions = african_transactions.filter(
                country_code=country_code
            ).count()
            
            if country_users > 0:
                conversion_rate = (country_transactions / country_users * 100)
                conversion_by_country[country_code] = round(conversion_rate, 2)
        
        # Analyse des échecs
        failure_analysis = self._analyze_payment_failures(african_transactions)
        
        return {
            'african_adoption_rate': round(african_adoption_rate, 2),
            'total_african_transactions': total_african,
            'hourly_distribution': hourly_distribution,
            'peak_hours': self._get_peak_hours(hourly_distribution),
            'conversion_by_country': conversion_by_country,
            'failure_analysis': failure_analysis,
            'recommended_actions': self._get_recommendations(african_transactions)
        }
    
    def get_subscription_analytics(self) -> Dict[str, Any]:
        """Analytics des abonnements"""
        subscription_transactions = PaymentTransaction.objects.filter(
            transaction_type='subscription',
            created_at__gte=self.start_date,
            created_at__lte=self.end_date,
            status='completed'
        )
        
        # MRR (Monthly Recurring Revenue)
        monthly_revenue = subscription_transactions.aggregate(
            total=Sum('net_amount')
        )['total'] or Decimal('0.00')
        
        # Convertir en MRR si la période n'est pas d'un mois
        period_days = (self.end_date - self.start_date).days
        if period_days != 30:
            monthly_revenue = monthly_revenue * (30 / period_days)
        
        # Nouveaux abonnements vs renouvellements
        new_subscriptions = subscription_transactions.filter(
            user__date_joined__gte=self.start_date
        ).count()
        
        renewals = subscription_transactions.count() - new_subscriptions
        
        # ARPU (Average Revenue Per User)
        unique_subscribers = subscription_transactions.values('user').distinct().count()
        arpu = float(monthly_revenue / unique_subscribers) if unique_subscribers > 0 else 0
        
        # Churn rate (approximation)
        churn_rate = self._calculate_churn_rate()
        
        return {
            'monthly_recurring_revenue': float(monthly_revenue),
            'new_subscriptions': new_subscriptions,
            'renewals': renewals,
            'total_subscribers': unique_subscribers,
            'arpu': round(arpu, 2),
            'churn_rate': churn_rate,
            'subscription_types': self._get_subscription_breakdown(),
            'ltv_estimate': round(arpu / (churn_rate / 100), 2) if churn_rate > 0 else 0
        }
    
    def _get_daily_revenue_trend(self, transactions) -> List[Dict[str, Any]]:
        """Tendance quotidienne des revenus"""
        from django.db.models import TruncDate
        
        daily_data = transactions.filter(
            status='completed'
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            revenue=Sum('net_amount'),
            count=Count('id')
        ).order_by('date')
        
        return [
            {
                'date': item['date'].isoformat(),
                'revenue': float(item['revenue']),
                'transactions': item['count']
            }
            for item in daily_data
        ]
    
    def _calculate_avg_processing_time(self, transactions) -> float:
        """Calcule le temps moyen de traitement"""
        completed_transactions = transactions.filter(
            status='completed',
            completed_at__isnull=False
        )
        
        total_time = timedelta()
        count = 0
        
        for transaction in completed_transactions:
            processing_time = transaction.completed_at - transaction.created_at
            total_time += processing_time
            count += 1
        
        if count == 0:
            return 0
        
        avg_time = total_time / count
        return avg_time.total_seconds() / 60  # en minutes
    
    def _analyze_payment_failures(self, transactions) -> Dict[str, Any]:
        """Analyse les échecs de paiement"""
        failed_transactions = transactions.filter(status='failed')
        
        failure_reasons = {}
        for transaction in failed_transactions:
            reason = transaction.metadata.get('failure_reason', 'Unknown')
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        return {
            'total_failures': failed_transactions.count(),
            'failure_rate': round((failed_transactions.count() / transactions.count() * 100), 2) if transactions.count() > 0 else 0,
            'common_reasons': failure_reasons,
            'failures_by_provider': dict(
                failed_transactions.values('payment_provider').annotate(
                    count=Count('id')
                ).values_list('payment_provider', 'count')
            )
        }
    
    def _get_peak_hours(self, hourly_distribution: Dict[int, int]) -> List[int]:
        """Détermine les heures de pointe"""
        sorted_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]
    
    def _get_recommendations(self, transactions) -> List[str]:
        """Recommandations basées sur l'analyse"""
        recommendations = []
        
        # Analyse du taux de succès
        success_rate = transactions.filter(status='completed').count() / transactions.count() * 100
        if success_rate < 90:
            recommendations.append("Améliorer la stabilité des paiements mobiles")
        
        # Analyse de l'adoption
        orange_money_count = transactions.filter(payment_provider='orange_money').count()
        wave_count = transactions.filter(payment_provider='wave').count()
        
        if wave_count > orange_money_count:
            recommendations.append("Promouvoir davantage Wave qui performe bien")
        
        recommendations.append("Optimiser les campagnes pendant les heures de pointe")
        
        return recommendations
    
    def _calculate_churn_rate(self) -> float:
        """Calcule approximativement le taux de churn"""
        # Simplification : utilisateurs qui n'ont pas renouvelé leur abonnement
        previous_month = self.start_date - timedelta(days=30)
        
        prev_subscribers = set(
            PaymentTransaction.objects.filter(
                transaction_type='subscription',
                status='completed',
                created_at__gte=previous_month,
                created_at__lt=self.start_date
            ).values_list('user_id', flat=True)
        )
        
        current_subscribers = set(
            PaymentTransaction.objects.filter(
                transaction_type='subscription', 
                status='completed',
                created_at__gte=self.start_date,
                created_at__lte=self.end_date
            ).values_list('user_id', flat=True)
        )
        
        if not prev_subscribers:
            return 0.0
        
        churned = len(prev_subscribers - current_subscribers)
        return round((churned / len(prev_subscribers) * 100), 2)
    
    def _get_subscription_breakdown(self) -> Dict[str, int]:
        """Répartition par type d'abonnement"""
        return dict(
            PaymentTransaction.objects.filter(
                transaction_type='subscription',
                status='completed',
                created_at__gte=self.start_date,
                created_at__lte=self.end_date
            ).values('user__subscription_type').annotate(
                count=Count('id')
            ).values_list('user__subscription_type', 'count')
        )
    
    def export_financial_data(self, format_type: str = 'json') -> str:
        """Exporte les données financières"""
        data = {
            'revenue_overview': self.get_revenue_overview(),
            'provider_performance': self.get_provider_performance(),
            'african_insights': self.get_african_payment_insights(),
            'subscription_analytics': self.get_subscription_analytics()
        }
        
        if format_type == 'json':
            return json.dumps(data, indent=2, default=str)
        
        return str(data)