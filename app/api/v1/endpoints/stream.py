import asyncio
import json
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from app.core.events import event_bus
from app.core.logger import get_logger

logger = get_logger("stream_api")
router = APIRouter(prefix="/tasks", tags=["Stream"])


@router.get("/{task_id}/stream")
async def stream_task_events(task_id: str, request: Request):
    """
    Server-Sent Events (SSE) endpoint providing real-time streaming of
    agent thinking, tool actions, and state transitions.
    """
    queue = await event_bus.subscribe(task_id)

    async def event_generator():
        try:
            # Yield initial connection confirmation
            yield {
                "event": "connected",
                "data": json.dumps({"task_id": task_id, "status": "stream_connected"})
            }

            while True:
                # Check for client disconnect
                if await request.is_disconnected():
                    break

                try:
                    # Wait for next event with a periodic keep-alive
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": payload.get("event_type", "message"),
                        "data": json.dumps(payload)
                    }
                    
                    # If task is completed, rejected, or failed, terminate stream
                    if payload.get("event_type") in ("task_completed", "hitl_rejected", "pipeline_error"):
                        break

                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    yield {"event": "ping", "data": json.dumps({"ping": True})}

        finally:
            await event_bus.unsubscribe(task_id, queue)

    return EventSourceResponse(event_generator())
