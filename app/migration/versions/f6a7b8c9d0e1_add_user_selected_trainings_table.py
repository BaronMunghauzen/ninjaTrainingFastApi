"""add user_selected_trainings table

Revision ID: f6a7b8c9d0e1
Revises: f5a6b7c8d9e0
Create Date: 2026-03-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_selected_trainings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sa.UUID(), nullable=False),
        sa.Column("actual", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("training_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["training_id"], ["training.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "training_id", name="uq_user_selected_training"),
    )
    op.create_index(
        op.f("ix_user_selected_trainings_uuid"),
        "user_selected_trainings",
        ["uuid"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_selected_trainings_uuid"), table_name="user_selected_trainings")
    op.drop_table("user_selected_trainings")
