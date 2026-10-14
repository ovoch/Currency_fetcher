import decimal
from typing import List
from pydantic import BaseModel, ConfigDict

class AlertCreate(BaseModel):
    base: str
    target_rate : decimal.Decimal
    condition: str
    currencies : list[str]
    
    model_config = ConfigDict(from_attributes=True)
    
class AlertResponse(BaseModel):
    id: int
    user_id : int
    base_currency: str
    target_currency: str
    target_rate : decimal.Decimal
    condition: str
    
    model_config = ConfigDict(from_attributes=True)
    
class AlertResponseList(BaseModel):
    alerts: List[AlertResponse]