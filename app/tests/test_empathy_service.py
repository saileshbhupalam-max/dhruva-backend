"""Tests for Empathy Engine service."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.empathy import (
    DistressAnalysisRequest,
    DistressLevel,
    EmpathyTemplateCreate,
    DistressKeywordCreate,
    Language,
)
from app.services.empathy_service import EmpathyService, get_empathy_service


class TestDistressLevelCalculation:
    """Tests for distress level calculation logic."""

    def test_score_to_level_critical(self):
        """Test CRITICAL level detection for score >= 8.0."""
        service = EmpathyService(MagicMock())

        assert service._score_to_level(Decimal("10.0")) == DistressLevel.CRITICAL
        assert service._score_to_level(Decimal("8.5")) == DistressLevel.CRITICAL
        assert service._score_to_level(Decimal("8.0")) == DistressLevel.CRITICAL

    def test_score_to_level_high(self):
        """Test HIGH level detection for score >= 5.0."""
        service = EmpathyService(MagicMock())

        assert service._score_to_level(Decimal("7.9")) == DistressLevel.HIGH
        assert service._score_to_level(Decimal("6.0")) == DistressLevel.HIGH
        assert service._score_to_level(Decimal("5.0")) == DistressLevel.HIGH

    def test_score_to_level_medium(self):
        """Test MEDIUM level detection for score >= 2.0."""
        service = EmpathyService(MagicMock())

        assert service._score_to_level(Decimal("4.9")) == DistressLevel.MEDIUM
        assert service._score_to_level(Decimal("3.0")) == DistressLevel.MEDIUM
        assert service._score_to_level(Decimal("2.0")) == DistressLevel.MEDIUM

    def test_score_to_level_normal(self):
        """Test NORMAL level detection for score < 2.0."""
        service = EmpathyService(MagicMock())

        assert service._score_to_level(Decimal("1.9")) == DistressLevel.NORMAL
        assert service._score_to_level(Decimal("1.0")) == DistressLevel.NORMAL
        assert service._score_to_level(Decimal("0.0")) == DistressLevel.NORMAL


class TestSLAAdjustment:
    """Tests for SLA adjustment logic."""

    @pytest.mark.asyncio
    async def test_sla_critical_caps_at_1_day(self):
        """Test CRITICAL distress caps SLA at 1 day."""
        service = EmpathyService(MagicMock())

        result = await service.adjust_sla(30, DistressLevel.CRITICAL)
        assert result == 1

        result = await service.adjust_sla(7, DistressLevel.CRITICAL)
        assert result == 1

    @pytest.mark.asyncio
    async def test_sla_high_caps_at_3_days(self):
        """Test HIGH distress caps SLA at 3 days."""
        service = EmpathyService(MagicMock())

        result = await service.adjust_sla(30, DistressLevel.HIGH)
        assert result == 3

        result = await service.adjust_sla(7, DistressLevel.HIGH)
        assert result == 3

    @pytest.mark.asyncio
    async def test_sla_medium_caps_at_7_days(self):
        """Test MEDIUM distress caps SLA at 7 days."""
        service = EmpathyService(MagicMock())

        result = await service.adjust_sla(30, DistressLevel.MEDIUM)
        assert result == 7

        result = await service.adjust_sla(14, DistressLevel.MEDIUM)
        assert result == 7

    @pytest.mark.asyncio
    async def test_sla_normal_caps_at_30_days(self):
        """Test NORMAL distress caps SLA at 30 days."""
        service = EmpathyService(MagicMock())

        result = await service.adjust_sla(60, DistressLevel.NORMAL)
        assert result == 30

        result = await service.adjust_sla(30, DistressLevel.NORMAL)
        assert result == 30

    @pytest.mark.asyncio
    async def test_sla_keeps_lower_base(self):
        """Test that lower base SLA is preserved."""
        service = EmpathyService(MagicMock())

        # If base SLA is already lower than max, keep the base
        result = await service.adjust_sla(2, DistressLevel.HIGH)
        assert result == 2  # 2 < 3, so keep 2

        result = await service.adjust_sla(5, DistressLevel.MEDIUM)
        assert result == 5  # 5 < 7, so keep 5


class TestDistressAnalysis:
    """Tests for distress analysis."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an EmpathyService with mock DB."""
        return EmpathyService(mock_db)

    @pytest.mark.asyncio
    async def test_analyze_detects_critical_keyword(self, service, mock_db):
        """Test that CRITICAL keywords are detected."""
        # Mock keywords
        mock_keyword = MagicMock()
        mock_keyword.keyword = "dying"
        mock_keyword.distress_level = "CRITICAL"
        mock_keyword.weight = Decimal("1.50")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_keyword]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        # Mock template selection to return None (use fallback)
        service._select_template = AsyncMock(return_value=None)
        service.get_empathy_response = AsyncMock(return_value="Test response")

        request = DistressAnalysisRequest(
            text="My father is dying please help urgently",
            language=Language.ENGLISH,
            grievance_id="PGRS-2025-GTR-00001",
            department="Health",
            base_sla_days=30,
        )

        result = await service.analyze_distress(request)

        assert "dying" in result.detected_keywords
        # 4.0 (CRITICAL base) * 1.5 (weight) = 6.0 -> HIGH level
        assert result.distress_score >= Decimal("5.0")

    @pytest.mark.asyncio
    async def test_analyze_detects_telugu_keyword(self, service, mock_db):
        """Test that Telugu keywords are detected."""
        # Mock Telugu keyword
        mock_keyword = MagicMock()
        mock_keyword.keyword = "ఆకలి"  # hunger
        mock_keyword.distress_level = "CRITICAL"
        mock_keyword.weight = Decimal("1.50")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_keyword]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        service._select_template = AsyncMock(return_value=None)
        service.get_empathy_response = AsyncMock(return_value="Test response")

        request = DistressAnalysisRequest(
            text="మా కుటుంబం ఆకలి తో బాధపడుతుంది",  # My family is suffering from hunger
            language=Language.TELUGU,
            grievance_id="PGRS-2025-GTR-00002",
            department="Food",
            base_sla_days=30,
        )

        result = await service.analyze_distress(request)

        assert "ఆకలి" in result.detected_keywords

    @pytest.mark.asyncio
    async def test_analyze_with_no_keywords_returns_normal(self, service, mock_db):
        """Test that no keywords results in NORMAL level."""
        # Mock empty keywords
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        service._select_template = AsyncMock(return_value=None)
        service.get_empathy_response = AsyncMock(return_value="Test response")

        request = DistressAnalysisRequest(
            text="I would like to request a copy of my certificate",
            language=Language.ENGLISH,
            grievance_id="PGRS-2025-GTR-00003",
            department="Revenue",
            base_sla_days=30,
        )

        result = await service.analyze_distress(request)

        assert result.distress_level == DistressLevel.NORMAL
        assert result.distress_score == Decimal("0.0")
        assert len(result.detected_keywords) == 0


class TestEmpathyResponse:
    """Tests for empathy response generation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an EmpathyService with mock DB."""
        return EmpathyService(mock_db)

    @pytest.mark.asyncio
    async def test_get_empathy_response_with_template(self, service, mock_db):
        """Test response generation with template."""
        mock_template = MagicMock()
        mock_template.template_text = "Your case {case_id} has been received by {department}."

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute = AsyncMock(return_value=mock_result)

        placeholders = {
            "case_id": "PGRS-2025-GTR-00001",
            "department": "Revenue",
        }

        response = await service.get_empathy_response("test_template", placeholders)

        assert "PGRS-2025-GTR-00001" in response
        assert "Revenue" in response

    @pytest.mark.asyncio
    async def test_get_empathy_response_fallback(self, service, mock_db):
        """Test response generation with fallback when template not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        placeholders = {
            "case_id": "PGRS-2025-GTR-00001",
        }

        response = await service.get_empathy_response("nonexistent_template", placeholders)

        assert "PGRS-2025-GTR-00001" in response
        assert "received" in response.lower()


class TestTemplateManagement:
    """Tests for template CRUD operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an EmpathyService with mock DB."""
        return EmpathyService(mock_db)

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self, service, mock_db):
        """Test listing templates with filters."""
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_key = "critical_generic_en"
        mock_template.distress_level = "CRITICAL"
        mock_template.category = None
        mock_template.language = "en"
        mock_template.template_text = "Test template"
        mock_template.placeholders = {}
        mock_template.is_active = True
        mock_template.created_at = MagicMock()
        mock_template.updated_at = MagicMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_template]
        mock_db.execute = AsyncMock(return_value=mock_result)

        templates = await service.list_templates(
            distress_level=DistressLevel.CRITICAL,
            language=Language.ENGLISH,
        )

        assert len(templates) == 1
        assert templates[0].template_key == "critical_generic_en"
        assert templates[0].distress_level == DistressLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_create_template(self, service, mock_db):
        """Test creating a new template."""
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_key = "new_template"
        mock_template.distress_level = "HIGH"
        mock_template.category = "Pension"
        mock_template.language = "te"
        mock_template.template_text = "New template text"
        mock_template.placeholders = {}
        mock_template.is_active = True
        mock_template.created_at = MagicMock()
        mock_template.updated_at = MagicMock()

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(side_effect=lambda x: setattr(x, 'id', 1))

        # We need to mock the template that gets created
        with patch('app.services.empathy_service.EmpathyTemplate') as MockTemplate:
            MockTemplate.return_value = mock_template

            template_data = EmpathyTemplateCreate(
                template_key="new_template",
                distress_level=DistressLevel.HIGH,
                category="Pension",
                language=Language.TELUGU,
                template_text="New template text",
            )

            result = await service.create_template(template_data)

            assert result.template_key == "new_template"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()


class TestKeywordManagement:
    """Tests for keyword CRUD operations."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an EmpathyService with mock DB."""
        return EmpathyService(mock_db)

    @pytest.mark.asyncio
    async def test_list_keywords_with_filters(self, service, mock_db):
        """Test listing keywords with filters."""
        mock_keyword = MagicMock()
        mock_keyword.id = 1
        mock_keyword.keyword = "dying"
        mock_keyword.language = "en"
        mock_keyword.distress_level = "CRITICAL"
        mock_keyword.weight = Decimal("1.50")
        mock_keyword.is_active = True
        mock_keyword.created_at = MagicMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_keyword]
        mock_db.execute = AsyncMock(return_value=mock_result)

        keywords = await service.list_keywords(
            language=Language.ENGLISH,
            distress_level=DistressLevel.CRITICAL,
        )

        assert len(keywords) == 1
        assert keywords[0].keyword == "dying"
        assert keywords[0].distress_level == DistressLevel.CRITICAL


class TestKeywordCreation:
    """Tests for keyword creation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an EmpathyService with mock DB."""
        return EmpathyService(mock_db)

    @pytest.mark.asyncio
    async def test_create_keyword(self, service, mock_db):
        """Test creating a new keyword."""
        mock_keyword = MagicMock()
        mock_keyword.id = 1
        mock_keyword.keyword = "new_keyword"
        mock_keyword.language = "te"
        mock_keyword.distress_level = "HIGH"
        mock_keyword.weight = Decimal("1.20")
        mock_keyword.is_active = True
        mock_keyword.created_at = MagicMock()

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch('app.services.empathy_service.DistressKeyword') as MockKeyword:
            MockKeyword.return_value = mock_keyword

            keyword_data = DistressKeywordCreate(
                keyword="new_keyword",
                language=Language.TELUGU,
                distress_level=DistressLevel.HIGH,
                weight=Decimal("1.20"),
            )

            result = await service.create_keyword(keyword_data)

            assert result.keyword == "new_keyword"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()


class TestTemplateSelection:
    """Tests for template selection logic."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an EmpathyService with mock DB."""
        return EmpathyService(mock_db)

    @pytest.mark.asyncio
    async def test_select_category_specific_template(self, service, mock_db):
        """Test selecting category-specific template."""
        mock_template = MagicMock()
        mock_template.template_key = "critical_pension_te"
        mock_template.distress_level = "CRITICAL"
        mock_template.category = "Pension"
        mock_template.language = "te"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute = AsyncMock(return_value=mock_result)

        template = await service._select_template(
            DistressLevel.CRITICAL,
            Language.TELUGU,
            "Pension",
        )

        assert template is not None
        assert template.template_key == "critical_pension_te"
        assert template.category == "Pension"

    @pytest.mark.asyncio
    async def test_select_fallback_to_generic_template(self, service, mock_db):
        """Test fallback to generic template when category-specific not found."""
        # First call returns None (no category-specific)
        # Second call returns generic template
        mock_generic = MagicMock()
        mock_generic.template_key = "critical_generic_te"
        mock_generic.category = None

        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None

        mock_result_generic = MagicMock()
        mock_result_generic.scalar_one_or_none.return_value = mock_generic

        mock_db.execute = AsyncMock(side_effect=[mock_result_none, mock_result_generic])

        template = await service._select_template(
            DistressLevel.CRITICAL,
            Language.TELUGU,
            "NonExistentCategory",
        )

        assert template is not None
        assert template.template_key == "critical_generic_te"
        assert template.category is None

    @pytest.mark.asyncio
    async def test_select_template_no_category(self, service, mock_db):
        """Test template selection when no category provided."""
        mock_generic = MagicMock()
        mock_generic.template_key = "high_generic_en"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_generic
        mock_db.execute = AsyncMock(return_value=mock_result)

        template = await service._select_template(
            DistressLevel.HIGH,
            Language.ENGLISH,
            None,  # No category
        )

        assert template is not None
        assert template.template_key == "high_generic_en"
        # Should only query once (no category-specific query)
        assert mock_db.execute.call_count == 1


class TestEmpathyNotification:
    """Tests for empathy notification sending."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an EmpathyService with mock DB."""
        return EmpathyService(mock_db)

    @pytest.mark.asyncio
    async def test_send_notification_success(self, service):
        """Test successful notification sending."""
        mock_result = MagicMock()
        mock_result.success = True

        mock_whatsapp = MagicMock()
        mock_whatsapp.send_message = AsyncMock(return_value=mock_result)

        with patch('app.services.whatsapp_service.get_whatsapp_service', return_value=mock_whatsapp):
            result = await service.send_empathy_notification(
                phone="9876543210",
                empathy_response="Test empathy message",
            )

            assert result is True
            mock_whatsapp.send_message.assert_called_once_with(
                to_phone="9876543210",
                message="Test empathy message",
                fallback_to_sms=True,
            )

    @pytest.mark.asyncio
    async def test_send_notification_failure(self, service):
        """Test notification sending failure."""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "WhatsApp unavailable"

        mock_whatsapp = MagicMock()
        mock_whatsapp.send_message = AsyncMock(return_value=mock_result)

        with patch('app.services.whatsapp_service.get_whatsapp_service', return_value=mock_whatsapp):
            result = await service.send_empathy_notification(
                phone="9876543210",
                empathy_response="Test empathy message",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_exception(self, service):
        """Test notification sending with exception."""
        with patch('app.services.whatsapp_service.get_whatsapp_service', side_effect=Exception("Service error")):
            result = await service.send_empathy_notification(
                phone="9876543210",
                empathy_response="Test empathy message",
            )

            assert result is False


class TestGrievanceSentiment:
    """Tests for grievance sentiment retrieval."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an EmpathyService with mock DB."""
        return EmpathyService(mock_db)

    @pytest.mark.asyncio
    async def test_get_sentiment_found(self, service, mock_db):
        """Test retrieving existing sentiment."""
        from datetime import datetime

        mock_sentiment = MagicMock()
        mock_sentiment.grievance_id = "PGRS-2025-GTR-00001"
        mock_sentiment.distress_score = Decimal("8.5")
        mock_sentiment.distress_level = "CRITICAL"
        mock_sentiment.detected_keywords = ["dying", "starving"]
        mock_sentiment.empathy_template_used = "critical_generic_en"
        mock_sentiment.original_sla_days = 30
        mock_sentiment.adjusted_sla_days = 1
        mock_sentiment.analyzed_at = datetime.now()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sentiment
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_grievance_sentiment("PGRS-2025-GTR-00001")

        assert result is not None
        assert result.grievance_id == "PGRS-2025-GTR-00001"
        assert result.distress_level == DistressLevel.CRITICAL
        assert result.adjusted_sla_days == 1

    @pytest.mark.asyncio
    async def test_get_sentiment_not_found(self, service, mock_db):
        """Test retrieving non-existent sentiment."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_grievance_sentiment("PGRS-2025-GTR-99999")

        assert result is None


class TestServiceFactory:
    """Tests for service factory function."""

    def test_get_empathy_service_returns_instance(self):
        """Test that get_empathy_service returns an EmpathyService."""
        mock_db = MagicMock()
        service = get_empathy_service(mock_db)

        assert isinstance(service, EmpathyService)
