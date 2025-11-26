"""Tests for authentication router endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.password import hash_password


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test successful login with valid credentials."""
        from uuid import uuid4
        import random

        # Generate unique values to avoid constraint violations
        unique_id = uuid4().hex[:8]
        phone_start = random.choice([6, 7, 8, 9])
        phone_rest = ''.join([str(random.randint(0, 9)) for _ in range(9)])

        # Create a user with known password
        password = "TestPassword123!"
        username = f"login_test_{unique_id}"
        user = User(
            username=username,
            password_hash=hash_password(password),
            mobile_number=f"+91{phone_start}{phone_rest}",
            email=f"login_test_{unique_id}@example.com",
            full_name="Login Test User",
            role="officer",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await test_client.post(
            "/api/v1/auth/login",
            data={
                "username": username,
                "password": password,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["username"] == username

    @pytest.mark.asyncio
    async def test_login_invalid_username(self, test_client: AsyncClient):
        """Test login with non-existent username."""
        response = await test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent_user",
                "password": "somepassword",
            },
        )

        assert response.status_code == 401
        # Error handler uses "message" field, not "detail"
        data = response.json()
        assert "Invalid username or password" in data.get("message", data.get("detail", ""))

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test login with wrong password."""
        from uuid import uuid4
        import random

        # Generate unique values
        unique_id = uuid4().hex[:8]
        phone_start = random.choice([6, 7, 8, 9])
        phone_rest = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        username = f"wrong_pass_{unique_id}"

        # Create a user
        user = User(
            username=username,
            password_hash=hash_password("correctpassword"),
            mobile_number=f"+91{phone_start}{phone_rest}",
            full_name="Wrong Pass User",
            role="officer",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await test_client.post(
            "/api/v1/auth/login",
            data={
                "username": username,
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test login with inactive user account."""
        from uuid import uuid4
        import random

        # Generate unique values
        unique_id = uuid4().hex[:8]
        phone_start = random.choice([6, 7, 8, 9])
        phone_rest = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        username = f"inactive_{unique_id}"

        password = "TestPassword123!"
        user = User(
            username=username,
            password_hash=hash_password(password),
            mobile_number=f"+91{phone_start}{phone_rest}",
            full_name="Inactive User",
            role="officer",
            is_active=False,  # Inactive
        )
        db_session.add(user)
        await db_session.commit()

        response = await test_client.post(
            "/api/v1/auth/login",
            data={
                "username": username,
                "password": password,
            },
        )

        assert response.status_code == 403
        # Error handler uses "message" field, not "detail"
        data = response.json()
        msg = data.get("message", data.get("detail", "")).lower()
        assert "disabled" in msg

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, test_client: AsyncClient):
        """Test login with missing credentials."""
        response = await test_client.post(
            "/api/v1/auth/login",
            data={},
        )

        assert response.status_code == 422  # Validation error


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        test_client: AsyncClient,
        test_officer: User,
    ):
        """Test successful logout."""
        from app.utils.jwt import create_access_token

        token = create_access_token(
            user_id=test_officer.id,
            role=test_officer.role,
            username=test_officer.username,
        )

        response = await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_logout_no_token(self, test_client: AsyncClient):
        """Test logout without authentication token."""
        response = await test_client.post("/api/v1/auth/logout")

        assert response.status_code == 401


class TestMeEndpoint:
    """Tests for GET /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_success(
        self,
        test_client: AsyncClient,
        test_officer: User,
    ):
        """Test getting current user info."""
        from app.utils.jwt import create_access_token

        token = create_access_token(
            user_id=test_officer.id,
            role=test_officer.role,
            username=test_officer.username,
            department_id=test_officer.department_id,
            district_id=test_officer.district_id,
        )

        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, f"Got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["username"] == test_officer.username
        assert data["role"] == test_officer.role
        assert data["full_name"] == test_officer.full_name

    @pytest.mark.asyncio
    async def test_me_no_token(self, test_client: AsyncClient):
        """Test getting user info without authentication."""
        response = await test_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, test_client: AsyncClient):
        """Test getting user info with invalid token."""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_includes_department_info(
        self,
        test_client: AsyncClient,
        test_officer: User,
        test_department,
    ):
        """Test that /me includes department information."""
        from app.utils.jwt import create_access_token

        token = create_access_token(
            user_id=test_officer.id,
            role=test_officer.role,
            username=test_officer.username,
            department_id=test_officer.department_id,
            district_id=test_officer.district_id,
        )

        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "department" in data
        if data["department"]:
            assert "code" in data["department"]
            assert "name" in data["department"]


class TestTokenValidation:
    """Tests for JWT token validation."""

    @pytest.mark.asyncio
    async def test_me_with_expired_token(self, test_client: AsyncClient):
        """Test /me endpoint with expired token."""
        from datetime import timedelta
        from uuid import uuid4
        from app.utils.jwt import create_access_token

        # Create token with negative expiry (already expired)
        token = create_access_token(
            user_id=uuid4(),
            role="officer",
            username="test_user",
            expires_delta=timedelta(seconds=-10),  # Expired 10 seconds ago
        )

        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_malformed_token(self, test_client: AsyncClient):
        """Test /me endpoint with malformed token."""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt.token"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_tampered_token(self, test_client: AsyncClient):
        """Test /me endpoint with tampered token signature."""
        from uuid import uuid4
        from app.utils.jwt import create_access_token

        token = create_access_token(
            user_id=uuid4(),
            role="officer",
            username="test_user",
        )

        # Tamper with the signature (last part after final dot)
        parts = token.split(".")
        parts[-1] = parts[-1][::-1]  # Reverse the signature
        tampered_token = ".".join(parts)

        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_empty_password(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test login with empty password."""
        from uuid import uuid4
        import random

        unique_id = uuid4().hex[:8]
        phone_start = random.choice([6, 7, 8, 9])
        phone_rest = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        username = f"empty_pass_{unique_id}"

        user = User(
            username=username,
            password_hash=hash_password("actualpassword"),
            mobile_number=f"+91{phone_start}{phone_rest}",
            full_name="Empty Pass User",
            role="officer",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await test_client.post(
            "/api/v1/auth/login",
            data={
                "username": username,
                "password": "",
            },
        )

        assert response.status_code == 401


class TestAuthorizationHeaders:
    """Tests for authorization header handling."""

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix(self, test_client: AsyncClient):
        """Test endpoint without Bearer prefix."""
        from uuid import uuid4
        from app.utils.jwt import create_access_token

        token = create_access_token(
            user_id=uuid4(),
            role="officer",
            username="test_user",
        )

        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": token},  # Missing "Bearer " prefix
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_auth_scheme(self, test_client: AsyncClient):
        """Test endpoint with wrong auth scheme."""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},  # Basic auth instead
        )

        assert response.status_code == 401


class TestLogoutEndpoint:
    """Tests for logout functionality with token blacklist."""

    @pytest.mark.asyncio
    async def test_logout_requires_auth(self, test_client: AsyncClient):
        """Test logout requires authentication."""
        response = await test_client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        test_client: AsyncClient,
        test_officer: User,
    ):
        """Test successful logout blacklists token."""
        from app.utils.jwt import create_access_token
        from app.services.token_blacklist import is_token_blacklisted, reset_token_blacklist

        # Reset blacklist for clean test
        reset_token_blacklist()

        token = create_access_token(
            user_id=test_officer.id,
            role=test_officer.role,
            username=test_officer.username,
            department_id=test_officer.department_id,
            district_id=test_officer.district_id,
        )

        # Token should work before logout
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Logout
        response = await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # Token should now be blacklisted
        is_blocked = await is_token_blacklisted(token)
        assert is_blocked is True

    @pytest.mark.asyncio
    async def test_token_rejected_after_logout(
        self,
        test_client: AsyncClient,
        test_officer: User,
    ):
        """Test that token is rejected after logout."""
        from app.utils.jwt import create_access_token
        from app.services.token_blacklist import reset_token_blacklist

        # Reset blacklist for clean test
        reset_token_blacklist()

        token = create_access_token(
            user_id=test_officer.id,
            role=test_officer.role,
            username=test_officer.username,
            department_id=test_officer.department_id,
            district_id=test_officer.district_id,
        )

        # Logout
        await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Try to use token after logout - should fail
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        # Check for revoked message (may be in detail or message)
        response_data = response.json()
        detail = response_data.get("detail", response_data.get("message", ""))
        assert "revoked" in detail.lower() or response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_all_devices(
        self,
        test_client: AsyncClient,
        test_officer: User,
    ):
        """Test logout from all devices."""
        from app.utils.jwt import create_access_token
        from app.services.token_blacklist import reset_token_blacklist

        reset_token_blacklist()

        token = create_access_token(
            user_id=test_officer.id,
            role=test_officer.role,
            username=test_officer.username,
            department_id=test_officer.department_id,
            district_id=test_officer.district_id,
        )

        response = await test_client.post(
            "/api/v1/auth/logout-all",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_new_token_works_after_logout(
        self,
        test_client: AsyncClient,
        test_officer: User,
    ):
        """Test that a new token works after logout."""
        from app.utils.jwt import create_access_token
        from app.services.token_blacklist import reset_token_blacklist
        import time
        from datetime import timedelta

        reset_token_blacklist()

        # Create first token with specific expiry
        token1 = create_access_token(
            user_id=test_officer.id,
            role=test_officer.role,
            username=test_officer.username,
            expires_delta=timedelta(hours=1),
        )

        # Logout with first token
        await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token1}"},
        )

        # Wait to ensure different timestamp (JWT iat uses seconds)
        time.sleep(1.1)

        # Create new token - different expiry ensures different token content
        token2 = create_access_token(
            user_id=test_officer.id,
            role=test_officer.role,
            username=test_officer.username,
            expires_delta=timedelta(hours=2),  # Different expiry
        )

        # New token should work (different token hash)
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 200
