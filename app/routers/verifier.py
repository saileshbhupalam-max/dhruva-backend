"""Verifier Portal Router.

Provides community verification gamification endpoints:
- GET /verification/queue - Public verification queue
- POST /verification/submit - Submit verification result (OTP-protected)
- GET /verification/verifier-stats - Get verifier statistics
- GET /verification/leaderboard - Community leaderboard
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.schemas.verifier import (
    LeaderboardPeriod,
    LeaderboardResponse,
    QueueStatus,
    VerificationQueueResponse,
    VerificationSubmitRequest,
    VerificationSubmitResponse,
    VerifierStatsResponse,
)
from app.services.verifier_service import get_verifier_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/verification", tags=["Verifier Portal"])


@router.get(
    "/queue",
    response_model=VerificationQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Get verification queue",
    description="Public endpoint - returns grievances resolved and awaiting community verification.",
)
async def get_verification_queue(
    status_filter: Optional[QueueStatus] = Query(
        None,
        alias="status",
        description="Filter by status (pending/in_progress)",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of items to return",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of items to skip",
    ),
    db: AsyncSession = Depends(get_db_session),
) -> VerificationQueueResponse:
    """Get verification queue for community verifiers.

    This endpoint returns grievances that have been resolved by departments
    and are awaiting community verification. The queue is ordered by
    resolution date (oldest first).

    Args:
        status_filter: Optional filter by status
        limit: Maximum items to return (1-100)
        offset: Number of items to skip for pagination
        db: Database session

    Returns:
        VerificationQueueResponse with queue items, total count, and pagination info
    """
    try:
        service = get_verifier_service(db)
        result = await service.get_verification_queue(
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        logger.info(f"Retrieved verification queue: {len(result.items)} items")
        return result
    except Exception as e:
        logger.error(f"Error fetching verification queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "VERIFIER_001",
                "message": "Failed to fetch verification queue",
                "details": str(e),
            },
        )


@router.post(
    "/submit",
    response_model=VerificationSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit verification result",
    description="OTP-protected endpoint - submit community verification result for a grievance.",
)
async def submit_verification(
    request: VerificationSubmitRequest,
    db: AsyncSession = Depends(get_db_session),
) -> VerificationSubmitResponse:
    """Submit verification result and earn points.

    This endpoint processes a community verification submission:
    1. Validates the verifier phone number
    2. Calculates points based on result, confidence, and streak
    3. Updates verifier profile statistics
    4. Creates activity record for streak tracking
    5. Awards badges if thresholds are met

    Point system:
    - VERIFIED: 10 points (base)
    - DISPUTED: 5 points (base)
    - INCONCLUSIVE: 3 points (base)
    - Streak bonus: 1.5x multiplier for 3+ day streaks
    - High confidence bonus: +5 points for confidence >= 0.8

    Badge levels:
    - BRONZE: 0-99 points
    - SILVER: 100-499 points
    - GOLD: 500-999 points
    - CHAMPION: 1000+ points

    NOTE: In production, this endpoint should be protected with OTP verification.
    For now, it accepts the verifier_phone in the request body.

    Args:
        request: Verification submission data
        db: Database session

    Returns:
        VerificationSubmitResponse with points earned and badge info
    """
    try:
        service = get_verifier_service(db)
        result = await service.submit_verification(request)
        logger.info(
            f"Verification submitted successfully: {request.grievance_id} "
            f"by {request.verifier_phone}"
        )
        return result
    except ValueError as e:
        # Business logic validation errors
        logger.warning(f"Validation error in verification submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VERIFIER_002",
                "message": "Invalid verification submission",
                "details": str(e),
            },
        )
    except Exception as e:
        logger.error(f"Error submitting verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "VERIFIER_003",
                "message": "Failed to submit verification",
                "details": str(e),
            },
        )


@router.get(
    "/verifier-stats",
    response_model=VerifierStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get verifier statistics",
    description="Public endpoint - get statistics and gamification data for a verifier by phone number.",
)
async def get_verifier_stats(
    phone: str = Query(
        ...,
        pattern=r"^\+91[6-9]\d{9}$",
        description="Verifier phone number (+91XXXXXXXXXX)",
    ),
    db: AsyncSession = Depends(get_db_session),
) -> VerifierStatsResponse:
    """Get statistics for a community verifier.

    Returns comprehensive statistics including:
    - Total verifications and breakdown by result type
    - Accuracy rate (percentage of VERIFIED results)
    - Total points and current leaderboard rank
    - Badge level and all badges earned
    - Current streak and join date

    Args:
        phone: Verifier phone number
        db: Database session

    Returns:
        VerifierStatsResponse with complete statistics

    Raises:
        404: If verifier profile not found
    """
    try:
        service = get_verifier_service(db)
        result = await service.get_verifier_stats(phone)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "VERIFIER_004",
                    "message": "Verifier profile not found",
                    "details": f"No profile found for phone: {phone}",
                },
            )

        logger.info(f"Retrieved stats for verifier: {phone}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching verifier stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "VERIFIER_005",
                "message": "Failed to fetch verifier statistics",
                "details": str(e),
            },
        )


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get verifier leaderboard",
    description="Public endpoint - get ranked list of top community verifiers.",
)
async def get_leaderboard(
    period: LeaderboardPeriod = Query(
        LeaderboardPeriod.ALL_TIME,
        description="Time period (weekly/monthly/all_time)",
    ),
    district: Optional[str] = Query(
        None,
        description="Optional filter by district name",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of entries to return",
    ),
    db: AsyncSession = Depends(get_db_session),
) -> LeaderboardResponse:
    """Get community verifier leaderboard.

    Returns ranked list of verifiers based on total points earned.
    Supports filtering by time period and district.

    Rankings are ordered by:
    1. Total points (descending)
    2. Join date (ascending) - earlier joiners ranked higher for ties

    Phone numbers are masked for privacy (e.g., +91****12).

    Args:
        period: Time period filter
        district: Optional district name filter
        limit: Maximum entries to return (1-100)
        db: Database session

    Returns:
        LeaderboardResponse with rankings and period info
    """
    try:
        service = get_verifier_service(db)
        result = await service.get_leaderboard(
            period=period,
            district=district,
            limit=limit,
        )
        logger.info(
            f"Retrieved leaderboard: period={period.value}, "
            f"district={district}, entries={len(result.leaders)}"
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "VERIFIER_006",
                "message": "Failed to fetch leaderboard",
                "details": str(e),
            },
        )
