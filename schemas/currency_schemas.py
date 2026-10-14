import decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from schemas.user_schemas import UserShort

class FetchCurrency(BaseModel):
    base: str
    target: str
    
class HistoryForUser(BaseModel):
    id : int 
    base_currency : str
    target_currency : str 
    currency_rate : decimal.Decimal
    date_n_time : datetime
    main_users : UserShort
    
    model_config = ConfigDict(from_attributes=True)