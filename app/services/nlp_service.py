"""NLP Service for department classification using IndicBERT.

Provides automatic department classification for grievance text.
Includes interface-first design with graceful degradation on failure.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ClassificationResult:
    """Result of department classification."""

    def __init__(
        self,
        department_id: Optional[int],
        confidence: float,
        department_code: Optional[str] = None,
        department_name: Optional[str] = None,
        fallback_used: bool = False,
        error: Optional[str] = None,
    ):
        self.department_id = department_id
        self.confidence = confidence
        self.department_code = department_code
        self.department_name = department_name
        self.fallback_used = fallback_used
        self.error = error

    def is_confident(self, threshold: Optional[float] = None) -> bool:
        """Check if classification meets confidence threshold."""
        if threshold is None:
            threshold = settings.NLP_CONFIDENCE_THRESHOLD
        return self.confidence >= threshold and self.department_id is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "department_id": self.department_id,
            "confidence": self.confidence,
            "department_code": self.department_code,
            "department_name": self.department_name,
            "fallback_used": self.fallback_used,
            "error": self.error,
        }


class INLPService(ABC):
    """Interface for NLP department classification service.

    All implementations must provide the classify_text method.
    """

    @abstractmethod
    async def classify_text(
        self,
        text: str,
        language: str = "te",
        district_code: Optional[str] = None,
    ) -> ClassificationResult:
        """Classify grievance text to determine department.

        Args:
            text: Grievance text to classify
            language: Language code (te=Telugu, en=English, hi=Hindi)
            district_code: Optional district code for context

        Returns:
            ClassificationResult with department_id and confidence
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if NLP service is healthy.

        Returns:
            Dict with status and details
        """
        pass


class IndicBERTNLPService(INLPService):
    """Production NLP service using IndicBERT for department classification.

    Calls external NLP service API for classification.
    Implements graceful degradation on failure.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = base_url or settings.NLP_SERVICE_URL
        self.timeout = timeout or settings.NLP_SERVICE_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def classify_text(
        self,
        text: str,
        language: str = "te",
        district_code: Optional[str] = None,
    ) -> ClassificationResult:
        """Classify grievance text using IndicBERT service.

        Makes POST request to NLP service API.
        Returns fallback result on any failure.

        Args:
            text: Grievance text to classify
            language: Language code (te, en, hi)
            district_code: Optional district code

        Returns:
            ClassificationResult with department prediction
        """
        if not settings.NLP_ENABLED:
            return ClassificationResult(
                department_id=None,
                confidence=0.0,
                fallback_used=True,
                error="NLP service disabled",
            )

        try:
            client = await self._get_client()

            payload = {
                "text": text,
                "language": language,
            }
            if district_code:
                payload["district_code"] = district_code

            response = await client.post(
                "/api/nlp/classify",
                json=payload,
            )

            if response.status_code != 200:
                logger.warning(
                    f"NLP service returned {response.status_code}: {response.text}"
                )
                return ClassificationResult(
                    department_id=None,
                    confidence=0.0,
                    fallback_used=True,
                    error=f"Service returned {response.status_code}",
                )

            data = response.json()

            return ClassificationResult(
                department_id=data.get("department_id"),
                confidence=data.get("confidence", 0.0),
                department_code=data.get("department_code"),
                department_name=data.get("department_name"),
                fallback_used=False,
            )

        except httpx.TimeoutException:
            logger.warning("NLP service timeout")
            return ClassificationResult(
                department_id=None,
                confidence=0.0,
                fallback_used=True,
                error="Service timeout",
            )

        except httpx.RequestError as e:
            logger.error(f"NLP service request error: {e}")
            return ClassificationResult(
                department_id=None,
                confidence=0.0,
                fallback_used=True,
                error=str(e),
            )

        except Exception as e:
            logger.error(f"NLP service unexpected error: {e}")
            return ClassificationResult(
                department_id=None,
                confidence=0.0,
                fallback_used=True,
                error=str(e),
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check NLP service health.

        Returns:
            Dict with status and latency
        """
        if not settings.NLP_ENABLED:
            return {
                "status": "disabled",
                "enabled": False,
            }

        try:
            import time

            client = await self._get_client()
            start = time.time()

            response = await client.get("/health")
            latency_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "enabled": True,
                    "latency_ms": round(latency_ms, 2),
                    "url": self.base_url,
                }
            else:
                return {
                    "status": "unhealthy",
                    "enabled": True,
                    "latency_ms": round(latency_ms, 2),
                    "error": f"Status code: {response.status_code}",
                }

        except Exception as e:
            return {
                "status": "unreachable",
                "enabled": True,
                "error": str(e),
                "url": self.base_url,
            }


class MockNLPService(INLPService):
    """Mock NLP service for testing.

    Returns configurable mock responses for testing purposes.
    """

    def __init__(
        self,
        default_department_id: Optional[int] = 1,
        default_confidence: float = 0.85,
        should_fail: bool = False,
    ):
        self.default_department_id = default_department_id
        self.default_confidence = default_confidence
        self.should_fail = should_fail
        self.call_count = 0
        self.last_text: Optional[str] = None

    async def classify_text(
        self,
        text: str,
        language: str = "te",
        district_code: Optional[str] = None,
    ) -> ClassificationResult:
        """Return mock classification result."""
        self.call_count += 1
        self.last_text = text

        if self.should_fail:
            return ClassificationResult(
                department_id=None,
                confidence=0.0,
                fallback_used=True,
                error="Mock failure",
            )

        # Simple keyword-based mock classification
        department_mapping = {
            "hospital": (1, "HLTH", "Health Department"),
            "doctor": (1, "HLTH", "Health Department"),
            "medicine": (1, "HLTH", "Health Department"),
            "road": (2, "PWD", "Public Works Department"),
            "water": (3, "WRDS", "Water Resources Department"),
            "electricity": (4, "APSPDCL", "Electricity Department"),
            "school": (5, "EDU", "Education Department"),
            "police": (6, "POL", "Police Department"),
            "tax": (7, "REV", "Revenue Department"),
            "land": (7, "REV", "Revenue Department"),
        }

        text_lower = text.lower()
        for keyword, (dept_id, code, name) in department_mapping.items():
            if keyword in text_lower:
                return ClassificationResult(
                    department_id=dept_id,
                    confidence=self.default_confidence,
                    department_code=code,
                    department_name=name,
                    fallback_used=False,
                )

        return ClassificationResult(
            department_id=self.default_department_id,
            confidence=self.default_confidence * 0.5,  # Lower confidence for default
            department_code="GEN",
            department_name="General Administration",
            fallback_used=False,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Return mock health status."""
        return {
            "status": "healthy" if not self.should_fail else "unhealthy",
            "mock": True,
            "call_count": self.call_count,
        }


# Singleton instance for the application
_nlp_service: Optional[INLPService] = None


def get_nlp_service() -> INLPService:
    """Get the NLP service instance.

    Returns production service by default, or mock if NLP_ENABLED=false.

    Returns:
        INLPService instance
    """
    global _nlp_service

    if _nlp_service is None:
        if settings.NLP_ENABLED:
            _nlp_service = IndicBERTNLPService()
        else:
            _nlp_service = MockNLPService()

    return _nlp_service


async def classify_grievance(
    text: str,
    language: str = "te",
    district_code: Optional[str] = None,
) -> ClassificationResult:
    """Convenience function to classify grievance text.

    Args:
        text: Grievance text
        language: Language code
        district_code: Optional district code

    Returns:
        ClassificationResult
    """
    service = get_nlp_service()
    return await service.classify_text(text, language, district_code)
