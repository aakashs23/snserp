"""Request logging middleware with request ID generation.

Generates a unique X-Request-ID for every incoming request, logs
structured information about the request/response lifecycle, and
injects the ID into the response headers for end-to-end traceability.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("snserp.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request ID and logs request/response details."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or propagate a request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store on request state so downstream code can access it
        request.state.request_id = request_id

        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        logger.info(
            "request_start | id=%s method=%s path=%s ip=%s",
            request_id,
            method,
            path,
            client_ip,
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "request_error | id=%s method=%s path=%s duration=%.1fms",
                request_id,
                method,
                path,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "request_end | id=%s method=%s path=%s status=%d duration=%.1fms",
            request_id,
            method,
            path,
            response.status_code,
            duration_ms,
        )

        # Inject into response headers
        response.headers["X-Request-ID"] = request_id
        return response
