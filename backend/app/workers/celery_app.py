from celery import Celery
from celery.schedules import crontab
import app.workers.tasks 

from app.core.settings import settings

celery = Celery(
    "sixth_degree_py",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery.conf.timezone = "UTC"

celery.conf.beat_schedule = {}


