import decimal
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import mapped_column,Mapped
from models.base_models import Base
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from models.user_models import User

class ExchangeRate(Base):
    __tablename__ = "exchange_rate"
    
    id: Mapped[int] = mapped_column(primary_key = True)
    base_currency: Mapped[str] = mapped_column()
    target_currency: Mapped[str] = mapped_column()
    currency_rate : Mapped[decimal.Decimal] = mapped_column()
    date_n_time : Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"), index = True)
    
    main_users : Mapped['User'] = relationship('User', back_populates= 'currency_rates')