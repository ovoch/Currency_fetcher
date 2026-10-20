from celery import Celery
from core.celery_settings import cel


celery_app = Celery(
    "currency_worker",
    broker=  cel.Brocker,
    backend = cel.Backend,
    include = ["tasks.email_task"]
)

celery_app.conf.beat_schedule = {
    'check-rates-every-5-minutes': {
        'task': 'check currency rates',
        'schedule': 300.0
    },
}
celery_app.conf.timezone = 'UTC'

