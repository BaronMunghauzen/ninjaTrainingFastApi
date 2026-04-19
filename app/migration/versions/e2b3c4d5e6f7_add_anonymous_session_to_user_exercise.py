"""add anonymous_session_id to user_exercise

Revision ID: e2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "e1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_exercise",
        sa.Column(
            "anonymous_session_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_user_exercise_anonymous_session_id",
        "user_exercise",
        ["anonymous_session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_exercise_anonymous_session_id",
        table_name="user_exercise",
    )
    op.drop_column("user_exercise", "anonymous_session_id")

