"""add_image_id_to_achievement_types

Revision ID: 978a3dc7089c
Revises: 8efaa0ea8cf1
Create Date: 2025-12-26 20:01:18.556226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '978a3dc7089c'
down_revision: Union[str, Sequence[str], None] = '8efaa0ea8cf1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('achievement_types', sa.Column('image_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'achievement_types', 'files', ['image_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Находим имя foreign key constraint
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    fk_constraints = [
        fk['name'] for fk in inspector.get_foreign_keys('achievement_types')
        if 'image_id' in [col['name'] for col in fk['constrained_columns']]
    ]
    
    # Удаляем foreign key constraint если он существует
    for fk_name in fk_constraints:
        op.drop_constraint(fk_name, 'achievement_types', type_='foreignkey')
    
    op.drop_column('achievement_types', 'image_id')
