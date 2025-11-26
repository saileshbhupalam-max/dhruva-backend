"""Add grievance fields for Smart Resolution Engine

Revision ID: 3b_grievance_fields
Revises: dade9ecbca0b
Create Date: 2025-11-25 19:30:00.000000+05:30

Adds fields required by Task 3B Smart Resolution Engine:
- officer_notes: For signal detection from officer remarks
- contact_attempts: For citizen unreachable detection
- category: String field for template matching (not FK)

Migration chain:
dade9ecbca0b -> 3b_grievance_fields -> 3a_empathy_001 -> 3b_resolution_001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b_grievance_fields'
down_revision: Union[str, None] = 'dade9ecbca0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add grievance fields for Smart Resolution Engine."""
    # Add officer_notes - for signal detection
    op.add_column(
        'grievances',
        sa.Column(
            'officer_notes',
            sa.Text(),
            nullable=True,
            comment='Internal officer remarks for signal detection'
        )
    )

    # Add contact_attempts - for citizen unreachable detection
    op.add_column(
        'grievances',
        sa.Column(
            'contact_attempts',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of times officer tried to contact citizen'
        )
    )

    # Add category - string field for template matching
    op.add_column(
        'grievances',
        sa.Column(
            'category',
            sa.String(100),
            nullable=True,
            comment='Category string for resolution template matching'
        )
    )

    # Add index for category lookups
    op.create_index(
        'idx_grievances_category',
        'grievances',
        ['category'],
        postgresql_where=sa.text("deleted_at IS NULL")
    )


def downgrade() -> None:
    """Remove grievance fields."""
    op.drop_index('idx_grievances_category', table_name='grievances')
    op.drop_column('grievances', 'category')
    op.drop_column('grievances', 'contact_attempts')
    op.drop_column('grievances', 'officer_notes')
