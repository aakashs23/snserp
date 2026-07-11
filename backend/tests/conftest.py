"""Shared test fixtures.

The user objects here are transient: constructed, never added to a session,
never committed. That is safe because every RBAC-gated route only reads
`current_user.id`, `.email`, `.full_name`, and `.role.name` — `.role` is set
directly at construction, so nothing lazy-loads and no DB is touched.
"""

import uuid

import pytest
from fastapi import FastAPI

from app.models.users import Role, User


def make_user(role_name: str, **overrides) -> User:
    """Build an in-memory User with the given role. No DB, no session."""
    role = Role(id=uuid.uuid4(), name=role_name, description=role_name)
    defaults = dict(
        id=uuid.uuid4(),
        full_name=f"Test {role_name}",
        email=f"{role_name}@test.local",
        role_id=role.id,
        role=role,
        is_active=True,
    )
    defaults.update(overrides)
    return User(**defaults)


@pytest.fixture
def admin_user() -> User:
    return make_user("admin")


@pytest.fixture
def employee_user() -> User:
    return make_user("employee")


@pytest.fixture
def accountant_user() -> User:
    return make_user("accountant")


@pytest.fixture
def viewer_user() -> User:
    return make_user("viewer")


def build_app(*routers_with_prefix) -> FastAPI:
    """Mount a bare app with only the routers under test.

    Deliberately avoids importing `main.app`: its lifespan makes a real
    Supabase Storage call and seeds roles against the real DB.
    """
    app = FastAPI()
    for router, prefix in routers_with_prefix:
        app.include_router(router, prefix=prefix)
    return app
