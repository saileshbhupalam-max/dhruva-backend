"""Empathy Engine Service for distress detection and compassionate responses.

This service analyzes grievance text to detect emotional distress signals,
assigns appropriate distress levels, adjusts SLAs, and generates empathetic
responses in the citizen's language (Telugu, English, or Hindi).
"""

import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.empathy import (
    DistressKeyword,
    EmpathyTemplate,
    GrievanceSentiment,
)
from app.schemas.empathy import (
    DistressAnalysisRequest,
    DistressAnalysisResult,
    DistressKeywordCreate,
    DistressKeywordResponse,
    DistressLevel,
    EmpathyTemplateCreate,
    EmpathyTemplateResponse,
    GrievanceSentimentResponse,
    Language,
)

logger = logging.getLogger(__name__)


class IEmpathyService(ABC):
    """Interface for Empathy Engine service."""

    @abstractmethod
    async def analyze_distress(
        self, request: DistressAnalysisRequest
    ) -> DistressAnalysisResult:
        """Analyze grievance text for distress signals."""
        pass

    @abstractmethod
    async def get_grievance_sentiment(
        self, grievance_id: str
    ) -> Optional[GrievanceSentimentResponse]:
        """Get stored sentiment analysis for a grievance."""
        pass

    @abstractmethod
    async def get_empathy_response(
        self,
        template_key: str,
        placeholders: Dict[str, str],
    ) -> str:
        """Generate empathy response from template with placeholders filled."""
        pass

    @abstractmethod
    async def adjust_sla(
        self, base_sla_days: int, distress_level: DistressLevel
    ) -> int:
        """Adjust SLA based on distress level."""
        pass

    @abstractmethod
    async def list_templates(
        self,
        distress_level: Optional[DistressLevel] = None,
        language: Optional[Language] = None,
        category: Optional[str] = None,
    ) -> List[EmpathyTemplateResponse]:
        """List empathy templates with optional filters."""
        pass

    @abstractmethod
    async def create_template(
        self, template_data: EmpathyTemplateCreate
    ) -> EmpathyTemplateResponse:
        """Create a new empathy template."""
        pass

    @abstractmethod
    async def list_keywords(
        self,
        language: Optional[Language] = None,
        distress_level: Optional[DistressLevel] = None,
    ) -> List[DistressKeywordResponse]:
        """List distress keywords with optional filters."""
        pass

    @abstractmethod
    async def create_keyword(
        self, keyword_data: DistressKeywordCreate
    ) -> DistressKeywordResponse:
        """Create a new distress keyword."""
        pass

    @abstractmethod
    async def send_empathy_notification(
        self,
        phone: str,
        empathy_response: str,
    ) -> bool:
        """Send empathy message to citizen via WhatsApp/SMS."""
        pass


class EmpathyService(IEmpathyService):
    """Concrete implementation of Empathy Engine service."""

    # SLA mapping by distress level (in days)
    SLA_MAPPING: Dict[DistressLevel, int] = {
        DistressLevel.CRITICAL: 1,   # 24 hours
        DistressLevel.HIGH: 3,       # 3 days
        DistressLevel.MEDIUM: 7,     # 7 days
        DistressLevel.NORMAL: 30,    # 30 days
    }

    # Score thresholds for distress levels
    SCORE_THRESHOLDS: Dict[DistressLevel, Decimal] = {
        DistressLevel.CRITICAL: Decimal("8.0"),
        DistressLevel.HIGH: Decimal("5.0"),
        DistressLevel.MEDIUM: Decimal("2.0"),
        DistressLevel.NORMAL: Decimal("0.0"),
    }

    # Base scores by distress level (used in scoring algorithm)
    LEVEL_BASE_SCORES: Dict[str, Decimal] = {
        "CRITICAL": Decimal("4.0"),
        "HIGH": Decimal("2.5"),
        "MEDIUM": Decimal("1.5"),
        "NORMAL": Decimal("0.5"),
    }

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def analyze_distress(
        self, request: DistressAnalysisRequest
    ) -> DistressAnalysisResult:
        """Analyze grievance text for distress signals.

        Algorithm:
        1. Get all keywords for the language
        2. Scan text for keywords and calculate weighted score
        3. Convert score to distress level
        4. Adjust SLA based on distress level
        5. Select appropriate empathy template
        6. Generate response with placeholders filled
        7. Store analysis result
        """
        # Step 1: Get keywords for the language
        keywords = await self._get_keywords_for_language(request.language)

        # Step 2: Scan text for keywords and calculate score
        detected_keywords: List[str] = []
        total_score = Decimal("0.0")
        text_lower = request.text.lower()

        for kw in keywords:
            if kw.keyword.lower() in text_lower:
                detected_keywords.append(kw.keyword)
                # Weight by keyword level and weight
                level_base = self.LEVEL_BASE_SCORES.get(
                    kw.distress_level, Decimal("0.5")
                )
                total_score += level_base * kw.weight

        # Step 3: Normalize score to 0-10 range
        distress_score = min(Decimal("10.0"), total_score)

        # Step 4: Determine distress level from score
        distress_level = self._score_to_level(distress_score)

        # Step 5: Adjust SLA
        adjusted_sla_days = await self.adjust_sla(
            request.base_sla_days, distress_level
        )
        recommended_sla_hours = adjusted_sla_days * 24

        # Step 6: Select appropriate template
        template = await self._select_template(
            distress_level, request.language, request.category
        )
        template_key = (
            template.template_key
            if template is not None
            else f"{distress_level.value.lower()}_generic_{request.language.value}"
        )

        # Step 7: Generate empathy response
        placeholders = {
            "case_id": request.grievance_id,
            "department": request.department,
            "category": request.category or "",
        }
        empathy_response = await self.get_empathy_response(template_key, placeholders)

        # Step 8: Store sentiment analysis
        sentiment = GrievanceSentiment(
            grievance_id=request.grievance_id,
            distress_score=distress_score,
            distress_level=distress_level.value,
            detected_keywords=detected_keywords,
            empathy_template_used=template_key,
            original_sla_days=request.base_sla_days,
            adjusted_sla_days=adjusted_sla_days,
        )
        self._db.add(sentiment)
        await self._db.commit()

        logger.info(
            f"Analyzed distress for {request.grievance_id}: "
            f"score={distress_score}, level={distress_level.value}, "
            f"keywords={len(detected_keywords)}"
        )

        return DistressAnalysisResult(
            grievance_id=request.grievance_id,
            distress_score=distress_score,
            distress_level=distress_level,
            detected_keywords=detected_keywords,
            recommended_sla_hours=recommended_sla_hours,
            adjusted_sla_days=adjusted_sla_days,
            empathy_template_key=template_key,
            empathy_response=empathy_response,
        )

    async def get_grievance_sentiment(
        self, grievance_id: str
    ) -> Optional[GrievanceSentimentResponse]:
        """Get stored sentiment analysis for a grievance."""
        stmt = select(GrievanceSentiment).where(
            GrievanceSentiment.grievance_id == grievance_id
        )
        result = await self._db.execute(stmt)
        sentiment = result.scalar_one_or_none()

        if sentiment is None:
            return None

        return GrievanceSentimentResponse(
            grievance_id=sentiment.grievance_id,
            distress_score=sentiment.distress_score,
            distress_level=DistressLevel(sentiment.distress_level),
            detected_keywords=sentiment.detected_keywords or [],
            empathy_template_used=sentiment.empathy_template_used,
            original_sla_days=sentiment.original_sla_days,
            adjusted_sla_days=sentiment.adjusted_sla_days,
            analyzed_at=sentiment.analyzed_at,
        )

    async def get_empathy_response(
        self,
        template_key: str,
        placeholders: Dict[str, str],
    ) -> str:
        """Generate empathy response from template."""
        stmt = select(EmpathyTemplate).where(
            and_(
                EmpathyTemplate.template_key == template_key,
                EmpathyTemplate.is_active == True,  # noqa: E712
            )
        )
        result = await self._db.execute(stmt)
        template = result.scalar_one_or_none()

        if template is None:
            # Return generic fallback
            case_id = placeholders.get("case_id", "")
            return f"Your case {case_id} has been received. We will help you."

        # Substitute placeholders
        response = template.template_text
        for key, value in placeholders.items():
            response = response.replace(f"{{{key}}}", str(value))

        return response

    async def adjust_sla(
        self, base_sla_days: int, distress_level: DistressLevel
    ) -> int:
        """Adjust SLA based on distress level.

        The adjusted SLA is the MINIMUM of:
        - The base SLA for the department/category
        - The maximum SLA for the distress level
        """
        max_sla = self.SLA_MAPPING[distress_level]
        return min(base_sla_days, max_sla)

    async def list_templates(
        self,
        distress_level: Optional[DistressLevel] = None,
        language: Optional[Language] = None,
        category: Optional[str] = None,
    ) -> List[EmpathyTemplateResponse]:
        """List empathy templates with optional filters."""
        stmt = select(EmpathyTemplate).where(
            EmpathyTemplate.is_active == True  # noqa: E712
        )

        if distress_level is not None:
            stmt = stmt.where(EmpathyTemplate.distress_level == distress_level.value)
        if language is not None:
            stmt = stmt.where(EmpathyTemplate.language == language.value)
        if category is not None:
            stmt = stmt.where(EmpathyTemplate.category == category)

        result = await self._db.execute(stmt)
        templates = result.scalars().all()

        return [
            EmpathyTemplateResponse(
                id=t.id,
                template_key=t.template_key,
                distress_level=DistressLevel(t.distress_level),
                category=t.category,
                language=Language(t.language),
                template_text=t.template_text,
                placeholders=t.placeholders or {},
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ]

    async def create_template(
        self, template_data: EmpathyTemplateCreate
    ) -> EmpathyTemplateResponse:
        """Create a new empathy template."""
        template = EmpathyTemplate(
            template_key=template_data.template_key,
            distress_level=template_data.distress_level.value,
            category=template_data.category,
            language=template_data.language.value,
            template_text=template_data.template_text,
            placeholders=template_data.placeholders,
        )
        self._db.add(template)
        await self._db.commit()
        await self._db.refresh(template)

        return EmpathyTemplateResponse(
            id=template.id,
            template_key=template.template_key,
            distress_level=DistressLevel(template.distress_level),
            category=template.category,
            language=Language(template.language),
            template_text=template.template_text,
            placeholders=template.placeholders or {},
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    async def list_keywords(
        self,
        language: Optional[Language] = None,
        distress_level: Optional[DistressLevel] = None,
    ) -> List[DistressKeywordResponse]:
        """List distress keywords with optional filters."""
        stmt = select(DistressKeyword).where(
            DistressKeyword.is_active == True  # noqa: E712
        )

        if language is not None:
            stmt = stmt.where(DistressKeyword.language == language.value)
        if distress_level is not None:
            stmt = stmt.where(DistressKeyword.distress_level == distress_level.value)

        result = await self._db.execute(stmt)
        keywords = result.scalars().all()

        return [
            DistressKeywordResponse(
                id=kw.id,
                keyword=kw.keyword,
                language=Language(kw.language),
                distress_level=DistressLevel(kw.distress_level),
                weight=kw.weight,
                is_active=kw.is_active,
                created_at=kw.created_at,
            )
            for kw in keywords
        ]

    async def create_keyword(
        self, keyword_data: DistressKeywordCreate
    ) -> DistressKeywordResponse:
        """Create a new distress keyword."""
        keyword = DistressKeyword(
            keyword=keyword_data.keyword,
            language=keyword_data.language.value,
            distress_level=keyword_data.distress_level.value,
            weight=keyword_data.weight,
        )
        self._db.add(keyword)
        await self._db.commit()
        await self._db.refresh(keyword)

        return DistressKeywordResponse(
            id=keyword.id,
            keyword=keyword.keyword,
            language=Language(keyword.language),
            distress_level=DistressLevel(keyword.distress_level),
            weight=keyword.weight,
            is_active=keyword.is_active,
            created_at=keyword.created_at,
        )

    # =========================================================================
    # Private helper methods
    # =========================================================================

    async def _get_keywords_for_language(
        self, language: Language
    ) -> List[DistressKeyword]:
        """Get all active keywords for a language."""
        stmt = select(DistressKeyword).where(
            and_(
                DistressKeyword.language == language.value,
                DistressKeyword.is_active == True,  # noqa: E712
            )
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    def _score_to_level(self, score: Decimal) -> DistressLevel:
        """Convert numeric score to distress level."""
        if score >= self.SCORE_THRESHOLDS[DistressLevel.CRITICAL]:
            return DistressLevel.CRITICAL
        elif score >= self.SCORE_THRESHOLDS[DistressLevel.HIGH]:
            return DistressLevel.HIGH
        elif score >= self.SCORE_THRESHOLDS[DistressLevel.MEDIUM]:
            return DistressLevel.MEDIUM
        else:
            return DistressLevel.NORMAL

    async def _select_template(
        self,
        distress_level: DistressLevel,
        language: Language,
        category: Optional[str],
    ) -> Optional[EmpathyTemplate]:
        """Select the best matching template.

        Priority order:
        1. Category + Language + Distress Level (most specific)
        2. Language + Distress Level (generic)
        """
        # First try category-specific template
        if category is not None:
            stmt = select(EmpathyTemplate).where(
                and_(
                    EmpathyTemplate.distress_level == distress_level.value,
                    EmpathyTemplate.language == language.value,
                    EmpathyTemplate.category == category,
                    EmpathyTemplate.is_active == True,  # noqa: E712
                )
            )
            result = await self._db.execute(stmt)
            template = result.scalar_one_or_none()
            if template is not None:
                return template

        # Fall back to generic template for the level/language
        stmt = select(EmpathyTemplate).where(
            and_(
                EmpathyTemplate.distress_level == distress_level.value,
                EmpathyTemplate.language == language.value,
                EmpathyTemplate.category.is_(None),
                EmpathyTemplate.is_active == True,  # noqa: E712
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def send_empathy_notification(
        self,
        phone: str,
        empathy_response: str,
    ) -> bool:
        """Send empathy message to citizen via WhatsApp/SMS.

        Uses the existing WhatsApp service with SMS fallback.

        Args:
            phone: Citizen's phone number
            empathy_response: The empathy message to send

        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            from app.services.whatsapp_service import get_whatsapp_service

            whatsapp = get_whatsapp_service()
            result = await whatsapp.send_message(
                to_phone=phone,
                message=empathy_response,
                fallback_to_sms=True,
            )
            if result.success:
                logger.info(f"Sent empathy notification to {phone[-4:]}")
            else:
                logger.warning(f"Failed to send empathy notification: {result.error}")
            return result.success
        except Exception as e:
            logger.error(f"Error sending empathy notification: {e}")
            return False


# =============================================================================
# Service factory
# =============================================================================

_empathy_service: Optional[EmpathyService] = None


def get_empathy_service(db: AsyncSession) -> EmpathyService:
    """Get EmpathyService instance.

    Args:
        db: Database session

    Returns:
        EmpathyService instance
    """
    return EmpathyService(db)
