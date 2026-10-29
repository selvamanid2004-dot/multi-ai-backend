from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logger import get_logger

logger = get_logger("exception_handler")


async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches all unhandled exceptions and formats a consistent, secure JSON response.
    """
    logger.error(f"Unhandled Exception on [{request.method}] {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the request.",
            "path": request.url.path
        }
    )
