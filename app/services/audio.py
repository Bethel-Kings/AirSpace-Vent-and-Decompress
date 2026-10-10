from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.session import AirSpaceSession
from app.models.audio_asset import AudioAsset
from app.schemas.audio import AudioTranscriptionRequest


def record_audio_transcription(
    db: Session,
    session: AirSpaceSession,
    transcription_in: AudioTranscriptionRequest,
) -> AudioAsset:
    """
    FR-016 & Audio extension requirements:
    Stores audio metadata in AudioAsset without blocking text sessions.
    Updates session content with transcribed text.
    """
    session.content = transcription_in.transcript
    session.input_type = "audio"

    existing_asset = db.query(AudioAsset).filter(AudioAsset.session_id == session.id).first()
    if existing_asset:
        existing_asset.duration = transcription_in.duration
        existing_asset.storage_key = transcription_in.storage_key
        existing_asset.transcription_status = "completed"
        db.commit()
        db.refresh(existing_asset)
        return existing_asset
        
    asset = AudioAsset(
        session_id=session.id,
        duration=transcription_in.duration,
        storage_key=transcription_in.storage_key,
        transcription_status="completed",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset