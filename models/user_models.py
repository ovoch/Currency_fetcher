from typing import List,TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from models.base_models import Base

if TYPE_CHECKING:
    from models.currency_models import ExchangeRate
    from models.currency_allerts import CurrencyAlerts

class User(Base):
    __tablename__ = 'users'
    
    # id = mapped_column(Integer, primary_key = True)
    # name = mapped_column(String)
    # email = mapped_column(String, unique = True)
    #Было в старых версиях по-новому снизу
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password : Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default= True)
    
    
    currency_rates : Mapped[List['ExchangeRate']] = relationship('ExchangeRate', back_populates = 'main_users')
    alerts: Mapped[List['CurrencyAlerts']] = relationship('CurrencyAlerts', back_populates = 'model_users')
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name})>"
        