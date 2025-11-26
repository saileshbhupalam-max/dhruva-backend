"""Departments Router.

Provides department reference data endpoints:
- GET /departments - List all departments
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import get_db_session
from app.models.department import Department

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/departments")


class DepartmentDict(TypedDict):
    """Type definition for department dictionary."""

    id: str
    code: str
    name: str
    name_telugu: Optional[str]
    description: Optional[str]
    sla_days: int


# In-memory cache for departments (24-hour TTL)
_departments_cache: Optional[List[DepartmentDict]] = None
_departments_cache_time: Optional[datetime] = None


class DepartmentResponse(BaseModel):
    """Department response model."""

    id: str = Field(..., description="Department UUID")
    code: str = Field(..., description="Department code")
    name: str = Field(..., description="Department name in English")
    name_telugu: Optional[str] = Field(None, description="Department name in Telugu")
    description: Optional[str] = Field(None, description="Department description")
    sla_days: int = Field(..., description="Default SLA in days")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "HLTH",
                "name": "Health Department",
                "name_telugu": "ఆరోగ్య శాఖ",
                "description": "Handles health-related grievances",
                "sla_days": 7,
            }
        }


class DepartmentListResponse(BaseModel):
    """Department list response model."""

    data: List[DepartmentResponse] = Field(..., description="List of departments")
    total: int = Field(..., description="Total number of departments")


def _is_cache_valid() -> bool:
    """Check if cache is still valid."""
    if _departments_cache is None or _departments_cache_time is None:
        return False

    cache_age = (datetime.now(timezone.utc) - _departments_cache_time).total_seconds()
    return cache_age < settings.CACHE_REFERENCE_DATA_TTL


def _clear_cache() -> None:
    """Clear the departments cache."""
    global _departments_cache, _departments_cache_time
    _departments_cache = None
    _departments_cache_time = None


@router.get(
    "",
    response_model=DepartmentListResponse,
    summary="List all departments",
    description="Get list of all government departments. Data is cached for 24 hours.",
)
async def list_departments(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> DepartmentListResponse:
    """Get all departments.

    Returns all government departments with their SLA configurations.
    Data is cached in memory for 24 hours.

    Args:
        response: FastAPI response for adding headers
        db: Database session

    Returns:
        DepartmentListResponse with all departments
    """
    global _departments_cache, _departments_cache_time

    # Check cache
    if _is_cache_valid():
        logger.debug("Returning cached departments")
        response.headers["X-Cache"] = "HIT"
        response.headers["Cache-Control"] = f"max-age={settings.CACHE_REFERENCE_DATA_TTL}"
        assert _departments_cache is not None  # _is_cache_valid() ensures this
        return DepartmentListResponse(
            data=[DepartmentResponse(**d) for d in _departments_cache],
            total=len(_departments_cache),
        )

    # Query database
    logger.debug("Fetching departments from database")
    stmt = select(Department).order_by(Department.dept_code)
    result = await db.execute(stmt)
    departments = result.scalars().all()

    # Build response data
    department_data: List[DepartmentDict] = [
        {
            "id": str(d.id),
            "code": d.dept_code,
            "name": d.dept_name,
            "name_telugu": d.name_telugu,
            "description": d.description,
            "sla_days": d.sla_days,
        }
        for d in departments
    ]

    # Update cache
    _departments_cache = department_data
    _departments_cache_time = datetime.now(timezone.utc)

    # Set cache headers
    response.headers["X-Cache"] = "MISS"
    response.headers["Cache-Control"] = f"max-age={settings.CACHE_REFERENCE_DATA_TTL}"

    logger.info(f"Cached {len(departments)} departments")

    return DepartmentListResponse(
        data=[DepartmentResponse(**d) for d in department_data],
        total=len(department_data),
    )


@router.get(
    "/{department_code}",
    response_model=DepartmentResponse,
    summary="Get department by code",
    description="Get a specific department by its code.",
)
async def get_department_by_code(
    department_code: str,
    db: AsyncSession = Depends(get_db_session),
) -> DepartmentResponse:
    """Get department by code.

    Args:
        department_code: Department code (e.g., "HLTH")
        db: Database session

    Returns:
        DepartmentResponse

    Raises:
        HTTPException 404: Department not found
    """
    from fastapi import HTTPException, status

    stmt = select(Department).where(Department.dept_code == department_code)
    result = await db.execute(stmt)
    department = result.scalar_one_or_none()

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with code '{department_code}' not found",
        )

    return DepartmentResponse(
        id=str(department.id),
        code=department.dept_code,
        name=department.dept_name,
        name_telugu=department.name_telugu,
        description=department.description,
        sla_days=department.sla_days,
    )
