from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import settings
from app.schemas.check_in import CheckInResponse
from app.schemas.reflection import ReflectionResponse
from app.schemas.audio import AudioAssetResponse


class SessionCreate(BaseModel):
    content: str = Field("", max_length=settings.MAX_VENT_CHARS, description="Raw venting / stream of consciousness text")
    input_type: Optional[str] = Field("text", description="Input type: text or audio")
    initial_mood: Optional[str] = Field(None, description="Optional pre-session mood rating (1-5 or descriptor)")
    status: Optional[str] = Field("draft", description="Session state: draft or completed")

    @model_validator(mode="after")
    def completed_sessions_need_content(self):
        if (self.status or "draft") == "completed" and not (self.content or "").strip():
            raise ValueError("Completed sessions require venting content.")
        return self


class SessionUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=settings.MAX_VENT_CHARS)
    status: Optional[str] = Field(None)


class SessionResponse(BaseModel):
    id: int
    user_id: int
    content: str
    input_type: str = "text"
    status: str = "completed"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(BaseModel):
    id: int
    user_id: int
    content: str
    input_type: str = "text"
    status: str = "completed"
    created_at: datetime
    updated_at: datetime
    check_ins: List[CheckInResponse] = []
    reflection: Optional[ReflectionResponse] = None
    audio_asset: Optional[AudioAssetResponse] = None
    safety: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

    
class SessionListResponse(BaseModel):
    sessions: List[SessionDetailResponse]
    total: int