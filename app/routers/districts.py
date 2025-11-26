"""Districts Router.

Provides district reference data endpoints:
- GET /districts - List all districts
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
from app.models.district import District

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/districts")


class DistrictDict(TypedDict):
    """Type definition for district dictionary."""

    id: str
    code: str
    name: str


# In-memory cache for districts (24-hour TTL)
_districts_cache: Optional[List[DistrictDict]] = None
_districts_cache_time: Optional[datetime] = None


class DistrictResponse(BaseModel):
    """District response model."""

    id: str = Field(..., description="District UUID")
    code: str = Field(..., description="District code (01-13)")
    name: str = Field(..., description="District name")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "05",
                "name": "Krishna",
            }
        }


class DistrictListResponse(BaseModel):
    """District list response model."""

    data: List[DistrictResponse] = Field(..., description="List of districts")
    total: int = Field(..., description="Total number of districts")


def _is_cache_valid() -> bool:
    """Check if cache is still valid."""
    if _districts_cache is None or _districts_cache_time is None:
        return False

    cache_age = (datetime.now(timezone.utc) - _districts_cache_time).total_seconds()
    return cache_age < settings.CACHE_REFERENCE_DATA_TTL


def _clear_cache() -> None:
    """Clear the districts cache."""
    global _districts_cache, _districts_cache_time
    _districts_cache = None
    _districts_cache_time = None


@router.get(
    "",
    response_model=DistrictListResponse,
    summary="List all districts",
    description="Get list of all districts in Andhra Pradesh. Data is cached for 24 hours.",
)
async def list_districts(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> DistrictListResponse:
    """Get all districts.

    Returns all 13 districts of Andhra Pradesh.
    Data is cached in memory for 24 hours.

    Args:
        response: FastAPI response for adding headers
        db: Database session

    Returns:
        DistrictListResponse with all districts
    """
    global _districts_cache, _districts_cache_time

    # Check cache
    if _is_cache_valid():
        logger.debug("Returning cached districts")
        response.headers["X-Cache"] = "HIT"
        response.headers["Cache-Control"] = f"max-age={settings.CACHE_REFERENCE_DATA_TTL}"
        assert _districts_cache is not None  # _is_cache_valid() ensures this
        return DistrictListResponse(
            data=[DistrictResponse(**d) for d in _districts_cache],
            total=len(_districts_cache),
        )

    # Query database
    logger.debug("Fetching districts from database")
    stmt = select(District).order_by(District.district_code)
    result = await db.execute(stmt)
    districts = result.scalars().all()

    # Build response data
    district_data: List[DistrictDict] = [
        {
            "id": str(d.id),
            "code": d.district_code,
            "name": d.district_name,
        }
        for d in districts
    ]

    # Update cache
    _districts_cache = district_data
    _districts_cache_time = datetime.now(timezone.utc)

    # Set cache headers
    response.headers["X-Cache"] = "MISS"
    response.headers["Cache-Control"] = f"max-age={settings.CACHE_REFERENCE_DATA_TTL}"

    logger.info(f"Cached {len(districts)} districts")

    return DistrictListResponse(
        data=[DistrictResponse(**d) for d in district_data],
        total=len(district_data),
    )


@router.get(
    "/{district_code}",
    response_model=DistrictResponse,
    summary="Get district by code",
    description="Get a specific district by its code.",
)
async def get_district_by_code(
    district_code: str,
    db: AsyncSession = Depends(get_db_session),
) -> DistrictResponse:
    """Get district by code.

    Args:
        district_code: District code (e.g., "05")
        db: Database session

    Returns:
        DistrictResponse

    Raises:
        HTTPException 404: District not found
    """
    from fastapi import HTTPException, status

    stmt = select(District).where(District.district_code == district_code)
    result = await db.execute(stmt)
    district = result.scalar_one_or_none()

    if district is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District with code '{district_code}' not found",
        )

    return DistrictResponse(
        id=str(district.id),
        code=district.district_code,
        name=district.district_name,
    )
