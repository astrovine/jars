import os
from celery import Celery

broker_url = os.getenv('CELERY_BROKER_URL', 'amqp://guest:guest@rabbitmq:5672//')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')


celery_app = Celery(
    'application',
    broker=broker_url,
    backend=result_backend,
)


celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    beat_schedule={
        'fetch-exchange-rate-hourly': {
            'task': 'application.core.tasks.task_fetch_and_store_rate',
            'schedule': 3600.0,
        },
    },
)

celery_app.conf.imports = ['application.core.tasks']
