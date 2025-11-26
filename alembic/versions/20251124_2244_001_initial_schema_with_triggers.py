"""Initial schema with updated_at triggers and pgcrypto

Revision ID: 001
Revises:
Create Date: 2025-11-24 22:44:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables, triggers, and constraints."""

    # ============================================
    # PHASE 1: ENABLE REQUIRED EXTENSIONS
    # ============================================
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ============================================
    # PHASE 2: CREATE TABLES
    # ============================================

    # Districts table
    op.create_table(
        'districts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('district_code', sa.String(10), unique=True, nullable=False),
        sa.Column('district_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_districts_district_code', 'districts', ['district_code'])

    # Departments table
    op.create_table(
        'departments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('dept_code', sa.String(20), unique=True, nullable=False),
        sa.Column('dept_name', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_departments_dept_code', 'departments', ['dept_code'])

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('mobile_number', sa.String(15), unique=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='citizen'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_mobile_number', 'users', ['mobile_number'])
    op.create_index('ix_users_email', 'users', ['email'])

    # Grievances table
    op.create_table(
        'grievances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('grievance_id', sa.String(50), unique=True, nullable=False),
        sa.Column('citizen_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('district_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('districts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('department_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('departments.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='submitted'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_grievances_grievance_id', 'grievances', ['grievance_id'])
    op.create_index('ix_grievances_citizen_id', 'grievances', ['citizen_id'])
    op.create_index('ix_grievances_district_id', 'grievances', ['district_id'])
    op.create_index('ix_grievances_department_id', 'grievances', ['department_id'])
    op.create_index('ix_grievances_status', 'grievances', ['status'])

    # Attachments table
    op.create_table(
        'attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('grievance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grievances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_attachments_grievance_id', 'attachments', ['grievance_id'])

    # Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('grievance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grievances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('details', sa.Text, nullable=False),
        sa.Column('previous_hash', sa.String(64), nullable=True),
        sa.Column('current_hash', sa.String(64), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_logs_grievance_id', 'audit_logs', ['grievance_id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_current_hash', 'audit_logs', ['current_hash'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])

    # Verifications table
    op.create_table(
        'verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('grievance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grievances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('verification_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('verification_details', sa.Text, nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_verifications_grievance_id', 'verifications', ['grievance_id'])
    op.create_index('ix_verifications_verification_type', 'verifications', ['verification_type'])
    op.create_index('ix_verifications_status', 'verifications', ['status'])

    # ============================================
    # PHASE 3: CREATE UPDATED_AT TRIGGER FUNCTION
    # ============================================
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP AT TIME ZONE 'UTC';
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # ============================================
    # PHASE 4: APPLY TRIGGERS TO ALL TABLES
    # ============================================
    tables_with_timestamps = [
        'districts', 'departments', 'users', 'grievances',
        'attachments', 'audit_logs', 'verifications'
    ]

    for table in tables_with_timestamps:
        op.execute(f"""
        CREATE TRIGGER update_{table}_updated_at
        BEFORE UPDATE ON {table}
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop all tables and triggers."""

    # Drop triggers first
    tables_with_timestamps = [
        'districts', 'departments', 'users', 'grievances',
        'attachments', 'audit_logs', 'verifications'
    ]

    for table in tables_with_timestamps:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")

    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables (in reverse order of dependencies)
    op.drop_table('verifications')
    op.drop_table('audit_logs')
    op.drop_table('attachments')
    op.drop_table('grievances')
    op.drop_table('users')
    op.drop_table('departments')
    op.drop_table('districts')

    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
