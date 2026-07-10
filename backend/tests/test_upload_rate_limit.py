"""POST /documents/upload must enforce settings.rate_limit_upload.

Uploads buffer the whole file, call Supabase Storage, and queue the OCR /
embedding pipeline, so they need a tighter limit than the global default.

Each request here carries an unsupported MIME type, which the handler rejects
with 400 before touching the DB or Storage. The rate limiter runs *before* the
handler body, so the request is still counted — that lets us exhaust the limit
without any real I/O.
"""

import pytest
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.documents import _upload_limiter
from app.api.documents import router as documents_router
from app.config.settings import settings
from app.database.session import get_db
from app.middleware.auth import get_current_user
from conftest import build_app, make_user

UPLOAD = "/api/v1/documents/upload"
# Parsed from settings.rate_limit_upload, e.g. "10/minute" -> 10
LIMIT = int(settings.rate_limit_upload.split("/")[0])


class _FakeSession:
    async def execute(self, *_a, **_kw):
        raise AssertionError("handler reached the database; it should 400 first")


@pytest.fixture
def client():
    app = build_app((documents_router, "/api/v1/documents"))
    app.state.limiter = _upload_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    async def _fake_db():
        yield _FakeSession()

    app.dependency_overrides[get_current_user] = lambda: make_user("admin")
    app.dependency_overrides[get_db] = _fake_db

    # slowapi counters live on the module-level Limiter for the whole session.
    _upload_limiter.reset()
    yield TestClient(app)
    _upload_limiter.reset()
    app.dependency_overrides.clear()


def _post(client):
    return client.post(
        UPLOAD,
        files={"file": ("payload.bin", b"x", "application/x-msdownload")},
    )


def test_upload_route_is_wired_to_the_upload_rate_limit_setting():
    """rate_limit_upload was dead config until this phase — assert it's live."""
    registered = [
        limit.limit
        for name, limits in _upload_limiter._route_limits.items()
        if name.endswith("upload_document")
        for limit in limits
    ]
    assert len(registered) == 1, "upload_document has no route-level rate limit"
    assert str(registered[0]) == "10 per 1 minute"


def test_requests_under_the_limit_are_not_rate_limited(client):
    for i in range(LIMIT):
        response = _post(client)
        assert response.status_code == 400, (
            f"request {i + 1}/{LIMIT} got {response.status_code}, expected the "
            "handler's unsupported-file-type 400"
        )


def test_request_over_the_limit_is_rejected_with_429(client):
    for _ in range(LIMIT):
        _post(client)

    response = _post(client)
    assert response.status_code == 429, (
        f"the {LIMIT + 1}th upload got {response.status_code}, not 429 — "
        "the rate limit is not being enforced"
    )
