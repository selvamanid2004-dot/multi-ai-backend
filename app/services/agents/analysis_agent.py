import time
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.base_agent import BaseAgent
from app.services.ai.base import BaseAIProvider
from app.core.logger import get_logger

logger = get_logger("analysis_agent")


class AnalysisAgent(BaseAgent):
    """
    Data Analysis Agent:
    Evaluates gathered research materials, detects cross-source correlations,
    extracts actionable insights, and quantifies potential risks and bottlenecks.
    """
    def __init__(self, ai_provider: BaseAIProvider):
        super().__init__(name="Analysis Agent", ai_provider=ai_provider)

    async def execute(self, task_id: str, db: AsyncSession, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        citations: List[Dict[str, Any]] = context.get("citations", [])
        title = context.get("title", "")
        hypotheses = context.get("hypotheses", [])

        await self.emit_event(task_id, "agent_started", {
            "message": "Synthesizing multi-source data and identifying patterns...",
            "phase": "ANALYZING"
        })

        system_prompt = (
            "You are a Senior Strategic Data Analyst. "
            "Synthesize the provided research data and citations. "
            "Return JSON containing: "
            "'key_findings' (list of 3-4 deep qualitative/quantitative takeaways), "
            "'emerging_trends' (list of 2-3 current industry or technological shifts), "
            "'risk_factors' (list of 2-3 significant risks, blockers, or limitations)."
        )

        sources_summary = "\n".join([f"- [{c.get('domain', 'source')}] {c.get('title', '')}: {c.get('snippet', '')[:160]}" for c in citations[:6]])
        prompt = (
            f"Topic: {title}\n"
            f"Hypotheses Investigated:\n{chr(10).join(f'- {h}' for h in hypotheses)}\n\n"
            f"Extracted Sources:\n{sources_summary}\n\n"
            "Deliver deep, analytical insights."
        )

        insights_data = await self.ai.generate_json(prompt=prompt, system_prompt=system_prompt)

        latency_ms = (time.time() - start_time) * 1000
        tokens_used = self.ai.get_token_estimate(str(insights_data))

        await self.record_step(
            db=db,
            task_id=task_id,
            step_name="Cross-Source Analytical Synthesis",
            input_payload={"sources_evaluated": len(citations)},
            output_payload=insights_data,
            logs=f"Extracted {len(insights_data.get('key_findings', []))} core findings and {len(insights_data.get('risk_factors', []))} risk parameters.",
            latency_ms=latency_ms,
            tokens_used=tokens_used
        )

        await self.emit_event(task_id, "agent_completed", {
            "message": "Data analysis and thematic pattern recognition complete.",
            "insights": insights_data,
            "latency_ms": round(latency_ms, 2)
        })

        return insights_data
