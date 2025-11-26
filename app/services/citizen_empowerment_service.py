"""Citizen Empowerment Service Implementation.

This module implements the Citizen Empowerment service for Task 3C,
providing opt-in management, rights information, and proactive triggers.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.citizen_empowerment import (
    CitizenEmpowermentPreference,
    EmpowermentInteraction,
    ProactiveTriggerConfig,
    RightsKnowledgeBase,
)
from app.models.grievance import Grievance
from app.schemas.citizen_empowerment import (
    EmpowermentResponse,
    InteractionType,
    OptInChoice,
    OptInRequest,
    OptInResponse,
    RightEntryCreate,
    RightEntryResponse,
    RightInfo,
    TriggerResponse,
)
from app.services.interfaces.empowerment_service import ICitizenEmpowermentService
from app.templates.empowerment_messages import (
    OPT_IN_PROMPT_EN,
    OPT_IN_PROMPT_TE,
    RIGHTS_LEVEL_1_EN,
    RIGHTS_LEVEL_1_TE,
    format_rights_list,
)

logger = logging.getLogger(__name__)


class CitizenEmpowermentService(ICitizenEmpowermentService):
    """Concrete implementation of Citizen Empowerment service.

    Provides:
    - Opt-in/out management
    - Progressive rights disclosure
    - Proactive trigger checking
    - WhatsApp message integration
    """

    MAX_DISCLOSURE_LEVEL = 4

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            db: Async database session
        """
        self._db = db

    async def handle_opt_in(self, request: OptInRequest) -> OptInResponse:
        """Process citizen's opt-in decision.

        Args:
            request: OptInRequest with phone, grievance_id, and response

        Returns:
            OptInResponse with success status and optional rights
        """
        # Get or create preference record
        pref = await self._get_or_create_preference(request.citizen_phone)

        # Log the interaction
        interaction_type = self._choice_to_interaction_type(request.response)
        await self._log_interaction(
            grievance_id=request.grievance_id,
            citizen_phone=request.citizen_phone,
            interaction_type=interaction_type,
            citizen_response=request.response.value,
        )

        if request.response == OptInChoice.YES:
            # Update preference
            pref.opted_in = True
            pref.opted_out = False
            pref.ask_later = False
            pref.opted_in_at = datetime.utcnow()
            pref.preferred_language = request.preferred_language.value
            await self._db.commit()

            # Get and send rights
            empowerment = await self.get_rights_for_grievance(
                request.grievance_id,
                disclosure_level=1,
                language=request.preferred_language.value,
            )

            return OptInResponse(
                success=True,
                message="Opted in successfully. Rights information sent.",
                rights_sent=True,
                empowerment_response=empowerment,
            )

        elif request.response == OptInChoice.NO:
            pref.opted_in = False
            pref.opted_out = True
            pref.ask_later = False
            await self._db.commit()

            return OptInResponse(
                success=True,
                message="Preference saved. No further empowerment messages.",
                rights_sent=False,
                empowerment_response=None,
            )

        else:  # LATER
            pref.ask_later = True
            pref.ask_later_count += 1
            pref.last_ask_later_at = datetime.utcnow()
            await self._db.commit()

            return OptInResponse(
                success=True,
                message="We will ask again later.",
                rights_sent=False,
                empowerment_response=None,
            )

    async def get_rights_for_grievance(
        self,
        grievance_id: str,
        disclosure_level: int = 1,
        language: str = "te",
    ) -> EmpowermentResponse:
        """Get rights information for a grievance.

        Args:
            grievance_id: The grievance ID
            disclosure_level: Level of detail (1-4)
            language: Language code (te/en)

        Returns:
            EmpowermentResponse with rights and formatted message
        """
        # Get grievance details
        grievance = await self._get_grievance(grievance_id)
        if grievance is None:
            raise ValueError(f"Grievance {grievance_id} not found")

        # Get department name
        department = "General"
        if grievance.department:
            department = grievance.department.name if hasattr(grievance.department, 'name') else str(grievance.department)

        # Get category
        category = grievance.category or "All"

        # Get rights for the category and level
        rights = await self._get_rights(
            department=department,
            category=category,
            level=disclosure_level,
        )

        # If no category-specific rights, try department + All
        if len(rights) == 0:
            rights = await self._get_rights(
                department=department,
                category="All",
                level=disclosure_level,
            )

        # If still empty, get generic rights
        if len(rights) == 0:
            rights = await self._get_rights(
                department="General",
                category="All",
                level=disclosure_level,
            )

        # Convert to RightInfo with correct language
        right_infos = self._convert_rights(rights, language)

        # Format message
        message = self._format_rights_message(right_infos, language)

        # Check if more levels available
        has_more = disclosure_level < self.MAX_DISCLOSURE_LEVEL

        # Log interaction
        await self._log_interaction(
            grievance_id=grievance_id,
            citizen_phone=grievance.citizen_phone or "",
            interaction_type=InteractionType.RIGHTS_SENT,
            disclosure_level=disclosure_level,
            rights_sent=[r.id for r in right_infos],
            message_sent=message,
        )

        return EmpowermentResponse(
            grievance_id=grievance_id,
            disclosure_level=disclosure_level,
            rights=right_infos,
            has_more_levels=has_more,
            message_text=message,
        )

    async def request_level_up(
        self,
        grievance_id: str,
        citizen_phone: str,
    ) -> EmpowermentResponse:
        """Move citizen to next disclosure level.

        Args:
            grievance_id: The grievance ID
            citizen_phone: Citizen's phone number

        Returns:
            EmpowermentResponse with next level rights
        """
        # Get current preference
        pref = await self._get_preference(citizen_phone)
        if pref is None or not pref.opted_in:
            raise ValueError("Citizen not opted in")

        current_level = pref.max_disclosure_level

        # Check if already at max level
        if current_level >= self.MAX_DISCLOSURE_LEVEL:
            # Log the request even though at max
            await self._log_interaction(
                grievance_id=grievance_id,
                citizen_phone=citizen_phone,
                interaction_type=InteractionType.LEVEL_UP_REQUEST,
                disclosure_level=current_level,
            )

            # Return max level rights with "no more levels" message
            grievance = await self._get_grievance(grievance_id)
            officer_contact = "1902 (toll-free)"
            if grievance and grievance.assigned_officer_id:
                officer_contact = f"Officer: {grievance.assigned_officer_id}"

            max_level_msg = (
                f"You are at the maximum information level (Level {self.MAX_DISCLOSURE_LEVEL}). "
                f"For additional help, contact: {officer_contact}"
                if pref.preferred_language == "en"
                else f"మీరు గరిష్ట సమాచార స్థాయి (లెవెల్ {self.MAX_DISCLOSURE_LEVEL}) లో ఉన్నారు. "
                f"అదనపు సహాయం కోసం సంప్రదించండి: {officer_contact}"
            )

            return EmpowermentResponse(
                grievance_id=grievance_id,
                disclosure_level=current_level,
                rights=[],
                has_more_levels=False,
                message_text=max_level_msg,
            )

        # Increment level
        new_level = current_level + 1
        pref.max_disclosure_level = new_level
        pref.total_info_requests += 1
        await self._db.commit()

        # Log level up request
        await self._log_interaction(
            grievance_id=grievance_id,
            citizen_phone=citizen_phone,
            interaction_type=InteractionType.LEVEL_UP_REQUEST,
            disclosure_level=new_level,
        )

        # Get rights for new level
        return await self.get_rights_for_grievance(
            grievance_id,
            disclosure_level=new_level,
            language=pref.preferred_language,
        )

    async def check_proactive_triggers(self) -> List[Dict[str, Any]]:
        """Check all grievances for proactive trigger conditions.

        Returns:
            List of triggered actions
        """
        triggers_fired: List[Dict[str, Any]] = []

        # Get enabled trigger configs
        configs = await self._get_enabled_triggers()

        for config in configs:
            grievances = await self._get_grievances_for_trigger(config)

            for grievance in grievances:
                # Check if citizen opted in
                if not grievance.citizen_phone:
                    continue

                pref = await self._get_preference(grievance.citizen_phone)
                if pref is None or not pref.opted_in:
                    continue

                # Check if we already sent this trigger today
                already_sent = await self._check_trigger_sent_today(
                    grievance.grievance_id, config.trigger_type
                )
                if already_sent:
                    continue

                # Send proactive message
                result = await self.send_proactive_empowerment(
                    grievance.grievance_id,
                    config.trigger_type,
                )

                triggers_fired.append({
                    "grievance_id": grievance.grievance_id,
                    "trigger_type": config.trigger_type,
                    "success": result.success,
                })

        return triggers_fired

    async def send_proactive_empowerment(
        self,
        grievance_id: str,
        trigger_type: str,
    ) -> TriggerResponse:
        """Send proactive empowerment message.

        Args:
            grievance_id: The grievance ID
            trigger_type: Type of trigger

        Returns:
            TriggerResponse with send status
        """
        grievance = await self._get_grievance(grievance_id)
        if grievance is None:
            return TriggerResponse(
                success=False,
                message_sent=False,
                reason="Grievance not found",
            )

        if not grievance.citizen_phone:
            return TriggerResponse(
                success=False,
                message_sent=False,
                reason="No citizen phone",
            )

        pref = await self._get_preference(grievance.citizen_phone)
        if pref is None or not pref.opted_in:
            return TriggerResponse(
                success=False,
                message_sent=False,
                reason="Citizen not opted in",
            )

        # Get trigger config
        config = await self._get_trigger_config(trigger_type)
        if config is None:
            return TriggerResponse(
                success=False,
                message_sent=False,
                reason="Trigger config not found",
            )

        # Format message
        template = (
            config.message_template_te
            if pref.preferred_language == "te"
            else config.message_template_en
        )

        # Calculate days
        days_elapsed = (datetime.utcnow() - grievance.created_at).days
        sla_days = grievance.sla_days or 30
        days_remaining = sla_days - days_elapsed

        message = template.format(
            case_id=grievance_id,
            days_elapsed=days_elapsed,
            days_remaining=max(0, days_remaining),
            status=grievance.status,
        )

        # Log interaction
        await self._log_interaction(
            grievance_id=grievance_id,
            citizen_phone=grievance.citizen_phone,
            interaction_type=InteractionType.PROACTIVE_TRIGGER,
            trigger_reason=trigger_type,
            message_sent=message,
        )

        # Send via WhatsApp (integration point)
        sent = await self._send_message(grievance.citizen_phone, message)

        return TriggerResponse(
            success=True,
            message_sent=sent,
            reason=None if sent else "Message send failed",
        )

    async def send_opt_in_prompt(
        self,
        grievance_id: str,
        citizen_phone: str,
        department: str,
        language: str = "te",
    ) -> bool:
        """Send opt-in prompt to citizen.

        Args:
            grievance_id: The grievance ID
            citizen_phone: Citizen's phone number
            department: Department name
            language: Language code

        Returns:
            True if sent successfully
        """
        template = OPT_IN_PROMPT_TE if language == "te" else OPT_IN_PROMPT_EN
        message = template.format(case_id=grievance_id, department=department)

        # Log the interaction BEFORE sending
        await self._log_interaction(
            grievance_id=grievance_id,
            citizen_phone=citizen_phone,
            interaction_type=InteractionType.OPT_IN_PROMPT,
            message_sent=message,
        )

        # Send via WhatsApp
        return await self._send_message(citizen_phone, message)

    async def list_knowledge_base(
        self,
        department: Optional[str] = None,
        category: Optional[str] = None,
        level: Optional[int] = None,
    ) -> List[RightEntryResponse]:
        """List rights entries with optional filters.

        Args:
            department: Filter by department
            category: Filter by category
            level: Filter by disclosure level

        Returns:
            List of matching rights entries
        """
        stmt = select(RightsKnowledgeBase).where(
            RightsKnowledgeBase.is_active == True
        )

        if department is not None:
            stmt = stmt.where(RightsKnowledgeBase.department == department)
        if category is not None:
            stmt = stmt.where(RightsKnowledgeBase.category == category)
        if level is not None:
            stmt = stmt.where(RightsKnowledgeBase.disclosure_level == level)

        stmt = stmt.order_by(
            RightsKnowledgeBase.department,
            RightsKnowledgeBase.category,
            RightsKnowledgeBase.disclosure_level,
            RightsKnowledgeBase.priority_order,
        )

        result = await self._db.execute(stmt)
        entries = result.scalars().all()

        return [RightEntryResponse.model_validate(e) for e in entries]

    async def add_right_entry(self, entry: RightEntryCreate) -> RightEntryResponse:
        """Add new entry to knowledge base.

        Args:
            entry: RightEntryCreate with all fields

        Returns:
            Created entry with ID
        """
        db_entry = RightsKnowledgeBase(
            department=entry.department,
            category=entry.category,
            disclosure_level=entry.disclosure_level,
            right_title=entry.right_title,
            right_description_en=entry.right_description_en,
            right_description_te=entry.right_description_te,
            legal_reference=entry.legal_reference,
            helpful_contact=entry.helpful_contact,
            priority_order=entry.priority_order,
        )
        self._db.add(db_entry)
        await self._db.commit()
        await self._db.refresh(db_entry)

        return RightEntryResponse.model_validate(db_entry)

    # ============================================
    # Private Helper Methods
    # ============================================

    async def _get_grievance(self, grievance_id: str) -> Optional[Grievance]:
        """Get grievance by ID."""
        stmt = select(Grievance).where(Grievance.grievance_id == grievance_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_or_create_preference(
        self, phone: str
    ) -> CitizenEmpowermentPreference:
        """Get or create citizen preference record."""
        stmt = select(CitizenEmpowermentPreference).where(
            CitizenEmpowermentPreference.citizen_phone == phone
        )
        result = await self._db.execute(stmt)
        pref = result.scalar_one_or_none()

        if pref is None:
            pref = CitizenEmpowermentPreference(citizen_phone=phone)
            self._db.add(pref)
            await self._db.commit()
            await self._db.refresh(pref)

        return pref

    async def _get_preference(
        self, phone: str
    ) -> Optional[CitizenEmpowermentPreference]:
        """Get citizen preference if exists."""
        stmt = select(CitizenEmpowermentPreference).where(
            CitizenEmpowermentPreference.citizen_phone == phone
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_rights(
        self, department: str, category: str, level: int
    ) -> List[RightsKnowledgeBase]:
        """Get rights for department/category/level."""
        stmt = select(RightsKnowledgeBase).where(
            and_(
                RightsKnowledgeBase.department == department,
                RightsKnowledgeBase.category == category,
                RightsKnowledgeBase.disclosure_level == level,
                RightsKnowledgeBase.is_active == True,
            )
        ).order_by(RightsKnowledgeBase.priority_order)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    def _convert_rights(
        self, rights: List[RightsKnowledgeBase], language: str
    ) -> List[RightInfo]:
        """Convert database rights to RightInfo with correct language."""
        return [
            RightInfo(
                id=r.id,
                title=r.right_title,
                description=(
                    r.right_description_te if language == "te"
                    else r.right_description_en
                ),
                legal_reference=r.legal_reference,
                helpful_contact=r.helpful_contact,
            )
            for r in rights
        ]

    def _format_rights_message(
        self, rights: List[RightInfo], language: str
    ) -> str:
        """Format rights into a message."""
        template = RIGHTS_LEVEL_1_TE if language == "te" else RIGHTS_LEVEL_1_EN
        rights_text = format_rights_list(rights, language)
        return template.format(rights_list=rights_text)

    def _choice_to_interaction_type(self, choice: OptInChoice) -> InteractionType:
        """Map opt-in choice to interaction type."""
        mapping = {
            OptInChoice.YES: InteractionType.OPT_IN_YES,
            OptInChoice.NO: InteractionType.OPT_IN_NO,
            OptInChoice.LATER: InteractionType.OPT_IN_LATER,
        }
        return mapping[choice]

    async def _log_interaction(
        self,
        grievance_id: Optional[str],
        citizen_phone: str,
        interaction_type: InteractionType,
        disclosure_level: Optional[int] = None,
        rights_sent: Optional[List[int]] = None,
        trigger_reason: Optional[str] = None,
        citizen_response: Optional[str] = None,
        message_sent: Optional[str] = None,
    ) -> None:
        """Log an empowerment interaction."""
        interaction = EmpowermentInteraction(
            grievance_id=grievance_id,
            citizen_phone=citizen_phone,
            interaction_type=interaction_type.value,
            disclosure_level=disclosure_level,
            rights_sent=rights_sent,
            trigger_reason=trigger_reason,
            citizen_response=citizen_response,
            message_sent=message_sent,
        )
        self._db.add(interaction)
        await self._db.commit()

    async def _get_enabled_triggers(self) -> List[ProactiveTriggerConfig]:
        """Get all enabled trigger configs."""
        stmt = select(ProactiveTriggerConfig).where(
            ProactiveTriggerConfig.enabled == True
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _get_trigger_config(
        self, trigger_type: str
    ) -> Optional[ProactiveTriggerConfig]:
        """Get trigger config by type."""
        stmt = select(ProactiveTriggerConfig).where(
            ProactiveTriggerConfig.trigger_type == trigger_type
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_grievances_for_trigger(
        self, config: ProactiveTriggerConfig
    ) -> List[Grievance]:
        """Get grievances that match trigger conditions."""
        now = datetime.utcnow()

        if config.trigger_type == "SLA_50_PERCENT":
            # Cases at 50% of SLA - active cases with phone numbers
            stmt = select(Grievance).where(
                and_(
                    Grievance.status.in_(["assigned", "in_progress"]),
                    Grievance.citizen_phone.isnot(None),
                )
            )
        elif config.trigger_type == "SLA_APPROACHING":
            # Cases at 80% of SLA (approaching deadline)
            stmt = select(Grievance).where(
                and_(
                    Grievance.status.in_(["assigned", "in_progress"]),
                    Grievance.citizen_phone.isnot(None),
                    Grievance.due_date <= now + timedelta(days=5),
                    Grievance.due_date > now,
                )
            )
        elif config.trigger_type == "NO_UPDATE_7_DAYS":
            # No update in 7 days
            stmt = select(Grievance).where(
                and_(
                    Grievance.status.in_(["assigned", "in_progress"]),
                    Grievance.citizen_phone.isnot(None),
                    Grievance.updated_at <= now - timedelta(days=7),
                )
            )
        else:
            return []

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _check_trigger_sent_today(
        self, grievance_id: str, trigger_type: str
    ) -> bool:
        """Check if trigger was already sent today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count(EmpowermentInteraction.id)).where(
            and_(
                EmpowermentInteraction.grievance_id == grievance_id,
                EmpowermentInteraction.trigger_reason == trigger_type,
                EmpowermentInteraction.created_at >= today_start,
            )
        )
        result = await self._db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    async def _send_message(self, phone: str, message: str) -> bool:
        """Send message via WhatsApp with SMS fallback.

        Args:
            phone: Recipient phone number
            message: Message content

        Returns:
            True if sent successfully
        """
        try:
            # Import here to avoid circular imports
            from app.services.whatsapp_service import get_whatsapp_service

            whatsapp = get_whatsapp_service()
            result = await whatsapp.send_message(
                to_phone=phone,
                message=message,
                fallback_to_sms=True,
            )
            return result.success
        except Exception as e:
            logger.error(f"Failed to send message to {phone}: {e}")
            return False


def get_empowerment_service(db: AsyncSession) -> CitizenEmpowermentService:
    """Factory function to create empowerment service.

    Args:
        db: Async database session

    Returns:
        CitizenEmpowermentService instance
    """
    return CitizenEmpowermentService(db)
