"""API Router for Citizen Empowerment System (Task 3C).

Provides endpoints for:
- Opt-in handling
- Rights information retrieval
- Level-up requests
- Knowledge base management (admin)
- Manual trigger (admin)
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.citizen_empowerment import (
    EmpowermentResponse,
    LevelUpRequest,
    OptInRequest,
    OptInResponse,
    RightEntryCreate,
    RightEntryResponse,
    TriggerRequest,
    TriggerResponse,
)
from app.services.citizen_empowerment_service import get_empowerment_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/empowerment",
    tags=["empowerment"],
    responses={404: {"description": "Not found"}},
)


# ============================================
# Public Endpoints (for WhatsApp webhook integration)
# ============================================


@router.post(
    "/opt-in",
    response_model=OptInResponse,
    summary="Handle citizen opt-in decision",
    description="Process citizen's response to opt-in prompt (YES/NO/LATER)",
)
async def handle_opt_in(
    request: OptInRequest,
    db: AsyncSession = Depends(get_db_session),
) -> OptInResponse:
    """Handle citizen opt-in decision.

    This endpoint is called when a citizen responds to the opt-in prompt
    via WhatsApp. It processes their choice and sends rights information
    if they opted in.

    Args:
        request: OptInRequest with phone, grievance_id, response, and language

    Returns:
        OptInResponse with success status and optional rights
    """
    try:
        service = get_empowerment_service(db)
        result = await service.handle_opt_in(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error handling opt-in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process opt-in request",
        )


@router.get(
    "/rights/{grievance_id}",
    response_model=EmpowermentResponse,
    summary="Get rights information for a grievance",
    description="Retrieve rights information based on grievance category and disclosure level",
)
async def get_rights(
    grievance_id: str,
    level: int = Query(default=1, ge=1, le=4, description="Disclosure level (1-4)"),
    language: str = Query(default="te", pattern="^(te|en)$", description="Language code"),
    db: AsyncSession = Depends(get_db_session),
) -> EmpowermentResponse:
    """Get rights information for a grievance.

    Returns rights information matching the grievance's category and
    the requested disclosure level. Falls back to generic rights if
    no category-specific rights are found.

    Args:
        grievance_id: The grievance ID
        level: Disclosure level (1=basic, 2=officer details, 3=legal, 4=detailed)
        language: Language code (te=Telugu, en=English)

    Returns:
        EmpowermentResponse with rights and formatted message
    """
    try:
        service = get_empowerment_service(db)
        result = await service.get_rights_for_grievance(
            grievance_id=grievance_id,
            disclosure_level=level,
            language=language,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting rights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rights information",
        )


@router.post(
    "/level-up/{grievance_id}",
    response_model=EmpowermentResponse,
    summary="Request next level of information",
    description="Move citizen to the next disclosure level and return rights",
)
async def request_level_up(
    grievance_id: str,
    request: LevelUpRequest,
    db: AsyncSession = Depends(get_db_session),
) -> EmpowermentResponse:
    """Request next disclosure level.

    Increments the citizen's disclosure level and returns the next
    set of rights information.

    Args:
        grievance_id: The grievance ID
        request: LevelUpRequest with citizen_phone

    Returns:
        EmpowermentResponse with next level rights
    """
    try:
        service = get_empowerment_service(db)
        result = await service.request_level_up(
            grievance_id=grievance_id,
            citizen_phone=request.citizen_phone,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error processing level-up: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process level-up request",
        )


# ============================================
# Admin Endpoints
# ============================================


@router.get(
    "/knowledge-base",
    response_model=List[RightEntryResponse],
    summary="List rights entries (admin)",
    description="List all rights entries with optional filters",
)
async def list_knowledge_base(
    department: Optional[str] = Query(None, description="Filter by department"),
    category: Optional[str] = Query(None, description="Filter by category"),
    level: Optional[int] = Query(None, ge=1, le=4, description="Filter by level"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin()),
) -> List[RightEntryResponse]:
    """List rights entries from knowledge base.

    Admin endpoint to view all rights entries with optional filters.

    Args:
        department: Filter by department name
        category: Filter by category name
        level: Filter by disclosure level

    Returns:
        List of RightEntryResponse
    """
    service = get_empowerment_service(db)
    return await service.list_knowledge_base(
        department=department,
        category=category,
        level=level,
    )


@router.post(
    "/knowledge-base",
    response_model=RightEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add rights entry (admin)",
    description="Add a new entry to the rights knowledge base",
)
async def add_right_entry(
    entry: RightEntryCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin()),
) -> RightEntryResponse:
    """Add new rights entry to knowledge base.

    Admin endpoint to add new rights information.

    Args:
        entry: RightEntryCreate with all required fields

    Returns:
        Created RightEntryResponse with ID
    """
    service = get_empowerment_service(db)
    return await service.add_right_entry(entry)


@router.post(
    "/trigger/{grievance_id}",
    response_model=TriggerResponse,
    summary="Manually trigger empowerment message (admin)",
    description="Manually send a proactive empowerment message",
)
async def manual_trigger(
    grievance_id: str,
    request: TriggerRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin()),
) -> TriggerResponse:
    """Manually trigger empowerment message.

    Admin endpoint to manually send a proactive empowerment message
    to a citizen for testing or special circumstances.

    Args:
        grievance_id: The grievance ID
        request: TriggerRequest with trigger_type

    Returns:
        TriggerResponse with send status
    """
    service = get_empowerment_service(db)
    return await service.send_proactive_empowerment(
        grievance_id=grievance_id,
        trigger_type=request.trigger_type.value,
    )
