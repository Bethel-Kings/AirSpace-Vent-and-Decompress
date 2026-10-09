from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ReflectionRequest(BaseModel):
    # Optional prompt custom tag or tone preference if needed
    focus: Optional[str] = None


class ReflectionResponse(BaseModel):
    id: int
    session_id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
