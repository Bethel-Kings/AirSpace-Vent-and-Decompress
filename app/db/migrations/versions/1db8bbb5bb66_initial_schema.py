"""initial_schema

Revision ID: 1db8bbb5bb66
Revises:
Create Date: 2026-10-07 20:41:25.082761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1db8bbb5bb66"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "airspace_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("input_type", sa.String(length=32), nullable=False, server_default="text"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_airspace_sessions_id", "airspace_sessions", ["id"])
    op.create_index("ix_airspace_sessions_user_id", "airspace_sessions", ["user_id"])
    op.create_index("ix_airspace_sessions_created_at", "airspace_sessions", ["created_at"])

    op.create_table(
        "check_ins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("airspace_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("value", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("session_id", "stage", name="uq_checkin_session_stage"),
    )
    op.create_index("ix_check_ins_id", "check_ins", ["id"])
    op.create_index("ix_check_ins_session_id", "check_ins", ["session_id"])

    op.create_table(
        "reflections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("airspace_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="ai_gemini"),
        sa.Column("is_saved", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("ix_reflections_id", "reflections", ["id"])
    op.create_index("ix_reflections_session_id", "reflections", ["session_id"], unique=True)

    op.create_table(
        "audio_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("airspace_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("transcription_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("ix_audio_assets_id", "audio_assets", ["id"])
    op.create_index("ix_audio_assets_session_id", "audio_assets", ["session_id"], unique=True)


def downgrade() -> None:
    op.drop_table("audio_assets")
    op.drop_table("reflections")
    op.drop_table("check_ins")
    op.drop_table("airspace_sessions")
    op.drop_table("users")
