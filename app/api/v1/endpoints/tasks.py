import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.database.session import get_db, AsyncSessionLocal
from app.database.models.task import ResearchTask
from app.database.models.agent_step import AgentStep
from app.database.models.citation import Citation
from app.database.models.evaluation import TaskEvaluation
from app.schemas.task import TaskCreate, TaskResponse, TaskDetailResponse
from app.services.agents.orchestrator import orchestrator
from app.services.tools.document_tool import DocumentParserTool
from app.core.logger import get_logger

logger = get_logger("tasks_api")
router = APIRouter(prefix="/tasks", tags=["Tasks"])


async def _run_orchestrator_background(task_id: str, require_human_approval: bool):
    """Executes the pipeline in an isolated async database session."""
    async with AsyncSessionLocal() as db:
        await orchestrator.run_pipeline(task_id, db, require_human_approval=require_human_approval)


async def _run_document_orchestrator_background(task_id: str, parsed_doc: dict, require_human_approval: bool):
    """Executes the document & literature audit pipeline in an isolated session."""
    async with AsyncSessionLocal() as db:
        await orchestrator.run_document_pipeline(task_id, db, parsed_doc=parsed_doc, require_human_approval=require_human_approval)


@router.post("/upload-document", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_audit(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    query: Optional[str] = Form(None),
    provider: Optional[str] = Form("auto"),
    require_human_approval: Optional[bool] = Form(True),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests research literature or audit report (PDF, Markdown, TXT).
    Triggers multi-agent summarization, strategic project roadmaps, 
    visual architecture diagrams, and institutional compliance audits.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename = file.filename or "document.pdf"

    if filename.lower().endswith(".pdf"):
        parsed = DocumentParserTool.parse_pdf_bytes(contents, filename)
    else:
        parsed = DocumentParserTool.parse_text_bytes(contents, filename)

    task_title = title or f"Literature Audit: {filename}"
    task_query = query or (
        f"Analyze uploaded document '{filename}' ({parsed['total_pages']} pages, {parsed['total_words']} words). "
        "Perform deep hierarchical summarization, future project projections, visual architecture synthesis, and institutional audit."
    )

    task = ResearchTask(
        title=task_title,
        query=task_query,
        task_type="DOCUMENT_AUDIT",
        document_filename=filename,
        provider=provider or "auto",
        status="PENDING"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    background_tasks.add_task(
        _run_document_orchestrator_background,
        task.id,
        parsed,
        require_human_approval if require_human_approval is not None else True
    )

    return task


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_research_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new research task and initiates autonomous multi-agent orchestration.
    """
    task = ResearchTask(
        title=payload.title,
        query=payload.query,
        provider=payload.provider or "auto",
        status="PENDING"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Spawn asynchronous background orchestration
    background_tasks.add_task(
        _run_orchestrator_background, 
        task.id, 
        payload.require_human_approval
    )

    return task


@router.get("", response_model=List[TaskResponse])
async def list_research_tasks(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Lists recent research tasks ordered by creation date.
    """
    stmt = (
        select(ResearchTask)
        .order_by(desc(ResearchTask.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task_details(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full details of a research task including steps, citations, evaluation, and report.
    """
    stmt = (
        select(ResearchTask)
        .options(
            selectinload(ResearchTask.steps),
            selectinload(ResearchTask.citations),
            selectinload(ResearchTask.evaluation)
        )
        .where(ResearchTask.id == task_id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research task with ID '{task_id}' not found."
        )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes a research task and cascades to associated steps and citations.
    """
    task = await db.get(ResearchTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return None
