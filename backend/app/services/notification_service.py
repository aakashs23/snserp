import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notifications import Notification
from app.models.users import User
from app.database.session import async_session_factory
import logging

logger = logging.getLogger(__name__)

async def create_notification(db: AsyncSession, user_id: uuid.UUID, title: str, message: str | None = None) -> Notification:
    """Create a notification for a specific user."""
    notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        title=title,
        message=message
    )
    db.add(notification)
    return notification

async def notify_user(db: AsyncSession, user_id: uuid.UUID, title: str, message: str | None = None) -> Notification:
    """Create and immediately commit a notification for a user (useful for background tasks or standalone events)."""
    notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        title=title,
        message=message
    )
    db.add(notification)
    await db.commit()
    return notification

async def notify_admins(db: AsyncSession, title: str, message: str | None = None) -> None:
    """Send a notification to all admin users."""
    try:
        query = select(User).where(User.role.has(name="admin"))
        result = await db.execute(query)
        admins = result.scalars().all()
        for admin in admins:
            await create_notification(db, admin.id, title, message)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to notify admins: {e}")
        await db.rollback()
