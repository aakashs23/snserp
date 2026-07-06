import uuid
from datetime import datetime
from pydantic import BaseModel

class NotificationBase(BaseModel):
    title: str
    message: str | None = None
    is_read: bool = False

class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    is_read: bool
