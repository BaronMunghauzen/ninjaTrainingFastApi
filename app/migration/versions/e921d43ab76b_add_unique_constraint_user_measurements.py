"""add_unique_constraint_user_measurements

Revision ID: e921d43ab76b
Revises: d1d0db70a2a8
Create Date: 2025-09-13 22:48:56.181572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e921d43ab76b'
down_revision: Union[str, Sequence[str], None] = 'd1d0db70a2a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем уникальное ограничение для user_measurements
    op.create_unique_constraint(
        'uq_measurement_user_date_type',
        'user_measurements',
        ['user_id', 'measurement_date', 'measurement_type_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем уникальное ограничение для user_measurements
    op.drop_constraint(
        'uq_measurement_user_date_type',
        'user_measurements',
        type_='unique'
    )
