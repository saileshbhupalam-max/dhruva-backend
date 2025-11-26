"""Grievances Router.

Provides grievance CRUD endpoints:
- POST /grievances - Submit new grievance
- GET /grievances - List grievances (paginated, filtered)
- GET /grievances/{id} - Get single grievance
- PATCH /grievances/{id} - Update grievance
- DELETE /grievances/{id} - Soft delete grievance
- PATCH /grievances/bulk - Bulk update grievances
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Header, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import get_db_session
from app.dependencies.auth import (
    get_current_active_user,
    get_optional_user,
    require_role,
)
from app.models.department import Department
from app.models.district import District
from app.models.grievance import Grievance
from app.models.user import User
from app.schemas.grievance import (
    BulkUpdateRequest,
    BulkUpdateResponse,
    GrievanceCreateRequest,
    GrievanceDetailResponse,
    GrievanceListResponse,
    GrievanceResponse,
    GrievanceUpdateRequest,
)
from app.services.nlp_service import classify_grievance
from app.services.storage_service import get_storage_service
from app.services.empathy_service import get_empathy_service
from app.schemas.empathy import GrievanceSentimentResponse
from app.models.attachment import Attachment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/grievances")


# In-memory idempotency cache (for development - use Redis in production)
_idempotency_cache: Dict[str, Dict[str, Any]] = {}


def _generate_grievance_id(district_code: str) -> str:
    """Generate public grievance ID.

    Format: PGRS-YYYY-DD-NNNNN
    Where DD is district code and NNNNN is a sequential number.
    """
    now = datetime.now(timezone.utc)
    year = now.year

    # Generate unique number using timestamp + random
    unique_part = int(now.timestamp() * 1000) % 100000

    return f"PGRS-{year}-{district_code}-{unique_part:05d}"


def _hash_for_duplicate_detection(
    phone: str,
    text: str,
    district_code: str,
) -> str:
    """Generate hash for duplicate detection.

    Uses phone + first 100 chars of text + district + hour bucket.
    """
    hour_bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    content = f"{phone}:{text[:100]}:{district_code}:{hour_bucket}"
    return hashlib.sha256(content.encode()).hexdigest()


async def _check_idempotency(
    key: str,
) -> Optional[Dict[str, Any]]:
    """Check if request was already processed (idempotency).

    Args:
        key: Idempotency key

    Returns:
        Cached response if found, None otherwise
    """
    if key in _idempotency_cache:
        cached = _idempotency_cache[key]
        # Check if not expired (1 hour TTL)
        if (datetime.now(timezone.utc) - cached["time"]).total_seconds() < settings.IDEMPOTENCY_KEY_TTL:
            return cast(Dict[str, Any], cached["response"])
    return None


def _store_idempotency(key: str, response: Dict[str, Any]) -> None:
    """Store response for idempotency.

    Args:
        key: Idempotency key
        response: Response to cache
    """
    _idempotency_cache[key] = {
        "time": datetime.now(timezone.utc),
        "response": response,
    }


@router.post(
    "",
    response_model=GrievanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit new grievance",
    description="Submit a new grievance. NLP classification is automatic. Supports idempotency via Idempotency-Key header.",
)
async def create_grievance(
    request: GrievanceCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_optional_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> GrievanceResponse:
    """Submit a new grievance.

    Citizens can submit grievances without authentication.
    NLP automatically classifies to appropriate department.

    Args:
        request: Grievance creation request
        db: Database session
        current_user: Optional authenticated user
        idempotency_key: Optional idempotency key

    Returns:
        Created grievance

    Raises:
        HTTPException 400: Validation error
        HTTPException 404: District not found
        HTTPException 429: Rate limit exceeded
    """
    # Check idempotency
    if idempotency_key:
        cached = await _check_idempotency(idempotency_key)
        if cached:
            logger.info(f"Idempotency hit for key: {idempotency_key}")
            return GrievanceResponse(**cached)

    # Hash-based duplicate detection
    duplicate_hash = _hash_for_duplicate_detection(
        request.citizen_phone,
        request.grievance_text,
        request.district_code,
    )
    cached = await _check_idempotency(f"hash:{duplicate_hash}")
    if cached:
        logger.info("Duplicate grievance detected by hash")
        return GrievanceResponse(**cached)

    # Validate district exists
    district_stmt = select(District).where(District.district_code == request.district_code)
    district_result = await db.execute(district_stmt)
    district = district_result.scalar_one_or_none()

    if district is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District with code '{request.district_code}' not found",
        )

    # NLP classification
    department = None
    department_id = None
    sla_days = 7  # Default SLA

    if request.department_id:
        # Manual department assignment
        dept_stmt = select(Department).where(Department.id == request.department_id)
        dept_result = await db.execute(dept_stmt)
        department = dept_result.scalar_one_or_none()
        if department:
            department_id = department.id
            sla_days = department.sla_days
    else:
        # Automatic NLP classification
        try:
            classification = await classify_grievance(
                text=request.grievance_text,
                language=request.language.value,
                district_code=request.district_code,
            )

            if classification.is_confident():
                # Find department by ID from NLP response
                if classification.department_code:
                    dept_stmt = select(Department).where(
                        Department.dept_code == classification.department_code
                    )
                    dept_result = await db.execute(dept_stmt)
                    department = dept_result.scalar_one_or_none()
                    if department:
                        department_id = department.id
                        sla_days = department.sla_days
                        logger.info(
                            f"NLP classified to {department.dept_code} "
                            f"(confidence: {classification.confidence:.2f})"
                        )
            else:
                logger.info(
                    f"NLP confidence too low: {classification.confidence:.2f}. "
                    "Manual assignment needed."
                )
        except Exception as e:
            logger.warning(f"NLP classification failed: {e}. Manual assignment needed.")

    # Generate grievance ID
    grievance_id = _generate_grievance_id(request.district_code)

    # Calculate due date
    due_date = datetime.now(timezone.utc) + timedelta(days=sla_days)

    # Create grievance
    grievance = Grievance(
        grievance_id=grievance_id,
        citizen_id=current_user.id if current_user else None,
        citizen_name=request.citizen_name,
        citizen_phone=request.citizen_phone,
        citizen_email=request.citizen_email,
        citizen_address=request.citizen_address,
        district_id=district.id,
        department_id=department_id,
        subject=request.subject or request.grievance_text[:100],
        grievance_text=request.grievance_text,
        language=request.language.value,
        channel=request.channel.value,
        status="submitted",
        priority="normal",
        sla_days=sla_days,
        due_date=due_date,
        submitted_at=datetime.now(timezone.utc),
        latitude=request.latitude,
        longitude=request.longitude,
        extra_data=request.extra_data,
    )

    db.add(grievance)
    await db.commit()
    await db.refresh(grievance)

    logger.info(f"Grievance created: {grievance_id}")

    # Build response
    response_data = _build_grievance_response(grievance, district, department)

    # Store for idempotency
    if idempotency_key:
        _store_idempotency(idempotency_key, response_data)
    _store_idempotency(f"hash:{duplicate_hash}", response_data)

    return GrievanceResponse(**response_data)


@router.get(
    "",
    response_model=GrievanceListResponse,
    summary="List grievances",
    description="List grievances with pagination and filters. Officers see only their assigned grievances.",
)
async def list_grievances(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["officer", "supervisor", "admin"])),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    district_id: Optional[UUID] = Query(None, description="Filter by district"),
    department_id: Optional[UUID] = Query(None, description="Filter by department"),
    assigned_officer_id: Optional[UUID] = Query(None, description="Filter by assigned officer"),
    search: Optional[str] = Query(None, description="Search in subject/description"),
) -> GrievanceListResponse:
    """List grievances with filters.

    Officers see grievances in their department/district.
    Supervisors see all in their department.
    Admins see all grievances.

    Args:
        db: Database session
        current_user: Authenticated user
        page: Page number (1-indexed)
        page_size: Items per page
        status_filter: Filter by status
        district_id: Filter by district
        department_id: Filter by department
        assigned_officer_id: Filter by officer
        search: Search text

    Returns:
        Paginated grievance list
    """
    # Build base query
    stmt = select(Grievance).where(Grievance.deleted_at.is_(None))

    # Apply authorization filters
    if current_user.role == "officer":
        # Officers see only grievances assigned to them or in their department
        stmt = stmt.where(
            or_(
                Grievance.assigned_officer_id == current_user.id,
                Grievance.department_id == current_user.department_id,
            )
        )
    elif current_user.role == "supervisor":
        # Supervisors see all in their department
        if current_user.department_id:
            stmt = stmt.where(Grievance.department_id == current_user.department_id)

    # Apply filters
    if status_filter:
        stmt = stmt.where(Grievance.status == status_filter)
    if district_id:
        stmt = stmt.where(Grievance.district_id == district_id)
    if department_id:
        stmt = stmt.where(Grievance.department_id == department_id)
    if assigned_officer_id:
        stmt = stmt.where(Grievance.assigned_officer_id == assigned_officer_id)
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Grievance.subject.ilike(search_term),
                Grievance.grievance_text.ilike(search_term),
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Grievance.created_at.desc()).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(stmt)
    grievances = result.scalars().all()

    # Build response
    items = []
    for g in grievances:
        items.append(_build_grievance_response(g, g.district, g.department))

    total_pages = (total + page_size - 1) // page_size

    return GrievanceListResponse(
        data=[GrievanceResponse(**item) for item in items],
        pagination={
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
        },
    )


@router.get(
    "/{grievance_id}",
    response_model=GrievanceDetailResponse,
    summary="Get grievance details",
    description="Get detailed information about a specific grievance.",
)
async def get_grievance(
    grievance_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["officer", "supervisor", "admin"])),
) -> GrievanceDetailResponse:
    """Get grievance by ID.

    Args:
        grievance_id: Public grievance ID (PGRS-YYYY-DD-NNNNN)
        db: Database session
        current_user: Authenticated user

    Returns:
        Detailed grievance response

    Raises:
        HTTPException 404: Grievance not found
        HTTPException 403: Not authorized
    """
    stmt = select(Grievance).where(
        Grievance.grievance_id == grievance_id,
        Grievance.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    grievance = result.scalar_one_or_none()

    if grievance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance '{grievance_id}' not found",
        )

    # Check authorization
    if current_user.role == "officer":
        if (
            grievance.assigned_officer_id != current_user.id
            and grievance.department_id != current_user.department_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this grievance",
            )
    elif current_user.role == "supervisor":
        if (
            current_user.department_id
            and grievance.department_id != current_user.department_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this grievance",
            )

    # Build detailed response
    response_data = _build_grievance_response(grievance, grievance.district, grievance.department)

    # Add relationships
    response_data["attachments"] = [
        {
            "id": str(a.id),
            "file_name": a.file_name,
            "file_type": a.file_type,
            "file_size_bytes": a.file_size,
            "file_url": f"/uploads/{a.file_path}",
            "uploaded_at": a.created_at.isoformat(),
        }
        for a in grievance.attachments
    ]

    response_data["audit_logs"] = [
        {
            "id": str(log.id),
            "action": log.action,
            "actor": {"id": str(log.user_id)} if log.user_id else None,
            "created_at": log.timestamp.isoformat(),
        }
        for log in grievance.audit_logs
    ]

    response_data["verifications"] = [
        {
            "id": str(v.id),
            "verification_method": v.verification_type,
            "status": v.status,
            "verified": v.verified,
        }
        for v in grievance.verifications
    ]

    return GrievanceDetailResponse(**response_data)


@router.patch(
    "/{grievance_id}",
    response_model=GrievanceResponse,
    summary="Update grievance",
    description="Update grievance status, assignment, or resolution.",
)
async def update_grievance(
    grievance_id: str,
    request: GrievanceUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["officer", "supervisor", "admin"])),
) -> GrievanceResponse:
    """Update grievance.

    Officers can update status and resolution.
    Supervisors can also reassign department/officer.
    Admins can do everything.

    Args:
        grievance_id: Public grievance ID
        request: Update request
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated grievance

    Raises:
        HTTPException 404: Grievance not found
        HTTPException 403: Not authorized
        HTTPException 422: Invalid status transition
    """
    stmt = select(Grievance).where(
        Grievance.grievance_id == grievance_id,
        Grievance.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    grievance = result.scalar_one_or_none()

    if grievance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance '{grievance_id}' not found",
        )

    # Check authorization
    if current_user.role == "officer":
        if grievance.assigned_officer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only assigned officer can update this grievance",
            )
        # Officers cannot reassign
        if request.assigned_officer_id or request.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only supervisors can reassign grievances",
            )

    # Validate status transition
    if request.status:
        valid_transitions: Dict[str, List[str]] = {
            "submitted": ["assigned", "rejected"],
            "assigned": ["in_progress", "rejected"],
            "in_progress": ["resolved", "assigned"],
            "resolved": ["verified", "in_progress"],
            "verified": ["closed"],
            "rejected": [],
            "closed": [],
        }
        current_status = grievance.status
        if request.status.value not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status transition: {current_status} -> {request.status.value}",
            )

        # Validate resolution text for resolved status
        if request.status.value == "resolved" and not request.resolution_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resolution text required when marking as resolved",
            )

        grievance.status = request.status.value

        # Update timestamps
        if request.status.value == "resolved":
            grievance.resolved_at = datetime.now(timezone.utc)
        elif request.status.value == "verified":
            grievance.verified_at = datetime.now(timezone.utc)
        elif request.status.value == "closed":
            grievance.closed_at = datetime.now(timezone.utc)

    # Update officer assignment (supervisor/admin only)
    if request.assigned_officer_id:
        grievance.assigned_officer_id = UUID(request.assigned_officer_id)
        grievance.assigned_at = datetime.now(timezone.utc)
        if grievance.status == "submitted":
            grievance.status = "assigned"

    # Update department (supervisor/admin only)
    if request.department_id:
        grievance.department_id = request.department_id

    # Update resolution
    if request.resolution_text:
        grievance.resolution_text = request.resolution_text
    if request.resolution_notes:
        grievance.resolution_notes = request.resolution_notes

    await db.commit()
    await db.refresh(grievance)

    logger.info(f"Grievance updated: {grievance_id} by {current_user.username}")

    return GrievanceResponse(
        **_build_grievance_response(grievance, grievance.district, grievance.department)
    )


@router.delete(
    "/{grievance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete grievance",
    description="Soft delete a grievance. Admin only.",
)
async def delete_grievance(
    grievance_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["admin"])),
) -> None:
    """Soft delete grievance.

    Only admins can delete grievances.

    Args:
        grievance_id: Public grievance ID
        db: Database session
        current_user: Authenticated admin user

    Raises:
        HTTPException 404: Grievance not found
    """
    stmt = select(Grievance).where(
        Grievance.grievance_id == grievance_id,
        Grievance.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    grievance = result.scalar_one_or_none()

    if grievance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance '{grievance_id}' not found",
        )

    # Soft delete
    grievance.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info(f"Grievance deleted: {grievance_id} by {current_user.username}")


@router.post(
    "/{grievance_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    summary="Upload attachment",
    description="Upload a file attachment for a grievance. Max 5 files, 10MB each.",
)
async def upload_attachment(
    grievance_id: str,
    file: UploadFile = File(..., description="File to upload"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["officer", "supervisor", "admin"])),
) -> Dict[str, Any]:
    """Upload attachment to grievance.

    Supports: image/jpeg, image/png, application/pdf, audio/mpeg, video/mp4
    Max size: 10MB per file
    Max files: 5 per grievance

    Args:
        grievance_id: Public grievance ID
        file: File to upload
        db: Database session
        current_user: Authenticated user

    Returns:
        Attachment details

    Raises:
        HTTPException 400: Invalid file type or too many files
        HTTPException 404: Grievance not found
        HTTPException 413: File too large
    """
    # Find grievance
    stmt = select(Grievance).where(
        Grievance.grievance_id == grievance_id,
        Grievance.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    grievance = result.scalar_one_or_none()

    if grievance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance '{grievance_id}' not found",
        )

    # Check attachment count
    attachment_count = len(grievance.attachments) if grievance.attachments else 0
    if attachment_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 attachments per grievance",
        )

    # Get file info
    file_name = file.filename or "unnamed"
    content_type = file.content_type or "application/octet-stream"

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "application/pdf", "audio/mpeg", "video/mp4"]
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed: {content_type}. Allowed: {allowed_types}",
        )

    # Upload file
    storage = get_storage_service()
    upload_result = await storage.upload_file(
        file=file.file,
        file_name=file_name,
        file_type=content_type,
        grievance_id=grievance_id,
    )

    if not upload_result.success:
        if "too large" in (upload_result.error or "").lower():
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=upload_result.error,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=upload_result.error or "Upload failed",
        )

    # Create attachment record
    attachment = Attachment(
        grievance_id=grievance.id,
        file_name=file_name,
        file_path=upload_result.file_path or "",
        file_type=content_type,
        file_size=upload_result.file_size_bytes,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    logger.info(f"Attachment uploaded: {attachment.id} for {grievance_id} by {current_user.username}")

    return {
        "id": str(attachment.id),
        "file_name": attachment.file_name,
        "file_type": attachment.file_type,
        "file_size_bytes": attachment.file_size,
        "file_url": upload_result.file_url,
        "file_hash": upload_result.file_hash,
        "uploaded_at": attachment.created_at.isoformat() if attachment.created_at else None,
    }


@router.get(
    "/{grievance_id}/attachments",
    summary="List attachments",
    description="List all attachments for a grievance.",
)
async def list_attachments(
    grievance_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["officer", "supervisor", "admin"])),
) -> List[Dict[str, Any]]:
    """List attachments for a grievance.

    Args:
        grievance_id: Public grievance ID
        db: Database session
        current_user: Authenticated user

    Returns:
        List of attachment details

    Raises:
        HTTPException 404: Grievance not found
    """
    stmt = select(Grievance).where(
        Grievance.grievance_id == grievance_id,
        Grievance.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    grievance = result.scalar_one_or_none()

    if grievance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance '{grievance_id}' not found",
        )

    return [
        {
            "id": str(a.id),
            "file_name": a.file_name,
            "file_type": a.file_type,
            "file_size_bytes": a.file_size,
            "file_url": f"/uploads/{a.file_path}",
            "uploaded_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in grievance.attachments
    ]


@router.delete(
    "/{grievance_id}/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete attachment",
    description="Delete an attachment from a grievance.",
)
async def delete_attachment(
    grievance_id: str,
    attachment_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["supervisor", "admin"])),
) -> None:
    """Delete attachment from grievance.

    Args:
        grievance_id: Public grievance ID
        attachment_id: Attachment UUID
        db: Database session
        current_user: Authenticated supervisor/admin

    Raises:
        HTTPException 404: Grievance or attachment not found
    """
    # Find grievance
    stmt = select(Grievance).where(
        Grievance.grievance_id == grievance_id,
        Grievance.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    grievance = result.scalar_one_or_none()

    if grievance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance '{grievance_id}' not found",
        )

    # Find attachment
    try:
        attachment_uuid = UUID(attachment_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid attachment ID format",
        )

    attachment_stmt = select(Attachment).where(
        Attachment.id == attachment_uuid,
        Attachment.grievance_id == grievance.id,
    )
    attachment_result = await db.execute(attachment_stmt)
    attachment = attachment_result.scalar_one_or_none()

    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment '{attachment_id}' not found",
        )

    # Delete file from storage
    storage = get_storage_service()
    await storage.delete_file(attachment.file_path)

    # Delete database record
    await db.delete(attachment)
    await db.commit()

    logger.info(f"Attachment deleted: {attachment_id} from {grievance_id} by {current_user.username}")


@router.patch(
    "/bulk",
    response_model=BulkUpdateResponse,
    summary="Bulk update grievances",
    description="Update multiple grievances at once. Supervisor/Admin only.",
)
async def bulk_update_grievances(
    request: BulkUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role(["supervisor", "admin"])),
) -> BulkUpdateResponse:
    """Bulk update grievances.

    Apply updates to multiple grievances in a single transaction.

    Args:
        request: Bulk update request with grievance IDs and updates
        db: Database session
        current_user: Authenticated supervisor/admin

    Returns:
        BulkUpdateResponse with results
    """
    if len(request.grievance_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update more than 100 grievances at once",
        )

    results = []
    updated_count = 0
    failed_count = 0

    for gid in request.grievance_ids:
        try:
            stmt = select(Grievance).where(
                Grievance.grievance_id == gid,
                Grievance.deleted_at.is_(None),
            )
            result = await db.execute(stmt)
            grievance = result.scalar_one_or_none()

            if grievance is None:
                results.append({
                    "grievance_id": gid,
                    "status": "failed",
                    "error": "Not found",
                })
                failed_count += 1
                continue

            # Apply updates from request.updates dict
            updates = request.updates
            if "assigned_officer_id" in updates:
                grievance.assigned_officer_id = UUID(updates["assigned_officer_id"])
                grievance.assigned_at = datetime.now(timezone.utc)
            if "status" in updates:
                grievance.status = updates["status"]

            results.append({
                "grievance_id": gid,
                "status": "success",
            })
            updated_count += 1

        except Exception as e:
            results.append({
                "grievance_id": gid,
                "status": "failed",
                "error": str(e),
            })
            failed_count += 1

    await db.commit()

    logger.info(
        f"Bulk update: {updated_count} updated, {failed_count} failed "
        f"by {current_user.username}"
    )

    return BulkUpdateResponse(
        message=f"Successfully updated {updated_count} of {len(request.grievance_ids)} grievances",
        updated_count=updated_count,
        failed_count=failed_count,
        results=results,
    )


def _build_grievance_response(
    grievance: Grievance,
    district: Optional[District],
    department: Optional[Department],
) -> Dict[str, Any]:
    """Build grievance response dict."""
    return {
        "id": str(grievance.id),
        "grievance_id": grievance.grievance_id,
        "citizen_name": grievance.citizen_name,
        "citizen_phone": grievance.citizen_phone,
        "citizen_email": grievance.citizen_email,
        "citizen_address": grievance.citizen_address,
        "status": grievance.status,
        "priority": grievance.priority,
        "department": {
            "id": str(department.id),
            "code": department.dept_code,
            "name": department.dept_name,
            "name_telugu": department.name_telugu,
        } if department else None,
        "district": {
            "id": str(district.id),
            "code": district.district_code,
            "name": district.district_name,
        } if district else None,
        "assigned_officer": {
            "id": str(grievance.assigned_officer_id),
        } if grievance.assigned_officer_id else None,
        "sla_days": grievance.sla_days,
        "due_date": grievance.due_date.isoformat() if grievance.due_date else None,
        "grievance_text": grievance.grievance_text,
        "language": grievance.language,
        "channel": grievance.channel,
        "created_at": grievance.created_at.isoformat() if grievance.created_at else None,
        "updated_at": grievance.updated_at.isoformat() if grievance.updated_at else None,
        "resolved_at": grievance.resolved_at.isoformat() if grievance.resolved_at else None,
        "verified_at": grievance.verified_at.isoformat() if grievance.verified_at else None,
    }


@router.get(
    "/{grievance_id}/sentiment",
    response_model=GrievanceSentimentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sentiment analysis for grievance",
    description="Get stored sentiment analysis results for a grievance.",
    tags=["Empathy"],
)
async def get_grievance_sentiment(
    grievance_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> GrievanceSentimentResponse:
    """Get stored sentiment analysis for a grievance.

    This endpoint returns the distress analysis stored for a grievance,
    including distress score, level, detected keywords, and SLA adjustments.

    Args:
        grievance_id: The grievance ID (PGRS-YYYY-XXX-NNNNN format)

    Returns:
        GrievanceSentimentResponse with stored analysis data

    Raises:
        HTTPException 404 if grievance sentiment not found
    """
    service = get_empathy_service(db)
    sentiment = await service.get_grievance_sentiment(grievance_id)

    if sentiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "EMPATHY_003",
                "message": f"Sentiment not found for grievance {grievance_id}",
            },
        )

    return sentiment
