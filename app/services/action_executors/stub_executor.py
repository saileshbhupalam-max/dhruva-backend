"""MVP stub executor that logs all actions.

This executor handles all actions by logging them without actually
executing any real integrations. It serves as the default fallback
and allows the system to function before real integrations are built.

Replace individual actions with real executors in Phase 2.
"""

import logging
from typing import Any, Dict, Set

from app.schemas.resolution import ActionExecuted
from app.services.action_executors.base import IActionExecutor

logger = logging.getLogger(__name__)


class StubActionExecutor(IActionExecutor):
    """Stub executor that logs all actions (MVP).

    In MVP mode, this executor handles all action types by logging
    them. Real integrations will be added incrementally by creating
    specialized executors that handle specific action types.
    """

    # All supported action types
    SUPPORTED_ACTIONS: Set[str] = {
        # Notification actions
        "NOTIFY_CITIZEN",
        "NOTIFY_OFFICERS",
        "SEND_VERIFICATION_REQUEST",
        # Aadhaar/Bank actions
        "VERIFY_AADHAAR",
        "FETCH_BANK_DETAILS",
        "UPDATE_PENSION_RECORD",
        "TRIGGER_PAYMENT",
        # Case management actions
        "IDENTIFY_BLOCKER",
        "ESCALATE_TO_SENIOR",
        "SET_PRIORITY",
        "TRANSFER_CASE",
        "RESET_SLA",
        "CLOSE_DUPLICATE",
        # Field visit actions
        "CHECK_SURVEYOR_AVAILABILITY",
        "ASSIGN_SURVEYOR",
        "SCHEDULE_VISIT",
        "CREATE_REMINDER",
        "VERIFY_LOCATION",
        # Municipal/Infrastructure actions
        "ASSESS_SEVERITY",
        "ASSIGN_CONTRACTOR",
        "SCHEDULE_WORK",
        # Analysis actions
        "ANALYZE_CLARIFICATION",
        "IDENTIFY_CORRECT_DEPT",
        "IDENTIFY_ORIGINAL",
        "COMPARE_DETAILS",
        "MERGE_ATTACHMENTS",
        # Workload management
        "FIND_AVAILABLE_OFFICER",
        "UPDATE_WORKLOAD",
        # Community verification
        "FIND_VERIFIER",
        "SET_DEADLINE",
        "AWAIT_RESPONSE",
    }

    def can_execute(self, action_name: str) -> bool:
        """Check if this executor handles the action.

        The stub executor handles ALL actions as a fallback.
        """
        return action_name in self.SUPPORTED_ACTIONS

    async def execute(
        self,
        grievance_id: str,
        params: Dict[str, Any],
        officer_id: str,
    ) -> ActionExecuted:
        """Execute the action by logging it (MVP behavior).

        In production, this will be replaced by real integrations.
        For MVP, we log the action and return success to allow
        the workflow to proceed.
        """
        action = params.get("action", "UNKNOWN")
        description = params.get("description", "")

        # Log the action
        logger.info(
            f"[MVP STUB] Action '{action}' for grievance {grievance_id} "
            f"by officer {officer_id}: {description}"
        )

        # MVP: All actions "succeed" (they're just logged)
        return ActionExecuted(
            action=action,
            status="COMPLETED",
            details=f"[MVP] Logged: {description}. Manual follow-up required.",
        )
