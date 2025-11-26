"""Smart Resolution Engine service implementation.

This service analyzes grievances to detect root causes of delays/failures
and provides targeted interventions through resolution templates.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grievance import Grievance
from app.models.resolution import (
    ClarificationResponse,
    InterventionQuestion,
    ResolutionTemplate,
    RootCauseAnalysis,
    TemplateApplication,
)
from app.schemas.resolution import (
    ActionExecuted,
    ActionStep,
    ApplyTemplateRequest,
    ClarificationResult,
    ClarificationSubmission,
    InterventionQuestionResponse,
    InterventionResult,
    ResolutionTemplateResponse,
    ResponseType,
    RootCause,
    RootCauseAnalysisResult,
    TemplateApplicationResult,
)
from app.services.interfaces.resolution_service import ISmartResolutionService

logger = logging.getLogger(__name__)


class SmartResolutionService(ISmartResolutionService):
    """Concrete implementation of Smart Resolution Engine.

    Analyzes grievances for root causes and applies targeted interventions.
    """

    # Detection signal patterns for each root cause
    # BILINGUAL: English + Telugu patterns for AP deployment
    ROOT_CAUSE_SIGNALS: Dict[RootCause, List[str]] = {
        RootCause.WRONG_DEPARTMENT: [
            # English
            "not my department",
            "wrong department",
            "belongs to",
            "should go to",
            "transfer required",
            # Telugu
            "నా డిపార్ట్‌మెంట్ కాదు",
            "తప్పు డిపార్ట్‌మెంట్",
            "వేరే డిపార్ట్‌మెంట్",
            "బదిలీ చేయాలి",
            "ఇది మా పరిధిలో లేదు",
        ],
        RootCause.MISSING_INFORMATION: [
            # English
            "need more details",
            "please provide",
            "missing",
            "incomplete",
            "not specified",
            "survey number",
            "document number",
            # Telugu
            "మరిన్ని వివరాలు కావాలి",
            "దయచేసి అందించండి",
            "సర్వే నంబర్ లేదు",
            "డాక్యుమెంట్ లేదు",
            "అసంపూర్ణం",
            "వివరాలు లేవు",
            "ఆధార్ నంబర్ అవసరం",
            "పాస్‌బుక్ నంబర్",
        ],
        RootCause.DUPLICATE_CASE: [
            # English
            "duplicate",
            "already filed",
            "same complaint",
            "existing case",
            # Telugu
            "ఇప్పటికే ఫిర్యాదు ఉంది",
            "అదే ఫిర్యాదు",
            "డూప్లికేట్",
            "మునుపు దాఖలు చేశారు",
        ],
        RootCause.OUTSIDE_JURISDICTION: [
            # English
            "not in my area",
            "different mandal",
            "different district",
            "outside jurisdiction",
            # Telugu
            "నా పరిధిలో కాదు",
            "వేరే మండలం",
            "వేరే జిల్లా",
            "పరిధి బయట",
            "ఇతర గ్రామం",
        ],
        RootCause.NEEDS_FIELD_VISIT: [
            # English
            "need to visit",
            "field verification",
            "site inspection",
            "physical verification",
            # Telugu
            "సందర్శన అవసరం",
            "క్షేత్ర పరిశీలన",
            "స్థల పరిశీలన",
            "భౌతిక ధృవీకరణ",
            "సర్వే చేయాలి",
        ],
        RootCause.EXTERNAL_DEPENDENCY: [
            # English
            "waiting for",
            "pending from",
            "court order",
            "central approval",
            "depends on",
            # Telugu
            "కోసం వేచి ఉన్నాము",
            "పెండింగ్ లో ఉంది",
            "కోర్టు ఆర్డర్",
            "కేంద్ర అనుమతి",
            "ఆధారపడి ఉంది",
            "రాష్ట్ర ప్రభుత్వం నుండి",
        ],
        RootCause.CITIZEN_UNREACHABLE: [
            # English
            "not reachable",
            "phone not working",
            "no response",
            "cannot contact",
            "switched off",
            # Telugu
            "అందుబాటులో లేరు",
            "ఫోన్ పని చేయడం లేదు",
            "స్పందన లేదు",
            "సంప్రదించలేకపోయాము",
            "స్విచ్ ఆఫ్",
            "ఫోన్ రింగ్ అవడం లేదు",
        ],
        RootCause.POLICY_LIMITATION: [
            # English
            "not possible",
            "against rules",
            "policy does not allow",
            "cannot be done",
            # Telugu
            "సాధ్యం కాదు",
            "నిబంధనలకు విరుద్ధం",
            "పాలసీ అనుమతించదు",
            "చేయడం సాధ్యం కాదు",
            "GO ప్రకారం కాదు",
        ],
        RootCause.RESOURCE_CONSTRAINT: [
            # English
            "no budget",
            "no staff",
            "resource shortage",
            "waiting for funds",
            # Telugu
            "బడ్జెట్ లేదు",
            "సిబ్బంది లేరు",
            "వనరుల కొరత",
            "నిధులు లేవు",
            "ఖాళీలు లేవు",
        ],
        RootCause.OFFICER_OVERLOAD: [],  # Detected via case count, not signals
    }

    # Intervention descriptions for each root cause
    INTERVENTION_DESCRIPTIONS: Dict[RootCause, str] = {
        RootCause.WRONG_DEPARTMENT: "Ask clarifying questions and re-route to correct department",
        RootCause.MISSING_INFORMATION: "Request specific information from citizen",
        RootCause.DUPLICATE_CASE: "Merge with existing case or escalate",
        RootCause.OUTSIDE_JURISDICTION: "Transfer to correct jurisdiction",
        RootCause.NEEDS_FIELD_VISIT: "Schedule field visit with citizen",
        RootCause.EXTERNAL_DEPENDENCY: "Monitor external dependency and notify citizen",
        RootCause.CITIZEN_UNREACHABLE: "Try alternate contact or community verification",
        RootCause.POLICY_LIMITATION: "Explain limitation and provide alternatives",
        RootCause.RESOURCE_CONSTRAINT: "Add to priority queue with realistic timeline",
        RootCause.OFFICER_OVERLOAD: "Redistribute to less loaded officer",
    }

    # Threshold for officer case count to trigger OFFICER_OVERLOAD
    OFFICER_OVERLOAD_THRESHOLD = 100

    # Confidence threshold below which we default to MISSING_INFORMATION
    CONFIDENCE_THRESHOLD = Decimal("0.30")

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self._db = db

    async def analyze_root_cause(
        self, grievance_id: str
    ) -> RootCauseAnalysisResult:
        """Analyze grievance to detect root cause."""
        logger.info(f"Analyzing root cause for grievance {grievance_id}")

        # Step 1: Get grievance with history
        grievance = await self._get_grievance(grievance_id)
        if grievance is None:
            raise ValueError(f"Grievance {grievance_id} not found")

        # Step 2: Collect detection signals
        signals = await self._collect_signals(grievance)

        # Step 3: Detect root cause
        root_cause, confidence = await self._detect_root_cause(grievance, signals)

        # Step 4: Get department name (handle relationship)
        department_name = self._get_department_name(grievance)

        # Step 5: Get clarification questions
        questions = await self.get_clarification_questions(
            root_cause,
            department=department_name,
            category=grievance.category,
        )

        # Step 6: Get suggested templates
        templates = await self._get_matching_templates(
            department_name,
            grievance.category,
            root_cause,
        )

        # Step 7: Determine recommended intervention
        intervention = self.INTERVENTION_DESCRIPTIONS.get(
            root_cause, "Manual review required"
        )

        # Step 8: Store analysis
        analysis = RootCauseAnalysis(
            grievance_id=grievance_id,
            detected_root_cause=root_cause.value,
            confidence_score=confidence,
            detection_signals=signals,
        )
        self._db.add(analysis)
        await self._db.commit()

        logger.info(
            f"Root cause for {grievance_id}: {root_cause.value} "
            f"(confidence: {confidence})"
        )

        return RootCauseAnalysisResult(
            grievance_id=grievance_id,
            detected_root_cause=root_cause,
            confidence_score=confidence,
            detection_signals=signals,
            recommended_intervention=intervention,
            clarification_questions=questions,
            suggested_templates=templates,
        )

    async def get_suggested_templates(
        self, grievance_id: str
    ) -> List[ResolutionTemplateResponse]:
        """Get suggested templates for a grievance."""
        grievance = await self._get_grievance(grievance_id)
        if grievance is None:
            return []

        # Check if we have a recent analysis
        stmt = (
            select(RootCauseAnalysis)
            .where(RootCauseAnalysis.grievance_id == grievance_id)
            .order_by(RootCauseAnalysis.analyzed_at.desc())
        )
        result = await self._db.execute(stmt)
        analysis = result.scalar_one_or_none()

        root_cause = None
        if analysis is not None:
            root_cause = RootCause(analysis.detected_root_cause)

        department_name = self._get_department_name(grievance)

        return await self._get_matching_templates(
            department_name,
            grievance.category,
            root_cause,
        )

    async def apply_template(
        self,
        grievance_id: str,
        request: ApplyTemplateRequest,
        officer_id: str,
    ) -> TemplateApplicationResult:
        """Apply a resolution template."""
        logger.info(
            f"Applying template {request.template_key} to {grievance_id} "
            f"by officer {officer_id}"
        )

        # Get template
        stmt = select(ResolutionTemplate).where(
            ResolutionTemplate.template_key == request.template_key
        )
        result = await self._db.execute(stmt)
        template = result.scalar_one_or_none()

        if template is None:
            raise ValueError(f"Template {request.template_key} not found")

        # Execute action steps
        actions_executed: List[ActionExecuted] = []
        for step in template.action_steps:
            action_result = await self._execute_action(
                grievance_id, step, officer_id
            )
            actions_executed.append(action_result)

        # Record application
        application = TemplateApplication(
            grievance_id=grievance_id,
            template_id=template.id,
            applied_by=officer_id,
            notes=request.notes,
        )
        self._db.add(application)

        # Update template stats
        template.similar_cases_resolved += 1
        await self._db.commit()
        await self._db.refresh(application)

        # Determine next steps
        next_steps = self._get_next_steps(template, actions_executed)

        logger.info(
            f"Template {request.template_key} applied successfully. "
            f"Application ID: {application.id}"
        )

        return TemplateApplicationResult(
            success=True,
            application_id=application.id,
            actions_executed=actions_executed,
            next_steps=next_steps,
        )

    async def get_clarification_questions(
        self,
        root_cause: RootCause,
        department: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en",
    ) -> List[InterventionQuestionResponse]:
        """Get clarification questions for root cause."""
        # Build query with fallback to generic questions
        conditions = [
            InterventionQuestion.root_cause == root_cause.value,
            InterventionQuestion.is_active == True,  # noqa: E712
        ]

        # First try specific, then generic
        stmt = (
            select(InterventionQuestion)
            .where(
                and_(
                    *conditions,
                    or_(
                        and_(
                            InterventionQuestion.department == department,
                            InterventionQuestion.category == category,
                        ),
                        and_(
                            InterventionQuestion.department == department,
                            InterventionQuestion.category.is_(None),
                        ),
                        and_(
                            InterventionQuestion.department.is_(None),
                            InterventionQuestion.category.is_(None),
                        ),
                    ),
                )
            )
            .order_by(
                # Prioritize specific questions
                InterventionQuestion.department.desc().nulls_last(),
                InterventionQuestion.category.desc().nulls_last(),
                InterventionQuestion.question_order,
            )
        )

        result = await self._db.execute(stmt)
        questions = result.scalars().all()

        # Build response with correct language
        responses: List[InterventionQuestionResponse] = []
        for q in questions:
            question_text = (
                q.question_text_te if language == "te" else q.question_text_en
            )
            responses.append(
                InterventionQuestionResponse(
                    id=q.id,
                    question_text=question_text,
                    response_type=ResponseType(q.response_type),
                    response_options=q.response_options,
                    is_required=q.is_required,
                )
            )

        return responses

    async def submit_clarification(
        self,
        grievance_id: str,
        submission: ClarificationSubmission,
    ) -> ClarificationResult:
        """Submit clarification answers."""
        logger.info(
            f"Submitting {len(submission.responses)} clarification responses "
            f"for {grievance_id}"
        )

        saved_count = 0

        for answer in submission.responses:
            response = ClarificationResponse(
                grievance_id=grievance_id,
                question_id=answer.question_id,
                response_text=answer.response_text,
                response_choice=answer.response_choice,
                response_photo_url=answer.response_photo_url,
                response_number=answer.response_number,
                response_date=answer.response_date,
            )
            self._db.add(response)
            saved_count += 1

        await self._db.commit()

        # Trigger re-analysis with new information
        next_action = "RE_ANALYZE"

        logger.info(f"Saved {saved_count} clarification responses for {grievance_id}")

        return ClarificationResult(
            success=True,
            responses_saved=saved_count,
            next_action=next_action,
        )

    async def list_templates(
        self,
        department: Optional[str] = None,
        category: Optional[str] = None,
        root_cause: Optional[RootCause] = None,
    ) -> List[ResolutionTemplateResponse]:
        """List templates with filters."""
        stmt = select(ResolutionTemplate).where(
            ResolutionTemplate.is_active == True  # noqa: E712
        )

        if department is not None:
            stmt = stmt.where(ResolutionTemplate.department == department)
        if category is not None:
            stmt = stmt.where(ResolutionTemplate.category == category)
        if root_cause is not None:
            stmt = stmt.where(ResolutionTemplate.root_cause == root_cause.value)

        stmt = stmt.order_by(ResolutionTemplate.success_rate.desc())

        result = await self._db.execute(stmt)
        templates = result.scalars().all()

        return [self._template_to_response(t) for t in templates]

    async def update_application_result(
        self,
        application_id: int,
        result: InterventionResult,
        notes: Optional[str] = None,
    ) -> None:
        """Update the result of a template application."""
        logger.info(
            f"Updating application {application_id} result to {result.value}"
        )

        stmt = select(TemplateApplication).where(
            TemplateApplication.id == application_id
        )
        db_result = await self._db.execute(stmt)
        application = db_result.scalar_one_or_none()

        if application is None:
            raise ValueError(f"Application {application_id} not found")

        application.result = result.value
        application.result_updated_at = datetime.utcnow()
        if notes:
            application.notes = notes

        # Update template success rate
        await self._update_template_success_rate(application.template_id)
        await self._db.commit()

        logger.info(f"Application {application_id} updated to {result.value}")

    # =========================================================================
    # Private helper methods
    # =========================================================================

    async def _get_grievance(self, grievance_id: str) -> Optional[Grievance]:
        """Get grievance by ID."""
        stmt = select(Grievance).where(Grievance.grievance_id == grievance_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    def _get_department_name(self, grievance: Grievance) -> str:
        """Get department name from grievance relationship."""
        if grievance.department is not None:
            return grievance.department.dept_name
        return "General"

    async def _collect_signals(self, grievance: Grievance) -> List[str]:
        """Collect detection signals from grievance history."""
        signals: List[str] = []

        # Check officer remarks/notes
        if grievance.officer_notes is not None:
            signals.append(f"Officer note: {grievance.officer_notes}")

        # Check resolution notes
        if grievance.resolution_notes is not None:
            signals.append(f"Resolution note: {grievance.resolution_notes}")

        # Check status for return patterns
        if grievance.status == "rejected":
            signals.append("Case was rejected/returned")

        # Check if citizen was contacted multiple times
        if grievance.contact_attempts is not None and grievance.contact_attempts >= 3:
            signals.append(f"Contact attempts: {grievance.contact_attempts}")

        # Check officer workload
        if grievance.assigned_officer_id is not None:
            officer_cases = await self._get_officer_case_count(
                grievance.assigned_officer_id
            )
            if officer_cases >= self.OFFICER_OVERLOAD_THRESHOLD:
                signals.append(f"Officer has {officer_cases} pending cases")

        return signals

    async def _detect_root_cause(
        self, grievance: Grievance, signals: List[str]
    ) -> tuple[RootCause, Decimal]:
        """Detect root cause from signals."""
        scores: Dict[RootCause, Decimal] = {
            cause: Decimal("0.0") for cause in RootCause
        }

        # Check text signals against patterns
        signal_text = " ".join(signals).lower()
        for cause, patterns in self.ROOT_CAUSE_SIGNALS.items():
            for pattern in patterns:
                if pattern.lower() in signal_text:
                    scores[cause] += Decimal("0.25")

        # Check special cases

        # Officer overload check
        if grievance.assigned_officer_id is not None:
            officer_cases = await self._get_officer_case_count(
                grievance.assigned_officer_id
            )
            if officer_cases >= self.OFFICER_OVERLOAD_THRESHOLD:
                scores[RootCause.OFFICER_OVERLOAD] = Decimal("0.90")

        # Duplicate check
        duplicate = await self._check_duplicate(grievance)
        if duplicate:
            scores[RootCause.DUPLICATE_CASE] = Decimal("0.95")

        # Citizen unreachable check (contact attempts)
        if (
            grievance.contact_attempts is not None
            and grievance.contact_attempts >= 3
        ):
            scores[RootCause.CITIZEN_UNREACHABLE] += Decimal("0.40")

        # Field visit categories
        field_visit_categories = ["Land Survey", "Road Repair", "Building"]
        if grievance.category in field_visit_categories:
            scores[RootCause.NEEDS_FIELD_VISIT] += Decimal("0.30")

        # Find highest score
        best_cause = max(scores, key=lambda k: scores[k])
        confidence = min(Decimal("1.0"), scores[best_cause])

        # Default to MISSING_INFORMATION if no clear signal
        if confidence < self.CONFIDENCE_THRESHOLD:
            best_cause = RootCause.MISSING_INFORMATION
            confidence = Decimal("0.50")

        return (best_cause, confidence)

    async def _get_officer_case_count(self, officer_id: UUID | str | None) -> int:
        """Get count of pending cases for an officer.

        Args:
            officer_id: UUID of the assigned officer
        """
        stmt = select(func.count(Grievance.grievance_id)).where(
            and_(
                Grievance.assigned_officer_id == officer_id,
                Grievance.status.in_(["assigned", "in_progress"]),
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar() or 0

    async def _check_duplicate(self, grievance: Grievance) -> bool:
        """Check if grievance is a duplicate."""
        # Look for similar cases from same citizen in last 30 days
        stmt = select(func.count(Grievance.grievance_id)).where(
            and_(
                Grievance.citizen_phone == grievance.citizen_phone,
                Grievance.department_id == grievance.department_id,
                Grievance.grievance_id != grievance.grievance_id,
                Grievance.created_at >= func.now() - text("INTERVAL '30 days'"),
            )
        )
        result = await self._db.execute(stmt)
        count = result.scalar() or 0
        return count > 0

    async def _get_matching_templates(
        self,
        department: str,
        category: Optional[str],
        root_cause: Optional[RootCause],
    ) -> List[ResolutionTemplateResponse]:
        """Get templates matching grievance."""
        stmt = select(ResolutionTemplate).where(
            and_(
                ResolutionTemplate.is_active == True,  # noqa: E712
                or_(
                    ResolutionTemplate.department == department,
                    ResolutionTemplate.department == "General",
                ),
            )
        )

        if root_cause is not None:
            stmt = stmt.where(
                or_(
                    ResolutionTemplate.root_cause == root_cause.value,
                    ResolutionTemplate.root_cause.is_(None),
                )
            )

        stmt = stmt.order_by(ResolutionTemplate.success_rate.desc()).limit(5)

        result = await self._db.execute(stmt)
        templates = result.scalars().all()

        return [self._template_to_response(t) for t in templates]

    def _template_to_response(
        self, template: ResolutionTemplate
    ) -> ResolutionTemplateResponse:
        """Convert template model to response schema."""
        return ResolutionTemplateResponse(
            id=template.id,
            template_key=template.template_key,
            department=template.department,
            category=template.category,
            root_cause=(
                RootCause(template.root_cause) if template.root_cause else None
            ),
            title=template.template_title,
            description=template.template_description,
            action_steps=[
                ActionStep(**step) for step in template.action_steps
            ],
            success_rate=template.success_rate,
            avg_resolution_hours=template.avg_resolution_hours,
            similar_cases_resolved=template.similar_cases_resolved,
        )

    async def _execute_action(
        self, grievance_id: str, step: Dict[str, Any], officer_id: str
    ) -> ActionExecuted:
        """Execute a single action step.

        In MVP, actions are logged but not executed.
        Real integrations will be added in Phase 2.
        """
        action = step.get("action", "UNKNOWN")
        description = step.get("description", "")

        # MVP: Log the action
        logger.info(
            f"[MVP STUB] Action '{action}' for grievance {grievance_id} "
            f"by officer {officer_id}: {description}"
        )

        # In MVP, all actions "succeed" (they're just logged)
        return ActionExecuted(
            action=action,
            status="COMPLETED",
            details=f"[MVP] Logged: {description}. Manual follow-up required.",
        )

    def _get_next_steps(
        self, template: ResolutionTemplate, actions: List[ActionExecuted]
    ) -> List[str]:
        """Determine next steps after template application."""
        next_steps = []

        all_completed = all(a.status == "COMPLETED" for a in actions)
        if all_completed:
            next_steps.append("Monitor for citizen confirmation")
            next_steps.append("Check resolution in 24-48 hours")
        else:
            next_steps.append("Review failed actions")
            next_steps.append("Consider manual intervention")

        return next_steps

    async def _update_template_success_rate(self, template_id: int) -> None:
        """Recalculate template success rate from applications."""
        stmt = select(
            func.count(TemplateApplication.id).label("total"),
            func.sum(
                case(
                    (TemplateApplication.result == "SUCCESS", 1),
                    else_=0,
                )
            ).label("successes"),
        ).where(
            and_(
                TemplateApplication.template_id == template_id,
                TemplateApplication.result.in_(["SUCCESS", "FAILED", "PARTIAL"]),
            )
        )
        result = await self._db.execute(stmt)
        row = result.one()

        if row.total > 0:
            success_rate = (row.successes / row.total) * 100
            update_stmt = (
                update(ResolutionTemplate)
                .where(ResolutionTemplate.id == template_id)
                .values(success_rate=success_rate)
            )
            await self._db.execute(update_stmt)


# =============================================================================
# Dependency injection helper
# =============================================================================


def get_resolution_service(db: AsyncSession) -> SmartResolutionService:
    """Factory function for dependency injection.

    Args:
        db: Async SQLAlchemy session

    Returns:
        SmartResolutionService instance
    """
    return SmartResolutionService(db)
