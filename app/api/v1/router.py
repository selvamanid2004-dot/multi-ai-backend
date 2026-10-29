from fastapi import APIRouter
from app.api.v1.endpoints import tasks, stream, hitl, evaluation, health

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(stream.router)
api_router.include_router(hitl.router)
api_router.include_router(evaluation.router)
