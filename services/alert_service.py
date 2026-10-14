from sqlalchemy import Numeric
from repository.alerts_repository import AlertsRepository
from sqlalchemy.ext.asyncio import AsyncSession
from models.currency_allerts import CurrencyAlerts

class AlertsService():
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def commit_alert(self, user_id: int, base_currency: str, target_currencies: list[str], target_rate: Numeric, condition: str):
        alerts_list = []
        for target_currency in target_currencies:
            alerts_list.append(CurrencyAlerts(user_id = user_id, base_currency = base_currency,target_currency = target_currency,target_rate = target_rate,condition= condition))
        await AlertsRepository(self.session).add_multi_alerts_to_db(alerts_list)
        await self.session.commit()
        return alerts_list