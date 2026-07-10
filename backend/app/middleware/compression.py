"""Content-type exclusions for gzip response compression.

Starlette's GZipMiddleware consults a module-level tuple to decide which
responses to leave alone, and exposes no constructor argument for it. We widen
that tuple so already-compressed payloads (export PDFs, XLSX workbooks) are
passed through untouched instead of being re-compressed for no gain.
"""

from starlette.middleware import gzip as _starlette_gzip

# Prefix-matched against the response Content-Type. Includes Starlette's own
# default so streaming responses keep working.
EXCLUDED_CONTENT_TYPES = (
    "text/event-stream",
    "application/pdf",
    "application/zip",
    "application/gzip",
    "application/x-7z-compressed",
    # .xlsx / .docx / .pptx are zip containers
    "application/vnd.openxmlformats-officedocument.",
    "image/",
    "video/",
    "audio/",
)


def install_compression_exclusions() -> None:
    """Widen the content types GZipMiddleware refuses to compress.

    Must be called before the first response is sent.
    """
    # ponytail: monkeypatch because starlette 1.3 has no excluded_content_types
    # kwarg; switch to the kwarg if a later release adds one. test_compression.py
    # fails loudly if this constant is ever renamed or removed.
    _starlette_gzip.DEFAULT_EXCLUDED_CONTENT_TYPES = EXCLUDED_CONTENT_TYPES
