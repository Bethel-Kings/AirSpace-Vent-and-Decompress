from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("airspace_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage = Column(String(32), nullable=False)  # "before" or "after"
    value = Column(String(64), nullable=False)  # e.g., "1".."5" or emotional descriptor
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("AirSpaceSession", back_populates="check_ins")
