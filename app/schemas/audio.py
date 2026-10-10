from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class AudioAssetResponse(BaseModel):
    id: int
    session_id: int
    storage_key: Optional[str] = None
    duration: Optional[float] = None
    transcription_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AudioTranscriptionRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="Transcribed text from audio pipeline")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    storage_key: Optional[str] = Field(None, description="Object storage reference key")

