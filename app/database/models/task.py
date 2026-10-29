import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.agent_step import AgentStep
    from app.database.models.citation import Citation
    from app.database.models.evaluation import TaskEvaluation


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True)
    task_type: Mapped[str] = mapped_column(String(50), default="RESEARCH", index=True)  # RESEARCH or DOCUMENT_AUDIT
    document_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), default="auto")
    model_name: Mapped[str] = mapped_column(String(100), default="default")
    
    # Structured Agent Artifacts
    research_plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    intermediate_findings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    analysis_insights: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    verification_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Document Audit, Visual Diagrams, & Strategic Projections
    document_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    strategic_projections: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    visual_diagrams: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    audit_dossier: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    final_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Human Review & Feedback
    human_approved: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    human_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Error state
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    steps: Mapped[List["AgentStep"]] = relationship(
        "AgentStep", 
        back_populates="task", 
        cascade="all, delete-orphan",
        order_by="AgentStep.created_at"
    )
    citations: Mapped[List["Citation"]] = relationship(
        "Citation", 
        back_populates="task", 
        cascade="all, delete-orphan"
    )
    evaluation: Mapped[Optional["TaskEvaluation"]] = relationship(
        "TaskEvaluation", 
        back_populates="task", 
        uselist=False, 
        cascade="all, delete-orphan"
    )
