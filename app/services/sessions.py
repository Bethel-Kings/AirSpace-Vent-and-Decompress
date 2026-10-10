from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.session import AirSpaceSession
from app.models.check_in import CheckIn
from app.schemas.session import SessionCreate, SessionUpdate


def get_user_session_or_404(db: Session, session_id: int, user: User) -> AirSpaceSession:
    """Enforces strict server-side resource ownership (FR-014, FR-044, NFR-002)."""
    session = (
        db.query(AirSpaceSession)
        .filter(AirSpaceSession.id == session_id, AirSpaceSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return session


def create_session(db: Session, user: User, session_in: SessionCreate) -> AirSpaceSession:
    """Creates a private venting session with optional pre-session mood check-in."""
    session = AirSpaceSession(
        user_id=user.id,
        content=session_in.content,
        input_type=session_in.input_type or "text",
        status=session_in.status or "completed",
    )
    db.add(session)
    db.flush()

    if session_in.initial_mood:
        check_in = CheckIn(
            session_id=session.id,
            stage="before",
            value=session_in.initial_mood,
        )
        db.add(check_in)

    db.commit()
    db.refresh(session)
    return session


def list_user_sessions(db: Session, user: User) -> List[AirSpaceSession]:
    return (
        db.query(AirSpaceSession)
        .filter(AirSpaceSession.user_id == user.id)
        .order_by(AirSpaceSession.created_at.desc())
        .all()
    )


def update_session(db: Session, session: AirSpaceSession, update_in: SessionUpdate) -> AirSpaceSession:
    if update_in.content is not None:
        session.content = update_in.content
    if update_in.status is not None:
        session.status = update_in.status
    db.commit()
    db.refresh(session)
    return session

    
def delete_session(db: Session, session: AirSpaceSession) -> None:
    db.delete(session)
    db.commit()