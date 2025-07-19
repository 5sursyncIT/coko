"""Celery configuration for coko project."""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coko.settings')

app = Celery('coko')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'update-reading-streaks': {
        'task': 'reading_service.tasks.update_reading_streaks',
        'schedule': 86400.0,  # Run daily
    },
    'generate-recommendations': {
        'task': 'recommendation_service.tasks.generate_daily_recommendations',
        'schedule': 3600.0,  # Run hourly
    },
    'cleanup-expired-sessions': {
        'task': 'auth_service.tasks.cleanup_expired_sessions',
        'schedule': 3600.0,  # Run hourly
    },
}

app.conf.timezone = 'Africa/Dakar'

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')