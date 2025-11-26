"""Unit tests for Action Executor framework.

Tests cover:
- IActionExecutor interface
- StubActionExecutor MVP implementation
- ActionExecutorRegistry singleton pattern
"""

import pytest
from decimal import Decimal

from app.schemas.resolution import ActionExecuted
from app.services.action_executors.base import IActionExecutor
from app.services.action_executors.stub_executor import StubActionExecutor
from app.services.action_executors.registry import (
    ActionExecutorRegistry,
    get_action_registry,
)


class TestStubActionExecutor:
    """Unit tests for StubActionExecutor."""

    @pytest.fixture
    def executor(self):
        """Create a stub executor."""
        return StubActionExecutor()

    def test_can_execute_supported_action(self, executor):
        """Test can_execute returns True for supported actions."""
        assert executor.can_execute("NOTIFY_CITIZEN") is True
        assert executor.can_execute("VERIFY_AADHAAR") is True
        assert executor.can_execute("TRANSFER_CASE") is True
        assert executor.can_execute("SCHEDULE_VISIT") is True

    def test_can_execute_unsupported_action(self, executor):
        """Test can_execute returns False for unsupported actions."""
        assert executor.can_execute("UNKNOWN_ACTION") is False
        assert executor.can_execute("INVALID") is False
        assert executor.can_execute("") is False

    @pytest.mark.asyncio
    async def test_execute_returns_completed(self, executor):
        """Test execute returns COMPLETED status for MVP."""
        result = await executor.execute(
            grievance_id="PGRS-2025-GTR-00001",
            params={
                "action": "NOTIFY_CITIZEN",
                "description": "Send SMS to citizen",
            },
            officer_id="OFF001",
        )

        assert isinstance(result, ActionExecuted)
        assert result.action == "NOTIFY_CITIZEN"
        assert result.status == "COMPLETED"
        assert "[MVP]" in result.details

    @pytest.mark.asyncio
    async def test_execute_includes_description(self, executor):
        """Test execute includes description in details."""
        result = await executor.execute(
            grievance_id="PGRS-2025-GTR-00001",
            params={
                "action": "VERIFY_AADHAAR",
                "description": "Verify Aadhaar number",
            },
            officer_id="OFF002",
        )

        assert "Verify Aadhaar number" in result.details

    @pytest.mark.asyncio
    async def test_execute_handles_missing_params(self, executor):
        """Test execute handles missing action and description."""
        result = await executor.execute(
            grievance_id="PGRS-2025-GTR-00001",
            params={},
            officer_id="OFF001",
        )

        assert result.action == "UNKNOWN"
        assert result.status == "COMPLETED"

    def test_supported_actions_count(self, executor):
        """Test all 27 action types are supported."""
        expected_actions = {
            "NOTIFY_CITIZEN",
            "NOTIFY_OFFICERS",
            "SEND_VERIFICATION_REQUEST",
            "VERIFY_AADHAAR",
            "FETCH_BANK_DETAILS",
            "UPDATE_PENSION_RECORD",
            "TRIGGER_PAYMENT",
            "IDENTIFY_BLOCKER",
            "ESCALATE_TO_SENIOR",
            "SET_PRIORITY",
            "TRANSFER_CASE",
            "RESET_SLA",
            "CLOSE_DUPLICATE",
            "CHECK_SURVEYOR_AVAILABILITY",
            "ASSIGN_SURVEYOR",
            "SCHEDULE_VISIT",
            "CREATE_REMINDER",
            "VERIFY_LOCATION",
            "ASSESS_SEVERITY",
            "ASSIGN_CONTRACTOR",
            "SCHEDULE_WORK",
            "ANALYZE_CLARIFICATION",
            "IDENTIFY_CORRECT_DEPT",
            "IDENTIFY_ORIGINAL",
            "COMPARE_DETAILS",
            "MERGE_ATTACHMENTS",
            "FIND_AVAILABLE_OFFICER",
            "UPDATE_WORKLOAD",
            "FIND_VERIFIER",
            "SET_DEADLINE",
            "AWAIT_RESPONSE",
        }

        for action in expected_actions:
            assert executor.can_execute(action), f"Missing support for {action}"


class TestActionExecutorRegistry:
    """Unit tests for ActionExecutorRegistry."""

    def test_registry_has_default_stub(self):
        """Test registry initializes with stub executor."""
        registry = ActionExecutorRegistry()
        executors = registry.list_executors()

        assert len(executors) >= 1
        assert any(isinstance(e, StubActionExecutor) for e in executors)

    def test_get_executor_returns_stub_for_supported(self):
        """Test get_executor returns stub for supported actions."""
        registry = ActionExecutorRegistry()

        executor = registry.get_executor("NOTIFY_CITIZEN")

        assert isinstance(executor, StubActionExecutor)

    def test_get_executor_raises_for_unsupported(self):
        """Test get_executor raises ValueError for unsupported actions."""
        registry = ActionExecutorRegistry()

        with pytest.raises(ValueError, match="No executor found"):
            registry.get_executor("COMPLETELY_UNKNOWN_ACTION")

    def test_register_adds_executor_with_priority(self):
        """Test registered executors take priority over stub."""
        registry = ActionExecutorRegistry()

        class CustomExecutor(IActionExecutor):
            def can_execute(self, action_name: str) -> bool:
                return action_name == "CUSTOM_ACTION"

            async def execute(self, grievance_id, params, officer_id):
                return ActionExecuted(
                    action="CUSTOM_ACTION",
                    status="SUCCESS",
                    details="Custom executor",
                )

        custom = CustomExecutor()
        registry.register(custom)

        # Custom executor should be first
        executors = registry.list_executors()
        assert executors[0] is custom

        # Should be able to get custom executor
        executor = registry.get_executor("CUSTOM_ACTION")
        assert executor is custom

    def test_register_priority_order(self):
        """Test multiple registered executors maintain priority order."""
        registry = ActionExecutorRegistry()

        class Executor1(IActionExecutor):
            def can_execute(self, action_name: str) -> bool:
                return action_name == "ACTION_1"

            async def execute(self, grievance_id, params, officer_id):
                return ActionExecuted(action="ACTION_1", status="SUCCESS")

        class Executor2(IActionExecutor):
            def can_execute(self, action_name: str) -> bool:
                return action_name == "ACTION_2"

            async def execute(self, grievance_id, params, officer_id):
                return ActionExecuted(action="ACTION_2", status="SUCCESS")

        exec1 = Executor1()
        exec2 = Executor2()

        registry.register(exec1)
        registry.register(exec2)

        executors = registry.list_executors()
        # Last registered should be first (priority)
        assert executors[0] is exec2
        assert executors[1] is exec1


class TestGetActionRegistry:
    """Unit tests for get_action_registry singleton."""

    def test_returns_registry_instance(self):
        """Test get_action_registry returns ActionExecutorRegistry."""
        registry = get_action_registry()

        assert isinstance(registry, ActionExecutorRegistry)

    def test_returns_same_instance(self):
        """Test get_action_registry returns singleton."""
        registry1 = get_action_registry()
        registry2 = get_action_registry()

        assert registry1 is registry2

    def test_singleton_has_stub_executor(self):
        """Test singleton registry has stub executor."""
        registry = get_action_registry()
        executors = registry.list_executors()

        assert any(isinstance(e, StubActionExecutor) for e in executors)
