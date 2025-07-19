"""Health check views for Coko project."""

import json
from django.http import JsonResponse
from django.db import connections
from django.core.cache import cache
from django.conf import settings
import redis


def health_check(request):
    """Basic health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'coko-backend',
        'version': '1.0.0'
    })


def readiness_check(request):
    """Readiness check - verifies all dependencies are available."""
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'cache': check_cache(),
    }
    
    all_healthy = all(check['status'] == 'healthy' for check in checks.values())
    
    response_data = {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks
    }
    
    status_code = 200 if all_healthy else 503
    return JsonResponse(response_data, status=status_code)


def liveness_check(request):
    """Liveness check - verifies the application is running."""
    return JsonResponse({
        'status': 'alive',
        'service': 'coko-backend'
    })


def check_database():
    """Check database connectivity."""
    try:
        # Check default database
        db_conn = connections['default']
        db_conn.cursor().execute('SELECT 1')
        
        # Check other databases
        for db_name in ['auth_db', 'catalog_db', 'reading_db']:
            if db_name in connections.databases:
                db_conn = connections[db_name]
                db_conn.cursor().execute('SELECT 1')
        
        return {'status': 'healthy', 'message': 'Database connections OK'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Database error: {str(e)}'}


def check_redis():
    """Check Redis connectivity."""
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        return {'status': 'healthy', 'message': 'Redis connection OK'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Redis error: {str(e)}'}


def check_cache():
    """Check cache functionality."""
    try:
        test_key = 'health_check_test'
        test_value = 'test_value'
        
        cache.set(test_key, test_value, 30)
        cached_value = cache.get(test_key)
        
        if cached_value == test_value:
            cache.delete(test_key)
            return {'status': 'healthy', 'message': 'Cache working OK'}
        else:
            return {'status': 'unhealthy', 'message': 'Cache not working properly'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Cache error: {str(e)}'}