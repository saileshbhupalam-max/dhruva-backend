"""Action executor framework for resolution template actions.

This module provides a pluggable architecture for executing resolution
template actions. In MVP, all actions are logged but not executed.
Real integrations can be added by implementing IActionExecutor.
"""

from app.services.action_executors.base import IActionExecutor
from app.services.action_executors.stub_executor import StubActionExecutor
from app.services.action_executors.registry import (
    ActionExecutorRegistry,
    get_action_registry,
)

__all__ = [
    "IActionExecutor",
    "StubActionExecutor",
    "ActionExecutorRegistry",
    "get_action_registry",
]
