import time
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.base_agent import BaseAgent
from app.services.ai.base import BaseAIProvider
from app.core.logger import get_logger

logger = get_logger("summarizer_agent")


class SummarizerAgent(BaseAgent):
    """
    Literature & Document Summarizer Agent:
    Performs deep hierarchical summarization of documents, academic papers,
    and enterprise audit reports. Extracts methodology, key empirical findings, and claims.
    """
    def __init__(self, ai_provider: BaseAIProvider):
        super().__init__(name="Document Summarizer Agent", ai_provider=ai_provider)

    async def execute(self, task_id: str, db: AsyncSession, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        title = context.get("title", "Literature Document")
        full_text = context.get("full_text", "")
        pages = context.get("pages", [])

        await self.emit_event(task_id, "agent_started", {
            "message": f"Analyzing and summarizing {len(pages)} pages of literature...",
            "phase": "SUMMARIZING"
        })

        system_prompt = (
            "You are an Expert Scientific Literature Analyst. "
            "Synthesize an authoritative summary of the provided literature. "
            "Return JSON containing: "
            "'executive_summary' (concise high-level abstract), "
            "'core_methodology' (breakdown of how the authors / study conducted their work), "
            "'key_findings' (list of 4-5 core takeaways with page grounding), "
            "'quantitative_benchmarks' (list of extracted metrics, percentages, or statistics), "
            "'limitations_noted' (list of limitations acknowledged in the text)."
        )

        # Truncate prompt context if excessively long (e.g. 5000 words max for speed and token limits)
        truncated_text = full_text[:12000] if len(full_text) > 12000 else full_text
        prompt = (
            f"Document Title: {title}\n"
            f"Document Content Excerpt:\n{truncated_text}\n\n"
            "Generate the comprehensive structured literature summary."
        )

        summary_data = await self.ai.generate_json(prompt=prompt, system_prompt=system_prompt)

        latency_ms = (time.time() - start_time) * 1000
        tokens_used = self.ai.get_token_estimate(str(summary_data))

        await self.record_step(
            db=db,
            task_id=task_id,
            step_name="Hierarchical Literature Summarization",
            input_payload={"title": title, "pages_count": len(pages)},
            output_payload=summary_data,
            logs=f"Summarized document ({len(summary_data.get('key_findings', []))} findings, {len(summary_data.get('quantitative_benchmarks', []))} metrics).",
            latency_ms=latency_ms,
            tokens_used=tokens_used
        )

        await self.emit_event(task_id, "agent_completed", {
            "message": "Literature summary and empirical benchmarks extracted.",
            "findings_count": len(summary_data.get("key_findings", [])),
            "latency_ms": round(latency_ms, 2)
        })

        return summary_data
