"""add image_id and video_id in tables

Revision ID: 2aef130fee19
Revises: 8eaa14d20cc0
Create Date: 2025-07-19 15:15:03.998763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2aef130fee19'
down_revision: Union[str, Sequence[str], None] = '8eaa14d20cc0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exercise', sa.Column('image_id', sa.Integer(), nullable=True))
    op.add_column('exercise', sa.Column('video_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'exercise', 'files', ['video_id'], ['id'])
    op.create_foreign_key(None, 'exercise', 'files', ['image_id'], ['id'])
    op.add_column('exercise_group', sa.Column('image_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'exercise_group', 'files', ['image_id'], ['id'])
    op.add_column('program', sa.Column('image_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'program', 'files', ['image_id'], ['id'])
    op.add_column('training', sa.Column('image_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'training', 'files', ['image_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'training', type_='foreignkey')
    op.drop_column('training', 'image_id')
    op.drop_constraint(None, 'program', type_='foreignkey')
    op.drop_column('program', 'image_id')
    op.drop_constraint(None, 'exercise_group', type_='foreignkey')
    op.drop_column('exercise_group', 'image_id')
    op.drop_constraint(None, 'exercise', type_='foreignkey')
    op.drop_constraint(None, 'exercise', type_='foreignkey')
    op.drop_column('exercise', 'video_id')
    op.drop_column('exercise', 'image_id')
    # ### end Alembic commands ###
