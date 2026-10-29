from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import get_logger
from app.database.session import init_db
from app.api.v1.router import api_router
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.error_handler import global_exception_handler

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for clean startup and shutdown events.
    """
    logger.info("Initializing database schemas...")
    await init_db()
    logger.info(f"System ready: {settings.PROJECT_NAME} v{settings.VERSION}")
    yield
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Multi-Agent AI Research & Decision System API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# 1. Custom Request Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Global Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# 4. Mount API Routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    }
