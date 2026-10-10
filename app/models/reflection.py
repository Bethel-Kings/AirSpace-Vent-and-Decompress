from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class Reflection(Base):
    __tablename__ = "reflections"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("airspace_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    content = Column(Text, nullable=False)
    source = Column(String(64), default="ai_gemini", nullable=False)  # "ai_gemini", "mock", "system"
    is_saved = Column(Boolean, default=True, nullable=False)  # User retention control (FR-023, FR-024)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("AirSpaceSession", back_populates="reflection")
