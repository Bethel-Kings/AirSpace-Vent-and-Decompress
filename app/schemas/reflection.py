from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ReflectionRequest(BaseModel):
    focus: Optional[str] = Field(None, description="Optional prompt focus area, e.g. workload, relationships, boundaries")
    save_immediately: bool = Field(True, description="Whether to persist to session immediately or leave drafted (FR-023)")


class ReflectionResponse(BaseModel):
    id: int
    session_id: int
    content: str
    source: str = "ai_gemini"
    is_saved: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReflectionRetentionUpdate(BaseModel):
    is_saved: bool = Field(..., description="User choice to save/retain or discard reflection (FR-023, FR-024)")    