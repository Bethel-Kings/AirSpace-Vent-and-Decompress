from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.check_in import CheckInResponse
from app.schemas.reflection import ReflectionResponse


class SessionCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Raw venting / stream of consciousness text")
    initial_mood: Optional[str] = Field(None, description="Optional pre-session mood rating (1-5 or descriptor)")


class SessionUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)


class SessionResponse(BaseModel):
    id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(BaseModel):
    id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    check_ins: List[CheckInResponse] = []
    reflection: Optional[ReflectionResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    sessions: List[SessionDetailResponse]
    total: int
