import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.services.ai.factory import get_ai_provider
from app.services.agents.orchestrator import orchestrator
from app.database.models.task import ResearchTask

# Test in-memory SQLite database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_ai_factory():
    """Verify that the AI factory defaults safely to the high-fidelity mock provider when no keys exist."""
    provider, name, model = get_ai_provider("mock")
    assert name == "mock"
    assert model == "simulation-v1"
    
    text = await provider.generate_text("Test query")
    assert len(text) > 0

    json_res = await provider.generate_json("Test prompt", system_prompt="coordinator")
    assert "hypotheses" in json_res
    assert len(json_res["hypotheses"]) > 0


@pytest.mark.asyncio
async def test_full_agent_orchestration_with_hitl(test_session: AsyncSession):
    """
    Tests end-to-end multi-agent orchestration:
    1. Creates task
    2. Runs pipeline (pauses at HITL)
    3. Verifies claims and verification score
    4. Simulates human reviewer approval
    5. Verifies completed status and final report synthesis
    """
    # 1. Create task
    task = ResearchTask(
        title="Autonomous AI Multi-Agent Systems in Healthcare",
        query="Investigate multi-agent systems for medical record synthesis, diagnostic support, and clinical safety compliance.",
        provider="mock"
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)

    # 2. Run pipeline with HITL enabled
    await orchestrator.run_pipeline(task.id, test_session, require_human_approval=True)
    await test_session.refresh(task)

    # Must be paused for Human Review
    assert task.status == "AWAITING_APPROVAL"
    assert task.research_plan is not None
    assert task.intermediate_findings is not None
    assert task.analysis_insights is not None
    assert task.verification_report is not None
    assert "overall_confidence" in task.verification_report

    # 3. Resume with Human Approval
    await orchestrator.resume_after_approval(
        task_id=task.id,
        db=test_session,
        approved=True,
        feedback="Verified against clinical validation protocol."
    )
    await test_session.refresh(task)

    # Must be completed with final report
    assert task.status == "COMPLETED"
    assert task.human_approved is True
    assert task.final_report is not None
    assert "Executive Summary" in task.final_report or "Decision" in task.final_report


@pytest.mark.asyncio
async def test_document_audit_pipeline(test_session: AsyncSession):
    """
    Tests the new Literature Audit & Strategic Projection pipeline:
    1. Ingests mock document
    2. Runs Summarizer, Projection, Visual SVG, and Audit agents
    3. Verifies SVG diagram and Audit Grade
    4. Resumes after human approval
    5. Verifies completed audit dossier
    """
    from app.services.tools.document_tool import DocumentParserTool

    mock_literature = b"""
    # Clinical Multi-Agent Architecture for Oncology Decision Support
    Abstract: We present an empirical evaluation of multi-agent distributed systems in oncology diagnostic verification.
    Methods: Tested across 500 patient cohorts measuring diagnostic precision and cross-agent hallucination reduction.
    Results: Hallucination rate dropped by 64.2% with real-time SSE telemetry latency under 180ms.
    Conclusion: Decoupled multi-agent systems with human review gates provide institutional-grade safety.
    """

    parsed_doc = DocumentParserTool.parse_text_bytes(mock_literature, "oncology_multi_agent.pdf")
    assert parsed_doc["total_words"] > 20

    task = ResearchTask(
        title="Literature Audit: Oncology Multi-Agent Clinical Study",
        query="Perform literature audit, strategic projections, visual architecture, and compliance verification.",
        task_type="DOCUMENT_AUDIT",
        document_filename="oncology_multi_agent.pdf",
        provider="mock"
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)

    # Run document pipeline with HITL enabled
    await orchestrator.run_document_pipeline(task.id, test_session, parsed_doc=parsed_doc, require_human_approval=True)
    await test_session.refresh(task)

    assert task.status == "AWAITING_APPROVAL"
    assert task.document_summary is not None
    assert len(task.document_summary.get("key_findings", [])) > 0
    assert task.strategic_projections is not None
    assert len(task.strategic_projections.get("project_phases", [])) > 0
    assert task.visual_diagrams is not None
    assert "<svg" in task.visual_diagrams.get("svg_diagram", "")
    assert task.audit_dossier is not None
    assert task.audit_dossier.get("audit_grade") is not None

    # Resume with approval
    await orchestrator.resume_after_approval(task.id, test_session, approved=True, feedback="Approved audit by clinical team.")
    await test_session.refresh(task)

    assert task.status == "COMPLETED"
    assert task.final_report is not None

