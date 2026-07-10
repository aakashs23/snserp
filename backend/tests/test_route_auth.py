"""Route-level authentication and authorization regression tests.

No live DB and no network: `get_current_user` is overridden to inject a
transient user, and `get_db` is stubbed where a handler body would otherwise
run a query. The real RBAC comparison (`role.name not in allowed_roles`) still
executes for every test — only the JWT check and the DB I/O are faked.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.analytics import router as analytics_router
from app.api.customers import router as customers_router
from app.api.invoices import router as invoices_router
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import RequireRole
from conftest import build_app, make_user

# Endpoints that shipped with NO auth dependency at all until this phase.
PREVIOUSLY_OPEN_ENDPOINTS = [
    "/api/v1/invoices/",
    "/api/v1/invoices/00000000-0000-0000-0000-000000000001",
    "/api/v1/customers/",
    "/api/v1/customers/00000000-0000-0000-0000-000000000001",
]


class _FakeResult:
    def scalars(self):
        return self

    def all(self):
        return []

    def scalar_one_or_none(self):
        return None


class _FakeSession:
    """Minimal stand-in: every list query comes back empty."""

    async def execute(self, *_a, **_kw):
        return _FakeResult()

    async def get(self, *_a, **_kw):
        return None


@pytest.fixture
def app():
    return build_app(
        (invoices_router, "/api/v1/invoices"),
        (customers_router, "/api/v1/customers"),
        (analytics_router, "/api/v1/analytics"),
    )


@pytest.fixture
def client(app):
    async def _fake_db():
        yield _FakeSession()

    app.dependency_overrides[get_db] = _fake_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _as(app, user):
    app.dependency_overrides[get_current_user] = lambda: user


# ── The fix: these four were fully unauthenticated ───────────────────────────
@pytest.mark.parametrize("path", PREVIOUSLY_OPEN_ENDPOINTS)
def test_previously_open_endpoints_reject_missing_credentials(client, path):
    """Regression guard: a request with no Authorization header must not get data.

    FastAPI's HTTPBearer(auto_error=True) rejects this before the handler runs.
    """
    response = client.get(path)
    assert response.status_code == 401, (
        f"{path} responded {response.status_code} to an unauthenticated request"
    )


@pytest.mark.parametrize("path", PREVIOUSLY_OPEN_ENDPOINTS)
def test_previously_open_endpoints_reject_non_bearer_scheme(client, path):
    response = client.get(path, headers={"Authorization": "Basic abc123"})
    assert response.status_code == 401


# ── ...but still serve every authenticated role, as before the fix ───────────
@pytest.mark.parametrize("role", ["admin", "employee", "accountant", "viewer"])
@pytest.mark.parametrize("path", ["/api/v1/invoices/", "/api/v1/customers/"])
def test_list_endpoints_still_allow_every_authenticated_role(app, client, role, path):
    """The fix adds authentication, not authorization. No role lost access."""
    _as(app, make_user(role))
    response = client.get(path)
    assert response.status_code == 200, (
        f"{role} lost access to {path}: {response.status_code} {response.text[:120]}"
    )
    assert response.json() == []


# ── Revenue endpoints: admin + employee only ─────────────────────────────────
REVENUE_ENDPOINTS = ["/api/v1/analytics/revenue", "/api/v1/analytics/revenue/export"]


@pytest.mark.parametrize("path", REVENUE_ENDPOINTS)
@pytest.mark.parametrize("role", ["accountant", "viewer"])
def test_revenue_endpoints_reject_accountant_and_viewer(app, client, path, role):
    """docs/09: accountant has no revenue dashboard. The frontend RoleGuard is
    not a security boundary — the API must refuse on its own."""
    _as(app, make_user(role))
    response = client.get(path)
    assert response.status_code == 403, (
        f"{role} reached {path} (got {response.status_code}) — RBAC bypass"
    )


@pytest.mark.parametrize("path", REVENUE_ENDPOINTS)
def test_revenue_endpoints_reject_missing_credentials(client, path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("role", ["admin", "employee"])
def test_revenue_dependency_admits_admin_and_employee(role):
    """Asserted at the dependency, not over HTTP: the handler body would run
    the real aggregation queries against the live DB."""
    guard = RequireRole(["admin", "employee"])
    user = make_user(role)
    assert guard(user=user) is user


# ── Dashboard endpoints stay open to every role (deliberately not restricted) ─
def _role_guards_on(router, path):
    """The RequireRole instances wired into a route, via the router's own
    dependency graph. Avoids running the handler (which would query the DB)."""
    route = next(r for r in router.routes if r.path == path)
    return [
        d.call
        for d in route.dependant.dependencies
        if isinstance(getattr(d, "call", None), RequireRole)
    ]


@pytest.mark.parametrize("path", ["/dashboard/stats", "/dashboard/activity"])
def test_dashboard_endpoints_are_not_role_restricted(path):
    """The landing page has no RoleGuard and every role loads it today. Locking
    these down would 403 the dashboard for accountant/viewer — a regression,
    not a fix. This test fails if someone restricts them without gating the UI.
    """
    assert _role_guards_on(analytics_router, path) == [], (
        f"{path} gained a role restriction; the dashboard page would now 403 "
        "for accountant/viewer"
    )


@pytest.mark.parametrize("path", ["/revenue", "/revenue/export"])
def test_revenue_endpoints_are_role_restricted(path):
    """Positive control for the check above: it can detect a guard when present."""
    guards = _role_guards_on(analytics_router, path)
    assert len(guards) == 1, f"{path} lost its role restriction"
    assert sorted(guards[0].allowed_roles) == ["admin", "employee"]
