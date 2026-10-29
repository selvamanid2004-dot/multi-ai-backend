import time
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.base_agent import BaseAgent
from app.services.ai.base import BaseAIProvider
from app.core.logger import get_logger

logger = get_logger("coordinator_agent")


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent:
    Deconstructs the research query into structured sub-hypotheses, 
    formulates targeted search strategies, and establishes the pipeline execution plan.
    """
    def __init__(self, ai_provider: BaseAIProvider):
        super().__init__(name="Coordinator Agent", ai_provider=ai_provider)

    async def execute(self, task_id: str, db: AsyncSession, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        query = context.get("query", "")
        title = context.get("title", "")

        await self.emit_event(task_id, "agent_started", {
            "message": "Analyzing query and orchestrating research strategy...",
            "phase": "PLANNING"
        })

        system_prompt = (
            "You are an Elite Research Coordinator and Systems Architect. "
            "Deconstruct the user's research topic into a rigorous plan. "
            "Return JSON with: "
            "'hypotheses' (list of 3 core investigation angles), "
            "'search_queries' (list of 3 specific search queries), "
            "'methodology' (brief sentence explaining research framework)."
        )

        prompt = f"Research Topic: {title}\nDetailed Prompt: {query}"

        plan_data = await self.ai.generate_json(prompt=prompt, system_prompt=system_prompt)
        
        # Fallback if structure missing
        if "search_queries" not in plan_data:
            plan_data["search_queries"] = [
                f"{title} market trends and benchmarks",
                f"{title} architecture analysis",
                f"{title} challenges and best practices"
            ]

        latency_ms = (time.time() - start_time) * 1000
        tokens_used = self.ai.get_token_estimate(str(plan_data))

        await self.record_step(
            db=db,
            task_id=task_id,
            step_name="Deconstruct Research Query & Formulate Strategy",
            input_payload={"title": title, "query": query},
            output_payload=plan_data,
            logs=f"Generated {len(plan_data.get('hypotheses', []))} hypotheses and {len(plan_data.get('search_queries', []))} search vectors.",
            latency_ms=latency_ms,
            tokens_used=tokens_used
        )

        await self.emit_event(task_id, "agent_completed", {
            "message": "Research blueprint formulated successfully.",
            "plan": plan_data,
            "latency_ms": round(latency_ms, 2)
        })

        return plan_data
