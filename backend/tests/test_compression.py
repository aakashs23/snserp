"""Verify gzip negotiation and that already-compressed media is passed through."""

import json

import pytest
from fastapi import FastAPI, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.testclient import TestClient
from starlette.middleware import gzip as starlette_gzip

from app.middleware.compression import (
    EXCLUDED_CONTENT_TYPES,
    install_compression_exclusions,
)

# Comfortably above the 1000-byte minimum_size, and highly compressible.
_BIG_ROWS = [{"invoice_number": f"INV-{i:05d}", "status": "paid"} for i in range(200)]
_BIG_BLOB = b"x" * 5000


def test_starlette_still_exposes_the_constant_we_patch():
    """If starlette renames this, install_compression_exclusions() silently no-ops."""
    assert hasattr(starlette_gzip, "DEFAULT_EXCLUDED_CONTENT_TYPES")


@pytest.fixture
def client():
    install_compression_exclusions()
    app = FastAPI()
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

    @app.get("/json-big")
    async def json_big():
        return _BIG_ROWS

    @app.get("/json-small")
    async def json_small():
        return {"ok": True}

    @app.get("/pdf")
    async def pdf():
        return Response(content=_BIG_BLOB, media_type="application/pdf")

    @app.get("/xlsx")
    async def xlsx():
        return Response(
            content=_BIG_BLOB,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @app.get("/csv")
    async def csv():
        return Response(content=_BIG_BLOB, media_type="text/csv")

    return TestClient(app)


def test_large_json_is_compressed_and_still_parses(client):
    r = client.get("/json-big", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert r.headers["content-encoding"] == "gzip"
    # httpx transparently decodes; the payload must survive the round trip.
    assert r.json() == _BIG_ROWS
    # Wire size must actually be smaller than the raw payload.
    assert int(r.headers["content-length"]) < len(json.dumps(_BIG_ROWS))


def test_without_accept_encoding_response_is_identity(client):
    r = client.get("/json-big", headers={"Accept-Encoding": "identity"})
    assert r.status_code == 200
    assert "content-encoding" not in r.headers
    assert r.json() == _BIG_ROWS


def test_small_json_is_not_compressed(client):
    r = client.get("/json-small", headers={"Accept-Encoding": "gzip"})
    assert "content-encoding" not in r.headers
    assert r.json() == {"ok": True}


@pytest.mark.parametrize("path", ["/pdf", "/xlsx"])
def test_already_compressed_media_is_passed_through(client, path):
    r = client.get(path, headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert "content-encoding" not in r.headers
    assert r.content == _BIG_BLOB


def test_csv_export_is_still_compressed(client):
    """CSV is plain text and benefits from compression, unlike xlsx/pdf."""
    r = client.get("/csv", headers={"Accept-Encoding": "gzip"})
    assert r.headers["content-encoding"] == "gzip"
    assert r.content == _BIG_BLOB


def test_excluded_types_cover_images_and_zips():
    for content_type in ("image/png", "application/zip", "application/pdf"):
        assert content_type.startswith(EXCLUDED_CONTENT_TYPES)
