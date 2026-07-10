"""Async wrappers around the synchronous supabase-py storage client.

supabase-py's storage client makes a real network call per method and offers
no async variant. Calling it directly from an ``async def`` handler blocks
the single event loop for the full round trip, stalling every other
concurrent request. Every network-triggering call is routed through
``asyncio.to_thread`` here so it runs on a worker thread instead.

``.from_(bucket)`` itself does not touch the network — it just builds a
proxy object — so callers may still call that directly.
"""

import asyncio
from typing import Any, Optional

from app.config.supabase import supabase


async def storage_upload(
    bucket: str,
    path: str,
    file: bytes,
    file_options: Optional[dict[str, Any]] = None,
) -> Any:
    return await asyncio.to_thread(
        supabase.storage.from_(bucket).upload,
        path=path,
        file=file,
        file_options=file_options,
    )


async def storage_remove(bucket: str, paths: list[str]) -> Any:
    return await asyncio.to_thread(supabase.storage.from_(bucket).remove, paths)


async def storage_signed_url(
    bucket: str,
    path: str,
    expires_in: int = 3600,
    options: Optional[dict[str, Any]] = None,
) -> Any:
    return await asyncio.to_thread(
        supabase.storage.from_(bucket).create_signed_url,
        path,
        expires_in,
        options,
    )


async def storage_create_bucket(name: str, options: Optional[dict[str, Any]] = None) -> Any:
    return await asyncio.to_thread(supabase.storage.create_bucket, name, options=options)


async def storage_list_buckets() -> Any:
    return await asyncio.to_thread(supabase.storage.list_buckets)
