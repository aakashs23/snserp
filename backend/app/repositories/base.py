"""Generic async repository with standard CRUD operations."""

import uuid
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository providing async CRUD operations for any SQLAlchemy model."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: uuid.UUID) -> ModelType | None:
        """Get a single record by primary key."""
        return await self.session.get(self.model, id)

    async def get_by(self, **kwargs: Any) -> ModelType | None:
        """Get a single record matching the given filters."""
        query = select(self.model).filter_by(**kwargs)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Any | None = None,
        **filters: Any,
    ) -> Sequence[ModelType]:
        """Get multiple records with pagination and optional filtering."""
        query = select(self.model)

        if filters:
            query = query.filter_by(**filters)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self, **filters: Any) -> int:
        """Count records matching the given filters."""
        query = select(func.count()).select_from(self.model)
        if filters:
            query = query.filter_by(**filters)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """Create a new record from a dictionary of values."""
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self, db_obj: ModelType, obj_in: dict[str, Any]
    ) -> ModelType:
        """Update an existing record with new values."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete a record by primary key. Returns True if deleted."""
        db_obj = await self.get(id)
        if db_obj:
            await self.session.delete(db_obj)
            await self.session.flush()
            return True
        return False

    def _apply_filters(
        self, query: Select, filters: dict[str, Any]
    ) -> Select:
        """Apply dynamic filters to a query. Override in subclasses for custom logic."""
        return query.filter_by(**filters)
