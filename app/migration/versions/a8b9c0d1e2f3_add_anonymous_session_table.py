"""add anonymous_session table

Revision ID: a8b9c0d1e2f3
Revises: d3e4f5a6b7c8
Create Date: 2026-04-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "anonymous_session",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("actual", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("anonymous_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_anonymous_session_uuid", "anonymous_session", ["uuid"], unique=True)
    op.create_index(
        "ix_anonymous_session_anonymous_session_id",
        "anonymous_session",
        ["anonymous_session_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_anonymous_session_anonymous_session_id", table_name="anonymous_session")
    op.drop_index("ix_anonymous_session_uuid", table_name="anonymous_session")
    op.drop_table("anonymous_session")
