from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HumanApprovalRequest(BaseModel):
    approved: bool = Field(..., description="True if approved to synthesize final report; False if rejected or needs re-query")
    feedback: Optional[str] = Field(None, description="Guidance, corrections, or notes injected by the human reviewer")
    additional_guidelines: Optional[str] = Field(None, description="Specific instructions for the final report")
