"""add anonymous_session_id to user_program_plan

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-03-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_program_plan",
        sa.Column(
            "anonymous_session_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_user_program_plan_anonymous_session_id",
        "user_program_plan",
        ["anonymous_session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_program_plan_anonymous_session_id",
        table_name="user_program_plan",
    )
    op.drop_column("user_program_plan", "anonymous_session_id")
