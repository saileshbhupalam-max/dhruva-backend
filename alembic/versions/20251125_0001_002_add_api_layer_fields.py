"""Add API layer fields for authentication, departments, grievances

Revision ID: 002
Revises: 001
Create Date: 2025-11-25 00:01:00

This migration adds:
- Users: username, password_hash, is_active, department_id, district_id, last_login_at
- Departments: name_telugu, description, sla_days
- Grievances: Many new fields for citizen info, content, SLA tracking, resolution, location
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new columns and constraints for API layer."""

    # ============================================
    # PHASE 1: UPDATE USERS TABLE
    # ============================================

    # Add new authentication columns
    op.add_column('users', sa.Column('username', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('department_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('users', sa.Column('district_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))

    # Add foreign keys
    op.create_foreign_key(
        'fk_users_department_id',
        'users', 'departments',
        ['department_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_users_district_id',
        'users', 'districts',
        ['district_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add indexes for new columns
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_department_id', 'users', ['department_id'])
    op.create_index('ix_users_district_id', 'users', ['district_id'])
    op.create_index('ix_users_role', 'users', ['role'])

    # Add composite indexes for common queries
    op.create_index('idx_users_role_mobile', 'users', ['role', 'mobile_number'])
    op.create_index('idx_users_email_role', 'users', ['email', 'role'])
    op.create_index('idx_users_role_department', 'users', ['role', 'department_id'])
    op.create_index('idx_users_role_district', 'users', ['role', 'district_id'])
    op.create_index('idx_users_active_role', 'users', ['is_active', 'role'])

    # ============================================
    # PHASE 2: UPDATE DEPARTMENTS TABLE
    # ============================================

    op.add_column('departments', sa.Column('name_telugu', sa.String(200), nullable=True))
    op.add_column('departments', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('departments', sa.Column('sla_days', sa.Integer(), nullable=False, server_default='7'))

    # ============================================
    # PHASE 3: UPDATE GRIEVANCES TABLE
    # ============================================

    # Rename 'description' to 'grievance_text' for clarity
    op.alter_column('grievances', 'description', new_column_name='grievance_text')

    # Add citizen information columns
    op.add_column('grievances', sa.Column('citizen_name', sa.String(200), nullable=True))
    op.add_column('grievances', sa.Column('citizen_phone', sa.String(15), nullable=True))
    op.add_column('grievances', sa.Column('citizen_email', sa.String(255), nullable=True))
    op.add_column('grievances', sa.Column('citizen_address', sa.Text(), nullable=True))

    # Add content columns
    op.add_column('grievances', sa.Column('grievance_text_original', sa.Text(), nullable=True))

    # Add language and channel columns
    op.add_column('grievances', sa.Column('language', sa.String(5), nullable=False, server_default='te'))
    op.add_column('grievances', sa.Column('channel', sa.String(20), nullable=False, server_default='web'))

    # Add officer assignment columns
    op.add_column('grievances', sa.Column('assigned_officer_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('grievances', sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True))

    # Add SLA tracking columns
    op.add_column('grievances', sa.Column('sla_days', sa.Integer(), nullable=False, server_default='7'))
    op.add_column('grievances', sa.Column('due_date', sa.DateTime(timezone=True), nullable=True))

    # Add resolution columns
    op.add_column('grievances', sa.Column('resolution_text', sa.Text(), nullable=True))
    op.add_column('grievances', sa.Column('resolution_notes', sa.Text(), nullable=True))
    op.add_column('grievances', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('grievances', sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True))

    # Add location columns
    op.add_column('grievances', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('grievances', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('grievances', sa.Column('location_accuracy', sa.Float(), nullable=True))

    # Add extra_data column (JSONB)
    op.add_column('grievances', sa.Column('extra_data', postgresql.JSONB(), nullable=True))

    # Allow department_id to be nullable (until NLP classification)
    op.alter_column('grievances', 'department_id', nullable=True)

    # Allow citizen_id to be nullable (for anonymous submissions)
    op.alter_column('grievances', 'citizen_id', nullable=True)

    # Change default priority from 'medium' to 'normal'
    op.alter_column('grievances', 'priority', server_default='normal')

    # Add foreign key for assigned_officer_id
    op.create_foreign_key(
        'fk_grievances_assigned_officer_id',
        'grievances', 'users',
        ['assigned_officer_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add indexes for new columns
    op.create_index('ix_grievances_citizen_phone', 'grievances', ['citizen_phone'])
    op.create_index('ix_grievances_assigned_officer_id', 'grievances', ['assigned_officer_id'])
    op.create_index('ix_grievances_language', 'grievances', ['language'])
    op.create_index('ix_grievances_channel', 'grievances', ['channel'])
    op.create_index('ix_grievances_priority', 'grievances', ['priority'])

    # Add composite indexes
    op.execute("""
        CREATE INDEX idx_grievances_district_status
        ON grievances (district_id, status)
        WHERE deleted_at IS NULL
    """)
    op.create_index('idx_grievances_department_created', 'grievances', ['department_id', 'created_at'])
    op.execute("""
        CREATE INDEX idx_grievances_officer_status
        ON grievances (assigned_officer_id, status)
        WHERE deleted_at IS NULL
    """)
    op.create_index('idx_grievances_citizen_phone_created', 'grievances', ['citizen_phone', 'created_at'])
    op.execute("""
        CREATE INDEX idx_grievances_status_due_date
        ON grievances (status, due_date)
        WHERE deleted_at IS NULL
    """)
    op.create_index('idx_grievances_channel_language', 'grievances', ['channel', 'language'])

    # Add check constraints
    op.execute("""
        ALTER TABLE grievances
        ADD CONSTRAINT check_resolved_at_valid
        CHECK (resolved_at IS NULL OR resolved_at >= submitted_at)
    """)
    op.execute("""
        ALTER TABLE grievances
        ADD CONSTRAINT check_verified_at_valid
        CHECK (verified_at IS NULL OR verified_at >= resolved_at)
    """)
    op.execute("""
        ALTER TABLE grievances
        ADD CONSTRAINT check_closed_at_valid
        CHECK (closed_at IS NULL OR closed_at >= submitted_at)
    """)
    op.execute("""
        ALTER TABLE grievances
        ADD CONSTRAINT check_status_valid
        CHECK (status IN ('submitted', 'assigned', 'in_progress', 'resolved', 'verified', 'closed', 'rejected'))
    """)
    op.execute("""
        ALTER TABLE grievances
        ADD CONSTRAINT check_priority_valid
        CHECK (priority IN ('critical', 'high', 'normal'))
    """)
    op.execute("""
        ALTER TABLE grievances
        ADD CONSTRAINT check_language_valid
        CHECK (language IN ('te', 'en', 'hi'))
    """)
    op.execute("""
        ALTER TABLE grievances
        ADD CONSTRAINT check_channel_valid
        CHECK (channel IN ('web', 'mobile', 'whatsapp', 'sms', 'voice'))
    """)
    op.execute("""
        ALTER TABLE grievances
        ADD CONSTRAINT check_latitude_valid
        CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90))
    """)
    op.execute("""
        ALTER TABLE grievances
        ADD CONSTRAINT check_longitude_valid
        CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180))
    """)

    # ============================================
    # PHASE 4: UPDATE ATTACHMENTS TABLE
    # ============================================

    # Add file_hash column for deduplication
    op.add_column('attachments', sa.Column('file_hash', sa.String(64), nullable=True))
    op.create_index('ix_attachments_file_hash', 'attachments', ['file_hash'])

    # ============================================
    # PHASE 5: BACKFILL DATA
    # ============================================

    # Set due_date for existing grievances (7 days after submission)
    op.execute("""
        UPDATE grievances
        SET due_date = submitted_at + INTERVAL '7 days'
        WHERE due_date IS NULL
    """)

    # Make due_date NOT NULL after backfill
    op.alter_column('grievances', 'due_date', nullable=False)

    # Backfill citizen_name from users table
    op.execute("""
        UPDATE grievances g
        SET citizen_name = u.full_name,
            citizen_phone = u.mobile_number,
            citizen_email = u.email
        FROM users u
        WHERE g.citizen_id = u.id
        AND g.citizen_name IS NULL
    """)

    # For any remaining nulls, set defaults
    op.execute("""
        UPDATE grievances
        SET citizen_name = 'Unknown',
            citizen_phone = '0000000000',
            citizen_address = 'Not provided'
        WHERE citizen_name IS NULL
    """)

    # Make citizen columns NOT NULL after backfill
    op.alter_column('grievances', 'citizen_name', nullable=False)
    op.alter_column('grievances', 'citizen_phone', nullable=False)
    op.alter_column('grievances', 'citizen_address', nullable=False)


def downgrade() -> None:
    """Remove API layer fields."""

    # ============================================
    # PHASE 1: REMOVE GRIEVANCES CHANGES
    # ============================================

    # Drop check constraints
    op.execute("ALTER TABLE grievances DROP CONSTRAINT IF EXISTS check_resolved_at_valid")
    op.execute("ALTER TABLE grievances DROP CONSTRAINT IF EXISTS check_verified_at_valid")
    op.execute("ALTER TABLE grievances DROP CONSTRAINT IF EXISTS check_closed_at_valid")
    op.execute("ALTER TABLE grievances DROP CONSTRAINT IF EXISTS check_status_valid")
    op.execute("ALTER TABLE grievances DROP CONSTRAINT IF EXISTS check_priority_valid")
    op.execute("ALTER TABLE grievances DROP CONSTRAINT IF EXISTS check_language_valid")
    op.execute("ALTER TABLE grievances DROP CONSTRAINT IF EXISTS check_channel_valid")
    op.execute("ALTER TABLE grievances DROP CONSTRAINT IF EXISTS check_latitude_valid")
    op.execute("ALTER TABLE grievances DROP CONSTRAINT IF EXISTS check_longitude_valid")

    # Drop composite indexes
    op.drop_index('idx_grievances_channel_language', table_name='grievances')
    op.drop_index('idx_grievances_status_due_date', table_name='grievances')
    op.drop_index('idx_grievances_citizen_phone_created', table_name='grievances')
    op.drop_index('idx_grievances_officer_status', table_name='grievances')
    op.drop_index('idx_grievances_department_created', table_name='grievances')
    op.drop_index('idx_grievances_district_status', table_name='grievances')

    # Drop indexes
    op.drop_index('ix_grievances_priority', table_name='grievances')
    op.drop_index('ix_grievances_channel', table_name='grievances')
    op.drop_index('ix_grievances_language', table_name='grievances')
    op.drop_index('ix_grievances_assigned_officer_id', table_name='grievances')
    op.drop_index('ix_grievances_citizen_phone', table_name='grievances')

    # Drop foreign key
    op.drop_constraint('fk_grievances_assigned_officer_id', 'grievances', type_='foreignkey')

    # Drop columns
    op.drop_column('grievances', 'extra_data')
    op.drop_column('grievances', 'location_accuracy')
    op.drop_column('grievances', 'longitude')
    op.drop_column('grievances', 'latitude')
    op.drop_column('grievances', 'closed_at')
    op.drop_column('grievances', 'verified_at')
    op.drop_column('grievances', 'resolution_notes')
    op.drop_column('grievances', 'resolution_text')
    op.drop_column('grievances', 'due_date')
    op.drop_column('grievances', 'sla_days')
    op.drop_column('grievances', 'assigned_at')
    op.drop_column('grievances', 'assigned_officer_id')
    op.drop_column('grievances', 'channel')
    op.drop_column('grievances', 'language')
    op.drop_column('grievances', 'grievance_text_original')
    op.drop_column('grievances', 'citizen_address')
    op.drop_column('grievances', 'citizen_email')
    op.drop_column('grievances', 'citizen_phone')
    op.drop_column('grievances', 'citizen_name')

    # Rename grievance_text back to description
    op.alter_column('grievances', 'grievance_text', new_column_name='description')

    # Restore NOT NULL constraints
    op.alter_column('grievances', 'department_id', nullable=False)
    op.alter_column('grievances', 'citizen_id', nullable=False)

    # Restore default priority
    op.alter_column('grievances', 'priority', server_default='medium')

    # ============================================
    # PHASE 2: REMOVE DEPARTMENTS CHANGES
    # ============================================

    op.drop_column('departments', 'sla_days')
    op.drop_column('departments', 'description')
    op.drop_column('departments', 'name_telugu')

    # ============================================
    # PHASE 3: REMOVE USERS CHANGES
    # ============================================

    # Drop composite indexes
    op.drop_index('idx_users_active_role', table_name='users')
    op.drop_index('idx_users_role_district', table_name='users')
    op.drop_index('idx_users_role_department', table_name='users')
    op.drop_index('idx_users_email_role', table_name='users')
    op.drop_index('idx_users_role_mobile', table_name='users')

    # Drop indexes
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_district_id', table_name='users')
    op.drop_index('ix_users_department_id', table_name='users')
    op.drop_index('ix_users_username', table_name='users')

    # Drop foreign keys
    op.drop_constraint('fk_users_district_id', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_department_id', 'users', type_='foreignkey')

    # Drop columns
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'district_id')
    op.drop_column('users', 'department_id')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'username')

    # ============================================
    # PHASE 4: REMOVE ATTACHMENTS CHANGES
    # ============================================

    op.drop_index('ix_attachments_file_hash', table_name='attachments')
    op.drop_column('attachments', 'file_hash')
