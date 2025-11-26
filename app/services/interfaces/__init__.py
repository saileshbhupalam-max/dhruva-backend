"""Service interfaces for dependency injection and testing."""

from app.services.interfaces.resolution_service import ISmartResolutionService
from app.services.interfaces.empowerment_service import ICitizenEmpowermentService

__all__ = [
    "ISmartResolutionService",
    "ICitizenEmpowermentService",
]
