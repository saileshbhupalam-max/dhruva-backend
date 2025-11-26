"""Add Smart Resolution Engine tables

Revision ID: 3b_resolution_001
Revises: 3a_empathy_001
Create Date: 2025-11-25 20:00:00.000000+05:30

This migration creates the core tables for Task 3B Smart Resolution Engine:
- root_cause_analysis: Stores root cause detection results
- resolution_templates: Pre-built resolution workflows
- intervention_questions: Clarification questions by root cause
- clarification_responses: Citizen responses to questions
- template_applications: Tracks template usage and outcomes

Migration chain:
dade9ecbca0b -> 3b_grievance_fields -> 3a_empathy_001 -> 3b_resolution_001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3b_resolution_001'
down_revision: Union[str, None] = '3a_empathy_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Smart Resolution Engine tables."""

    # Create root_cause_enum type using raw SQL with IF NOT EXISTS
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'root_cause_enum') THEN
                CREATE TYPE root_cause_enum AS ENUM (
                    'WRONG_DEPARTMENT',
                    'MISSING_INFORMATION',
                    'DUPLICATE_CASE',
                    'OUTSIDE_JURISDICTION',
                    'NEEDS_FIELD_VISIT',
                    'EXTERNAL_DEPENDENCY',
                    'CITIZEN_UNREACHABLE',
                    'POLICY_LIMITATION',
                    'RESOURCE_CONSTRAINT',
                    'OFFICER_OVERLOAD'
                );
            END IF;
        END
        $$;
    """)

    # Create intervention_result_enum type using raw SQL with IF NOT EXISTS
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'intervention_result_enum') THEN
                CREATE TYPE intervention_result_enum AS ENUM (
                    'SUCCESS',
                    'PARTIAL',
                    'FAILED',
                    'PENDING'
                );
            END IF;
        END
        $$;
    """)

    # Define enum references for table columns
    root_cause_enum = postgresql.ENUM(
        'WRONG_DEPARTMENT',
        'MISSING_INFORMATION',
        'DUPLICATE_CASE',
        'OUTSIDE_JURISDICTION',
        'NEEDS_FIELD_VISIT',
        'EXTERNAL_DEPENDENCY',
        'CITIZEN_UNREACHABLE',
        'POLICY_LIMITATION',
        'RESOURCE_CONSTRAINT',
        'OFFICER_OVERLOAD',
        name='root_cause_enum',
        create_type=False
    )

    intervention_result_enum = postgresql.ENUM(
        'SUCCESS',
        'PARTIAL',
        'FAILED',
        'PENDING',
        name='intervention_result_enum',
        create_type=False
    )

    # Table 1: root_cause_analysis
    op.create_table(
        'root_cause_analysis',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('grievance_id', sa.String(50), nullable=False),
        sa.Column(
            'detected_root_cause',
            root_cause_enum,
            nullable=False
        ),
        sa.Column(
            'confidence_score',
            sa.Numeric(4, 2),
            nullable=True
        ),
        sa.Column(
            'detection_signals',
            postgresql.JSONB(),
            server_default='[]',
            nullable=False
        ),
        sa.Column('intervention_applied', sa.String(100), nullable=True),
        sa.Column(
            'intervention_result',
            intervention_result_enum,
            server_default='PENDING'
        ),
        sa.Column(
            'analyzed_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('analyzed_by', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(
            ['grievance_id'],
            ['grievances.grievance_id'],
            ondelete='CASCADE'
        ),
        sa.CheckConstraint(
            'confidence_score >= 0.00 AND confidence_score <= 1.00',
            name='ck_root_cause_confidence'
        )
    )
    op.create_index(
        'idx_root_cause_grievance',
        'root_cause_analysis',
        ['grievance_id']
    )
    op.create_index(
        'idx_root_cause_type',
        'root_cause_analysis',
        ['detected_root_cause']
    )
    op.create_index(
        'idx_root_cause_result',
        'root_cause_analysis',
        ['intervention_result']
    )

    # Table 2: resolution_templates
    op.create_table(
        'resolution_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('template_key', sa.String(100), unique=True, nullable=False),
        sa.Column('department', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('root_cause', root_cause_enum, nullable=True),
        sa.Column('template_title', sa.String(200), nullable=False),
        sa.Column('template_description', sa.Text(), nullable=False),
        sa.Column('action_steps', postgresql.JSONB(), nullable=False),
        sa.Column(
            'success_rate',
            sa.Numeric(5, 2),
            server_default='0.00'
        ),
        sa.Column('avg_resolution_hours', sa.Integer(), server_default='0'),
        sa.Column('similar_cases_resolved', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            'success_rate >= 0.00 AND success_rate <= 100.00',
            name='ck_templates_success_rate'
        )
    )
    op.create_index(
        'idx_resolution_templates_lookup',
        'resolution_templates',
        ['department', 'category', 'root_cause'],
        postgresql_where=sa.text('is_active = TRUE')
    )

    # Table 3: intervention_questions
    op.create_table(
        'intervention_questions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('root_cause', root_cause_enum, nullable=False),
        sa.Column('department', sa.String(50), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('question_text_en', sa.Text(), nullable=False),
        sa.Column('question_text_te', sa.Text(), nullable=False),
        sa.Column('question_order', sa.Integer(), server_default='1'),
        sa.Column('response_type', sa.String(30), nullable=False),
        sa.Column('response_options', postgresql.JSONB(), nullable=True),
        sa.Column('is_required', sa.Boolean(), server_default='true'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "response_type IN ('TEXT', 'SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'PHOTO', 'DATE', 'NUMBER')",
            name='ck_questions_response_type'
        )
    )
    op.create_index(
        'idx_intervention_questions_lookup',
        'intervention_questions',
        ['root_cause', 'department', 'category'],
        postgresql_where=sa.text('is_active = TRUE')
    )

    # Table 4: clarification_responses
    op.create_table(
        'clarification_responses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('grievance_id', sa.String(50), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('response_choice', postgresql.JSONB(), nullable=True),
        sa.Column('response_photo_url', sa.String(500), nullable=True),
        sa.Column('response_number', sa.Numeric(15, 2), nullable=True),
        sa.Column('response_date', sa.Date(), nullable=True),
        sa.Column(
            'responded_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ['grievance_id'],
            ['grievances.grievance_id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['question_id'],
            ['intervention_questions.id'],
            ondelete='CASCADE'
        )
    )
    op.create_index(
        'idx_clarification_grievance',
        'clarification_responses',
        ['grievance_id']
    )

    # Table 5: template_applications
    op.create_table(
        'template_applications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('grievance_id', sa.String(50), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('applied_by', sa.String(50), nullable=False),
        sa.Column(
            'applied_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
        sa.Column(
            'result',
            intervention_result_enum,
            server_default='PENDING'
        ),
        sa.Column('result_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ['grievance_id'],
            ['grievances.grievance_id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['template_id'],
            ['resolution_templates.id'],
            ondelete='CASCADE'
        )
    )
    op.create_index(
        'idx_template_app_grievance',
        'template_applications',
        ['grievance_id']
    )
    op.create_index(
        'idx_template_app_template',
        'template_applications',
        ['template_id']
    )


def downgrade() -> None:
    """Remove Smart Resolution Engine tables."""
    op.drop_table('template_applications')
    op.drop_table('clarification_responses')
    op.drop_table('intervention_questions')
    op.drop_table('resolution_templates')
    op.drop_table('root_cause_analysis')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS intervention_result_enum')
    op.execute('DROP TYPE IF EXISTS root_cause_enum')
