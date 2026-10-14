import decimal
import json
import logging
import asyncio
import decimal
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from services.external_api import currency_api
from repository.currency_repostirory import CurrencyRepository
from services.currency_service import CurrencyService

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