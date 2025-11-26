"""Interface definition for Smart Resolution Engine service."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.schemas.resolution import (
    ApplyTemplateRequest,
    ClarificationResult,
    ClarificationSubmission,
    InterventionQuestionResponse,
    InterventionResult,
    ResolutionTemplateResponse,
    RootCause,
    RootCauseAnalysisResult,
    TemplateApplicationResult,
)


class ISmartResolutionService(ABC):
    """Interface for Smart Resolution Engine service.

    This interface defines the contract for the resolution service,
    enabling dependency injection and easier testing through mocking.
    """

    @abstractmethod
    async def analyze_root_cause(
        self, grievance_id: str
    ) -> RootCauseAnalysisResult:
        """Analyze a grievance to detect root cause of delay/failure.

        Args:
            grievance_id: The grievance ID to analyze (PGRS-YYYY-DD-NNNNN format)

        Returns:
            RootCauseAnalysisResult with detected cause, confidence, and suggestions

        Raises:
            ValueError: If grievance not found
        """
        pass

    @abstractmethod
    async def get_suggested_templates(
        self, grievance_id: str
    ) -> List[ResolutionTemplateResponse]:
        """Get resolution templates matching the grievance pattern.

        Args:
            grievance_id: The grievance ID

        Returns:
            List of matching templates sorted by success rate
        """
        pass

    @abstractmethod
    async def apply_template(
        self,
        grievance_id: str,
        request: ApplyTemplateRequest,
        officer_id: str,
    ) -> TemplateApplicationResult:
        """Apply a resolution template to a grievance.

        Args:
            grievance_id: The grievance ID
            request: Template application request with template_key
            officer_id: ID of the officer applying the template

        Returns:
            TemplateApplicationResult with execution details

        Raises:
            ValueError: If template or grievance not found
        """
        pass

    @abstractmethod
    async def get_clarification_questions(
        self,
        root_cause: RootCause,
        department: Optional[str] = None,
        category: Optional[str] = None,
        language: str = "en",
    ) -> List[InterventionQuestionResponse]:
        """Get clarification questions for a root cause.

        Args:
            root_cause: The detected root cause
            department: Optional department filter
            category: Optional category filter
            language: Language for questions (en/te)

        Returns:
            List of questions to ask citizen
        """
        pass

    @abstractmethod
    async def submit_clarification(
        self,
        grievance_id: str,
        submission: ClarificationSubmission,
    ) -> ClarificationResult:
        """Submit citizen's clarification answers.

        Args:
            grievance_id: The grievance ID
            submission: Citizen's answers

        Returns:
            ClarificationResult with next action
        """
        pass

    @abstractmethod
    async def list_templates(
        self,
        department: Optional[str] = None,
        category: Optional[str] = None,
        root_cause: Optional[RootCause] = None,
    ) -> List[ResolutionTemplateResponse]:
        """List resolution templates with optional filters.

        Args:
            department: Filter by department
            category: Filter by category
            root_cause: Filter by root cause

        Returns:
            List of matching templates
        """
        pass

    @abstractmethod
    async def update_application_result(
        self,
        application_id: int,
        result: InterventionResult,
        notes: Optional[str] = None,
    ) -> None:
        """Update the result of a template application.

        Args:
            application_id: ID of the template application
            result: The outcome (SUCCESS, PARTIAL, FAILED)
            notes: Optional notes about the outcome

        Raises:
            ValueError: If application not found
        """
        pass
