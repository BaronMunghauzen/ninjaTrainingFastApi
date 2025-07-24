"""user_program and program may be null in tables ver2

Revision ID: 7b95baeff19a
Revises: 20e9fdd27516
Create Date: 2025-07-22 21:35:10.840621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b95baeff19a'
down_revision: Union[str, Sequence[str], None] = '20e9fdd27516'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('user_program', 'program_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('user_training', 'user_program_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('user_training', 'program_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('user_exercise', 'program_id', existing_type=sa.Integer(), nullable=True)
    op.alter_column('training', 'program_id', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('user_program', 'program_id', existing_type=sa.Integer(), nullable=False)
    op.alter_column('user_training', 'user_program_id', existing_type=sa.Integer(), nullable=False)
    op.alter_column('user_training', 'program_id', existing_type=sa.Integer(), nullable=False)
    op.alter_column('user_exercise', 'program_id', existing_type=sa.Integer(), nullable=False)
    op.alter_column('training', 'program_id', existing_type=sa.Integer(), nullable=False)
