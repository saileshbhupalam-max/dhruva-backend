"""add_idx_users_username_active

Revision ID: 6e4f18e0c7cd
Revises: 002
Create Date: 2025-11-25 08:12:53.954051+05:30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e4f18e0c7cd'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite index on (username, is_active) for login queries."""
    # Create composite index for efficient login validation queries
    op.create_index(
        'idx_users_username_active',
        'users',
        ['username', 'is_active'],
        unique=False
    )


def downgrade() -> None:
    """Remove composite index on (username, is_active)."""
    op.drop_index('idx_users_username_active', table_name='users')
