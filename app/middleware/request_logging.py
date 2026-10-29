import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.logger import get_logger

logger = get_logger("http_access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting unique correlation ID (X-Request-ID) 
    and logging response times for API requests.
    """
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Request-ID"] = correlation_id
        
        # Don't clutter logs with SSE heartbeat streams or health checks
        if not request.url.path.endswith("/stream") and not request.url.path.endswith("/health"):
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)",
                extra={"correlation_id": correlation_id}
            )
            
        return response
