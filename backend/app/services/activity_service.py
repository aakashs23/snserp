import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity import ActivityLog

async def log_activity(
    db: AsyncSession,
    user_id: Optional[uuid.UUID],
    action: str,
    module: str,
    object_affected: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """Helper function to create an activity log entry."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        module=module,
        object_affected=object_affected,
        entity_type=entity_type or module,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    # Note: We rely on the caller to commit the transaction if needed,
    # or it will be committed automatically by FastAPI if the session is managed properly.
