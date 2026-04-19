"""add anonymous_session_id to training and user_training

Revision ID: e1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-03-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "training",
        sa.Column(
            "anonymous_session_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "user_training",
        sa.Column(
            "anonymous_session_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_training_anonymous_session_id",
        "training",
        ["anonymous_session_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_training_anonymous_session_id",
        "user_training",
        ["anonymous_session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_training_anonymous_session_id",
        table_name="user_training",
    )
    op.drop_index(
        "ix_training_anonymous_session_id",
        table_name="training",
    )
    op.drop_column("user_training", "anonymous_session_id")
    op.drop_column("training", "anonymous_session_id")

