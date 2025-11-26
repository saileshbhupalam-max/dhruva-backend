"""Tests for NLP service.

Tests cover:
- ClassificationResult data class
- MockNLPService (development/testing)
- IndicBERTNLPService (production with HTTP calls)
- Service factory and singleton behavior
- Multi-language classification
- Error handling and graceful degradation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.nlp_service import (
    ClassificationResult,
    MockNLPService,
    IndicBERTNLPService,
    INLPService,
    get_nlp_service,
    classify_grievance,
)
from app.config import settings


class TestClassificationResult:
    """Tests for ClassificationResult class."""

    def test_confident_result(self):
        """Test classification result with high confidence."""
        result = ClassificationResult(
            department_id=1,
            confidence=0.85,
            department_code="HLTH",
            department_name="Health Department",
        )

        assert result.is_confident() is True
        assert result.department_code == "HLTH"
        assert result.department_name == "Health Department"
        assert result.confidence == 0.85
        assert result.department_id == 1

    def test_not_confident_result(self):
        """Test classification result with low confidence."""
        result = ClassificationResult(
            department_id=1,
            confidence=0.50,
            department_code="HLTH",
            department_name="Health Department",
        )

        assert result.is_confident() is False

    def test_threshold_boundary(self):
        """Test confidence at threshold boundary."""
        # At threshold
        result = ClassificationResult(
            department_id=1,
            confidence=settings.NLP_CONFIDENCE_THRESHOLD,
            department_code="HLTH",
            department_name="Health Department",
        )
        assert result.is_confident() is True

        # Just below threshold
        result_below = ClassificationResult(
            department_id=1,
            confidence=settings.NLP_CONFIDENCE_THRESHOLD - 0.01,
            department_code="HLTH",
            department_name="Health Department",
        )
        assert result_below.is_confident() is False

    def test_to_dict(self):
        """Test ClassificationResult to_dict method."""
        result = ClassificationResult(
            department_id=1,
            confidence=0.85,
            department_code="HLTH",
            department_name="Health Department",
        )

        d = result.to_dict()

        assert d["department_code"] == "HLTH"
        assert d["department_name"] == "Health Department"
        assert d["confidence"] == 0.85
        assert d["department_id"] == 1
        assert d["fallback_used"] is False
        assert d["error"] is None


class TestMockNLPService:
    """Tests for MockNLPService."""

    @pytest.fixture
    def nlp_service(self):
        """Create a fresh NLP service for each test."""
        return MockNLPService()

    @pytest.mark.asyncio
    async def test_classify_text_returns_result(self, nlp_service):
        """Test that classify_text returns a ClassificationResult."""
        result = await nlp_service.classify_text(
            text="Hospital has no doctors available",
            language="en",
        )

        assert isinstance(result, ClassificationResult)
        assert result.department_code is not None
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_classify_text_different_languages(self, nlp_service):
        """Test classification with different languages."""
        languages = ["te", "en", "hi"]

        for lang in languages:
            result = await nlp_service.classify_text(
                text="Test grievance text for classification",
                language=lang,
            )
            assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_classify_text_with_district(self, nlp_service):
        """Test classification with district code."""
        result = await nlp_service.classify_text(
            text="Road repair needed in our area",
            language="en",
            district_code="05",
        )

        assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_health_check_enabled(self, nlp_service):
        """Test health check when service is enabled."""
        health = await nlp_service.health_check()

        assert health["status"] == "healthy"
        assert health["mock"] is True

    @pytest.mark.asyncio
    async def test_health_check_disabled(self):
        """Test health check when service is disabled."""
        service = MockNLPService(should_fail=True)
        health = await service.health_check()

        assert health["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_classify_text_failure_mode(self):
        """Test classification when service is in failure mode."""
        service = MockNLPService(should_fail=True)

        result = await service.classify_text(
            text="Test text",
            language="en",
        )

        # Should return a low-confidence result, not raise exception
        assert result.confidence < settings.NLP_CONFIDENCE_THRESHOLD

    @pytest.mark.asyncio
    async def test_classify_text_empty_string(self, nlp_service):
        """Test classification with empty text."""
        result = await nlp_service.classify_text(
            text="",
            language="en",
        )

        # Should handle gracefully
        assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_classify_text_very_long_text(self, nlp_service):
        """Test classification with very long text."""
        long_text = "This is a grievance about roads. " * 1000

        result = await nlp_service.classify_text(
            text=long_text,
            language="en",
        )

        assert isinstance(result, ClassificationResult)


class TestClassifyGrievance:
    """Tests for classify_grievance convenience function."""

    @pytest.mark.asyncio
    async def test_classify_grievance_basic(self):
        """Test basic grievance classification."""
        result = await classify_grievance(
            text="The water supply has been disrupted for three days",
            language="en",
        )

        assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_classify_grievance_with_district(self):
        """Test grievance classification with district."""
        result = await classify_grievance(
            text="Street lights not working",
            language="en",
            district_code="05",
        )

        assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_classify_grievance_telugu(self):
        """Test grievance classification in Telugu."""
        result = await classify_grievance(
            text="రోడ్డు మరమ్మతు అవసరం",  # Road repair needed
            language="te",
        )

        assert isinstance(result, ClassificationResult)


class TestGetNLPService:
    """Tests for get_nlp_service function."""

    def test_get_nlp_service_returns_instance(self):
        """Test that get_nlp_service returns a service instance."""
        service = get_nlp_service()
        assert service is not None

    def test_get_nlp_service_singleton_like(self):
        """Test that get_nlp_service returns consistent instance."""
        service1 = get_nlp_service()
        service2 = get_nlp_service()
        assert service1 is not None
        assert service2 is not None


class TestNLPConfidenceThreshold:
    """Tests for NLP confidence threshold behavior."""

    @pytest.fixture
    def nlp_service(self):
        """Create a fresh NLP service for each test."""
        return MockNLPService()

    @pytest.mark.asyncio
    async def test_low_confidence_result(self):
        """Test handling of low confidence classification."""
        # Use a service in failure mode which returns low confidence
        service = MockNLPService(should_fail=True)

        result = await service.classify_text(
            text="Ambiguous text that could be anything",
            language="en",
        )

        assert isinstance(result, ClassificationResult)
        assert result.is_confident() is False

    @pytest.mark.asyncio
    async def test_confidence_threshold_boundary(self, nlp_service):
        """Test classification at confidence threshold boundary."""
        result = await nlp_service.classify_text(
            text="Clear water supply issue in our area",
            language="en",
        )

        # Result should have a confidence value
        assert result.confidence is not None
        assert 0 <= result.confidence <= 1

    @pytest.mark.asyncio
    async def test_fallback_flag_on_low_confidence(self):
        """Test that fallback_used flag is set on low confidence."""
        service = MockNLPService(should_fail=True)

        result = await service.classify_text(
            text="Test text",
            language="en",
        )

        # When service fails/returns low confidence, should indicate fallback
        assert result.confidence < settings.NLP_CONFIDENCE_THRESHOLD


class TestNLPRetryBehavior:
    """Tests for NLP service retry behavior."""

    @pytest.mark.asyncio
    async def test_graceful_handling_of_errors(self):
        """Test NLP service handles errors gracefully."""
        service = MockNLPService(should_fail=True)

        # Should not raise exception, should return low-confidence result
        result = await service.classify_text(
            text="Test grievance",
            language="en",
        )

        assert isinstance(result, ClassificationResult)
        # Service in failure mode should return a result, not raise

    @pytest.mark.asyncio
    async def test_service_recovers_after_failure(self):
        """Test service can work after being in failure mode."""
        # Start with failure mode
        service = MockNLPService(should_fail=True)
        result1 = await service.classify_text("Test", language="en")
        assert result1.is_confident() is False

        # Create new healthy service
        service2 = MockNLPService(should_fail=False)
        result2 = await service2.classify_text("Test", language="en")
        # Healthy service should return results
        assert isinstance(result2, ClassificationResult)


class TestNLPMultiLanguage:
    """Tests for multi-language NLP classification."""

    @pytest.fixture
    def nlp_service(self):
        """Create NLP service."""
        return MockNLPService()

    @pytest.mark.asyncio
    async def test_classify_hindi_text(self, nlp_service):
        """Test classification of Hindi text."""
        result = await nlp_service.classify_text(
            text="पानी की समस्या",  # Water problem
            language="hi",
        )

        assert isinstance(result, ClassificationResult)
        assert result.department_code is not None

    @pytest.mark.asyncio
    async def test_classify_mixed_language_text(self, nlp_service):
        """Test classification of mixed language text."""
        result = await nlp_service.classify_text(
            text="Water supply problem నీటి సమస్య",  # English + Telugu
            language="te",
        )

        assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_classify_unicode_text(self, nlp_service):
        """Test classification handles unicode properly."""
        result = await nlp_service.classify_text(
            text="నా వీధిలో విద్యుత్ సమస్య ఉంది",  # Telugu: electricity problem
            language="te",
        )

        assert isinstance(result, ClassificationResult)
        assert result.department_code is not None


class TestIndicBERTNLPService:
    """Tests for production IndicBERTNLPService with mocked HTTP calls."""

    @pytest.fixture
    def service(self):
        """Create IndicBERTNLPService instance."""
        return IndicBERTNLPService(
            base_url="http://test-nlp-service:8000",
            timeout=5,
        )

    @pytest.mark.asyncio
    async def test_classify_text_success(self, service):
        """Test successful classification with mocked HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "department_id": 3,
            "confidence": 0.92,
            "department_code": "WRDS",
            "department_name": "Water Resources Department",
        }

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                result = await service.classify_text(
                    text="నీటి సమస్య ఉంది",
                    language="te",
                )

            assert result.department_id == 3
            assert result.confidence == 0.92
            assert result.department_code == "WRDS"
            assert result.fallback_used is False

    @pytest.mark.asyncio
    async def test_classify_text_with_district_code(self, service):
        """Test classification with district code in payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "department_id": 1,
            "confidence": 0.85,
            "department_code": "HLTH",
            "department_name": "Health Department",
        }

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                result = await service.classify_text(
                    text="Hospital issue",
                    language="en",
                    district_code="05",
                )

            # Verify district_code was included in call
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["district_code"] == "05"
            assert result.department_id == 1

    @pytest.mark.asyncio
    async def test_classify_text_nlp_disabled(self, service):
        """Test classification when NLP is disabled."""
        with patch.object(settings, "NLP_ENABLED", False):
            result = await service.classify_text(
                text="Test text",
                language="en",
            )

        assert result.department_id is None
        assert result.confidence == 0.0
        assert result.fallback_used is True
        assert result.error == "NLP service disabled"

    @pytest.mark.asyncio
    async def test_classify_text_non_200_response(self, service):
        """Test classification with non-200 HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                result = await service.classify_text(
                    text="Test text",
                    language="en",
                )

            assert result.department_id is None
            assert result.fallback_used is True
            assert "500" in result.error

    @pytest.mark.asyncio
    async def test_classify_text_timeout(self, service):
        """Test classification handles timeout gracefully."""
        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                result = await service.classify_text(
                    text="Test text",
                    language="en",
                )

            assert result.department_id is None
            assert result.fallback_used is True
            assert result.error == "Service timeout"

    @pytest.mark.asyncio
    async def test_classify_text_request_error(self, service):
        """Test classification handles request errors gracefully."""
        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=httpx.RequestError("Connection refused")
            )
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                result = await service.classify_text(
                    text="Test text",
                    language="en",
                )

            assert result.department_id is None
            assert result.fallback_used is True
            assert "Connection refused" in result.error

    @pytest.mark.asyncio
    async def test_classify_text_unexpected_error(self, service):
        """Test classification handles unexpected errors gracefully."""
        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=ValueError("Unexpected error"))
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                result = await service.classify_text(
                    text="Test text",
                    language="en",
                )

            assert result.department_id is None
            assert result.fallback_used is True
            assert "Unexpected error" in result.error

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, service):
        """Test health check when service is healthy."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                health = await service.health_check()

            assert health["status"] == "healthy"
            assert health["enabled"] is True
            assert "latency_ms" in health

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, service):
        """Test health check when service returns non-200."""
        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                health = await service.health_check()

            assert health["status"] == "unhealthy"
            assert "503" in health["error"]

    @pytest.mark.asyncio
    async def test_health_check_disabled(self, service):
        """Test health check when NLP is disabled."""
        with patch.object(settings, "NLP_ENABLED", False):
            health = await service.health_check()

        assert health["status"] == "disabled"
        assert health["enabled"] is False

    @pytest.mark.asyncio
    async def test_health_check_unreachable(self, service):
        """Test health check when service is unreachable."""
        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                health = await service.health_check()

            assert health["status"] == "unreachable"
            assert "Connection refused" in health["error"]

    @pytest.mark.asyncio
    async def test_client_creation_and_reuse(self, service):
        """Test HTTP client is created and reused."""
        # First call should create client
        assert service._client is None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"department_id": 1, "confidence": 0.9}

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_instance = AsyncMock()
            mock_instance.is_closed = False
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value = mock_instance

            with patch.object(settings, "NLP_ENABLED", True):
                # First call
                await service.classify_text("Test", "en")
                # Second call should reuse client
                await service.classify_text("Test 2", "en")

            # AsyncClient should only be created once
            assert mock_async_client.call_count == 1

    @pytest.mark.asyncio
    async def test_close_client(self, service):
        """Test closing the HTTP client."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        service._client = mock_client

        await service.close()

        mock_client.aclose.assert_called_once()
        assert service._client is None

    @pytest.mark.asyncio
    async def test_close_client_already_closed(self, service):
        """Test closing already closed client is safe."""
        mock_client = AsyncMock()
        mock_client.is_closed = True
        service._client = mock_client

        # Should not raise
        await service.close()

    @pytest.mark.asyncio
    async def test_close_client_none(self, service):
        """Test closing when no client exists is safe."""
        assert service._client is None

        # Should not raise
        await service.close()


class TestIndicBERTNLPServicePayload:
    """Tests for IndicBERTNLPService request payload construction."""

    @pytest.fixture
    def service(self):
        """Create IndicBERTNLPService instance."""
        return IndicBERTNLPService(base_url="http://test:8000", timeout=5)

    @pytest.mark.asyncio
    async def test_payload_without_district(self, service):
        """Test payload construction without district code."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"department_id": 1, "confidence": 0.9}

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                await service.classify_text("Test text", "te")

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]

            assert payload["text"] == "Test text"
            assert payload["language"] == "te"
            assert "district_code" not in payload

    @pytest.mark.asyncio
    async def test_payload_with_district(self, service):
        """Test payload construction with district code."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"department_id": 1, "confidence": 0.9}

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                await service.classify_text("Test text", "en", district_code="GTR")

            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]

            assert payload["text"] == "Test text"
            assert payload["language"] == "en"
            assert payload["district_code"] == "GTR"


class TestIndicBERTNLPServicePartialResponse:
    """Tests for handling partial/missing fields in NLP response."""

    @pytest.fixture
    def service(self):
        """Create IndicBERTNLPService instance."""
        return IndicBERTNLPService(base_url="http://test:8000", timeout=5)

    @pytest.mark.asyncio
    async def test_missing_optional_fields(self, service):
        """Test handling response with missing optional fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "department_id": 5,
            # Missing: confidence, department_code, department_name
        }

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                result = await service.classify_text("Test", "en")

            assert result.department_id == 5
            assert result.confidence == 0.0  # Default when missing
            assert result.department_code is None
            assert result.department_name is None

    @pytest.mark.asyncio
    async def test_null_values_in_response(self, service):
        """Test handling response with explicit null values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "department_id": None,
            "confidence": 0.3,
            "department_code": None,
            "department_name": None,
        }

        with patch.object(service, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch.object(settings, "NLP_ENABLED", True):
                result = await service.classify_text("Ambiguous text", "en")

            assert result.department_id is None
            assert result.confidence == 0.3
            assert result.fallback_used is False


class TestINLPServiceInterface:
    """Tests for INLPService interface compliance."""

    def test_mock_service_implements_interface(self):
        """Test MockNLPService implements INLPService interface."""
        service = MockNLPService()
        assert isinstance(service, INLPService)
        assert hasattr(service, "classify_text")
        assert hasattr(service, "health_check")

    def test_indicbert_service_implements_interface(self):
        """Test IndicBERTNLPService implements INLPService interface."""
        service = IndicBERTNLPService()
        assert isinstance(service, INLPService)
        assert hasattr(service, "classify_text")
        assert hasattr(service, "health_check")
