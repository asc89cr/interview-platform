"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-21

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("subscription_tier", sa.String(50), nullable=False, server_default="free"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── candidate_profiles ───────────────────────────────────────────────────
    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("resume_url", sa.String(1024), nullable=True),
        sa.Column("parsed_resume", postgresql.JSONB, nullable=True),
        sa.Column("target_role", sa.String(255), nullable=True),
        sa.Column("target_salary_usd", sa.Integer, nullable=True),
        sa.Column(
            "skills",
            postgresql.ARRAY(sa.Text),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "weak_areas",
            postgresql.ARRAY(sa.Text),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("custom_notes", sa.Text, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ── interviewer_profiles ─────────────────────────────────────────────────
    op.create_table(
        "interviewer_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("role", sa.String(255), nullable=True),
        sa.Column("interview_style", sa.String(50), nullable=False, server_default="mixed"),
        sa.Column(
            "known_questions",
            postgresql.ARRAY(sa.Text),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ── sessions ─────────────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "interviewer_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interviewer_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ── attached_files ───────────────────────────────────────────────────────
    op.create_table(
        "attached_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(1024), nullable=False),
        sa.Column("file_type", sa.String(100), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ── turns ────────────────────────────────────────────────────────────────
    op.create_table(
        "turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("speaker", sa.String(50), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("generated_answer", sa.Text, nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("audio_url", sa.String(1024), nullable=True),
    )

    # ── analysis_reports ─────────────────────────────────────────────────────
    op.create_table(
        "analysis_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("overall_score", sa.Float, nullable=True),
        sa.Column("category_scores", postgresql.JSONB, nullable=True),
        sa.Column(
            "strengths",
            postgresql.ARRAY(sa.Text),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "weaknesses",
            postgresql.ARRAY(sa.Text),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("interviewer_intent_summary", sa.Text, nullable=True),
        sa.Column(
            "recommended_practice",
            postgresql.ARRAY(sa.Text),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("pdf_report_url", sa.String(1024), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("analysis_reports")
    op.drop_table("turns")
    op.drop_table("attached_files")
    op.drop_table("sessions")
    op.drop_table("interviewer_profiles")
    op.drop_table("candidate_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
