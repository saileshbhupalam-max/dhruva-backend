"""Smart Resolution Engine Router.

Provides resolution-related endpoints:
- POST /resolution/analyze/{grievance_id} - Analyze grievance for root cause
- GET /resolution/templates - List resolution templates
- GET /resolution/templates/{grievance_id}/suggested - Get suggested templates
- POST /resolution/apply/{grievance_id} - Apply resolution template
- GET /resolution/questions/{root_cause} - Get clarification questions
- POST /resolution/clarify/{grievance_id} - Submit clarification answers
- POST /resolution/applications/{application_id}/result - Update application result
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.dependencies.auth import (
    get_current_active_user,
    require_officer_or_above,
)
from app.models.user import User
from app.schemas.resolution import (
    ApplyTemplateRequest,
    ClarificationResult,
    ClarificationSubmission,
    InterventionQuestionResponse,
    InterventionResult,
    ResolutionTemplateResponse,
    RootCause,
    RootCauseAnalysisResult,
    TemplateApplicationResult,
    UpdateApplicationResultRequest,
)
from app.services.resolution_service import get_resolution_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resolution", tags=["Resolution"])


@router.post(
    "/analyze/{grievance_id}",
    response_model=RootCauseAnalysisResult,
    summary="Analyze grievance for root cause",
    description="Analyzes a stuck grievance to detect the root cause of delay/failure. "
    "Returns detected cause, confidence score, clarification questions, and suggested templates.",
)
async def analyze_root_cause(
    grievance_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_officer_or_above()),
) -> RootCauseAnalysisResult:
    """Analyze a grievance for root cause of delay."""
    logger.info(
        f"Root cause analysis requested for {grievance_id} by user {current_user.id}"
    )

    service = get_resolution_service(db)

    try:
        result = await service.analyze_root_cause(grievance_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/templates",
    response_model=List[ResolutionTemplateResponse],
    summary="List resolution templates",
    description="Get all active resolution templates, optionally filtered by "
    "department, category, or root cause.",
)
async def list_templates(
    department: Optional[str] = Query(None, description="Filter by department"),
    category: Optional[str] = Query(None, description="Filter by category"),
    root_cause: Optional[RootCause] = Query(None, description="Filter by root cause"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_officer_or_above()),
) -> List[ResolutionTemplateResponse]:
    """List resolution templates with optional filters."""
    service = get_resolution_service(db)
    return await service.list_templates(
        department=department,
        category=category,
        root_cause=root_cause,
    )


@router.get(
    "/templates/{grievance_id}/suggested",
    response_model=List[ResolutionTemplateResponse],
    summary="Get suggested templates for grievance",
    description="Get templates that match the grievance's department, category, "
    "and detected root cause (if analyzed). Templates are sorted by success rate.",
)
async def get_suggested_templates(
    grievance_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_officer_or_above()),
) -> List[ResolutionTemplateResponse]:
    """Get templates suggested for a specific grievance."""
    service = get_resolution_service(db)
    return await service.get_suggested_templates(grievance_id)


@router.post(
    "/apply/{grievance_id}",
    response_model=TemplateApplicationResult,
    summary="Apply resolution template to grievance",
    description="Apply a resolution template to a grievance. This executes the "
    "template's action steps and records the application for tracking.",
)
async def apply_template(
    grievance_id: str,
    request: ApplyTemplateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_officer_or_above()),
) -> TemplateApplicationResult:
    """Apply a resolution template to a grievance."""
    logger.info(
        f"Applying template {request.template_key} to {grievance_id} "
        f"by user {current_user.id}"
    )

    service = get_resolution_service(db)

    try:
        result = await service.apply_template(
            grievance_id,
            request,
            officer_id=str(current_user.id),
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/questions/{root_cause}",
    response_model=List[InterventionQuestionResponse],
    summary="Get clarification questions for root cause",
    description="Get questions to ask the citizen based on the detected root cause. "
    "Questions can be filtered by department and category, and returned in the "
    "specified language.",
)
async def get_clarification_questions(
    root_cause: RootCause,
    department: Optional[str] = Query(None, description="Filter by department"),
    category: Optional[str] = Query(None, description="Filter by category"),
    language: str = Query("en", regex="^(en|te)$", description="Language (en/te)"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_officer_or_above()),
) -> List[InterventionQuestionResponse]:
    """Get clarification questions for a root cause."""
    service = get_resolution_service(db)
    return await service.get_clarification_questions(
        root_cause=root_cause,
        department=department,
        category=category,
        language=language,
    )


@router.post(
    "/clarify/{grievance_id}",
    response_model=ClarificationResult,
    summary="Submit clarification answers",
    description="Submit the citizen's answers to clarification questions. "
    "This triggers a re-analysis of the grievance with the new information.",
)
async def submit_clarification(
    grievance_id: str,
    submission: ClarificationSubmission,
    db: AsyncSession = Depends(get_db_session),
) -> ClarificationResult:
    """Submit clarification answers from citizen."""
    logger.info(
        f"Clarification submitted for {grievance_id}: "
        f"{len(submission.responses)} responses"
    )

    service = get_resolution_service(db)
    return await service.submit_clarification(grievance_id, submission)


@router.post(
    "/applications/{application_id}/result",
    summary="Update template application result",
    description="Update the outcome of a template application. "
    "This updates the template's success rate statistics.",
)
async def update_application_result(
    application_id: int,
    request: UpdateApplicationResultRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_officer_or_above()),
) -> dict:
    """Update the result of a template application."""
    logger.info(
        f"Updating application {application_id} result to {request.result} "
        f"by user {current_user.id}"
    )

    service = get_resolution_service(db)

    try:
        await service.update_application_result(
            application_id=application_id,
            result=request.result,
            notes=request.notes,
        )
        return {"success": True, "application_id": application_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
