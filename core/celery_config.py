from celery import Celery
from core.celery_settings import cel


celery_app = Celery(
    "currency_worker",
    broker=  cel.Brocker,
    backend = cel.Backend,
    include = ["tasks.email_tasks"]
)

