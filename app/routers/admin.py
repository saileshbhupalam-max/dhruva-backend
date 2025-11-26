"""Admin analytics router.

Provides admin-only endpoints for:
- Fraud detection metrics
- NLP performance analytics
- Department analytics
- System overview metrics
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.admin import (
    DepartmentAnalyticsResponse,
    FraudMetricsResponse,
    NLPMetricsResponse,
    SystemMetricsResponse,
)
from app.services.admin_analytics_service import AdminAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin")


@router.get(
    "/fraud/metrics",
    response_model=FraudMetricsResponse,
    summary="Get fraud detection metrics",
    description=(
        "Admin only - Returns fraud detection analytics including:\n"
        "- Scatter plot data (photo similarity vs resolution time)\n"
        "- Box plot data (officer resolution time distribution)\n"
        "- Benford's Law analysis\n"
        "- Flagged cases for manual review\n"
        "- Summary statistics"
    ),
)
async def get_fraud_metrics(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
) -> FraudMetricsResponse:
    """Get fraud detection metrics.

    Analyzes grievance data for potential fraud patterns using:
    - Photo verification similarity scores
    - Officer resolution time patterns
    - Statistical anomaly detection (Benford's Law)

    Args:
        current_user: Current admin user
        db: Database session

    Returns:
        FraudMetricsResponse with comprehensive fraud detection data

    Raises:
        HTTPException 403: If user is not an admin
    """
    logger.info(f"Admin {current_user.username} requested fraud metrics")

    service = AdminAnalyticsService(db)
    metrics = await service.get_fraud_metrics()

    logger.info(
        f"Fraud metrics generated: {metrics.summary.total_analyzed} cases analyzed, "
        f"{metrics.summary.flagged_count} flagged"
    )

    return metrics


@router.get(
    "/nlp/metrics",
    response_model=NLPMetricsResponse,
    summary="Get NLP performance metrics",
    description=(
        "Admin only - Returns NLP classification performance including:\n"
        "- Overall accuracy\n"
        "- Accuracy trends over time\n"
        "- Confusion matrix\n"
        "- Top misclassifications\n"
        "- Language distribution\n"
        "- Model information"
    ),
)
async def get_nlp_metrics(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
) -> NLPMetricsResponse:
    """Get NLP performance metrics.

    Returns detailed analytics about the NLP classification model's
    performance including accuracy trends, confusion matrix, and
    common misclassification patterns.

    Note: Currently returns mock data with realistic structure.
    Will be replaced with actual classification logs in future.

    Args:
        current_user: Current admin user
        db: Database session

    Returns:
        NLPMetricsResponse with model performance data

    Raises:
        HTTPException 403: If user is not an admin
    """
    logger.info(f"Admin {current_user.username} requested NLP metrics")

    service = AdminAnalyticsService(db)
    metrics = await service.get_nlp_metrics()

    logger.info(f"NLP metrics generated: {metrics['overall_accuracy']:.2%} accuracy")

    return metrics


@router.get(
    "/departments/analytics",
    response_model=DepartmentAnalyticsResponse,
    summary="Get department analytics",
    description=(
        "Admin only - Returns department performance analytics including:\n"
        "- SLA compliance heatmap\n"
        "- Satisfaction trends over time\n"
        "- Performance ranking by department\n\n"
        "Supports time period filtering: 30d, 90d, 1y"
    ),
)
async def get_department_analytics(
    period: Literal["30d", "90d", "1y"] = Query(
        "30d",
        description="Time period for analytics (30 days, 90 days, or 1 year)",
    ),
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
) -> DepartmentAnalyticsResponse:
    """Get department analytics with SLA and satisfaction metrics.

    Analyzes department performance across multiple dimensions:
    - SLA compliance (within SLA, near breach, breached)
    - Satisfaction scores from call center data
    - Overall performance ranking

    Args:
        period: Time period for analysis (30d, 90d, 1y)
        current_user: Current admin user
        db: Database session

    Returns:
        DepartmentAnalyticsResponse with department performance data

    Raises:
        HTTPException 403: If user is not an admin
    """
    logger.info(
        f"Admin {current_user.username} requested department analytics "
        f"for period: {period}"
    )

    service = AdminAnalyticsService(db)
    analytics = await service.get_department_analytics(period=period)

    logger.info(
        f"Department analytics generated: {len(analytics['performance_ranking'])} "
        "departments analyzed"
    )

    return analytics


@router.get(
    "/system/metrics",
    response_model=SystemMetricsResponse,
    summary="Get system overview metrics",
    description=(
        "Admin only - Returns comprehensive system metrics including:\n"
        "- Grievance statistics (total, today, week, month, growth)\n"
        "- User statistics (officers, citizens)\n"
        "- Resolution performance\n"
        "- Empathy engine statistics\n"
        "- Verification statistics\n"
        "- Growth chart (30-day trend)"
    ),
)
async def get_system_metrics(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db_session),
) -> SystemMetricsResponse:
    """Get system-wide overview metrics.

    Provides a comprehensive dashboard view of the entire system including:
    - Grievance volume and trends
    - User activity
    - Resolution performance by department
    - Empathy engine effectiveness
    - Verification status
    - 30-day growth trends

    Args:
        current_user: Current admin user
        db: Database session

    Returns:
        SystemMetricsResponse with system-wide metrics

    Raises:
        HTTPException 403: If user is not an admin
    """
    logger.info(f"Admin {current_user.username} requested system metrics")

    service = AdminAnalyticsService(db)
    metrics = await service.get_system_metrics()

    logger.info(
        f"System metrics generated: {metrics['grievances'].total} total grievances, "
        f"{metrics['users'].total_officers} officers"
    )

    return metrics
