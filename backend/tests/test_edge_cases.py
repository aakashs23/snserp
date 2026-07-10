"""Edge cases from the Phase 6 checklist: duplicate invoices, expired sessions,
invalid permissions.

The real handler logic runs in every test; only the DB and the Supabase Auth
call are faked, so no network and no live credentials are needed.
"""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.api.customers import router as customers_router
from app.api.documents import router as documents_router
from app.api.invoices import router as invoices_router
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.documents import Document
from conftest import build_app, make_user


# ── Duplicate invoice number → 409, not 500 ──────────────────────────────────
class _DuplicateKeySession:
    """Simulates Postgres rejecting a second invoice with the same number."""

    def __init__(self):
        self.rolled_back = False

    def add(self, _obj):
        pass

    async def flush(self):
        raise IntegrityError(
            "INSERT INTO invoices ...",
            {},
            Exception('duplicate key value violates unique constraint "invoices_invoice_number_key"'),
        )

    async def rollback(self):
        self.rolled_back = True

    async def commit(self):
        pass


@pytest.fixture
def duplicate_invoice_client():
    app = build_app((invoices_router, "/api/v1/invoices"))
    session = _DuplicateKeySession()

    async def _fake_db():
        yield session

    app.dependency_overrides[get_current_user] = lambda: make_user("admin")
    app.dependency_overrides[get_db] = _fake_db
    yield TestClient(app, raise_server_exceptions=False), session
    app.dependency_overrides.clear()


def test_duplicate_invoice_number_returns_409_not_500(duplicate_invoice_client):
    client, session = duplicate_invoice_client
    payload = {
        "invoice_number": "INV-2026-0001",
        "customer_id": str(uuid.uuid4()),
        "invoice_date": date(2026, 3, 1).isoformat(),
    }

    response = client.post("/api/v1/invoices/", json=payload)

    assert response.status_code == 409, (
        f"got {response.status_code}; a duplicate invoice number must be a clean "
        "409, not an unhandled IntegrityError surfacing as 500"
    )
    assert "INV-2026-0001" in response.json()["detail"]
    assert session.rolled_back, "the failed transaction must be rolled back"


# ── Expired / invalid session → 401 ──────────────────────────────────────────
def test_invalid_or_expired_token_is_rejected_with_401(monkeypatch):
    """validate_supabase_jwt calls the real Supabase Auth API. Patch the shared
    client so an expired token can be simulated without a network call."""
    import app.config.supabase as supabase_config

    class _RejectingAuth:
        def get_user(self, jwt=None):
            raise Exception("token is expired")

    monkeypatch.setattr(supabase_config.supabase, "auth", _RejectingAuth())

    app = build_app((customers_router, "/api/v1/customers"))
    client = TestClient(app)

    response = client.get(
        "/api/v1/customers/", headers={"Authorization": "Bearer expired.token.here"}
    )
    assert response.status_code == 401


def test_valid_token_for_unknown_user_is_rejected_with_401(monkeypatch):
    """A token Supabase accepts, for a user with no row in our users table."""
    import app.config.supabase as supabase_config

    class _AcceptingAuth:
        def get_user(self, jwt=None):
            return type(
                "Resp", (), {"user": type("U", (), {"id": str(uuid.uuid4()), "email": "ghost@x.com"})()}
            )()

    monkeypatch.setattr(supabase_config.supabase, "auth", _AcceptingAuth())

    class _NoUserSession:
        async def execute(self, *_a, **_kw):
            class _R:
                def scalar_one_or_none(self_inner):
                    return None

            return _R()

    async def _fake_db():
        yield _NoUserSession()

    app = build_app((customers_router, "/api/v1/customers"))
    app.dependency_overrides[get_db] = _fake_db
    client = TestClient(app)

    response = client.get("/api/v1/customers/", headers={"Authorization": "Bearer valid.but.unknown"})
    assert response.status_code == 401
    assert "not found" in response.json()["detail"].lower()


# ── Invalid document permissions → 403 ───────────────────────────────────────
class _NoPermissionSession:
    """An approved document exists, but the user has no DocumentPermission row."""

    def __init__(self, doc):
        self._doc = doc

    async def get(self, *_a, **_kw):
        return self._doc

    async def execute(self, *_a, **_kw):
        class _R:
            def scalar_one_or_none(self_inner):
                return None

        return _R()


def _approved_document():
    return Document(
        id=uuid.uuid4(),
        file_name="secret.pdf",
        original_name="secret.pdf",
        storage_path="someone-else/secret.pdf",
        uploaded_by=uuid.uuid4(),
        is_deleted=False,
        status="approved",
    )


@pytest.mark.parametrize("role", ["viewer", "accountant"])
@pytest.mark.parametrize("action", ["preview", "download"])
def test_document_without_an_explicit_grant_is_forbidden(role, action):
    """RBAC alone is not enough: restricted roles need a DocumentPermission row."""
    doc = _approved_document()
    app = build_app((documents_router, "/api/v1/documents"))

    async def _fake_db():
        yield _NoPermissionSession(doc)

    app.dependency_overrides[get_current_user] = lambda: make_user(role)
    app.dependency_overrides[get_db] = _fake_db
    client = TestClient(app)

    response = client.get(f"/api/v1/documents/{doc.id}/{action}")
    assert response.status_code == 403, (
        f"{role} reached {action} for a document they were never granted "
        f"(got {response.status_code})"
    )
    app.dependency_overrides.clear()


@pytest.mark.parametrize("action", ["preview", "download"])
def test_admin_does_not_need_an_explicit_grant(action, monkeypatch):
    """Admins bypass the per-document check — confirm the fix didn't lock them out."""
    doc = _approved_document()

    async def _fake_signed_url(*_a, **_kw):
        return {"signedURL": "https://example/signed"}

    monkeypatch.setattr("app.api.documents.storage_signed_url", _fake_signed_url)

    app = build_app((documents_router, "/api/v1/documents"))

    async def _fake_db():
        yield _NoPermissionSession(doc)

    app.dependency_overrides[get_current_user] = lambda: make_user("admin")
    app.dependency_overrides[get_db] = _fake_db
    client = TestClient(app)

    response = client.get(f"/api/v1/documents/{doc.id}/{action}")
    assert response.status_code == 200
    assert response.json()["url"] == "https://example/signed"
    app.dependency_overrides.clear()
