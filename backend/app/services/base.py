"""Base service layer pattern."""

import uuid
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """Base service providing common business operations on top of a repository.

    Subclasses should override methods to add business logic, validation,
    and authorization checks.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.repository = BaseRepository(model, session)
        self.session = session

    async def get(self, id: uuid.UUID) -> ModelType | None:
        """Get a single record by ID."""
        return await self.repository.get(id)

    async def get_by(self, **kwargs: Any) -> ModelType | None:
        """Get a single record by arbitrary filters."""
        return await self.repository.get_by(**kwargs)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Any | None = None,
        **filters: Any,
    ) -> Sequence[ModelType]:
        """Get a paginated list of records."""
        return await self.repository.get_multi(
            skip=skip, limit=limit, order_by=order_by, **filters
        )

    async def count(self, **filters: Any) -> int:
        """Count records matching filters."""
        return await self.repository.count(**filters)

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """Create a new record."""
        return await self.repository.create(obj_in)

    async def update(
        self, id: uuid.UUID, obj_in: dict[str, Any]
    ) -> ModelType | None:
        """Update an existing record by ID."""
        db_obj = await self.repository.get(id)
        if not db_obj:
            return None
        return await self.repository.update(db_obj, obj_in)

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete a record by ID."""
        return await self.repository.delete(id)
