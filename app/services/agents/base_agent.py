import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai.base import BaseAIProvider
from app.core.events import event_bus
from app.core.logger import get_logger
from app.database.models.agent_step import AgentStep

logger = get_logger("base_agent")


class BaseAgent(ABC):
    """
    Base Agent class providing execution hooks, telemetry capture, 
    database step logging, and SSE real-time streaming.
    """
    def __init__(self, name: str, ai_provider: BaseAIProvider):
        self.name = name
        self.ai = ai_provider

    async def emit_event(self, task_id: str, event_type: str, data: dict) -> None:
        """Broadcasts real-time agent progress to connected web clients."""
        await event_bus.publish(
            task_id=task_id,
            event_type=event_type,
            agent=self.name,
            data=data
        )

    async def record_step(
        self,
        db: AsyncSession,
        task_id: str,
        step_name: str,
        input_payload: Optional[dict] = None,
        output_payload: Optional[dict] = None,
        logs: Optional[str] = None,
        latency_ms: float = 0.0,
        tokens_used: int = 0
    ) -> AgentStep:
        """Persists the agent's action and telemetry into the database."""
        step = AgentStep(
            task_id=task_id,
            agent_name=self.name,
            step_name=step_name,
            status="COMPLETED",
            input_payload=input_payload,
            output_payload=output_payload,
            logs=logs,
            latency_ms=latency_ms,
            tokens_used=tokens_used
        )
        db.add(step)
        await db.commit()
        await db.refresh(step)
        return step

    @abstractmethod
    async def execute(self, task_id: str, db: AsyncSession, context: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution logic for the agent."""
        pass
