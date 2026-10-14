from sqlalchemy.ext.asyncio import AsyncSession
from models.AuditLog import AuditLog

class AuditLogRep():
    def __init__(self, background_session : AsyncSession):
        self.background_session = background_session
        
    async def add_audit_log_to_db(self, user_id: int, action: str):
        audit_log = AuditLog(user_id = user_id, action = action)
        self.background_session.add(audit_log)
        await self.background_session.flush()
        return audit_log
        