from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class AirSpaceSession(Base):
    __tablename__ = "airspace_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    input_type = Column(String(32), default="text", nullable=False)  # "text" or "audio"
    status = Column(String(32), default="completed", nullable=False)  # "draft", "active", "completed"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="sessions")
    check_ins = relationship(
        "CheckIn",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="CheckIn.created_at",
    )
    reflection = relationship(
        "Reflection",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    audio_asset = relationship("AudioAsset", back_populates="session", uselist=False)
