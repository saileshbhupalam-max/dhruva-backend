"""Pytest configuration and shared fixtures for PGRS API tests."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.base import Base
from app.models.department import Department
from app.models.district import District
from app.models.user import User


# Test database URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for each test with proper isolation.

    Uses a transaction-based approach:
    1. Start a transaction on a connection
    2. Bind session to that connection
    3. Fixtures and tests use the session normally (commits work within transaction)
    4. Rollback the transaction at the end to undo ALL changes

    This ensures complete test isolation - no data persists between tests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables (idempotent)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create a connection that will hold our transaction
    connection = await engine.connect()

    # Start a transaction that we will rollback at the end
    transaction = await connection.begin()

    # Create session bound to this connection
    # All operations go through this connection's transaction
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        # Close session first
        await session.close()

        # Rollback the transaction - this undoes ALL changes made during test
        if transaction.is_active:
            await transaction.rollback()

        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override."""
    from app.main import app
    from app.database.connection import get_db_session

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# Sample data fixtures


@pytest.fixture
def sample_district_data() -> dict[str, Any]:
    """Sample district data for testing.

    District code must be exactly 2 digits to match schema pattern ^[0-9]{2}$.
    We use random 2-digit numbers (10-99) to ensure uniqueness across tests.
    """
    import random
    # Generate random 2-digit code (10-99) for uniqueness
    district_code = f"{random.randint(10, 99):02d}"
    return {
        "district_code": district_code,
        "district_name": f"Test District {district_code}",
    }


@pytest.fixture
def sample_department_data() -> dict[str, Any]:
    """Sample department data for testing."""
    return {
        "dept_code": f"TD{uuid4().hex[:4].upper()}",
        "dept_name": "Test Department",
        "name_telugu": "పరీక్ష శాఖ",
        "description": "Test department for unit tests",
        "sla_days": 7,
    }


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user data for testing."""
    # Phone must match pattern ^\+91[6-9]\d{9}$
    import random
    phone_start = random.choice([6, 7, 8, 9])
    phone_rest = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    return {
        "username": f"testuser_{uuid4().hex[:8]}",
        "mobile_number": f"+91{phone_start}{phone_rest}",
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "full_name": "Test User",
        "role": "citizen",
        "is_active": True,
    }


@pytest.fixture
def sample_officer_data() -> dict[str, Any]:
    """Sample officer data for testing."""
    # Phone must match pattern ^\+91[6-9]\d{9}$
    import random
    phone_start = random.choice([6, 7, 8, 9])
    phone_rest = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    return {
        "username": f"officer_{uuid4().hex[:8]}",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.VQ7T8z9c/q8xE6O",  # "password123"
        "mobile_number": f"+91{phone_start}{phone_rest}",
        "email": f"officer_{uuid4().hex[:8]}@gov.in",
        "full_name": "Test Officer",
        "role": "officer",
        "is_active": True,
    }


@pytest.fixture
def sample_grievance_data() -> dict[str, Any]:
    """Sample grievance data for testing."""
    from datetime import datetime, timedelta, timezone
    return {
        "grievance_id": f"PGRS-2025-01-{str(uuid4().int)[:5]}",
        "citizen_name": "Test Citizen",
        "citizen_phone": "+919876543210",
        "citizen_email": "citizen@example.com",
        "citizen_address": "123 Test Street, Test City, AP 500001",
        "subject": "Test Grievance Subject",
        "grievance_text": "This is a detailed test grievance description that is at least 20 characters long.",
        "language": "en",
        "channel": "web",
        "status": "submitted",
        "priority": "normal",
        "sla_days": 7,
        "due_date": datetime.now(timezone.utc) + timedelta(days=7),
    }


@pytest_asyncio.fixture
async def test_district(db_session: AsyncSession, sample_district_data: dict) -> District:
    """Create a test district in the database."""
    district = District(**sample_district_data)
    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)
    return district


@pytest_asyncio.fixture
async def test_department(db_session: AsyncSession, sample_department_data: dict) -> Department:
    """Create a test department in the database."""
    department = Department(**sample_department_data)
    db_session.add(department)
    await db_session.commit()
    await db_session.refresh(department)
    return department


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, sample_user_data: dict) -> User:
    """Create a test user in the database."""
    user = User(**sample_user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_officer(
    db_session: AsyncSession,
    sample_officer_data: dict,
    test_department: Department,
    test_district: District,
) -> User:
    """Create a test officer in the database."""
    officer = User(
        **sample_officer_data,
        department_id=test_department.id,
        district_id=test_district.id,
    )
    db_session.add(officer)
    await db_session.commit()
    await db_session.refresh(officer)
    return officer


# JWT token fixtures


@pytest.fixture
def auth_headers(test_officer: User) -> dict[str, str]:
    """Generate auth headers with valid JWT token."""
    from app.utils.jwt import create_access_token

    token = create_access_token(
        user_id=test_officer.id,
        role=test_officer.role,
        username=test_officer.username,
        department_id=test_officer.department_id,
        district_id=test_officer.district_id,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers() -> dict[str, str]:
    """Generate auth headers for admin user."""
    from app.utils.jwt import create_access_token

    token = create_access_token(
        user_id=uuid4(),
        role="admin",
        username="admin_test",
        department_id=None,
        district_id=None,
    )
    return {"Authorization": f"Bearer {token}"}
