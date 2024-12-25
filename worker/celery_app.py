# worker/celery_app.py
from celery import Celery
from common.config import Config

celery = Celery(
    main='worker',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=['worker.tasks']
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    task_routes={
        'worker.tasks.*': {'queue': 'youtube_tasks'}
    }
)

with celery.connection() as connection:
    connection.ensure_connection()
    print("connected to redis successfully")
