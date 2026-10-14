from sqlalchemy.ext.asyncio import AsyncSession
from models.currency_allerts import CurrencyAlerts
from sqlalchemy import select
from sqlalchemy.orm import joinedload

class AlertsRepository():
    def __init__(self, session : AsyncSession):
        self.session = session
    
    async def add_multi_alerts_to_db(self,currencies : list[CurrencyAlerts]):
        self.session.add_all(currencies)
        await self.session.flush()
        return currencies
    
    async def get_alerts_from_db(self):
        query = select(CurrencyAlerts).options(joinedload(CurrencyAlerts.model_users))
        result = await self.session.execute(query)
        alerts = result.scalars().all()
        return alerts