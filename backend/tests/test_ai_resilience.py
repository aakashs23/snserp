"""Circuit breaker, per-attempt timeout, and bounded concurrency for AI providers.

Uses fake providers throughout — no network, no API keys.
"""

import asyncio

import pytest

from app.config.settings import settings
from app.services import ai_service
from app.services.ai_service import (
    CircuitOpenError,
    LLMProvider,
    _CircuitBreaker,
    _breaker_for,
    _call_guarded,
    ai_generate,
    reset_breakers,
)


class FakeProvider(LLMProvider):
    """Records calls; fails on demand."""

    def __init__(self, name: str, *, fail_with: Exception | None = None, delay: float = 0.0):
        self.name = name
        self.fail_with = fail_with
        self.delay = delay
        self.calls = 0
        self.in_flight = 0
        self.max_in_flight = 0

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        self.calls += 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            if self.fail_with:
                raise self.fail_with
            return f"ok from {self.name}"
        finally:
            self.in_flight -= 1

    async def embed(self, text: str) -> list[float]:
        return [0.0]


@pytest.fixture(autouse=True)
def _clean_breakers():
    reset_breakers()
    yield
    reset_breakers()


# ── The breaker itself (pure, no I/O) ────────────────────────────────────────
def test_breaker_opens_after_threshold_consecutive_failures():
    b = _CircuitBreaker("x", threshold=3, reset_seconds=60)
    assert b.allow()
    b.record_failure()
    b.record_failure()
    assert b.allow(), "must stay closed below threshold"
    assert not b.is_open
    b.record_failure()
    assert b.is_open
    assert not b.allow(), "must fail fast once open"


def test_success_resets_the_failure_count():
    b = _CircuitBreaker("x", threshold=3, reset_seconds=60)
    b.record_failure()
    b.record_failure()
    b.record_success()
    b.record_failure()
    assert not b.is_open, "counter must not carry across a success"


def test_breaker_half_opens_after_cooldown_and_closes_on_success():
    b = _CircuitBreaker("x", threshold=1, reset_seconds=0.05)
    b.record_failure()
    assert not b.allow()
    import time as _t

    _t.sleep(0.06)
    assert b.allow(), "cooldown elapsed -> half-open probe allowed"
    b.record_success()
    assert not b.is_open


def test_failed_probe_reopens_the_breaker():
    b = _CircuitBreaker("x", threshold=1, reset_seconds=0.05)
    b.record_failure()
    import time as _t

    _t.sleep(0.06)
    assert b.allow()
    b.record_failure()
    assert not b.allow(), "failed probe must reopen"


# ── Guarded calls ────────────────────────────────────────────────────────────
def test_open_circuit_fails_fast_without_calling_provider():
    p = FakeProvider("p")
    breaker = _breaker_for("p")
    for _ in range(settings.ai_circuit_breaker_threshold):
        breaker.record_failure()

    with pytest.raises(CircuitOpenError):
        asyncio.run(_call_guarded(p, "generate", "hi"))
    assert p.calls == 0, "provider must not be touched while the circuit is open"


def test_normal_operation_is_unchanged():
    p = FakeProvider("p")
    result = asyncio.run(_call_guarded(p, "generate", "hi"))
    assert result == "ok from p"
    assert p.calls == 1, "no retries on the happy path"
    assert not _breaker_for("p").is_open


def test_per_attempt_timeout_aborts_a_hanging_provider(monkeypatch):
    """A provider that hangs must not hang the request forever."""
    monkeypatch.setattr(settings, "ai_request_timeout_seconds", 0.01)
    p = FakeProvider("slow", delay=5.0)

    async def run():
        with pytest.raises(TimeoutError):
            await _call_guarded(p, "generate", "hi")

    asyncio.run(run())
    # tenacity retries transient TimeoutError up to 3 attempts, then reraises.
    assert p.calls == 3
    # The exhausted retry sequence counts as a single breaker failure.
    assert not _breaker_for("slow").is_open, "one failure is below the threshold"


def test_httpx_transport_errors_are_treated_as_transient():
    """Regression: httpx errors derive from Exception, not OSError/ConnectionError."""
    import httpx

    assert isinstance(httpx.ConnectError("x"), ai_service._TRANSIENT_EXCEPTIONS)
    assert isinstance(httpx.ReadTimeout("x"), ai_service._TRANSIENT_EXCEPTIONS)
    # A 4xx is a permanent error and must NOT be retried.
    status_err = httpx.HTTPStatusError(
        "bad", request=httpx.Request("GET", "http://x"), response=httpx.Response(400)
    )
    assert not isinstance(status_err, ai_service._TRANSIENT_EXCEPTIONS)


def test_connect_errors_are_actually_retried():
    import httpx

    p = FakeProvider("flaky", fail_with=httpx.ConnectError("refused"))
    with pytest.raises(httpx.ConnectError):
        asyncio.run(_call_guarded(p, "generate", "hi"))
    assert p.calls == 3, f"expected 3 attempts, got {p.calls}"


def test_concurrency_is_bounded_by_the_semaphore(monkeypatch):
    monkeypatch.setattr(ai_service, "_provider_semaphore", asyncio.Semaphore(2))
    p = FakeProvider("p", delay=0.02)

    async def run():
        await asyncio.gather(*(_call_guarded(p, "generate", f"q{i}") for i in range(8)))

    asyncio.run(run())
    assert p.calls == 8, "every call still completes"
    assert p.max_in_flight <= 2, f"semaphore breached: {p.max_in_flight} in flight"


# ── Failover interaction ─────────────────────────────────────────────────────
def test_open_primary_circuit_falls_through_to_fallback(monkeypatch):
    primary = FakeProvider("primary")
    fallback = FakeProvider("fallback")
    monkeypatch.setattr(ai_service, "get_primary_provider", lambda: primary)
    monkeypatch.setattr(ai_service, "get_fallback_provider", lambda: fallback)

    breaker = _breaker_for("primary")
    for _ in range(settings.ai_circuit_breaker_threshold):
        breaker.record_failure()

    answer, provider_name = asyncio.run(ai_generate("hello"))
    assert provider_name == "fallback"
    assert answer == "ok from fallback"
    assert primary.calls == 0, "open primary must be skipped, not retried"


def test_all_providers_down_still_raises(monkeypatch):
    monkeypatch.setattr(ai_service, "get_primary_provider", lambda: None)
    monkeypatch.setattr(ai_service, "get_fallback_provider", lambda: None)
    with pytest.raises(RuntimeError, match="All AI providers are unavailable"):
        asyncio.run(ai_generate("hello"))
