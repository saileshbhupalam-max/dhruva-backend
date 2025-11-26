"""Interface definition for Citizen Empowerment Service.

This module defines the abstract base class for the empowerment service,
following the dependency inversion principle.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.schemas.citizen_empowerment import (
    EmpowermentResponse,
    OptInRequest,
    OptInResponse,
    RightEntryCreate,
    RightEntryResponse,
    TriggerResponse,
)


class ICitizenEmpowermentService(ABC):
    """Interface for Citizen Empowerment service.

    Provides methods for:
    - Handling citizen opt-in decisions
    - Retrieving rights information
    - Managing disclosure levels
    - Proactive trigger checking
    - Knowledge base management
    """

    @abstractmethod
    async def handle_opt_in(self, request: OptInRequest) -> OptInResponse:
        """Process citizen's opt-in decision.

        Args:
            request: OptInRequest with phone, grievance_id, and response

        Returns:
            OptInResponse with success status and optional rights
        """
        pass

    @abstractmethod
    async def get_rights_for_grievance(
        self,
        grievance_id: str,
        disclosure_level: int = 1,
        language: str = "te",
    ) -> EmpowermentResponse:
        """Get rights information matching the grievance.

        Args:
            grievance_id: The grievance ID
            disclosure_level: Level of detail (1-4)
            language: Language code (te/en)

        Returns:
            EmpowermentResponse with rights and formatted message
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def check_proactive_triggers(self) -> List[Dict[str, Any]]:
        """Check all grievances for proactive trigger conditions.

        Called by background job hourly.

        Returns:
            List of triggered actions with grievance_id, trigger_type, success
        """
        pass

    @abstractmethod
    async def send_proactive_empowerment(
        self,
        grievance_id: str,
        trigger_type: str,
    ) -> TriggerResponse:
        """Send proactive empowerment message.

        Args:
            grievance_id: The grievance ID
            trigger_type: Type of trigger (SLA_50_PERCENT, etc.)

        Returns:
            TriggerResponse with send status
        """
        pass

    @abstractmethod
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
            department: Department name for message
            language: Language code (te/en)

        Returns:
            True if message sent successfully
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def add_right_entry(self, entry: RightEntryCreate) -> RightEntryResponse:
        """Add new entry to knowledge base.

        Args:
            entry: RightEntryCreate with all fields

        Returns:
            Created entry with ID
        """
        pass
