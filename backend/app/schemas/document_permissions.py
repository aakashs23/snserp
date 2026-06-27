import uuid
from datetime import datetime
from pydantic import BaseModel

class DocumentPermissionBase(BaseModel):
    can_view: bool = True
    can_download: bool = False
    can_edit: bool = False

class DocumentPermissionCreate(DocumentPermissionBase):
    user_id: uuid.UUID

class DocumentPermissionUpdate(DocumentPermissionBase):
    pass

class UserPermissionInfo(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    
    class Config:
        from_attributes = True

class DocumentPermissionResponse(DocumentPermissionBase):
    id: uuid.UUID
    document_id: uuid.UUID
    user_id: uuid.UUID
    granted_by: uuid.UUID | None
    granted_at: datetime
    
    user: UserPermissionInfo

    class Config:
        from_attributes = True
