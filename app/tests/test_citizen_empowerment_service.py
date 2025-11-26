"""Unit tests for Citizen Empowerment Service (Task 3C)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.citizen_empowerment import (
    OptInRequest,
    OptInChoice,
    Language,
    RightInfo,
)
from app.services.citizen_empowerment_service import CitizenEmpowermentService


class TestOptInFlow:
    """Unit tests for opt-in flow."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database."""
        return CitizenEmpowermentService(mock_db)

    @pytest.mark.asyncio
    async def test_opt_in_yes_sends_rights(self, service, mock_db):
        """Test that opting in sends Level 1 rights."""
        # Arrange
        mock_pref = MagicMock()
        mock_pref.opted_in = False
        mock_pref.opted_out = False
        mock_pref.ask_later = False
        mock_pref.ask_later_count = 0
        mock_pref.max_disclosure_level = 1
        mock_pref.preferred_language = "te"
        service._get_or_create_preference = AsyncMock(return_value=mock_pref)
        service._log_interaction = AsyncMock()

        mock_grievance = MagicMock()
        mock_grievance.department = MagicMock()
        mock_grievance.department.name = "Pension"
        mock_grievance.category = "Pension Delay"
        mock_grievance.citizen_phone = "9876543210"
        service._get_grievance = AsyncMock(return_value=mock_grievance)

        mock_rights = [
            MagicMock(
                id=1,
                right_title="Test",
                right_description_te="Telugu description",
                right_description_en="English description",
                legal_reference=None,
                helpful_contact=None,
            )
        ]
        service._get_rights = AsyncMock(return_value=mock_rights)

        request = OptInRequest(
            citizen_phone="9876543210",
            grievance_id="PGRS-2025-GTR-00001",
            response=OptInChoice.YES,
            preferred_language=Language.TELUGU,
        )

        # Act
        result = await service.handle_opt_in(request)

        # Assert
        assert result.success is True
        assert result.rights_sent is True
        assert result.empowerment_response is not None
        assert mock_pref.opted_in is True

    @pytest.mark.asyncio
    async def test_opt_in_no_does_not_send_rights(self, service, mock_db):
        """Test that opting out does not send rights."""
        # Arrange
        mock_pref = MagicMock()
        mock_pref.opted_in = False
        mock_pref.opted_out = False
        mock_pref.ask_later = False
        service._get_or_create_preference = AsyncMock(return_value=mock_pref)
        service._log_interaction = AsyncMock()

        request = OptInRequest(
            citizen_phone="9876543210",
            grievance_id="PGRS-2025-GTR-00001",
            response=OptInChoice.NO,
        )

        # Act
        result = await service.handle_opt_in(request)

        # Assert
        assert result.success is True
        assert result.rights_sent is False
        assert result.empowerment_response is None
        assert mock_pref.opted_out is True

    @pytest.mark.asyncio
    async def test_opt_in_later_increments_count(self, service, mock_db):
        """Test that 'Later' response increments ask_later_count."""
        # Arrange
        mock_pref = MagicMock()
        mock_pref.opted_in = False
        mock_pref.opted_out = False
        mock_pref.ask_later = False
        mock_pref.ask_later_count = 0
        service._get_or_create_preference = AsyncMock(return_value=mock_pref)
        service._log_interaction = AsyncMock()

        request = OptInRequest(
            citizen_phone="9876543210",
            grievance_id="PGRS-2025-GTR-00001",
            response=OptInChoice.LATER,
        )

        # Act
        result = await service.handle_opt_in(request)

        # Assert
        assert result.success is True
        assert result.rights_sent is False
        assert mock_pref.ask_later is True
        assert mock_pref.ask_later_count == 1


class TestRightsMatching:
    """Unit tests for rights matching."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database."""
        return CitizenEmpowermentService(mock_db)

    @pytest.mark.asyncio
    async def test_pension_category_gets_pension_rights(self, service):
        """Test Pension category gets pension-specific rights."""
        # Arrange
        mock_grievance = MagicMock()
        mock_grievance.department = MagicMock()
        mock_grievance.department.name = "Pension"
        mock_grievance.category = "Pension Delay"
        mock_grievance.citizen_phone = "9876543210"
        service._get_grievance = AsyncMock(return_value=mock_grievance)

        mock_rights = [
            MagicMock(
                id=1,
                right_title="Pension Timeline",
                right_description_te="పెన్షన్ టైమ్‌లైన్",
                right_description_en="Pension timeline info",
                legal_reference="Rule 12.3",
                helpful_contact=None,
            )
        ]
        service._get_rights = AsyncMock(return_value=mock_rights)
        service._log_interaction = AsyncMock()

        # Act
        result = await service.get_rights_for_grievance(
            "PGRS-2025-GTR-00001",
            disclosure_level=1,
            language="te",
        )

        # Assert
        assert len(result.rights) == 1
        assert result.disclosure_level == 1
        assert result.has_more_levels is True

    @pytest.mark.asyncio
    async def test_unknown_category_gets_generic_rights(self, service):
        """Test unknown category falls back to generic rights."""
        # Arrange
        mock_grievance = MagicMock()
        mock_grievance.department = MagicMock()
        mock_grievance.department.name = "Unknown"
        mock_grievance.category = "Unknown"
        mock_grievance.citizen_phone = "9876543210"
        service._get_grievance = AsyncMock(return_value=mock_grievance)

        # First two calls return empty (no specific rights), third returns generic
        service._get_rights = AsyncMock(
            side_effect=[
                [],  # No specific rights
                [],  # No department+All rights
                [MagicMock(
                    id=99,
                    right_title="Generic",
                    right_description_te="సాధారణ",
                    right_description_en="Generic info",
                    legal_reference=None,
                    helpful_contact=None,
                )],  # Generic rights
            ]
        )
        service._log_interaction = AsyncMock()

        # Act
        result = await service.get_rights_for_grievance(
            "PGRS-2025-GTR-00001",
            disclosure_level=1,
            language="en",
        )

        # Assert
        assert len(result.rights) >= 1


class TestLevelUp:
    """Unit tests for level-up functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database."""
        return CitizenEmpowermentService(mock_db)

    @pytest.mark.asyncio
    async def test_level_up_increments_level(self, service, mock_db):
        """Test level up increments disclosure level."""
        # Arrange
        mock_pref = MagicMock()
        mock_pref.opted_in = True
        mock_pref.max_disclosure_level = 1
        mock_pref.preferred_language = "te"
        mock_pref.total_info_requests = 0
        service._get_preference = AsyncMock(return_value=mock_pref)
        service._log_interaction = AsyncMock()

        mock_grievance = MagicMock()
        mock_grievance.department = MagicMock()
        mock_grievance.department.name = "Pension"
        mock_grievance.category = "Pension Delay"
        mock_grievance.citizen_phone = "9876543210"
        service._get_grievance = AsyncMock(return_value=mock_grievance)
        service._get_rights = AsyncMock(return_value=[])

        # Act
        result = await service.request_level_up(
            "PGRS-2025-GTR-00001",
            "9876543210",
        )

        # Assert
        assert result.disclosure_level == 2
        assert mock_pref.max_disclosure_level == 2
        assert mock_pref.total_info_requests == 1

    @pytest.mark.asyncio
    async def test_level_up_not_opted_in_raises(self, service):
        """Test level up fails if citizen not opted in."""
        # Arrange
        service._get_preference = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(ValueError, match="not opted in"):
            await service.request_level_up(
                "PGRS-2025-GTR-00001",
                "9876543210",
            )


class TestConvertRights:
    """Unit tests for rights conversion."""

    @pytest.fixture
    def service(self):
        """Create service with mock database."""
        return CitizenEmpowermentService(AsyncMock())

    def test_convert_rights_telugu(self, service):
        """Test rights conversion to Telugu."""
        # Arrange
        mock_rights = [
            MagicMock(
                id=1,
                right_title="Test Right",
                right_description_te="తెలుగు వివరణ",
                right_description_en="English description",
                legal_reference="Rule 1",
                helpful_contact="1800-123",
            )
        ]

        # Act
        result = service._convert_rights(mock_rights, "te")

        # Assert
        assert len(result) == 1
        assert result[0].description == "తెలుగు వివరణ"
        assert result[0].legal_reference == "Rule 1"

    def test_convert_rights_english(self, service):
        """Test rights conversion to English."""
        # Arrange
        mock_rights = [
            MagicMock(
                id=1,
                right_title="Test Right",
                right_description_te="తెలుగు వివరణ",
                right_description_en="English description",
                legal_reference=None,
                helpful_contact=None,
            )
        ]

        # Act
        result = service._convert_rights(mock_rights, "en")

        # Assert
        assert len(result) == 1
        assert result[0].description == "English description"
