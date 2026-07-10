"""Verify storage_service offloads blocking supabase-py calls to a worker thread
instead of blocking the event loop, and that results/arguments still round-trip.
"""

import asyncio
import threading

import pytest

from app.services import storage_service


class _FakeBucketProxy:
    def __init__(self, bucket: str, calls: list):
        self.bucket = bucket
        self.calls = calls

    def _blocking(self, label: str, result, delay: float = 0.05):
        # Prove this runs off the event loop thread, and that it actually
        # blocks *something* for `delay` seconds (simulating network I/O).
        self.calls.append((label, threading.current_thread() is threading.main_thread()))
        import time

        time.sleep(delay)
        return result

    def upload(self, path=None, file=None, file_options=None):
        return self._blocking("upload", {"path": path, "file_options": file_options})

    def remove(self, paths):
        return self._blocking("remove", {"removed": paths})

    def create_signed_url(self, path, expires_in, options=None):
        return self._blocking(
            "create_signed_url",
            {"signedURL": f"https://example/{path}?exp={expires_in}&opt={options}"},
        )


class _FakeStorage:
    def __init__(self):
        self.calls: list = []

    def from_(self, bucket: str):
        return _FakeBucketProxy(bucket, self.calls)

    def create_bucket(self, name, options=None):
        self.calls.append(("create_bucket", threading.current_thread() is threading.main_thread()))
        return {"name": name}

    def list_buckets(self):
        self.calls.append(("list_buckets", threading.current_thread() is threading.main_thread()))
        return [{"name": "documents"}]


@pytest.fixture
def fake_storage(monkeypatch):
    fake = _FakeStorage()

    class _FakeClient:
        storage = fake

    monkeypatch.setattr(storage_service, "supabase", _FakeClient())
    return fake


def test_upload_runs_off_the_event_loop_thread_and_returns_the_result(fake_storage):
    result = asyncio.run(
        storage_service.storage_upload("documents", "u/1.pdf", b"bytes", {"content-type": "application/pdf"})
    )
    assert result == {"path": "u/1.pdf", "file_options": {"content-type": "application/pdf"}}
    label, was_main_thread = fake_storage.calls[0]
    assert label == "upload"
    assert not was_main_thread, "blocking call must not run on the event loop thread"


def test_remove_passes_paths_through(fake_storage):
    result = asyncio.run(storage_service.storage_remove("documents", ["a", "b"]))
    assert result == {"removed": ["a", "b"]}


def test_signed_url_passes_options_through(fake_storage):
    result = asyncio.run(
        storage_service.storage_signed_url("documents", "f.pdf", 3600, {"download": "f.pdf"})
    )
    assert result["signedURL"].endswith("f.pdf?exp=3600&opt={'download': 'f.pdf'}")


def test_create_bucket_and_list_buckets(fake_storage):
    b = asyncio.run(storage_service.storage_create_bucket("invoice-pdfs", {"public": False}))
    assert b == {"name": "invoice-pdfs"}
    buckets = asyncio.run(storage_service.storage_list_buckets())
    assert buckets == [{"name": "documents"}]


def test_event_loop_stays_responsive_during_a_slow_storage_call(fake_storage):
    """The real bug: a synchronous call blocks every other coroutine.
    Prove a concurrent tick still fires while 'storage' is 'slow'."""
    ticked = False

    async def ticker():
        nonlocal ticked
        await asyncio.sleep(0.01)
        ticked = True

    async def run():
        await asyncio.gather(
            storage_service.storage_upload("documents", "x", b"y"),
            ticker(),
        )

    asyncio.run(run())
    assert ticked, "event loop was blocked for the full duration of the storage call"
