from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.reflection import ReflectionRequest, ReflectionResponse, ReflectionRetentionUpdate
from app.services.reflection import delete_reflection, generate_session_reflection, update_reflection_retention
from app.services.sessions import get_user_session_or_404

router = APIRouter(prefix="/sessions", tags=["Reflections"])


@router.post("/{session_id}/reflect", response_model=ReflectionResponse)
@limiter.limit(settings.REFLECT_RATE_LIMIT)
def reflect_session(
    request: Request,
    session_id: int,
    reflect_req: ReflectionRequest = ReflectionRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_session_or_404(db, session_id, current_user)
    original = session.content
    reflection = generate_session_reflection(
        db,
        session,
        focus=reflect_req.focus,
        save_immediately=reflect_req.save_immediately,
    )
    db.refresh(session)
    if session.content != original:
        session.content = original
        db.commit()
    return reflection


@router.patch("/{session_id}/reflection", response_model=ReflectionResponse)
def set_reflection_retention(
    session_id: int,
    body: ReflectionRetentionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_session_or_404(db, session_id, current_user)
    return update_reflection_retention(db, session, body.is_saved)


@router.delete("/{session_id}/reflection")
def discard_reflection(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_session_or_404(db, session_id, current_user)
    delete_reflection(db, session)
    return {"message": "Reflection discarded"}
