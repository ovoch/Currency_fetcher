import decimal
import enum
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey,Enum, Numeric
from models.base_models import Base
from sqlalchemy.orm import mapped_column,Mapped
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from models.user_models import User

class Condition(str, enum.Enum):
    LESS = "less"
    MORE = "more"

class CurrencyAlerts(Base):
    __tablename__ = "currency_alerts"
    
    id: Mapped[int] = mapped_column(primary_key= True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"), index = True, ondelete = "CASCADE")
    base_currency: Mapped[str] = mapped_column()
    target_currency: Mapped[str] = mapped_column()
    target_rate : Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4))
    condition : Mapped[Condition] = mapped_column()
    
    
    model_users: Mapped['User'] = relationship('User', back_populates = 'alerts')