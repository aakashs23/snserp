from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

from app.database.session import get_db
from app.models.activity import ActivityLog
from app.models.users import User
from app.middleware.auth import get_current_user, require_roles

router = APIRouter()

class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    action: str
    entity_type: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None

class ActivityLogPaginated(BaseModel):
    items: List[ActivityLogResponse]
    total: int
    page: int
    size: int

@router.get("/", response_model=ActivityLogPaginated)
async def get_activity_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Fetch paginated activity logs (Admin/Management feature)."""
    
    offset = (page - 1) * size
    
    # Base query joined with User for names
    stmt = (
        select(ActivityLog, User.full_name, User.email)
        .outerjoin(User, ActivityLog.user_id == User.id)
        .order_by(desc(ActivityLog.created_at))
    )
    
    # Total count
    count_stmt = select(func.count()).select_from(ActivityLog)
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()
    
    # Paginated results
    res = await db.execute(stmt.offset(offset).limit(size))
    rows = res.all()
    
    items = []
    for log, name, email in rows:
        item = ActivityLogResponse.model_validate(log)
        item.user_name = name
        item.user_email = email
        items.append(item)
        
    return ActivityLogPaginated(
        items=items,
        total=total,
        page=page,
        size=size
    )
