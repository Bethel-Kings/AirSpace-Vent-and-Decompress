from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


CHECK_IN_STAGES = ("before", "after", "reset_3d", "reset_5d", "reset_7d", "reset_14d", "followup")
FOLLOWUP_STAGES = ("reset_3d", "reset_5d", "reset_7d")
FOLLOWUP_DELAY_DAYS = {"reset_3d": 3, "reset_5d": 5, "reset_7d": 7}


class CheckInCreate(BaseModel):
    stage: Literal["before", "after", "reset_3d", "reset_5d", "reset_7d", "reset_14d", "followup"]
    value: str = Field(..., min_length=1, max_length=64, description="Mood rating or emotional label")


class CheckInResponse(BaseModel):
    id: int
    session_id: int
    stage: str
    value: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CheckInHistoryResponse(BaseModel):
    check_ins: List[CheckInResponse]
    total: int


class ResetFollowupItem(BaseModel):
    session_id: int
    stage: str
    due_at: datetime
    days_since_session: int
    session_preview: str
    session_created_at: datetime
    completed: bool = False


class ResetFollowupListResponse(BaseModel):
    pending: List[ResetFollowupItem]
    completed: List[ResetFollowupItem]
