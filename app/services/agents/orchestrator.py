import time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.logger import get_logger
from app.core.events import event_bus
from app.database.models.task import ResearchTask
from app.database.models.evaluation import TaskEvaluation
from app.database.models.agent_step import AgentStep
from app.services.ai.factory import get_ai_provider
from app.services.agents.coordinator_agent import CoordinatorAgent
from app.services.agents.research_agent import ResearchAgent
from app.services.agents.analysis_agent import AnalysisAgent
from app.services.agents.verification_agent import VerificationAgent
from app.services.agents.report_agent import ReportAgent
from app.services.agents.summarizer_agent import SummarizerAgent
from app.services.agents.projection_agent import ProjectionAgent
from app.services.agents.visual_agent import VisualDiagramAgent
from app.services.agents.audit_agent import AuditAgent
from app.database.models.citation import Citation

logger = get_logger("orchestrator")


class AgentOrchestrator:
    """
    Central Multi-Agent Pipeline Orchestration Engine.
    Coordinates sequential agent execution, state transitions, event streaming,
    Human-In-The-Loop review checkpoints, and performance evaluations.
    """

    async def run_pipeline(
        self,
        task_id: str,
        db: AsyncSession,
        require_human_approval: Optional[bool] = None
    ) -> None:
        """
        Runs the primary pipeline from Planning through Verification.
        If HITL is enabled, pauses after Verification for human sign-off.
        """
        task = await db.get(ResearchTask, task_id)
        if not task:
            logger.error(f"Task [{task_id}] not found in database.")
            return

        if require_human_approval is None:
            require_human_approval = settings.REQUIRE_HUMAN_APPROVAL

        try:
            # 1. Resolve Provider
            ai_provider, provider_name, model_name = get_ai_provider(task.provider)
            task.provider = provider_name
            task.model_name = model_name
            await db.commit()

            # Initialize Micro-Agents
            coordinator = CoordinatorAgent(ai_provider)
            researcher = ResearchAgent(ai_provider)
            analyst = AnalysisAgent(ai_provider)
            verifier = VerificationAgent(ai_provider)

            # Phase 1: Planning
            task.status = "PLANNING"
            await db.commit()
            plan_context = {"title": task.title, "query": task.query}
            plan_data = await coordinator.execute(task_id, db, plan_context)
            task.research_plan = plan_data
            await db.commit()

            # Phase 2: Automated Research
            task.status = "RESEARCHING"
            await db.commit()
            research_context = {
                "title": task.title,
                "search_queries": plan_data.get("search_queries", [])
            }
            research_data = await researcher.execute(task_id, db, research_context)
            task.intermediate_findings = research_data
            await db.commit()

            # Phase 3: Data Analysis
            task.status = "ANALYZING"
            await db.commit()
            analysis_context = {
                "title": task.title,
                "hypotheses": plan_data.get("hypotheses", []),
                "citations": research_data.get("citations", [])
            }
            analysis_data = await analyst.execute(task_id, db, analysis_context)
            task.analysis_insights = analysis_data
            await db.commit()

            # Phase 4: Fact-Checking & Verification
            task.status = "VERIFYING"
            await db.commit()
            verification_context = {
                "key_findings": analysis_data.get("key_findings", []),
                "citations": research_data.get("citations", [])
            }
            verification_data = await verifier.execute(task_id, db, verification_context)
            task.verification_report = verification_data
            await db.commit()

            # Check Human-In-The-Loop Gate
            if require_human_approval:
                task.status = "AWAITING_APPROVAL"
                await db.commit()
                
                await event_bus.publish(
                    task_id=task_id,
                    event_type="hitl_required",
                    agent="Orchestration Engine",
                    data={
                        "message": "Pipeline paused. Verification audit requires human review & sign-off.",
                        "verification": verification_data,
                        "findings": analysis_data.get("key_findings", [])
                    }
                )
                logger.info(f"Task [{task_id}] paused at HITL review gate.")
                return

            # If HITL not required, proceed autonomously
            await self.resume_after_approval(task_id, db, approved=True, feedback="Autonomous execution.")

        except Exception as e:
            logger.error(f"Pipeline execution failure on task [{task_id}]: {e}", exc_info=True)
            task.status = "FAILED"
            task.error_message = str(e)
            await db.commit()
            await event_bus.publish(
                task_id=task_id,
                event_type="pipeline_error",
                agent="Orchestration Engine",
                data={"error": str(e)}
            )

    async def run_document_pipeline(
        self,
        task_id: str,
        db: AsyncSession,
        parsed_doc: dict,
        require_human_approval: Optional[bool] = None
    ) -> None:
        """
        Runs the literature & document analysis pipeline:
        1. Ingests document pages and anchors page citations
        2. Summarizer Agent: extracts executive summary, methodology, key findings
        3. Projection & Roadmap Agent: derives future milestones and strategic projections
        4. Visual Diagram Agent: generates interactive SVG architecture diagrams & concept prompts
        5. Literature Audit Agent: runs rigorous compliance & methodology audit
        6. Pauses at Human Review Gate (if enabled)
        7. Synthesizes publication-grade final audit brief
        """
        task = await db.get(ResearchTask, task_id)
        if not task:
            logger.error(f"Task [{task_id}] not found in database.")
            return

        if require_human_approval is None:
            require_human_approval = settings.REQUIRE_HUMAN_APPROVAL

        try:
            # 1. Resolve Provider
            ai_provider, provider_name, model_name = get_ai_provider(task.provider)
            task.provider = provider_name
            task.model_name = model_name
            task.task_type = "DOCUMENT_AUDIT"
            task.document_filename = parsed_doc.get("filename", "document.pdf")
            await db.commit()

            pages = parsed_doc.get("pages", [])
            full_text = parsed_doc.get("full_text", "")

            # 2. Anchor page citations
            for p in pages[:10]:
                if p.get("text"):
                    citation_model = Citation(
                        task_id=task_id,
                        title=f"{task.document_filename} - Page {p['page_number']}",
                        url=f"document://{task.document_filename}#page={p['page_number']}",
                        snippet=p["text"][:220],
                        domain="document.pdf",
                        reliability_score=0.98,
                        verified=True
                    )
                    db.add(citation_model)
            await db.commit()

            # Initialize Specialized Agents
            summarizer = SummarizerAgent(ai_provider)
            projector = ProjectionAgent(ai_provider)
            visualizer = VisualDiagramAgent(ai_provider)
            auditor = AuditAgent(ai_provider)

            # Phase 1: Summarization
            task.status = "SUMMARIZING"
            await db.commit()
            summary_context = {
                "title": task.title,
                "full_text": full_text,
                "pages": pages
            }
            summary_data = await summarizer.execute(task_id, db, summary_context)
            task.document_summary = summary_data
            await db.commit()

            # Phase 2: Strategic Projections & Roadmapping
            task.status = "PROJECTING"
            await db.commit()
            projection_context = {
                "title": task.title,
                "summary": summary_data.get("executive_summary", ""),
                "key_findings": summary_data.get("key_findings", [])
            }
            projection_data = await projector.execute(task_id, db, projection_context)
            task.strategic_projections = projection_data
            await db.commit()

            # Phase 3: Visual Infographics & Architecture Diagrams
            task.status = "VISUALIZING"
            await db.commit()
            visual_context = {
                "title": task.title,
                "summary": summary_data.get("executive_summary", ""),
                "projections": projection_data
            }
            visual_data = await visualizer.execute(task_id, db, visual_context)
            task.visual_diagrams = visual_data
            await db.commit()

            # Phase 4: Final Compliance & Methodology Audit
            task.status = "AUDITING"
            await db.commit()
            audit_context = {
                "title": task.title,
                "pages": pages,
                "summary": summary_data.get("executive_summary", ""),
                "findings": summary_data.get("key_findings", [])
            }
            audit_data = await auditor.execute(task_id, db, audit_context)
            task.audit_dossier = audit_data
            
            # Map audit into verification report schema for HITL compatibility
            verification_payload = {
                "overall_confidence": audit_data.get("factual_grounding_score", 96.0),
                "factual_accuracy_score": audit_data.get("methodology_rigor_score", 95.0),
                "coherence_score": audit_data.get("bias_and_limitation_score", 92.0),
                "hallucination_risk": "LOW" if audit_data.get("audit_grade", "A") in ["A+", "A"] else "MEDIUM",
                "verified_claims": [
                    {
                        "claim": s.get("statement", ""),
                        "status": "VERIFIED" if s.get("audit_status") == "GROUNDED" else "CONDITIONAL",
                        "confidence": 98.0 if s.get("audit_status") == "GROUNDED" else 85.0,
                        "source_ref": s.get("page_reference", "Document"),
                        "notes": s.get("auditor_notes", "")
                    }
                    for s in audit_data.get("audited_statements", [])
                ],
                "flagged_issues": audit_data.get("identified_fallacies_or_gaps", [])
            }
            task.verification_report = verification_payload
            await db.commit()

            # Phase 5: Human-in-the-Loop Review Gate
            if require_human_approval:
                task.status = "AWAITING_APPROVAL"
                await db.commit()

                await event_bus.publish(
                    task_id=task_id,
                    event_type="hitl_required",
                    agent="Orchestration Engine",
                    data={
                        "message": f"Literature audit complete ({audit_data.get('audit_grade')} - {audit_data.get('audit_verdict')}). Awaiting human approval sign-off.",
                        "verification": verification_payload,
                        "findings": summary_data.get("key_findings", []),
                        "audit_dossier": audit_data,
                        "visual_title": visual_data.get("diagram_title")
                    }
                )
                logger.info(f"Document Task [{task_id}] paused at HITL review gate.")
                return

            # Autonomous resumption
            await self.resume_after_approval(task_id, db, approved=True, feedback="Autonomous literature audit.")

        except Exception as e:
            logger.error(f"Document pipeline failure on task [{task_id}]: {e}", exc_info=True)
            task.status = "FAILED"
            task.error_message = str(e)
            await db.commit()
            await event_bus.publish(
                task_id=task_id,
                event_type="pipeline_error",
                agent="Orchestration Engine",
                data={"error": str(e)}
            )

    async def resume_after_approval(
        self,
        task_id: str,
        db: AsyncSession,
        approved: bool,
        feedback: Optional[str] = None,
        additional_guidelines: Optional[str] = None
    ) -> None:
        """
        Resumes pipeline execution after human review:
        - If approved: synthesizes final decision report and records evaluation telemetry.
        - If rejected: marks task as REJECTED with reviewer feedback.
        """
        task = await db.get(ResearchTask, task_id)
        if not task:
            logger.error(f"Task [{task_id}] not found.")
            return

        task.human_approved = approved
        task.human_feedback = feedback

        if not approved:
            task.status = "REJECTED"
            await db.commit()
            await event_bus.publish(
                task_id=task_id,
                event_type="hitl_rejected",
                agent="Human Reviewer",
                data={"message": "Task rejected by human reviewer.", "feedback": feedback}
            )
            return

        try:
            task.status = "GENERATING_REPORT"
            await db.commit()

            ai_provider, _, _ = get_ai_provider(task.provider)
            reporter = ReportAgent(ai_provider)

            report_context = {
                "title": task.title,
                "query": task.query,
                "key_findings": (task.document_summary or {}).get("key_findings") or (task.analysis_insights or {}).get("key_findings", []),
                "verified_claims": (task.verification_report or {}).get("verified_claims", []),
                "human_feedback": feedback,
                "additional_guidelines": additional_guidelines
            }

            report_data = await reporter.execute(task_id, db, report_context)
            task.final_report = report_data.get("final_report", "")
            task.status = "COMPLETED"

            # Compute and persist task evaluation telemetry
            await self._finalize_evaluation(task_id, db)
            await db.commit()

            await event_bus.publish(
                task_id=task_id,
                event_type="task_completed",
                agent="Orchestration Engine",
                data={
                    "message": "Multi-agent research and decision synthesis completed successfully.",
                    "task_id": task_id
                }
            )
            logger.info(f"Task [{task_id}] successfully completed and evaluated.")

        except Exception as err:
            logger.error(f"Error during report synthesis for task [{task_id}]: {err}", exc_info=True)
            task.status = "FAILED"
            task.error_message = str(err)
            await db.commit()

    async def _finalize_evaluation(self, task_id: str, db: AsyncSession) -> None:
        """Calculates end-to-end telemetry, cost, accuracy scores, and logs evaluation."""
        task = await db.get(ResearchTask, task_id)
        if not task:
            return

        stmt = select(AgentStep).where(AgentStep.task_id == task_id)
        result = await db.execute(stmt)
        steps = result.scalars().all()

        total_latency = sum(s.latency_ms for s in steps)
        total_tokens = sum(s.tokens_used for s in steps)

        # Standard blended cost model: $0.15 per 1M tokens for input, $0.60 for output
        estimated_cost = (total_tokens / 1_000_000) * 0.40

        v_report = task.verification_report or {}
        overall_conf = float(v_report.get("overall_confidence", 92.0))
        accuracy_score = float(v_report.get("factual_accuracy_score", 94.0))
        coherence = float(v_report.get("coherence_score", 93.0))
        risk = str(v_report.get("hallucination_risk", "LOW"))

        citations_count = len((task.intermediate_findings or {}).get("citations", []))
        verified_count = len(v_report.get("verified_claims", []))

        evaluation = TaskEvaluation(
            task_id=task_id,
            overall_confidence=overall_conf,
            factual_accuracy_score=accuracy_score,
            coherence_score=coherence,
            hallucination_risk=risk,
            sources_analyzed_count=citations_count,
            verified_claims_count=verified_count,
            total_latency_ms=total_latency,
            total_tokens=total_tokens,
            estimated_cost_usd=round(estimated_cost, 6)
        )
        db.add(evaluation)


orchestrator = AgentOrchestrator()
