"""add user fields and enums

Revision ID: 0e82396ee96a
Revises: 62b115c3ed0b
Create Date: 2025-07-10 16:57:03.058379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e82396ee96a'
down_revision: Union[str, Sequence[str], None] = '62b115c3ed0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    gender_enum = sa.Enum('male', 'female', name='genderenum')
    subscription_status_enum = sa.Enum('pending', 'active', 'expired', name='subscriptionstatusenum')
    theme_enum = sa.Enum('light', 'dark', name='themeenum')

    gender_enum.create(op.get_bind(), checkfirst=True)
    subscription_status_enum.create(op.get_bind(), checkfirst=True)
    theme_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('user', sa.Column('login', sa.String(), nullable=False))
    op.add_column('user', sa.Column('middle_name', sa.String(), nullable=True))
    op.add_column('user', sa.Column('gender', gender_enum, nullable=False, server_default='male'))
    op.add_column('user', sa.Column('description', sa.String(), nullable=True))
    op.add_column('user', sa.Column('subscription_status', subscription_status_enum, server_default='pending', nullable=False))
    op.add_column('user', sa.Column('subscription_until', sa.Date(), nullable=True))
    op.add_column('user', sa.Column('theme', theme_enum, nullable=False, server_default='dark'))
    op.create_unique_constraint('uq_user_login', 'user', ['login'])


def downgrade() -> None:
    op.drop_constraint('uq_user_login', 'user', type_='unique')
    op.drop_column('user', 'theme')
    op.drop_column('user', 'subscription_until')
    op.drop_column('user', 'subscription_status')
    op.drop_column('user', 'description')
    op.drop_column('user', 'gender')
    op.drop_column('user', 'middle_name')
    op.drop_column('user', 'login')

    gender_enum = sa.Enum('male', 'female', name='genderenum')
    subscription_status_enum = sa.Enum('pending', 'active', 'expired', name='subscriptionstatusenum')
    theme_enum = sa.Enum('light', 'dark', name='themeenum')
    gender_enum.drop(op.get_bind(), checkfirst=True)
    subscription_status_enum.drop(op.get_bind(), checkfirst=True)
    theme_enum.drop(op.get_bind(), checkfirst=True)
