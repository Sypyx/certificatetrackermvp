# notification_service/celery_app.py

from celery import Celery
from celery.schedules import crontab
from config import Config

celery = Celery(
    'notification_service',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=['tasks']
)

celery.conf.beat_schedule = {
    'send-expiry-notifications-30-daily': {
        'task': 'tasks.send_expiry_notifications_30',
        'schedule': crontab(hour=0, minute=0),
        'args': []
    },
    'send-expiry-notifications-10-daily': {
        'task': 'tasks.send_expiry_notifications_10',
        'schedule': crontab(hour=0, minute=0),
        'args': []
    },
}

celery.conf.timezone = 'UTC'
