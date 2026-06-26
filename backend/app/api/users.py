import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.models.users import User, Role
from app.schemas.users import UserResponse, RoleResponse, UserCreate, UserUpdate
from app.middleware.auth import get_current_user, require_roles
from app.config.supabase import supabase

router = APIRouter()

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    _current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Get all available roles."""
    result = await db.execute(select(Role).order_by(Role.name))
    return result.scalars().all()

@router.get("/", response_model=List[UserResponse])
async def list_users(
    _current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """List all users with their roles."""
    result = await db.execute(
        select(User).options(selectinload(User.role)).order_by(User.full_name)
    )
    return result.scalars().all()

@router.post("/", response_model=UserResponse)
async def create_user(
    payload: UserCreate,
    _current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user via Supabase Admin API and add to DB."""
    # Ensure role exists
    role = await db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role_id")
        
    try:
        # Create user in Supabase Auth bypassing email verification
        auth_res = supabase.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create user in Auth: {str(e)}")
        
    auth_user = auth_res.user
    if not auth_user:
        raise HTTPException(status_code=500, detail="Supabase Auth returned no user")

    # The Supabase auth trigger automatically creates a row in public.users.
    # We should UPDATE it instead of attempting an INSERT.
    user_id = uuid.UUID(auth_user.id)
    user_record = await db.get(User, user_id)
    
    if user_record:
        user_record.full_name = payload.full_name
        user_record.role_id = payload.role_id
        user_record.is_active = True
    else:
        # Fallback in case the trigger didn't fire
        user_record = User(
            id=user_id,
            full_name=payload.full_name,
            email=payload.email,
            role_id=payload.role_id,
            is_active=True
        )
        db.add(user_record)
    
    try:
        await db.commit()
        await db.refresh(user_record)
        # Eager load role
        result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.id == user_record.id)
        )
        return result.scalar_one()
    except Exception as e:
        await db.rollback()
        # Rollback auth if DB fails
        try:
            supabase.auth.admin.delete_user(auth_user.id)
        except:
            pass
        raise HTTPException(status_code=500, detail="Failed to create user in database")

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    _current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Update user role or active status."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if payload.role_id is not None:
        role = await db.get(Role, payload.role_id)
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role_id")
        user.role_id = payload.role_id
        
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    return result.scalar_one()

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user account."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user = await db.get(User, user_id, options=[selectinload(User.role)])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role.name == "admin":
        admin_count = await db.scalar(
            select(func.count(User.id)).where(User.role_id == user.role_id)
        )
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last administrator")

    try:
        await db.delete(user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete user with associated records. Please disable the account instead."
        )

    # Delete from Supabase Auth
    try:
        supabase.auth.admin.delete_user(str(user_id))
    except Exception:
        pass # If it fails here, the user is already gone from DB, which is acceptable

@router.patch("/me/last-login", status_code=status.HTTP_204_NO_CONTENT)
async def update_last_login(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update last login timestamp for the authenticated user."""
    current_user.last_login = func.now()
    await db.commit()
