from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.check_in import CheckInResponse
from app.schemas.reflection import ReflectionResponse
from app.schemas.audio import AudioAssetResponse


class SessionCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Raw venting / stream of consciousness text")
    input_type: Optional[str] = Field("text", description="Input type: text or audio")
    initial_mood: Optional[str] = Field(None, description="Optional pre-session mood rating (1-5 or descriptor)")
    status: Optional[str] = Field("completed", description="Session state: draft or completed")


class SessionUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
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

    model_config = ConfigDict(from_attributes=True)

    
class SessionListResponse(BaseModel):
    sessions: List[SessionDetailResponse]
    total: int