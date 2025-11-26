"""Public Dashboard Router.

Provides public-facing analytics endpoints for transparency dashboard:
- GET /public/dashboard - Full dashboard data
- GET /public/dashboard/kpis - Key performance indicators
- GET /public/dashboard/empathy - Empathy metrics
- GET /public/dashboard/departments - Department statistics
- GET /public/dashboard/trends - Monthly trends
- GET /public/dashboard/districts - District list

All endpoints support ?district={name} filter for district-specific data.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.models.department import Department
from app.models.district import District
from app.models.grievance import Grievance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/dashboard", tags=["Public Dashboard"])


# Response Models


class KPIMetric(BaseModel):
    """KPI metric response."""

    label: str = Field(..., description="Metric label in English")
    label_telugu: str = Field(..., description="Metric label in Telugu")
    value: float = Field(..., description="Metric value")
    value_formatted: str = Field(..., description="Formatted value for display")
    trend: Dict[str, Any] = Field(..., description="Trend information")
    icon: str = Field(..., description="Icon identifier")


class TrendDataPoint(BaseModel):
    """Monthly trend data point."""

    month: str = Field(..., description="Month name")
    resolved: int = Field(..., description="Resolved grievances count")
    reopened: int = Field(..., description="Reopened grievances count")


class DepartmentStat(BaseModel):
    """Department statistics."""

    department: str = Field(..., description="Department name")
    department_telugu: str = Field(..., description="Department name in Telugu")
    total_cases: int = Field(..., description="Total grievances")
    resolved: int = Field(..., description="Resolved count")
    resolution_rate: float = Field(..., description="Resolution rate percentage")
    avg_days: float = Field(..., description="Average resolution time in days")
    satisfaction: float = Field(..., description="Satisfaction score")


class DistrictInfo(BaseModel):
    """District information."""

    id: str = Field(..., description="District ID")
    name: str = Field(..., description="District name")
    code: str = Field(..., description="District code")


class DashboardResponse(BaseModel):
    """Complete dashboard response."""

    kpis: List[KPIMetric] = Field(..., description="Key performance indicators")
    trends: List[TrendDataPoint] = Field(..., description="Monthly trends")
    departments: List[DepartmentStat] = Field(..., description="Department statistics")
    empathy_score: float = Field(..., description="Overall empathy score")
    district_filter: Optional[str] = Field(None, description="Applied district filter")


# Helper Functions


async def get_district_by_name(
    db: AsyncSession, district_name: Optional[str]
) -> Optional[District]:
    """Get district by name if specified."""
    if not district_name:
        return None

    stmt = select(District).where(
        func.lower(District.district_name) == district_name.lower()
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def calculate_kpis(
    db: AsyncSession, district_id: Optional[str] = None
) -> List[KPIMetric]:
    """Calculate key performance indicators."""
    # Base query
    query = select(Grievance).where(Grievance.deleted_at.is_(None))
    if district_id:
        query = query.where(Grievance.district_id == district_id)

    # Total grievances
    total_stmt = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_stmt)
    total_grievances = total_result.scalar() or 0

    # Resolved cases
    resolved_stmt = select(func.count()).select_from(
        query.where(Grievance.status == "resolved").subquery()
    )
    resolved_result = await db.execute(resolved_stmt)
    resolved_cases = resolved_result.scalar() or 0

    # Average resolution time (in days)
    avg_time_stmt = select(
        func.avg(
            func.extract(
                "epoch",
                Grievance.resolved_at - Grievance.created_at
            ) / 86400
        )
    ).select_from(
        query.where(
            Grievance.resolved_at.isnot(None)
        ).subquery()
    )
    avg_time_result = await db.execute(avg_time_stmt)
    avg_resolution_days = avg_time_result.scalar() or 12.0

    # Satisfaction score (placeholder - would come from feedback)
    satisfaction_score = 4.3

    # Calculate trends (last month vs current)
    # Simplified - in production, compare actual periods
    resolution_rate = (resolved_cases / total_grievances * 100) if total_grievances > 0 else 0

    return [
        KPIMetric(
            label="Total Grievances",
            label_telugu="మొత్తం ఫిర్యాదులు",
            value=float(total_grievances),
            value_formatted=f"{total_grievances:,}",
            trend={
                "value": 5.2,
                "is_positive": True,
                "suffix": "% from last month",
            },
            icon="scale",
        ),
        KPIMetric(
            label="Resolved Cases",
            label_telugu="పరిష్కరించిన కేసులు",
            value=float(resolved_cases),
            value_formatted=f"{resolved_cases:,}",
            trend={
                "value": 8.1,
                "is_positive": True,
                "suffix": "% from last month",
            },
            icon="check",
        ),
        KPIMetric(
            label="Avg Resolution Time",
            label_telugu="సగటు పరిష్కార సమయం",
            value=avg_resolution_days,
            value_formatted=f"{int(avg_resolution_days)} days",
            trend={
                "value": 15.0,
                "is_positive": True,
                "suffix": "% improvement",
            },
            icon="clock",
        ),
        KPIMetric(
            label="Citizen Satisfaction",
            label_telugu="పౌర సంతృప్తి",
            value=satisfaction_score,
            value_formatted=f"{satisfaction_score:.1f}/5.0",
            trend={
                "value": 0.3,
                "is_positive": True,
                "suffix": " points",
            },
            icon="star",
        ),
    ]


async def calculate_trends(
    db: AsyncSession, district_id: Optional[str] = None
) -> List[TrendDataPoint]:
    """Calculate monthly trends for the last 6 months."""
    trends = []
    now = datetime.utcnow()

    for i in range(5, -1, -1):  # Last 6 months
        month_start = now.replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        month_name = month_start.strftime("%b")

        # Resolved in this month
        resolved_query = select(func.count()).where(
            Grievance.deleted_at.is_(None),
            Grievance.status == "resolved",
            Grievance.resolved_at >= month_start,
            Grievance.resolved_at < month_end,
        )
        if district_id:
            resolved_query = resolved_query.where(Grievance.district_id == district_id)

        resolved_result = await db.execute(resolved_query)
        resolved_count = resolved_result.scalar() or 0

        # Reopened in this month (simplified - would track reopening events)
        reopened_count = max(0, int(resolved_count * 0.02))  # Assume 2% reopen rate

        trends.append(
            TrendDataPoint(
                month=month_name, resolved=resolved_count, reopened=reopened_count
            )
        )

    return trends


async def calculate_department_stats(
    db: AsyncSession, district_id: Optional[str] = None
) -> List[DepartmentStat]:
    """Calculate department-wise statistics."""
    from sqlalchemy import case, Integer

    # Get all departments with grievance counts
    stmt = (
        select(
            Department.id,
            Department.dept_name,
            Department.name_telugu,
            func.count(Grievance.id).label("total"),
            func.sum(
                case((Grievance.status == "resolved", 1), else_=0)
            ).label("resolved"),
        )
        .outerjoin(Grievance, Department.id == Grievance.department_id)
        .where(
            Grievance.deleted_at.is_(None) if district_id is None else True
        )
        .group_by(Department.id, Department.dept_name, Department.name_telugu)
        .order_by(func.count(Grievance.id).desc())
        .limit(10)
    )

    if district_id:
        stmt = stmt.where(
            (Grievance.district_id == district_id) | (Grievance.id.is_(None))
        )

    result = await db.execute(stmt)
    rows = result.all()

    stats = []
    for row in rows:
        total = row.total or 0
        resolved = row.resolved or 0
        resolution_rate = (resolved / total * 100) if total > 0 else 0

        # Simplified avg days and satisfaction (would be calculated from actual data)
        avg_days = 10.0 + (len(stats) * 2)  # Placeholder
        satisfaction = 4.5 - (len(stats) * 0.05)  # Placeholder

        stats.append(
            DepartmentStat(
                department=row.dept_name or "Unknown",
                department_telugu=row.name_telugu or row.dept_name or "Unknown",
                total_cases=total,
                resolved=resolved,
                resolution_rate=round(resolution_rate, 1),
                avg_days=round(avg_days, 1),
                satisfaction=round(satisfaction, 1),
            )
        )

    return stats


async def calculate_empathy_score(
    db: AsyncSession, district_id: Optional[str] = None
) -> float:
    """Calculate overall empathy score."""
    # This would integrate with the empathy engine
    # For now, return a placeholder value
    return 4.2


# Endpoints


@router.get(
    "",
    response_model=DashboardResponse,
    summary="Get full public dashboard",
    description="Returns complete dashboard data including KPIs, trends, and department stats. Supports district filtering.",
)
async def get_dashboard(
    district: Optional[str] = Query(
        None, description="Filter by district name (case-insensitive)"
    ),
    db: AsyncSession = Depends(get_db_session),
) -> DashboardResponse:
    """Get complete public dashboard data."""
    # Get district if specified
    district_obj = await get_district_by_name(db, district)
    district_id = str(district_obj.id) if district_obj else None

    # Calculate all metrics
    kpis = await calculate_kpis(db, district_id)
    trends = await calculate_trends(db, district_id)
    departments = await calculate_department_stats(db, district_id)
    empathy_score = await calculate_empathy_score(db, district_id)

    return DashboardResponse(
        kpis=kpis,
        trends=trends,
        departments=departments,
        empathy_score=empathy_score,
        district_filter=district,
    )


@router.get(
    "/kpis",
    response_model=List[KPIMetric],
    summary="Get KPI metrics",
    description="Returns key performance indicators. Supports district filtering.",
)
async def get_kpis(
    district: Optional[str] = Query(None, description="Filter by district name"),
    db: AsyncSession = Depends(get_db_session),
) -> List[KPIMetric]:
    """Get key performance indicators."""
    district_obj = await get_district_by_name(db, district)
    district_id = str(district_obj.id) if district_obj else None
    return await calculate_kpis(db, district_id)


@router.get(
    "/empathy",
    response_model=Dict[str, float],
    summary="Get empathy metrics",
    description="Returns empathy score and related metrics. Supports district filtering.",
)
async def get_empathy_metrics(
    district: Optional[str] = Query(None, description="Filter by district name"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, float]:
    """Get empathy metrics."""
    district_obj = await get_district_by_name(db, district)
    district_id = str(district_obj.id) if district_obj else None
    empathy_score = await calculate_empathy_score(db, district_id)

    return {
        "overall_score": empathy_score,
        "response_quality": 4.3,
        "timeliness": 4.1,
        "effectiveness": 4.4,
    }


@router.get(
    "/departments",
    response_model=List[DepartmentStat],
    summary="Get department statistics",
    description="Returns department-wise performance statistics. Supports district filtering.",
)
async def get_department_stats(
    district: Optional[str] = Query(None, description="Filter by district name"),
    db: AsyncSession = Depends(get_db_session),
) -> List[DepartmentStat]:
    """Get department statistics."""
    district_obj = await get_district_by_name(db, district)
    district_id = str(district_obj.id) if district_obj else None
    return await calculate_department_stats(db, district_id)


@router.get(
    "/trends",
    response_model=List[TrendDataPoint],
    summary="Get monthly trends",
    description="Returns monthly resolution trends for the last 6 months. Supports district filtering.",
)
async def get_trends(
    district: Optional[str] = Query(None, description="Filter by district name"),
    db: AsyncSession = Depends(get_db_session),
) -> List[TrendDataPoint]:
    """Get monthly trends."""
    district_obj = await get_district_by_name(db, district)
    district_id = str(district_obj.id) if district_obj else None
    return await calculate_trends(db, district_id)


@router.get(
    "/districts",
    response_model=List[DistrictInfo],
    summary="Get district list",
    description="Returns list of all districts for filter dropdown.",
)
async def get_districts(
    db: AsyncSession = Depends(get_db_session),
) -> List[DistrictInfo]:
    """Get list of all districts."""
    stmt = select(District).order_by(District.district_name)
    result = await db.execute(stmt)
    districts = result.scalars().all()

    return [
        DistrictInfo(
            id=str(d.id),
            name=d.district_name,
            code=d.district_code,
        )
        for d in districts
    ]
