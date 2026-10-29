import time
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.base_agent import BaseAgent
from app.services.ai.base import BaseAIProvider
from app.core.logger import get_logger

logger = get_logger("report_agent")


class ReportAgent(BaseAgent):
    """
    Decision & Synthesis Report Agent:
    Compiles verified findings, human reviewer feedback, strategic decision matrices,
    and actionable recommendations into a comprehensive executive brief.
    """
    def __init__(self, ai_provider: BaseAIProvider):
        super().__init__(name="Decision & Report Agent", ai_provider=ai_provider)

    async def execute(self, task_id: str, db: AsyncSession, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        title = context.get("title", "")
        query = context.get("query", "")
        findings = context.get("key_findings", [])
        verified_claims = context.get("verified_claims", [])
        human_feedback = context.get("human_feedback", "")
        additional_guidelines = context.get("additional_guidelines", "")

        await self.emit_event(task_id, "agent_started", {
            "message": "Synthesizing executive decision brief and decision matrix...",
            "phase": "GENERATING_REPORT"
        })

        system_prompt = (
            "You are a World-Class Executive Strategy Advisor & Technical Director. "
            "Synthesize an authoritative, beautifully structured Executive Decision Brief in Markdown. "
            "Include: "
            "# Title, ## 1. Executive Summary, ## 2. Verified Strategic Findings, "
            "## 3. Human Reviewer Directives (if any), ## 4. Strategic Decision Matrix (Markdown Table), "
            "## 5. Risk Mitigation & Governance, and ## 6. Actionable Implementation Roadmap. "
            "Write with executive precision and high analytical clarity."
        )

        claims_summary = "\n".join([f"- [{c.get('status', 'VERIFIED')}] {c.get('claim', '')} (Confidence: {c.get('confidence', 95)}%)" for c in verified_claims])
        prompt = (
            f"Research Subject: {title}\n"
            f"Original Objective: {query}\n\n"
            f"Verified Claims & Intelligence:\n{claims_summary}\n\n"
            f"Human Reviewer Feedback:\n{human_feedback if human_feedback else 'Approved without modifications.'}\n"
            f"Special Guidelines:\n{additional_guidelines if additional_guidelines else 'Standard executive distribution.'}\n\n"
            "Compile the complete, publication-ready Executive Decision Brief."
        )

        report_markdown = await self.ai.generate_text(prompt=prompt, system_prompt=system_prompt)

        latency_ms = (time.time() - start_time) * 1000
        tokens_used = self.ai.get_token_estimate(report_markdown)

        await self.record_step(
            db=db,
            task_id=task_id,
            step_name="Executive Decision Synthesis & Report Generation",
            input_payload={"title": title, "has_human_feedback": bool(human_feedback)},
            output_payload={"report_length": len(report_markdown)},
            logs=f"Compiled executive decision brief ({len(report_markdown)} characters, ~{tokens_used} tokens).",
            latency_ms=latency_ms,
            tokens_used=tokens_used
        )

        await self.emit_event(task_id, "agent_completed", {
            "message": "Executive decision report synthesized successfully.",
            "report_length": len(report_markdown),
            "latency_ms": round(latency_ms, 2)
        })

        return {"final_report": report_markdown}
