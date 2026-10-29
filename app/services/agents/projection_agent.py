import time
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.base_agent import BaseAgent
from app.services.ai.base import BaseAIProvider
from app.core.logger import get_logger

logger = get_logger("projection_agent")


class ProjectionAgent(BaseAgent):
    """
    Strategic Projection & Project Roadmap Agent:
    Derives future implementation milestones, quantitative ROI projections,
    phased project roadmaps, and risk governance based on literature and reports.
    """
    def __init__(self, ai_provider: BaseAIProvider):
        super().__init__(name="Projection & Roadmap Agent", ai_provider=ai_provider)

    async def execute(self, task_id: str, db: AsyncSession, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        title = context.get("title", "Literature Study")
        findings = context.get("key_findings", [])
        summary = context.get("summary", "")

        await self.emit_event(task_id, "agent_started", {
            "message": "Generating strategic projections, project roadmaps, and milestone timelines...",
            "phase": "PROJECTING"
        })

        system_prompt = (
            "You are a Senior Strategic Project Architect and Systems Futurist. "
            "Based on the analyzed document findings, synthesize a rigorous strategic project projection. "
            "Return JSON containing: "
            "'project_phases' (list of objects with 'phase_name', 'timeline_weeks', 'key_deliverables' [list of strings], 'risk_mitigation'), "
            "'quantitative_projections' (list of 3 key expected ROI/metric trajectories, e.g. 'Latency reduction: ~40% by Q2'), "
            "'resource_requirements' (brief summary of required infrastructure or personnel), "
            "'critical_dependencies' (list of 2-3 dependencies)."
        )

        prompt = (
            f"Document Subject: {title}\n"
            f"Key Findings:\n{chr(10).join(f'- {f}' for f in findings[:5])}\n\n"
            f"Document Summary Excerpt:\n{summary[:800]}\n\n"
            "Formulate the strategic project roadmap and projections."
        )

        projection_data = await self.ai.generate_json(prompt=prompt, system_prompt=system_prompt)

        latency_ms = (time.time() - start_time) * 1000
        tokens_used = self.ai.get_token_estimate(str(projection_data))

        await self.record_step(
            db=db,
            task_id=task_id,
            step_name="Synthesize Strategic Project Roadmap & Projections",
            input_payload={"title": title},
            output_payload=projection_data,
            logs=f"Created {len(projection_data.get('project_phases', []))} project phases and {len(projection_data.get('quantitative_projections', []))} quantitative projection metrics.",
            latency_ms=latency_ms,
            tokens_used=tokens_used
        )

        await self.emit_event(task_id, "agent_completed", {
            "message": "Strategic roadmap and future milestone projections generated.",
            "phases_count": len(projection_data.get("project_phases", [])),
            "latency_ms": round(latency_ms, 2)
        })

        return projection_data
