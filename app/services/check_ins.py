from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.check_in import CheckIn
from app.models.session import AirSpaceSession
from app.models.user import User
from app.schemas.check_in import FOLLOWUP_DELAY_DAYS, ResetFollowupItem


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def list_user_check_ins(db: Session, user: User) -> List[CheckIn]:
    return (
        db.query(CheckIn)
        .join(AirSpaceSession, CheckIn.session_id == AirSpaceSession.id)
        .filter(AirSpaceSession.user_id == user.id)
        .order_by(CheckIn.created_at.desc())
        .all()
    )


def upsert_check_in(db: Session, session: AirSpaceSession, stage: str, value: str) -> CheckIn:
    existing = (
        db.query(CheckIn)
        .filter(CheckIn.session_id == session.id, CheckIn.stage == stage)
        .first()
    )
    if existing:
        existing.value = value
        db.commit()
        db.refresh(existing)
        return existing

    check_in = CheckIn(session_id=session.id, stage=stage, value=value)
    db.add(check_in)
    db.commit()
    db.refresh(check_in)
    return check_in


def compute_reset_followups(sessions: List[AirSpaceSession]) -> Tuple[List[ResetFollowupItem], List[ResetFollowupItem]]:
    now = datetime.now(timezone.utc)
    pending: List[ResetFollowupItem] = []
    completed: List[ResetFollowupItem] = []

    for session in sessions:
        created = _as_utc(session.created_at)
        existing_stages = {c.stage for c in (session.check_ins or [])}
        preview = (session.content or "").strip().replace("\n", " ")
        preview = (preview[:120] + "…") if len(preview) > 120 else preview
        days_since = max(0, (now - created).days)

        for stage, delay in FOLLOWUP_DELAY_DAYS.items():
            due_at = created + timedelta(days=delay)
            item = ResetFollowupItem(
                session_id=session.id,
                stage=stage,
                due_at=due_at,
                days_since_session=days_since,
                session_preview=preview or "(draft)",
                session_created_at=created,
                completed=stage in existing_stages,
            )
            if item.completed:
                completed.append(item)
            elif now >= due_at:
                pending.append(item)

    pending.sort(key=lambda i: i.due_at)
    completed.sort(key=lambda i: i.due_at, reverse=True)
    return pending, completed
