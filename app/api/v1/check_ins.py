from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.api.v1.sessions import _get_user_session
from app.db.session import get_db
from app.models.user import User
from app.models.check_in import CheckIn
from app.schemas.check_in import CheckInCreate, CheckInResponse

router = APIRouter(prefix="/sessions/{session_id}/check-ins", tags=["Emotional Check-Ins"])


@router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def create_check_in(
    session_id: int,
    check_in_in: CheckInCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FR-040, FR-041, FR-042:
    Records a before- or after-session emotional check-in linked to the session and user.
    """
    session = _get_user_session(session_id, current_user, db)

    # Check if a check-in for this stage already exists
    existing_check_in = (
        db.query(CheckIn)
        .filter(CheckIn.session_id == session.id, CheckIn.stage == check_in_in.stage)
        .first()
    )
    if existing_check_in:
        existing_check_in.value = check_in_in.value
        db.commit()
        db.refresh(existing_check_in)
        return existing_check_in

    check_in = CheckIn(
        session_id=session.id,
        stage=check_in_in.stage,
        value=check_in_in.value,
    )
    db.add(check_in)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.get("", response_model=List[CheckInResponse])
def get_session_check_ins(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """FR-043: Review all check-ins for the specified session."""
    session = _get_user_session(session_id, current_user, db)
    return session.check_ins
