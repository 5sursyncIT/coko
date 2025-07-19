# Système de monitoring spécialisé pour l'Afrique
# Implémente les recommandations pour le suivi des performances africaines

import time
import json
import psutil
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
import logging
from typing import Dict, List, Optional
from .african_geolocation import get_user_location, is_african_user

logger = logging.getLogger(__name__)

class AfricanMetricsCollector:
    """
    Collecteur de métriques spécialisé pour les conditions africaines
    """
    
    def __init__(self):
        self.cache_prefix = 'african_metrics'
        self.retention_minutes = 60  # Garder 1 heure de métriques
    
    def record_request_metrics(self, request, response_time_ms: float, response_size_bytes: int = 0):
        """
        Enregistre les métriques d'une requête
        """
        try:
            location = get_user_location(request)
            
            # Métriques de base
            metrics = {
                'timestamp': time.time(),
                'response_time_ms': response_time_ms,
                'response_size_bytes': response_size_bytes,
                'path': request.path,
                'method': request.method,
                'status_code': getattr(request, '_response_status', 200),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
                'is_african': location.get('is_african', False),
                'country_code': location.get('country_code'),
                'african_region': location.get('african_region'),
                'network_quality': location.get('network_quality'),
                'cdn_edge': location.get('cdn_edge')
            }
            
            # Détection de la qualité réseau depuis les headers
            connection_type = request.META.get('HTTP_CONNECTION_TYPE', '')
            downlink = request.META.get('HTTP_DOWNLINK', '')
            
            if connection_type:
                metrics['browser_connection_type'] = connection_type
            if downlink:
                try:
                    metrics['browser_downlink_mbps'] = float(downlink)
                except ValueError:
                    pass
            
            # Stocker dans le cache avec clé temporelle
            minute_key = int(time.time() // 60)
            cache_key = f"{self.cache_prefix}_requests_{minute_key}"
            
            # Récupérer les métriques existantes pour cette minute
            minute_metrics = cache.get(cache_key, [])
            minute_metrics.append(metrics)
            
            # Limiter à 1000 requêtes par minute pour éviter la surcharge
            if len(minute_metrics) > 1000:
                minute_metrics = minute_metrics[-1000:]
            
            cache.set(cache_key, minute_metrics, 3600)  # 1 heure
            
            # Métriques agrégées par minute
            self._update_aggregated_metrics(metrics, minute_key)
            
        except Exception as e:
            logger.error(f"Error recording African metrics: {e}")
    
    def _update_aggregated_metrics(self, metrics: Dict, minute_key: int):
        """
        Met à jour les métriques agrégées par minute
        """
        agg_key = f"{self.cache_prefix}_agg_{minute_key}"
        agg_metrics = cache.get(agg_key, {
            'total_requests': 0,
            'african_requests': 0,
            'slow_requests': 0,
            'total_response_time': 0,
            'total_response_size': 0,
            'by_country': {},
            'by_network_quality': {},
            'by_status_code': {},
            'errors': 0
        })
        
        # Mise à jour des compteurs
        agg_metrics['total_requests'] += 1
        agg_metrics['total_response_time'] += metrics['response_time_ms']
        agg_metrics['total_response_size'] += metrics['response_size_bytes']
        
        if metrics['is_african']:
            agg_metrics['african_requests'] += 1
        
        # Requêtes lentes (>500ms pour l'Afrique, >200ms pour le reste)
        slow_threshold = 500 if metrics['is_african'] else 200
        if metrics['response_time_ms'] > slow_threshold:
            agg_metrics['slow_requests'] += 1
        
        # Par pays
        country = metrics.get('country_code', 'unknown')
        agg_metrics['by_country'][country] = agg_metrics['by_country'].get(country, 0) + 1
        
        # Par qualité réseau
        network = metrics.get('network_quality', 'unknown')
        agg_metrics['by_network_quality'][network] = agg_metrics['by_network_quality'].get(network, 0) + 1
        
        # Par code de statut
        status = str(metrics['status_code'])
        agg_metrics['by_status_code'][status] = agg_metrics['by_status_code'].get(status, 0) + 1
        
        if metrics['status_code'] >= 400:
            agg_metrics['errors'] += 1
        
        cache.set(agg_key, agg_metrics, 3600)
    
    def get_african_performance_summary(self, minutes: int = 10) -> Dict:
        """
        Retourne un résumé des performances africaines
        """
        current_minute = int(time.time() // 60)
        summary = {
            'period_minutes': minutes,
            'total_requests': 0,
            'african_requests': 0,
            'avg_response_time_ms': 0,
            'african_avg_response_time_ms': 0,
            'slow_requests': 0,
            'error_rate': 0,
            'by_country': {},
            'by_network_quality': {},
            'performance_targets_met': False,
            'recommendations': []
        }
        
        total_response_time = 0
        african_response_time = 0
        african_count = 0
        
        # Agréger les données des X dernières minutes
        for i in range(minutes):
            minute_key = current_minute - i
            agg_key = f"{self.cache_prefix}_agg_{minute_key}"
            minute_data = cache.get(agg_key)
            
            if minute_data:
                summary['total_requests'] += minute_data['total_requests']
                summary['african_requests'] += minute_data['african_requests']
                summary['slow_requests'] += minute_data['slow_requests']
                summary['error_rate'] += minute_data['errors']
                
                total_response_time += minute_data['total_response_time']
                
                # Calculer le temps de réponse africain
                # (approximation basée sur la proportion de requêtes africaines)
                if minute_data['african_requests'] > 0:
                    african_ratio = minute_data['african_requests'] / minute_data['total_requests']
                    african_response_time += minute_data['total_response_time'] * african_ratio
                    african_count += minute_data['african_requests']
                
                # Agréger par pays
                for country, count in minute_data['by_country'].items():
                    summary['by_country'][country] = summary['by_country'].get(country, 0) + count
                
                # Agréger par qualité réseau
                for network, count in minute_data['by_network_quality'].items():
                    summary['by_network_quality'][network] = summary['by_network_quality'].get(network, 0) + count
        
        # Calculer les moyennes
        if summary['total_requests'] > 0:
            summary['avg_response_time_ms'] = total_response_time / summary['total_requests']
            summary['error_rate'] = (summary['error_rate'] / summary['total_requests']) * 100
        
        if african_count > 0:
            summary['african_avg_response_time_ms'] = african_response_time / african_count
        
        # Vérifier les objectifs de performance
        african_target = 500  # 500ms pour l'Afrique
        summary['performance_targets_met'] = summary['african_avg_response_time_ms'] <= african_target
        
        # Générer des recommandations
        summary['recommendations'] = self._generate_recommendations(summary)
        
        return summary
    
    def _generate_recommendations(self, summary: Dict) -> List[str]:
        """
        Génère des recommandations basées sur les métriques
        """
        recommendations = []
        
        # Performance
        if summary['african_avg_response_time_ms'] > 500:
            recommendations.append("Temps de réponse africain trop élevé. Considérer l'optimisation du cache ou CDN.")
        
        if summary['african_avg_response_time_ms'] > 1000:
            recommendations.append("Performance critique pour l'Afrique. Activer la compression agressive.")
        
        # Erreurs
        if summary['error_rate'] > 5:
            recommendations.append(f"Taux d'erreur élevé ({summary['error_rate']:.1f}%). Vérifier la stabilité des services.")
        
        # Qualité réseau
        network_stats = summary['by_network_quality']
        total_network = sum(network_stats.values())
        
        if total_network > 0:
            slow_network_ratio = (network_stats.get('2g_dominant', 0) + network_stats.get('2g_3g_mixed', 0)) / total_network
            if slow_network_ratio > 0.3:
                recommendations.append("Forte proportion d'utilisateurs sur réseaux lents. Optimiser pour 2G/3G.")
        
        # Requêtes lentes
        if summary['total_requests'] > 0:
            slow_ratio = summary['slow_requests'] / summary['total_requests']
            if slow_ratio > 0.2:
                recommendations.append(f"Trop de requêtes lentes ({slow_ratio*100:.1f}%). Optimiser les endpoints critiques.")
        
        return recommendations
    
    def get_real_time_metrics(self) -> Dict:
        """
        Retourne les métriques en temps réel
        """
        current_minute = int(time.time() // 60)
        current_metrics = cache.get(f"{self.cache_prefix}_agg_{current_minute}", {})
        
        # Métriques système
        system_metrics = self._get_system_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'current_minute_requests': current_metrics.get('total_requests', 0),
            'current_minute_african': current_metrics.get('african_requests', 0),
            'current_minute_errors': current_metrics.get('errors', 0),
            'system': system_metrics,
            'database': self._get_database_metrics()
        }
    
    def _get_system_metrics(self) -> Dict:
        """
        Retourne les métriques système
        """
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def _get_database_metrics(self) -> Dict:
        """
        Retourne les métriques de base de données
        """
        try:
            with connection.cursor() as cursor:
                # Requête simple pour tester la latence DB
                start_time = time.time()
                cursor.execute("SELECT 1")
                db_latency = (time.time() - start_time) * 1000
                
                return {
                    'latency_ms': round(db_latency, 2),
                    'connections': len(connection.queries) if settings.DEBUG else 0
                }
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {'latency_ms': -1, 'connections': 0}
    
    def cleanup_old_metrics(self):
        """
        Nettoie les anciennes métriques
        """
        current_minute = int(time.time() // 60)
        cutoff_minute = current_minute - self.retention_minutes
        
        # Supprimer les métriques détaillées anciennes
        for i in range(10):  # Nettoyer les 10 dernières minutes expirées
            old_key = f"{self.cache_prefix}_requests_{cutoff_minute - i}"
            cache.delete(old_key)
            
            old_agg_key = f"{self.cache_prefix}_agg_{cutoff_minute - i}"
            cache.delete(old_agg_key)


class AfricanPerformanceMonitor:
    """
    Moniteur de performance spécialisé pour l'Afrique
    """
    
    def __init__(self):
        self.metrics_collector = AfricanMetricsCollector()
        self.alert_thresholds = {
            'african_response_time_ms': 500,
            'global_response_time_ms': 200,
            'error_rate_percent': 5,
            'slow_requests_percent': 20
        }
    
    def check_performance_alerts(self) -> List[Dict]:
        """
        Vérifie les alertes de performance
        """
        alerts = []
        summary = self.metrics_collector.get_african_performance_summary(5)  # 5 dernières minutes
        
        # Alerte temps de réponse africain
        if summary['african_avg_response_time_ms'] > self.alert_thresholds['african_response_time_ms']:
            alerts.append({
                'type': 'performance',
                'severity': 'warning' if summary['african_avg_response_time_ms'] < 1000 else 'critical',
                'message': f"Temps de réponse africain élevé: {summary['african_avg_response_time_ms']:.0f}ms",
                'value': summary['african_avg_response_time_ms'],
                'threshold': self.alert_thresholds['african_response_time_ms']
            })
        
        # Alerte taux d'erreur
        if summary['error_rate'] > self.alert_thresholds['error_rate_percent']:
            alerts.append({
                'type': 'errors',
                'severity': 'critical',
                'message': f"Taux d'erreur élevé: {summary['error_rate']:.1f}%",
                'value': summary['error_rate'],
                'threshold': self.alert_thresholds['error_rate_percent']
            })
        
        # Alerte requêtes lentes
        if summary['total_requests'] > 0:
            slow_percent = (summary['slow_requests'] / summary['total_requests']) * 100
            if slow_percent > self.alert_thresholds['slow_requests_percent']:
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': f"Trop de requêtes lentes: {slow_percent:.1f}%",
                    'value': slow_percent,
                    'threshold': self.alert_thresholds['slow_requests_percent']
                })
        
        return alerts
    
    def get_health_status(self) -> Dict:
        """
        Retourne le statut de santé global
        """
        alerts = self.check_performance_alerts()
        real_time = self.metrics_collector.get_real_time_metrics()
        summary = self.metrics_collector.get_african_performance_summary(10)
        
        # Déterminer le statut global
        critical_alerts = [a for a in alerts if a['severity'] == 'critical']
        warning_alerts = [a for a in alerts if a['severity'] == 'warning']
        
        if critical_alerts:
            status = 'critical'
        elif warning_alerts:
            status = 'warning'
        else:
            status = 'healthy'
        
        return {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'alerts': alerts,
            'summary': {
                'total_requests_10min': summary['total_requests'],
                'african_requests_10min': summary['african_requests'],
                'avg_response_time_ms': summary['avg_response_time_ms'],
                'african_avg_response_time_ms': summary['african_avg_response_time_ms'],
                'error_rate_percent': summary['error_rate'],
                'performance_targets_met': summary['performance_targets_met']
            },
            'real_time': real_time,
            'recommendations': summary['recommendations']
        }


# Instance globale du collecteur de métriques
metrics_collector = AfricanMetricsCollector()
performance_monitor = AfricanPerformanceMonitor()


# Fonctions utilitaires
def record_request_metrics(request, response_time_ms: float, response_size_bytes: int = 0):
    """
    Fonction utilitaire pour enregistrer les métriques d'une requête
    """
    metrics_collector.record_request_metrics(request, response_time_ms, response_size_bytes)


def get_african_performance_dashboard() -> Dict:
    """
    Retourne les données pour le dashboard de performance africain
    """
    summary_10min = metrics_collector.get_african_performance_summary(10)
    summary_60min = metrics_collector.get_african_performance_summary(60)
    health_status = performance_monitor.get_health_status()
    
    return {
        'health_status': health_status['status'],
        'last_10_minutes': summary_10min,
        'last_hour': summary_60min,
        'alerts': health_status['alerts'],
        'recommendations': summary_10min['recommendations'],
        'real_time': health_status['real_time']
    }


def cleanup_metrics():
    """
    Fonction de nettoyage des métriques (à appeler périodiquement)
    """
    metrics_collector.cleanup_old_metrics()


# Vue Django pour exposer les métriques
def african_metrics_api(request):
    """
    API pour exposer les métriques africaines
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    action = request.GET.get('action', 'dashboard')
    
    if action == 'dashboard':
        data = get_african_performance_dashboard()
    elif action == 'health':
        data = performance_monitor.get_health_status()
    elif action == 'summary':
        minutes = int(request.GET.get('minutes', 10))
        data = metrics_collector.get_african_performance_summary(minutes)
    elif action == 'realtime':
        data = metrics_collector.get_real_time_metrics()
    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    return JsonResponse(data, json_dumps_params={'indent': 2})


# Tâche de nettoyage périodique (pour Celery)
def cleanup_african_metrics_task():
    """
    Tâche Celery pour nettoyer les métriques anciennes
    """
    try:
        cleanup_metrics()
        logger.info("African metrics cleanup completed")
    except Exception as e:
        logger.error(f"Error during metrics cleanup: {e}")


# Configuration des alertes par email/SMS
class AfricanAlertManager:
    """
    Gestionnaire d'alertes pour les métriques africaines
    """
    
    def __init__(self):
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes entre alertes du même type
    
    def should_send_alert(self, alert_type: str) -> bool:
        """
        Vérifie si une alerte doit être envoyée (évite le spam)
        """
        now = time.time()
        last_time = self.last_alert_time.get(alert_type, 0)
        
        if now - last_time > self.alert_cooldown:
            self.last_alert_time[alert_type] = now
            return True
        
        return False
    
    def send_performance_alert(self, alert: Dict):
        """
        Envoie une alerte de performance
        """
        if not self.should_send_alert(alert['type']):
            return
        
        # Ici on pourrait intégrer l'envoi d'emails, SMS, Slack, etc.
        logger.warning(f"AFRICAN PERFORMANCE ALERT: {alert['message']}")
        
        # Exemple d'intégration Slack/Discord
        # self.send_slack_alert(alert)
        
        # Exemple d'intégration SMS pour alertes critiques
        # if alert['severity'] == 'critical':
        #     self.send_sms_alert(alert)


# Instance globale du gestionnaire d'alertes
alert_manager = AfricanAlertManager()