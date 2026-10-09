from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class CheckInCreate(BaseModel):
    stage: Literal["before", "after"]
    value: str = Field(..., min_length=1, max_length=64, description="Mood rating or emotional label")


class CheckInResponse(BaseModel):
    id: int
    session_id: int
    stage: str
    value: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
