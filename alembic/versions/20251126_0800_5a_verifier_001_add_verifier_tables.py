"""Add verifier profiles and activities tables

Revision ID: 5a_verifier_001
Revises: 4_dashboard_001
Create Date: 2025-11-26 08:00:00.000000

Tables Created:
- verifier_profiles: Gamification profile for community verifiers
- verifier_activities: Log of verification actions for streak tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = '5a_verifier_001'
down_revision = '4_dashboard_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Table 1: Verifier Profiles (gamification)
    op.create_table(
        'verifier_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('phone', sa.String(15), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('district_id', UUID(as_uuid=True), sa.ForeignKey('districts.id'), nullable=True),
        sa.Column('total_points', sa.Integer(), default=0, nullable=False),
        sa.Column('total_verifications', sa.Integer(), default=0, nullable=False),
        sa.Column('verified_count', sa.Integer(), default=0, nullable=False),
        sa.Column('disputed_count', sa.Integer(), default=0, nullable=False),
        sa.Column('inconclusive_count', sa.Integer(), default=0, nullable=False),
        sa.Column('accuracy_rate', sa.Numeric(5, 2), default=0.0, nullable=False),
        sa.Column('current_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('longest_streak', sa.Integer(), default=0, nullable=False),
        sa.Column('last_verification_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('badge', sa.String(20), default='BRONZE', nullable=False),
        sa.Column('badges_json', JSONB, default=[], nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("badge IN ('BRONZE', 'SILVER', 'GOLD', 'CHAMPION')", name='ck_verifier_badge'),
    )

    # Indexes for verifier_profiles
    op.create_index('idx_verifier_phone', 'verifier_profiles', ['phone'])
    op.create_index('idx_verifier_points', 'verifier_profiles', ['total_points'], postgresql_ops={'total_points': 'DESC'})
    op.create_index('idx_verifier_district', 'verifier_profiles', ['district_id'])

    # Table 2: Verifier Activities (streak tracking)
    op.create_table(
        'verifier_activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('verifier_id', sa.Integer(), sa.ForeignKey('verifier_profiles.id'), nullable=False),
        sa.Column('grievance_id', sa.String(30), nullable=False),
        sa.Column('result', sa.String(20), nullable=False),
        sa.Column('points_earned', sa.Integer(), nullable=False),
        sa.Column('bonus_applied', sa.Boolean(), default=False, nullable=False),
        sa.Column('location_lat', sa.Numeric(10, 8), nullable=True),
        sa.Column('location_lng', sa.Numeric(11, 8), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("result IN ('VERIFIED', 'DISPUTED', 'INCONCLUSIVE')", name='ck_activity_result'),
    )

    # Indexes for verifier_activities
    op.create_index('idx_activity_verifier', 'verifier_activities', ['verifier_id'])
    op.create_index('idx_activity_date', 'verifier_activities', ['verified_at'])
    op.create_index('idx_activity_grievance', 'verifier_activities', ['grievance_id'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_activity_grievance')
    op.drop_index('idx_activity_date')
    op.drop_index('idx_activity_verifier')
    op.drop_table('verifier_activities')

    op.drop_index('idx_verifier_district')
    op.drop_index('idx_verifier_points')
    op.drop_index('idx_verifier_phone')
    op.drop_table('verifier_profiles')
