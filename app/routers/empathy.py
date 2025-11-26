"""Empathy Engine Router.

Provides empathy engine endpoints:
- POST /empathy/analyze - Analyze grievance text for distress
- GET /empathy/templates - List empathy templates (admin)
- POST /empathy/templates - Create new template (admin)
- GET /empathy/keywords - List distress keywords (admin)
- POST /empathy/keywords - Create new keyword (admin)

NOTE: GET /grievances/{grievance_id}/sentiment is in the grievances router per spec.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.dependencies.auth import get_current_active_user, require_role
from app.models.user import User
from app.schemas.empathy import (
    DistressAnalysisRequest,
    DistressAnalysisResult,
    DistressKeywordCreate,
    DistressKeywordResponse,
    DistressLevel,
    EmpathyTemplateCreate,
    EmpathyTemplateResponse,
    Language,
)
from app.services.empathy_service import get_empathy_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/empathy", tags=["Empathy Engine"])


@router.post(
    "/analyze",
    response_model=DistressAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Analyze grievance for distress",
    description="Analyze grievance text to detect distress signals and generate empathetic response.",
)
async def analyze_distress(
    request: DistressAnalysisRequest,
    db: AsyncSession = Depends(get_db_session),
) -> DistressAnalysisResult:
    """Analyze grievance text for distress signals.

    This endpoint:
    1. Scans text for distress keywords (Telugu/English/Hindi)
    2. Calculates distress score (0-10)
    3. Assigns distress level (CRITICAL/HIGH/MEDIUM/NORMAL)
    4. Adjusts SLA based on distress level
    5. Selects appropriate empathy template
    6. Generates personalized empathy response
    7. Stores analysis results

    Returns DistressAnalysisResult with score, level, keywords, and empathy response.
    """
    service = get_empathy_service(db)

    try:
        result = await service.analyze_distress(request)
        logger.info(
            f"Analyzed distress for {request.grievance_id}: "
            f"level={result.distress_level.value}"
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing distress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "EMPATHY_006",
                "message": "Database error during analysis",
                "details": str(e),
            },
        )


@router.get(
    "/templates",
    response_model=List[EmpathyTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="List empathy templates",
    description="List all empathy templates with optional filters (admin only).",
)
async def list_templates(
    distress_level: Optional[DistressLevel] = Query(
        None, description="Filter by distress level"
    ),
    language: Optional[Language] = Query(None, description="Filter by language"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(require_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db_session),
) -> List[EmpathyTemplateResponse]:
    """List empathy templates.

    Requires admin or super_admin role.

    Args:
        distress_level: Optional filter by distress level
        language: Optional filter by language (te/en/hi)
        category: Optional filter by category

    Returns:
        List of matching templates
    """
    service = get_empathy_service(db)
    return await service.list_templates(
        distress_level=distress_level,
        language=language,
        category=category,
    )


@router.post(
    "/templates",
    response_model=EmpathyTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create empathy template",
    description="Create a new empathy template (admin only).",
)
async def create_template(
    template_data: EmpathyTemplateCreate,
    current_user: User = Depends(require_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db_session),
) -> EmpathyTemplateResponse:
    """Create a new empathy template.

    Requires admin or super_admin role.

    Args:
        template_data: Template data to create

    Returns:
        Created template with ID
    """
    service = get_empathy_service(db)

    try:
        result = await service.create_template(template_data)
        logger.info(
            f"Created empathy template {template_data.template_key} "
            f"by user {current_user.username}"
        )
        return result
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "EMPATHY_005",
                    "message": f"Template key '{template_data.template_key}' already exists",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "EMPATHY_006",
                "message": "Database error creating template",
                "details": str(e),
            },
        )


@router.get(
    "/keywords",
    response_model=List[DistressKeywordResponse],
    status_code=status.HTTP_200_OK,
    summary="List distress keywords",
    description="List all distress keywords with optional filters (admin only).",
)
async def list_keywords(
    language: Optional[Language] = Query(None, description="Filter by language"),
    distress_level: Optional[DistressLevel] = Query(
        None, description="Filter by distress level"
    ),
    current_user: User = Depends(require_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db_session),
) -> List[DistressKeywordResponse]:
    """List distress keywords.

    Requires admin or super_admin role.

    Args:
        language: Optional filter by language (te/en/hi)
        distress_level: Optional filter by distress level

    Returns:
        List of matching keywords
    """
    service = get_empathy_service(db)
    return await service.list_keywords(
        language=language,
        distress_level=distress_level,
    )


@router.post(
    "/keywords",
    response_model=DistressKeywordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create distress keyword",
    description="Create a new distress keyword (admin only).",
)
async def create_keyword(
    keyword_data: DistressKeywordCreate,
    current_user: User = Depends(require_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db_session),
) -> DistressKeywordResponse:
    """Create a new distress keyword.

    Requires admin or super_admin role.

    Args:
        keyword_data: Keyword data to create

    Returns:
        Created keyword with ID
    """
    service = get_empathy_service(db)

    try:
        result = await service.create_keyword(keyword_data)
        logger.info(
            f"Created distress keyword '{keyword_data.keyword}' "
            f"by user {current_user.username}"
        )
        return result
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error_code": "EMPATHY_005",
                    "message": f"Keyword '{keyword_data.keyword}' already exists for language '{keyword_data.language.value}'",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "EMPATHY_006",
                "message": "Database error creating keyword",
                "details": str(e),
            },
        )
