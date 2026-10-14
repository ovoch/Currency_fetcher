from repository.audit_log_repository import AuditLogRep
from core.database import async_session_background


async def save_audit_log_background(user_id: int, action: str):
    async with async_session_background() as background_session:
        audit_log = await AuditLogRep(background_session).add_audit_log_to_db(user_id,action)
        await background_session.commit()
        return audit_log
    

