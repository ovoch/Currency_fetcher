from typing import List,TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from models.base_models import Base

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id : Mapped[int] = mapped_column(primary_key= True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"), index = True)
    action : Mapped[str] = mapped_column()
    created_at : Mapped[str] = mapped_column(DateTime, server_default=func.now())