"""Add citizen empowerment tables

Revision ID: 3c_empowerment_001
Revises: 3b_resolution_001
Create Date: 2025-11-25 21:00:00.000000+05:30

This migration creates the core tables for Task 3C Citizen Empowerment System:
- rights_knowledge_base: Stores rights information by department/category/level
- citizen_empowerment_preferences: Citizen opt-in/out preferences
- empowerment_interactions: Log of all empowerment interactions
- proactive_trigger_config: Configuration for proactive triggers

Migration chain:
dade9ecbca0b -> 3b_grievance_fields -> 3a_empathy_001 -> 3b_resolution_001 -> 3c_empowerment_001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3c_empowerment_001'
down_revision: Union[str, None] = '3b_resolution_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Citizen Empowerment tables."""

    # Table 1: Rights Knowledge Base
    op.create_table(
        'rights_knowledge_base',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('department', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('disclosure_level', sa.Integer(), nullable=False),
        sa.Column('right_title', sa.String(200), nullable=False),
        sa.Column('right_description_en', sa.Text(), nullable=False),
        sa.Column('right_description_te', sa.Text(), nullable=False),
        sa.Column('legal_reference', sa.String(200), nullable=True),
        sa.Column('helpful_contact', sa.String(100), nullable=True),
        sa.Column('priority_order', sa.Integer(), server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('disclosure_level >= 1 AND disclosure_level <= 4', name='ck_rights_disclosure_level')
    )
    op.create_index(
        'idx_rights_lookup',
        'rights_knowledge_base',
        ['department', 'category', 'disclosure_level'],
        postgresql_where=sa.text('is_active = TRUE')
    )

    # Table 2: Citizen Empowerment Preferences
    op.create_table(
        'citizen_empowerment_preferences',
        sa.Column('citizen_phone', sa.String(15), primary_key=True),
        sa.Column('opted_in', sa.Boolean(), server_default='false'),
        sa.Column('opted_out', sa.Boolean(), server_default='false'),
        sa.Column('ask_later', sa.Boolean(), server_default='false'),
        sa.Column('ask_later_count', sa.Integer(), server_default='0'),
        sa.Column('last_ask_later_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('preferred_language', sa.String(5), server_default='te'),
        sa.Column('max_disclosure_level', sa.Integer(), server_default='1'),
        sa.Column('opted_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_info_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_info_requests', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # Table 3: Empowerment Interactions Log
    op.create_table(
        'empowerment_interactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('grievance_id', sa.String(50), nullable=True),
        sa.Column('citizen_phone', sa.String(15), nullable=False),
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('disclosure_level', sa.Integer(), nullable=True),
        sa.Column('rights_sent', postgresql.JSONB(), nullable=True),
        sa.Column('trigger_reason', sa.String(100), nullable=True),
        sa.Column('citizen_response', sa.String(50), nullable=True),
        sa.Column('message_sent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ['grievance_id'],
            ['grievances.grievance_id'],
            ondelete='SET NULL',
            name='fk_empowerment_interactions_grievance'
        ),
        sa.CheckConstraint(
            "interaction_type IN ('OPT_IN_PROMPT', 'OPT_IN_YES', 'OPT_IN_NO', 'OPT_IN_LATER', "
            "'RIGHTS_SENT', 'LEVEL_UP_REQUEST', 'PROACTIVE_TRIGGER')",
            name='ck_interaction_type'
        )
    )
    op.create_index('idx_interactions_phone', 'empowerment_interactions', ['citizen_phone'])
    op.create_index('idx_interactions_grievance', 'empowerment_interactions', ['grievance_id'])
    op.create_index('idx_interactions_type', 'empowerment_interactions', ['interaction_type'])

    # Table 4: Proactive Trigger Configuration
    op.create_table(
        'proactive_trigger_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('trigger_type', sa.String(50), unique=True, nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('threshold_value', sa.Integer(), nullable=False),
        sa.Column('message_template_en', sa.Text(), nullable=False),
        sa.Column('message_template_te', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )


def downgrade() -> None:
    """Drop Citizen Empowerment tables."""
    op.drop_table('proactive_trigger_config')
    op.drop_table('empowerment_interactions')
    op.drop_table('citizen_empowerment_preferences')
    op.drop_table('rights_knowledge_base')
