"""Base interface for action executors."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from app.schemas.resolution import ActionExecuted


class IActionExecutor(ABC):
    """Base interface for action executors.

    Action executors are responsible for executing specific actions
    defined in resolution templates. Each executor handles a set of
    action types and performs the necessary operations.

    Example actions:
    - NOTIFY_CITIZEN: Send SMS/WhatsApp to citizen
    - TRANSFER_CASE: Move grievance to another department
    - ASSIGN_SURVEYOR: Assign a field surveyor to the case
    """

    @abstractmethod
    async def execute(
        self,
        grievance_id: str,
        params: Dict[str, Any],
        officer_id: str,
    ) -> ActionExecuted:
        """Execute the action and return result.

        Args:
            grievance_id: The grievance ID this action is for
            params: Action parameters including 'action' and 'description'
            officer_id: ID of the officer executing the action

        Returns:
            ActionExecuted with status and details
        """
        pass

    @abstractmethod
    def can_execute(self, action_name: str) -> bool:
        """Check if this executor handles the given action.

        Args:
            action_name: The action type to check

        Returns:
            True if this executor can handle the action
        """
        pass
