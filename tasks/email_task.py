import asyncio
import smtplib
import httpx
import redis.asyncio as redis
from core.database import async_session_celery
from core.celery_config import celery_app
from core.redis_config import rd
from services.currency_service import get_info_rates
from services.email_service import send_email_with_alerts

@celery_app.task(
    name = "check currency rates",
    bind = True,
    max_retries = 10,
    default_retry_delay = 3
)
def check_rates(self):
    asyncio.run(async_check_rates())

async def async_check_rates():
    async with (async_session_celery() as session,
        httpx.AsyncClient() as client,
        redis.Redis(host= rd.Host, port=6379, db=0, decode_responses=True, password= rd.Password) as redis_client):
        res = await get_info_rates(client, redis_client, session)
            
        for key,value in res.items():
            send_an_email_with_alerts.delay(key,value)
        
        

@celery_app.task(
    name = "Send an email of rate",
    bind = True,
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(smtplib.SMTPException, OSError)
)
def send_an_email_with_alerts(self,email:str, alerts: list):
        send_email_with_alerts(email, alerts)  