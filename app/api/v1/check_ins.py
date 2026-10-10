from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.check_in import (
    CheckInCreate,
    CheckInHistoryResponse,
    CheckInResponse,
    ResetFollowupListResponse,
)
from app.services.check_ins import compute_reset_followups, list_user_check_ins, upsert_check_in
from app.services.sessions import get_user_session_or_404, list_user_sessions

session_checkins_router = APIRouter(prefix="/sessions/{session_id}/check-ins", tags=["Emotional Check-Ins"])
history_router = APIRouter(tags=["Emotional Check-Ins"])


@session_checkins_router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def create_check_in(
    session_id: int,
    check_in_in: CheckInCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_session_or_404(db, session_id, current_user)
    return upsert_check_in(db, session, check_in_in.stage, check_in_in.value)


@session_checkins_router.get("", response_model=List[CheckInResponse])
def get_session_check_ins(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_user_session_or_404(db, session_id, current_user)
    return session.check_ins


@history_router.get("/check-ins", response_model=CheckInHistoryResponse)
def get_my_check_ins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_ins = list_user_check_ins(db, current_user)
    return CheckInHistoryResponse(check_ins=check_ins, total=len(check_ins))


@history_router.get("/reset-followups", response_model=ResetFollowupListResponse)
def get_reset_followups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = list_user_sessions(db, current_user)
    pending, completed = compute_reset_followups(sessions)
    return ResetFollowupListResponse(pending=pending, completed=completed)
