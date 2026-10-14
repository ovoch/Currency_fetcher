import decimal
import logging
import httpx
from fastapi import BackgroundTasks,APIRouter,Depends, Query
from sqlalchemy import Numeric
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.currency_schemas import FetchCurrency,HistoryForUser
from api.users import read_current_user
from core.database import get_db
from models.user_models import User
from core.depencies import get_http_client,rate_limiter
from core.redis_config import r
from repository.currency_repostirory import CurrencyRepository
from services.currency_service import CurrencyService,fetch_multiple_currencies
from services.audit_service import save_audit_log_background
from services.alert_service import AlertsService
from schemas.alerts_schemas import AlertResponseList,AlertCreate



router = APIRouter(prefix = "/currency", tags = ["Currency"])


@router.post("")
async def fetch_currency( 
    currencys_in: FetchCurrency, 
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(read_current_user),
    limiter : int = Depends(rate_limiter),
    http_client : httpx.AsyncClient = Depends(get_http_client)):
    
    currency = await CurrencyService(session,r).save_currency(currencys_in.base, currencys_in.target,current_user.id, http_client)
    return currency

@router.get("/history", response_model= list[HistoryForUser] )
async def get_currency_history( 
    offset : int = Query(default = 0,ge = 0),
    limit: int = Query(10, le = 100),
    session : AsyncSession = Depends(get_db),
    current_user : User = Depends(read_current_user)):
    
    
    list_of_history = await CurrencyRepository(session).get_history(current_user.id,limit,offset)
    logging.info("History is shown")
    return list_of_history

@router.get("/stats")
async def get_currency_stats(base: str, target: str, session : AsyncSession = Depends(get_db)):
    stats = await CurrencyRepository(session).count_and_avg_currency(base, target)
    return stats

@router.get("/multirates")
async def get_multi_currencies(base: str,
    background_tasks : BackgroundTasks,
    currencies: list[str] = Query(default=[]),
    # currencies: list[str],  
    current_user: User = Depends(read_current_user),
    http_client : httpx.AsyncClient = Depends(get_http_client)):
    dict_of_currencies = await fetch_multiple_currencies(base, currencies, http_client, r)
    background_tasks.add_task(save_audit_log_background, current_user.id,f"User searched for rates of currencies: {dict_of_currencies}")
    return dict_of_currencies

@router.post("/alerts",response_model= AlertResponseList)
async def set_an_alerts(
    base_info:AlertCreate,
    current_user: User = Depends(read_current_user),
    session : AsyncSession = Depends(get_db)
    ):
    alerts = await AlertsService(session).commit_alert(current_user.id, base_info.base, base_info.currencies, base_info.target_rate, base_info.condition)
    return {"alerts" : alerts}