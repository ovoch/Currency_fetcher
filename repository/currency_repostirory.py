import decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.currency_models import ExchangeRate
from sqlalchemy.orm import joinedload

class CurrencyRepository():
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add(self, base_currency: str, target_currency: str, currency_rate : decimal.Decimal, user_id : int):
        rate_note = ExchangeRate(base_currency = base_currency, target_currency = target_currency, currency_rate = currency_rate ,user_id = user_id)
        self.session.add(rate_note)
        await self.session.flush()
        return rate_note
    
    async def get_history(self,user_id,limit,offset):
        query = select(ExchangeRate).where(ExchangeRate.user_id == user_id).order_by(ExchangeRate.date_n_time.desc()).limit(limit).offset(offset).options(joinedload(ExchangeRate.main_users))
        result = await self.session.execute(query)
        history_for_user = result.scalars().all()
        return history_for_user
    
    async def count_and_avg_currency(self,base,target):
        query = select(func.count().label('Times asked'),func.avg(ExchangeRate.currency_rate).label("Average rate")).where(ExchangeRate.base_currency == base, ExchangeRate.target_currency == target)
        result = await self.session.execute(query)
        stats_of_currency = result.mappings().one()
        return stats_of_currency