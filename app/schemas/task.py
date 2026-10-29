from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Short title for the research mission")
    query: str = Field(..., min_length=5, description="Detailed research question or prompt")
    task_type: Optional[str] = Field("RESEARCH", description="'RESEARCH' or 'DOCUMENT_AUDIT'")
    provider: Optional[str] = Field("auto", description="AI Provider: 'auto', 'openai', 'gemini', or 'mock'")
    require_human_approval: Optional[bool] = Field(True, description="Pause for human review before final report")


class CitationSchema(BaseModel):
    id: int
    title: str
    url: str
    snippet: str
    domain: Optional[str] = None
    reliability_score: float
    verified: bool

    model_config = ConfigDict(from_attributes=True)


class AgentStepSchema(BaseModel):
    id: int
    agent_name: str
    step_name: str
    status: str
    latency_ms: float
    tokens_used: int
    logs: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationSchema(BaseModel):
    overall_confidence: float
    factual_accuracy_score: float
    coherence_score: float
    hallucination_risk: str
    sources_analyzed_count: int
    verified_claims_count: int
    total_latency_ms: float
    total_tokens: int
    estimated_cost_usd: float

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    id: str
    title: str
    query: str
    status: str
    task_type: str = "RESEARCH"
    document_filename: Optional[str] = None
    provider: str
    model_name: str
    human_approved: Optional[bool] = None
    human_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskDetailResponse(TaskResponse):
    research_plan: Optional[Dict[str, Any]] = None
    intermediate_findings: Optional[Dict[str, Any]] = None
    analysis_insights: Optional[Dict[str, Any]] = None
    verification_report: Optional[Dict[str, Any]] = None
    document_summary: Optional[Dict[str, Any]] = None
    strategic_projections: Optional[Dict[str, Any]] = None
    visual_diagrams: Optional[Dict[str, Any]] = None
    audit_dossier: Optional[Dict[str, Any]] = None
    final_report: Optional[str] = None
    error_message: Optional[str] = None
    steps: List[AgentStepSchema] = []
    citations: List[CitationSchema] = []
    evaluation: Optional[EvaluationSchema] = None

    model_config = ConfigDict(from_attributes=True)

