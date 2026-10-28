from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionDetailResponse,
    SessionListResponse,
)
from app.services.safety import evaluate_content_safety
from app.services.sessions import (
    create_session,
    delete_session,
    get_user_session_or_404,
    list_user_sessions,
    update_session,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _session_payload(session) -> SessionDetailResponse:
    payload = SessionDetailResponse.model_validate(session)
    return payload.model_copy(update={"safety": evaluate_content_safety(session.content or "")})


@router.post("", response_model=SessionDetailResponse, status_code=status.HTTP_201_CREATED)
def create_airspace_session(
    session_in: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = create_session(db, current_user, session_in)
    return _session_payload(session)


@router.get("", response_model=SessionListResponse)
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = list_user_sessions(db, current_user)
    return SessionListResponse(
        sessions=[_session_payload(s) for s in sessions],
        total=len(sessions),
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_session_or_404(db, session_id, current_user)
    return _session_payload(session)


@router.patch("/{session_id}", response_model=SessionDetailResponse)
def patch_session(
    session_id: int,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_session_or_404(db, session_id, current_user)
    session = update_session(db, session, session_update)
    return _session_payload(session)


@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
def remove_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_session_or_404(db, session_id, current_user)
    delete_session(db, session)
    return {"message": "Session successfully deleted"}
