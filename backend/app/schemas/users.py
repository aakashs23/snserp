"""Pydantic schemas for User and Role responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    phone: Optional[str] = None
    role_id: UUID
    role: Optional[RoleResponse] = None
    avatar_url: Optional[str] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    # Bounds mirror models/users.py column widths. UserResponse.email stays a
    # plain str: it serialises rows already in the DB and must not fail on them.
    full_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role_id: UUID

class UserUpdate(BaseModel):
    role_id: Optional[UUID] = None
    is_active: Optional[bool] = None
