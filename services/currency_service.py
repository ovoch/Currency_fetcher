import decimal
import json
import logging
import asyncio
import decimal
from collections import defaultdict
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from repository.alerts_repository import AlertsRepository
from services.external_api import currency_api
from repository.currency_repostirory import CurrencyRepository

class CurrencyService():
    def __init__(self,session : AsyncSession, redis_client : Redis):
        self.session = session
        self.redis_client = redis_client
        
    async def redis_cache(self, base, target, http_client):
        redis_key = f"base:{base}:target:{target}"
        pre_cached_data = await self.redis_client.get(redis_key)
        
        if not pre_cached_data:
            logging.debug("Cache is empty")
            api = await currency_api(base, target, http_client)
            data = json.dumps(api)
            await self.redis_client.set(redis_key, data,ex= 3600)
        else: 
            logging.debug("Cache is full")
            api = json.loads(pre_cached_data)
        
        return api
    
    async def add_currency_to_db(self, base, target, rate, user_id):
        await CurrencyRepository(self.session).add(base,target,rate,user_id)
        await self.session.commit()
        
    async def save_currency(self,base,target,user_id, http_client):
        api = await self.redis_cache(base,target,http_client)
        rate = decimal.Decimal(str(api.get("rates", {}).get(f"{target}"))).quantize(decimal.Decimal("0.001"))
        await self.add_currency_to_db(base,target,rate,user_id)
        return api
    
async def fetch_one_currency(base_curr: str, other_curr: str, http_client, redis_client, semaphore):
    async with semaphore: 
        curr_data = await CurrencyService(None,redis_client).redis_cache(base_curr, other_curr, http_client)
        rate = decimal.Decimal(str(curr_data.get("rates", {}).get(f"{other_curr}"))).quantize(decimal.Decimal("0.001"))
        return {"currency" : other_curr, "rate": rate} 
        
async def fetch_multiple_currencies(base: str, currencies : list[str], http_client, redis_client):
    sem = asyncio.Semaphore(10)
    resp = await asyncio.gather(*[asyncio.wait_for(fetch_one_currency(base,curr, http_client, redis_client,sem),timeout=2.0) for curr in currencies],return_exceptions=True)
    proper_resp = {}
    
    
    proper_resp["base_curr"] = base
    proper_resp["rates"] = {}
        
    for suc_resp in resp:
        if not isinstance(suc_resp,Exception):
            name_of_curr = suc_resp.get("currency")
            rate = suc_resp.get("rate")
            proper_resp["rates"][name_of_curr] = rate
            
    # 2. МЕСТО ДЛЯ БАЗЫ ДАННЫХ (если потребуется в будущем):
    # async with async_session_background() as db_session:
    #     await db_session.add_all(одна_большая_пачка_данных_из_proper_resp)
    #     await db_session.commit()
        
    return proper_resp    

async def get_info_rates(http_client,redis_client, session):
     
        alerts = await AlertsRepository(session).get_alerts_from_db()
        currency_dict = {}
        for alert in alerts:
            if alert.base_currency not in currency_dict:
                currency_dict[alert.base_currency] = set()
            if alert.base_currency in currency_dict:
                currency_dict[alert.base_currency].add(alert.target_currency)
                
        currency_rates = await asyncio.gather(*[fetch_multiple_currencies(base, currency_dict.get(base), http_client, redis_client) for base in currency_dict])
        
        
        dict_of_currency_rates = {element["base_curr"]: element["rates"] for element in currency_rates }
        res = defaultdict(list)
        current_rate = {}
        for alert in alerts:
            # current_rate = dict_of_currency_rates[alert.base_currency][alert.target_currency]
            rates = dict_of_currency_rates.get(alert.base_currency, {})
            current_rate = rates.get(alert.target_currency)

            if current_rate is None:
            # Валюта не загрузилась или упала по таймауту — пропускаем этот алерт
                continue
            if alert.condition == "less": 
                if current_rate < alert.target_rate:
                    res[alert.model_users.email].append({
                        "base": alert.base_currency,
                        "target": alert.target_currency,
                        "current_rate": str(current_rate),
                        "rate": str(alert.target_rate)
                    })
            elif alert.condition == "more":
                if current_rate > alert.target_rate:
                    res[alert.model_users.email].append({
                        "base": alert.base_currency,
                        "target": alert.target_currency,
                        "current_rate": str(current_rate),
                        "rate": str(alert.target_rate)
                    })
        
        return res
        