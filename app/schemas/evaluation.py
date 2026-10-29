from typing import List, Dict, Any
from pydantic import BaseModel


class AgentPerformanceMetric(BaseModel):
    agent_name: str
    total_calls: int
    avg_latency_ms: float
    total_tokens: int


class DashboardMetricsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    average_accuracy_score: float
    average_confidence_score: float
    total_tokens_consumed: int
    total_estimated_cost_usd: float
    agent_metrics: List[AgentPerformanceMetric]
    recent_evaluations: List[Dict[str, Any]]
