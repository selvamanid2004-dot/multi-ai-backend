import asyncio
import json
from typing import AsyncGenerator, Dict, Set
from datetime import datetime, timezone
from app.core.logger import get_logger

logger = get_logger("event_bus")


class EventBus:
    """
    In-memory asynchronous Pub/Sub Event Bus for Server-Sent Events (SSE).
    Enables streaming live agent execution, telemetry, and HITL states.
    """
    def __init__(self):
        # Maps task_id -> Set of asyncio.Queue instances
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, task_id: str) -> asyncio.Queue:
        """Subscribe a client stream to events for a specific task."""
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            if task_id not in self._subscribers:
                self._subscribers[task_id] = set()
            self._subscribers[task_id].add(queue)
            logger.info(f"Client subscribed to task [{task_id}]. Active listeners: {len(self._subscribers[task_id])}")
        return queue

    async def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        """Remove a subscriber queue when client disconnects."""
        async with self._lock:
            if task_id in self._subscribers:
                self._subscribers[task_id].discard(queue)
                if not self._subscribers[task_id]:
                    del self._subscribers[task_id]
                logger.info(f"Client disconnected from task [{task_id}]")

    async def publish(self, task_id: str, event_type: str, agent: str, data: dict) -> None:
        """
        Broadcast an event to all subscribers listening to a task.
        """
        payload = {
            "task_id": task_id,
            "event_type": event_type,
            "agent": agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        
        async with self._lock:
            queues = list(self._subscribers.get(task_id, []))
            
        for q in queues:
            try:
                await q.put(payload)
            except Exception as e:
                logger.error(f"Error publishing to subscriber queue: {e}")


# Singleton instance
event_bus = EventBus()
