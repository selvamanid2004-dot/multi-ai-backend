from typing import TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.task import ResearchTask


class TaskEvaluation(Base):
    __tablename__ = "task_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_tasks.id", ondelete="CASCADE"), unique=True, index=True)
    
    # AI Quality Metrics (0-100)
    overall_confidence: Mapped[float] = mapped_column(Float, default=90.0)
    factual_accuracy_score: Mapped[float] = mapped_column(Float, default=92.0)
    coherence_score: Mapped[float] = mapped_column(Float, default=95.0)
    hallucination_risk: Mapped[str] = mapped_column(String(20), default="LOW")  # LOW, MEDIUM, HIGH
    
    # Quantitative & Performance Metrics
    sources_analyzed_count: Mapped[int] = mapped_column(Integer, default=0)
    verified_claims_count: Mapped[int] = mapped_column(Integer, default=0)
    total_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )

    task: Mapped["ResearchTask"] = relationship("ResearchTask", back_populates="evaluation")
