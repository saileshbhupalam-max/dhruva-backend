"""Registry for action executors.

The registry maintains a list of executors in priority order.
When an action needs to be executed, the registry finds the first
executor that can handle it and delegates the execution.
"""

from typing import List, Optional

from app.services.action_executors.base import IActionExecutor
from app.services.action_executors.stub_executor import StubActionExecutor


class ActionExecutorRegistry:
    """Registry of action executors.

    Executors are checked in order - the first executor that can handle
    an action will be used. Register real executors before the stub
    to override default behavior.
    """

    def __init__(self) -> None:
        """Initialize registry with default stub executor."""
        self._executors: List[IActionExecutor] = []
        # Register default stub executor (MVP)
        self._executors.append(StubActionExecutor())

    def register(self, executor: IActionExecutor) -> None:
        """Register a new executor (takes priority over existing).

        Args:
            executor: The executor to register

        Note:
            New executors are inserted at the beginning of the list,
            so they take priority over existing executors.
        """
        self._executors.insert(0, executor)

    def get_executor(self, action_name: str) -> IActionExecutor:
        """Get executor for an action.

        Args:
            action_name: The action type to find an executor for

        Returns:
            The first executor that can handle the action

        Raises:
            ValueError: If no executor can handle the action
        """
        for executor in self._executors:
            if executor.can_execute(action_name):
                return executor
        raise ValueError(f"No executor found for action: {action_name}")

    def list_executors(self) -> List[IActionExecutor]:
        """Get all registered executors.

        Returns:
            List of executors in priority order
        """
        return list(self._executors)


# Singleton instance
_registry: Optional[ActionExecutorRegistry] = None


def get_action_registry() -> ActionExecutorRegistry:
    """Get the global action executor registry.

    Returns:
        The singleton ActionExecutorRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ActionExecutorRegistry()
    return _registry
