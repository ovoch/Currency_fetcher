import asyncio
import httpx
import redis.asyncio as redis
import smtplib
from collections import defaultdict
from time import sleep
from core.database import db,async_session
from core.celery_config import celery_app
from core.redis_config import rd
from repository.alerts_repository import AlertsRepository
from services.currency_service import fetch_multiple_currencies
from core.email_config import em

celery_app.conf.beat_schedule = {
    'check-rates-every-5-minutes': {
        'task': 'check_rates',
        'schedule': 300.0,
    },
}
celery_app.conf.timezone = 'UTC'

@celery_app.task(
    name = "check currency rates",
    bind = True,
    max_retries = 10,
    default_retry_delay = 3
)
def check_rates(self):
    asyncio.run(async_check_rates())

async def async_check_rates():
    async with (async_session() as session,
        httpx.AsyncClient() as client,
        redis.Redis(host= db.Host, port=6379, db=0, decode_responses=True, password= rd.Password) as redis_client): 
        alerts = await AlertsRepository(session).get_alerts_from_db()
        currency_dict = {}
        for alert in alerts:
            if alert.base_currency not in currency_dict:
                currency_dict[alert.base_currency] = set()
            if alert.base_currency in currency_dict:
                currency_dict[alert.base_currency].add(alert.target_currency)
                
        currency_rates = await asyncio.gather(*[fetch_multiple_currencies(base, currency_dict.get(base), client, redis_client) for base in currency_dict])
        
        dict_of_currency_rates = {key: value for element in currency_rates for key,value in element.items()}
        res = defaultdict(list)
        current_rate = {}
        for alert in alerts:
            current_rate = dict_of_currency_rates[alert.base_currency]["rates"][alert.target_currency]
            if alert.condition == "less": 
                if current_rate < alert.target_rate:
                    res[alert.model_users.email].append({
                        "base": alert.base_currency,
                        "target": alert.target_currency,
                        "current_rate": current_rate,
                        "rate": alert.target_rate
                    })
            elif alert.condition == "more":
                if current_rate > alert.target_rate:
                    res[alert.model_users.email].append({
                        "base": alert.base_currency,
                        "target": alert.target_currency,
                        "current_rate": current_rate,
                        "rate": alert.target_rate
                    })
            
        for key,value in res.items():
            send_an_email_with_rates.delay(key,value)
        
        

@celery_app.task(
    name = "Send an email of rate",
    bind = True,
    max_retries=3,
    default_retry_delay=5
)
def send_an_email_with_rates(self,email: str, curr:list):
    smtpObj.login(em.Login,em.Password)