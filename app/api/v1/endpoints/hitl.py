from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db, AsyncSessionLocal
from app.database.models.task import ResearchTask
from app.schemas.hitl import HumanApprovalRequest
from app.services.agents.orchestrator import orchestrator
from app.core.logger import get_logger

logger = get_logger("hitl_api")
router = APIRouter(prefix="/tasks", tags=["Human-In-The-Loop"])


async def _run_resume_background(task_id: str, approved: bool, feedback: str, guidelines: str):
    async with AsyncSessionLocal() as db:
        await orchestrator.resume_after_approval(
            task_id=task_id,
            db=db,
            approved=approved,
            feedback=feedback,
            additional_guidelines=guidelines
        )


@router.post("/{task_id}/review", status_code=status.HTTP_200_OK)
async def submit_human_review(
    task_id: str,
    payload: HumanApprovalRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits human approval or rejection with feedback for a paused research task.
    Resumes report generation if approved.
    """
    task = await db.get(ResearchTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Task is in status '{task.status}', not 'AWAITING_APPROVAL'."
        )

    # Resume pipeline in background
    background_tasks.add_task(
        _run_resume_background,
        task_id,
        payload.approved,
        payload.feedback or "",
        payload.additional_guidelines or ""
    )

    return {
        "status": "review_submitted",
        "task_id": task_id,
        "action": "approved" if payload.approved else "rejected",
        "message": "Pipeline resumption triggered." if payload.approved else "Task rejected."
    }
