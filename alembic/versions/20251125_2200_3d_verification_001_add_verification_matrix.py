"""Add verification matrix tables

Revision ID: 3d_verification_001
Revises: 3c_empowerment_001
Create Date: 2025-11-25 22:00:00.000000

NOTE: This migration was already applied to the database.
This file is a stub to maintain the migration chain.
"""
from alembic import op
import sqlalchemy as sa

revision = '3d_verification_001'
down_revision = '3c_empowerment_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables already exist in database - this is a stub migration
    # Original tables created:
    # - verification_requests
    # - verification_responses
    # - verification_templates
    # - photo_analysis_results
    pass


def downgrade() -> None:
    # Stub - tables managed externally
    pass
