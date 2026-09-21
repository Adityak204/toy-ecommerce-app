"""
FastAPI middleware for logging and correlation id management

This middleware:
1. Extracts or generates a correlation id for each request
2. Stores it in the request context
3. Logs the request start and completion
4. Measures the request duration
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.log_context import get_correlation_id, set_correlation_id, generate_correlation_id

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for logging and correlation id management

    This middleware runs before and after every HTTP request to:
    1. Extract or generate a correlation id for the request
    2. Log request details (method, path, status, duration)
    3. Ensure every log in the request has a correlation id
    """

    def __init__(self, app: ASGIApp,):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each HTTP request

        This method runs for every incoming request. It:
        1. Extracts or generates a correlation id for the request
        2. Sets it in the request context
        3. Logs request start
        4. Calls the actual endpoint function
        5. Logs request completion with status and duration

        Args:
            request: The incoming request
            call_next: The next endpoint function

        Returns:
            The response from the endpoint function
        """

        # Generate a new correlation id if one doesn't exist
        correlation_id = request.headers.get("X-Correlation-Id")

        if not correlation_id:
            correlation_id = generate_correlation_id()

        set_correlation_id(correlation_id)

        # Log request start
        logger.info(
            "Request started",
            extra={
                "event": "request_started",
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            }
        )

        # Measure request duration
        start_time = time.time()

        # Call the actual endpoint function
        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(
                "Request failed with exception",
                extra={
                    "event": "request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "exception": type(e).__name__,
                }
            )
            # Re-raise so FastAPI's exception handler can process it
            raise

        duration_ms = (time.time() - start_time) * 1000

        # Log request completion
        logger.info(
            "Request completed",
            extra={
                "event": "request_completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )

        # Add correlation id to the response headers
        # This allows clients to use it for their own logging
        response.headers["X-Correlation-Id"] = correlation_id

        return response