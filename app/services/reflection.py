from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.session import AirSpaceSession
from app.models.reflection import Reflection
from app.services.ai import ai_reflection_service, AIServiceError


def generate_session_reflection(
    db: Session,
    session: AirSpaceSession,
    focus: Optional[str] = None,
    save_immediately: bool = True,
) -> Reflection:
    """
    FR-020 to FR-024:
    Generates structured AI reflection while guaranteeing:
    - User's original content is NEVER modified or overwritten.
    - AI outage preserves user's session safely.
    - User has control over retention (persists or remains draftable).
    """
    try:
        reflection_text = ai_reflection_service.generate_reflection(
            vent_content=session.content,
            focus=focus,
        )
    except AIServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Decompress & Reframe service is temporarily busy: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error generating reflection",
        )

    existing = db.query(Reflection).filter(Reflection.session_id == session.id).first()
    source_tag = f"ai_{ai_reflection_service.provider}"
    
    if existing:
        existing.content = reflection_text
        existing.source = source_tag
        existing.is_saved = save_immediately
        db.commit()
        db.refresh(existing)
        return existing
    else:
        reflection = Reflection(
            session_id=session.id,
            content=reflection_text,
            source=source_tag,
            is_saved=save_immediately,
        )
        db.add(reflection)
        db.commit()
        db.refresh(reflection)
        return reflection


def update_reflection_retention(db: Session, session: AirSpaceSession, is_saved: bool) -> Reflection:
    reflection = db.query(Reflection).filter(Reflection.session_id == session.id).first()
    if not reflection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reflection not found")
    reflection.is_saved = is_saved
    db.commit()
    db.refresh(reflection)
    return reflection


def delete_reflection(db: Session, session: AirSpaceSession) -> None:
    reflection = db.query(Reflection).filter(Reflection.session_id == session.id).first()
    if reflection:
        db.delete(reflection)
        db.commit()