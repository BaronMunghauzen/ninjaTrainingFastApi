"""make user_id nullable for anonymous training/exercises

Revision ID: e3f4a5b6c7d8
Revises: e2b3c4d5e6f7
Create Date: 2026-03-17

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "e2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "user_training",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "user_exercise",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "user_training",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "user_exercise",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

