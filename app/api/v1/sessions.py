from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.session import AirSpaceSession
from app.models.check_in import CheckIn
from app.models.reflection import Reflection
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionDetailResponse,
    SessionListResponse,
)
from app.schemas.reflection import ReflectionRequest, ReflectionResponse
from app.services.ai import ai_reflection_service, AIServiceError

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _get_user_session(session_id: int, user: User, db: Session) -> AirSpaceSession:
    """Helper to enforce strict server-side resource ownership (FR-050, FR-051)."""
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


@router.post("", response_model=SessionDetailResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_in: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FR-020, FR-021, FR-022, FR-023:
    Creates a new venting session with unique ID and timestamp.
    Optionally records initial 'before' emotional check-in if provided.
    """
    session = AirSpaceSession(
        user_id=current_user.id,
        content=session_in.content,
    )
    db.add(session)
    db.flush()  # obtain session.id

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


@router.get("", response_model=SessionListResponse)
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-024: Returns all sessions belonging to the authenticated user."""
    sessions = (
        db.query(AirSpaceSession)
        .filter(AirSpaceSession.user_id == current_user.id)
        .order_by(AirSpaceSession.created_at.desc())
        .all()
    )
    return SessionListResponse(sessions=sessions, total=len(sessions))


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves a single session with its check-ins and reflection."""
    return _get_user_session(session_id, current_user, db)


@router.patch("/{session_id}", response_model=SessionDetailResponse)
def update_session(
    session_id: int,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates the content of an existing session draft."""
    session = _get_user_session(session_id, current_user, db)
    if session_update.content is not None:
        session.content = session_update.content
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-025: Deletes the user's session and associated data."""
    session = _get_user_session(session_id, current_user, db)
    db.delete(session)
    db.commit()
    return {"message": "Session successfully deleted"}


@router.post("/{session_id}/reflect", response_model=ReflectionResponse)
def reflect_session(
    session_id: int,
    reflect_req: ReflectionRequest = ReflectionRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FR-030 to FR-035:
    Requests an AI reflection for the selected session.
    Guarantees:
    - User content is not overwritten (FR-033).
    - If AI fails, saved session is preserved without loss (FR-034).
    - Reflection is separate entity (FR-032).
    """
    session = _get_user_session(session_id, current_user, db)

    # If reflection already exists, return existing or update
    existing_reflection = (
        db.query(Reflection).filter(Reflection.session_id == session.id).first()
    )

    try:
        reflection_text = ai_reflection_service.generate_reflection(
            vent_content=session.content,
            focus=reflect_req.focus,
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

    if existing_reflection:
        existing_reflection.content = reflection_text
        db.commit()
        db.refresh(existing_reflection)
        return existing_reflection
    else:
        reflection = Reflection(
            session_id=session.id,
            content=reflection_text,
        )
        db.add(reflection)
        db.commit()
        db.refresh(reflection)
        return reflection
