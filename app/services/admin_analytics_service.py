"""Admin analytics service for dashboard metrics.

Provides business logic for:
- Fraud detection metrics (scatter, box plot, Benford's Law)
- NLP performance metrics
- Department analytics (SLA, satisfaction)
- System overview metrics
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.empathy import GrievanceSentiment
from app.models.grievance import Grievance
from app.models.satisfaction_metric import SatisfactionMetric
from app.models.user import User
from app.models.verification import Verification
from app.schemas.admin import (
    AccuracyTrendPoint,
    BenfordDigitData,
    BoxPlotData,
    ConfusionMatrixData,
    DepartmentPerformance,
    EmpathyStats,
    FlaggedCase,
    FraudMetricsResponse,
    FraudSummary,
    GrievanceStats,
    GrowthChartPoint,
    LanguageDistribution,
    MisclassificationCase,
    ModelInfo,
    ResolutionStats,
    SatisfactionTrend,
    ScatterDataPoint,
    SLAHeatmapData,
    UserStats,
    VerificationStats,
)

logger = logging.getLogger(__name__)


class AdminAnalyticsService:
    """Service for admin analytics calculations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session.

        Args:
            db: AsyncIO database session
        """
        self.db = db

    async def get_fraud_metrics(self) -> FraudMetricsResponse:
        """Get fraud detection metrics.

        Analyzes:
        - Photo similarity vs resolution time (scatter plot)
        - Officer resolution time distribution (box plot)
        - Benford's Law analysis on resolution times
        - Flagged cases for manual review

        Returns:
            FraudMetricsResponse with all fraud detection data
        """
        # Get grievances with resolution data
        stmt = (
            select(
                Grievance.grievance_id,
                Grievance.assigned_officer_id,
                Grievance.submitted_at,
                Grievance.resolved_at,
                User.full_name.label("officer_name"),
            )
            .outerjoin(User, Grievance.assigned_officer_id == User.id)
            .where(
                and_(
                    Grievance.resolved_at.isnot(None),
                    Grievance.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        grievances = result.all()

        # Calculate scatter data (mocked photo similarity for now)
        scatter_data = []
        officer_times: Dict[str, List[float]] = defaultdict(list)

        for g in grievances:
            if g.resolved_at and g.submitted_at and g.assigned_officer_id:
                resolution_time = (g.resolved_at - g.submitted_at).total_seconds() / 86400

                # Mock photo similarity (in production, fetch from verification table)
                photo_similarity = self._mock_photo_similarity(resolution_time)

                is_flagged = photo_similarity > 0.92 and resolution_time < 2.0

                scatter_data.append(
                    ScatterDataPoint(
                        grievance_id=g.grievance_id,
                        photo_similarity=photo_similarity,
                        resolution_time_days=round(resolution_time, 2),
                        officer_id=str(g.assigned_officer_id),
                        officer_name=g.officer_name or "Unknown",
                        is_flagged=is_flagged,
                    )
                )

                officer_times[str(g.assigned_officer_id)].append(resolution_time)

        # Calculate box plot data per officer
        box_plot_data = []
        for officer_id, times in officer_times.items():
            if len(times) >= 5:  # Only include officers with enough data
                box_stats = self._calculate_box_plot_stats(times)
                officer_name = next(
                    (g.officer_name for g in grievances if str(g.assigned_officer_id) == officer_id),
                    "Unknown"
                )
                box_plot_data.append(
                    BoxPlotData(
                        officer_id=officer_id,
                        officer_name=officer_name or "Unknown",
                        **box_stats,
                    )
                )

        # Benford's Law analysis
        benford_data = self._calculate_benford_analysis(
            [g.resolution_time_days for g in scatter_data]
        )

        # Get flagged cases
        flagged_cases = [
            FlaggedCase(
                grievance_id=g.grievance_id,
                officer_id=g.officer_id,
                officer_name=g.officer_name,
                flag_reasons=["High photo similarity", "Suspiciously fast resolution"],
                photo_similarity=g.photo_similarity,
                resolution_time_days=g.resolution_time_days,
                flagged_at=datetime.now(timezone.utc),
                review_status="pending",
            )
            for g in scatter_data if g.is_flagged
        ]

        # Summary statistics
        summary = FraudSummary(
            total_analyzed=len(scatter_data),
            flagged_count=len(flagged_cases),
            reviewed_count=0,  # TODO: Track in database
            confirmed_fraud=0,  # TODO: Track in database
        )

        return FraudMetricsResponse(
            scatter_data=scatter_data,
            box_plot_data=box_plot_data,
            benford_data=benford_data,
            flagged_cases=flagged_cases,
            summary=summary,
        )

    async def get_nlp_metrics(self) -> dict:
        """Get NLP performance metrics.

        Since we don't have classification logs yet, returns realistic mock data
        with proper structure for future integration.

        Returns:
            Dict with NLP performance metrics
        """
        # Get language distribution from actual data
        stmt = (
            select(
                Grievance.language,
                func.count(Grievance.id).label("count"),
            )
            .where(Grievance.deleted_at.is_(None))
            .group_by(Grievance.language)
        )
        result = await self.db.execute(stmt)
        lang_data = result.all()

        total = sum(row.count for row in lang_data)
        language_distribution = [
            LanguageDistribution(
                language=row.language,
                count=row.count,
                percentage=round((row.count / total) * 100, 1) if total > 0 else 0.0,
            )
            for row in lang_data
        ]

        # Mock data for other metrics (replace with real data when classification logs exist)
        overall_accuracy = 0.87

        accuracy_trend = [
            AccuracyTrendPoint(
                date=(datetime.now(timezone.utc) - timedelta(days=30-i)).strftime("%Y-%m-%d"),
                accuracy=round(0.82 + (i * 0.002), 3),
                sample_count=120 + (i * 5),
            )
            for i in range(30)
        ]

        # Mock confusion matrix
        categories = ["Health", "Revenue", "Roads", "Water", "Education", "Other"]
        confusion_matrix = ConfusionMatrixData(
            labels=categories,
            matrix=[
                [45, 3, 1, 0, 1, 0],  # Health
                [2, 38, 1, 0, 0, 1],  # Revenue
                [1, 0, 42, 2, 0, 1],  # Roads
                [0, 1, 1, 40, 0, 0],  # Water
                [1, 0, 0, 0, 35, 2],  # Education
                [0, 2, 1, 1, 1, 30],  # Other
            ],
        )

        top_misclassifications = [
            MisclassificationCase(
                true_category="Health",
                predicted_category="Revenue",
                count=3,
                example_text="Medical bill payment issue at government hospital",
            ),
            MisclassificationCase(
                true_category="Revenue",
                predicted_category="Other",
                count=2,
                example_text="Property tax payment not reflecting in records",
            ),
            MisclassificationCase(
                true_category="Roads",
                predicted_category="Water",
                count=2,
                example_text="Drainage issue on main road causing flooding",
            ),
        ]

        model_info = ModelInfo(
            model_version="v3.2",
            training_samples=5000,
            categories=categories,
            last_trained=datetime.now(timezone.utc) - timedelta(days=7),
        )

        return {
            "overall_accuracy": overall_accuracy,
            "accuracy_trend": accuracy_trend,
            "confusion_matrix": confusion_matrix,
            "top_misclassifications": top_misclassifications,
            "language_distribution": language_distribution,
            "model_info": model_info,
        }

    async def get_department_analytics(self, period: str = "30d") -> dict:
        """Get department analytics with SLA and satisfaction data.

        Args:
            period: Time period (30d, 90d, 1y)

        Returns:
            Dict with department analytics
        """
        # Calculate date range
        days_map = {"30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(period, 30)
        since_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get department data with grievance stats
        stmt = (
            select(
                Department.dept_name,
                Department.sla_days,
                func.count(Grievance.id).label("total_grievances"),
                func.avg(
                    func.extract(
                        "epoch",
                        Grievance.resolved_at - Grievance.submitted_at
                    ) / 86400
                ).label("avg_resolution_days"),
            )
            .outerjoin(Grievance, Department.id == Grievance.department_id)
            .where(
                and_(
                    Grievance.submitted_at >= since_date,
                    Grievance.deleted_at.is_(None),
                )
            )
            .group_by(Department.id, Department.dept_name, Department.sla_days)
        )
        result = await self.db.execute(stmt)
        dept_data = result.all()

        # Calculate SLA compliance for each department
        sla_heatmap = []
        performance_ranking = []

        for dept in dept_data:
            # Get SLA breakdown
            sla_stmt = (
                select(
                    func.count(Grievance.id).label("count"),
                    func.extract(
                        "epoch",
                        Grievance.due_date - Grievance.submitted_at
                    ).label("sla_seconds"),
                    func.extract(
                        "epoch",
                        Grievance.resolved_at - Grievance.submitted_at
                    ).label("resolution_seconds"),
                )
                .where(
                    and_(
                        Grievance.department_id == Department.id,
                        Department.dept_name == dept.dept_name,
                        Grievance.submitted_at >= since_date,
                        Grievance.resolved_at.isnot(None),
                        Grievance.deleted_at.is_(None),
                    )
                )
            )
            sla_result = await self.db.execute(sla_stmt)
            sla_cases = sla_result.all()

            within_sla = 0
            near_breach = 0
            breached = 0

            for case in sla_cases:
                if case.resolution_seconds and case.sla_seconds:
                    ratio = case.resolution_seconds / case.sla_seconds
                    if ratio <= 1.0:
                        within_sla += 1
                    elif ratio <= 1.2:
                        near_breach += 1
                    else:
                        breached += 1

            sla_heatmap.append(
                SLAHeatmapData(
                    department=dept.dept_name,
                    within_sla=within_sla,
                    near_breach=near_breach,
                    breached=breached,
                )
            )

            # Calculate performance metrics
            total_cases = within_sla + near_breach + breached
            sla_compliance = within_sla / total_cases if total_cases > 0 else 0.0

            performance_ranking.append({
                "department": dept.dept_name,
                "avg_resolution_days": round(float(dept.avg_resolution_days or 0), 1),
                "sla_compliance_rate": round(sla_compliance, 2),
                "total_grievances": dept.total_grievances or 0,
            })

        # Get satisfaction data
        satisfaction_stmt = (
            select(
                Department.dept_name,
                SatisfactionMetric.avg_satisfaction_5,
                SatisfactionMetric.total_feedback,
            )
            .join(SatisfactionMetric, Department.id == SatisfactionMetric.department_id)
        )
        satisfaction_result = await self.db.execute(satisfaction_stmt)
        satisfaction_data = satisfaction_result.all()

        # Add satisfaction to performance ranking
        satisfaction_map = {
            row.dept_name: row.avg_satisfaction_5
            for row in satisfaction_data
        }

        for perf in performance_ranking:
            perf["satisfaction_score"] = satisfaction_map.get(perf["department"], 0.0)

        # Sort by composite score and add rank
        performance_ranking.sort(
            key=lambda x: (
                x["sla_compliance_rate"] * 0.4 +
                (1 - x["avg_resolution_days"] / 30) * 0.3 +  # Normalize to 30 days
                (x["satisfaction_score"] / 5) * 0.3
            ),
            reverse=True,
        )

        for i, perf in enumerate(performance_ranking, 1):
            perf["rank"] = i

        # Convert to Pydantic models
        performance_ranking = [
            DepartmentPerformance(**perf) for perf in performance_ranking
        ]

        # Mock satisfaction trends (replace with time-series data when available)
        satisfaction_trends = []
        for dept_name, avg_sat in satisfaction_map.items():
            for i in range(6):  # Last 6 months
                date = (datetime.now(timezone.utc) - timedelta(days=30*i)).strftime("%Y-%m")
                satisfaction_trends.append(
                    SatisfactionTrend(
                        department=dept_name,
                        date=date,
                        avg_satisfaction=round(avg_sat + ((-0.2 + (i * 0.05))), 1),
                        feedback_count=150 + (i * 10),
                    )
                )

        return {
            "sla_heatmap": sla_heatmap,
            "satisfaction_trends": satisfaction_trends,
            "performance_ranking": performance_ranking,
        }

    async def get_system_metrics(self) -> dict:
        """Get system overview metrics.

        Returns:
            Dict with system-wide metrics
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        prev_month_start = now - timedelta(days=60)

        # Grievance statistics
        total_stmt = select(func.count(Grievance.id)).where(
            Grievance.deleted_at.is_(None)
        )
        total_result = await self.db.execute(total_stmt)
        total_grievances = total_result.scalar() or 0

        today_stmt = select(func.count(Grievance.id)).where(
            and_(
                Grievance.submitted_at >= today_start,
                Grievance.deleted_at.is_(None),
            )
        )
        today_result = await self.db.execute(today_stmt)
        today_grievances = today_result.scalar() or 0

        week_stmt = select(func.count(Grievance.id)).where(
            and_(
                Grievance.submitted_at >= week_start,
                Grievance.deleted_at.is_(None),
            )
        )
        week_result = await self.db.execute(week_stmt)
        week_grievances = week_result.scalar() or 0

        month_stmt = select(func.count(Grievance.id)).where(
            and_(
                Grievance.submitted_at >= month_start,
                Grievance.deleted_at.is_(None),
            )
        )
        month_result = await self.db.execute(month_stmt)
        month_grievances = month_result.scalar() or 0

        prev_month_stmt = select(func.count(Grievance.id)).where(
            and_(
                Grievance.submitted_at >= prev_month_start,
                Grievance.submitted_at < month_start,
                Grievance.deleted_at.is_(None),
            )
        )
        prev_month_result = await self.db.execute(prev_month_stmt)
        prev_month_grievances = prev_month_result.scalar() or 0

        growth_rate = (
            (month_grievances - prev_month_grievances) / prev_month_grievances
            if prev_month_grievances > 0 else 0.0
        )

        grievances = GrievanceStats(
            total=total_grievances,
            today=today_grievances,
            this_week=week_grievances,
            this_month=month_grievances,
            growth_rate=round(growth_rate, 2),
        )

        # User statistics
        total_officers_stmt = select(func.count(User.id)).where(
            and_(
                User.role.in_(["officer", "supervisor", "admin"]),
                User.deleted_at.is_(None),
            )
        )
        total_officers_result = await self.db.execute(total_officers_stmt)
        total_officers = total_officers_result.scalar() or 0

        active_officers_stmt = select(func.count(User.id)).where(
            and_(
                User.role.in_(["officer", "supervisor", "admin"]),
                User.last_login_at >= month_start,
                User.deleted_at.is_(None),
            )
        )
        active_officers_result = await self.db.execute(active_officers_stmt)
        active_officers = active_officers_result.scalar() or 0

        total_citizens_stmt = select(func.count(User.id)).where(
            and_(
                User.role == "citizen",
                User.deleted_at.is_(None),
            )
        )
        total_citizens_result = await self.db.execute(total_citizens_stmt)
        total_citizens = total_citizens_result.scalar() or 0

        users = UserStats(
            total_officers=total_officers,
            active_officers=active_officers,
            total_citizens=total_citizens,
        )

        # Resolution statistics
        resolution_stmt = select(
            func.avg(
                func.extract(
                    "epoch",
                    Grievance.resolved_at - Grievance.submitted_at
                ) / 86400
            ).label("avg_days"),
        ).where(
            and_(
                Grievance.resolved_at.isnot(None),
                Grievance.deleted_at.is_(None),
            )
        )
        resolution_result = await self.db.execute(resolution_stmt)
        avg_resolution_days = resolution_result.scalar() or 0.0

        # Get fastest and slowest departments
        dept_resolution_stmt = (
            select(
                Department.dept_name,
                func.avg(
                    func.extract(
                        "epoch",
                        Grievance.resolved_at - Grievance.submitted_at
                    ) / 86400
                ).label("avg_days"),
            )
            .join(Grievance, Department.id == Grievance.department_id)
            .where(
                and_(
                    Grievance.resolved_at.isnot(None),
                    Grievance.deleted_at.is_(None),
                )
            )
            .group_by(Department.dept_name)
            .order_by("avg_days")
        )
        dept_resolution_result = await self.db.execute(dept_resolution_stmt)
        dept_resolutions = dept_resolution_result.all()

        fastest_dept = dept_resolutions[0].dept_name if dept_resolutions else "N/A"
        slowest_dept = dept_resolutions[-1].dept_name if dept_resolutions else "N/A"

        # Calculate trend (compare last 15 days vs previous 15 days)
        recent_15_start = now - timedelta(days=15)
        prev_15_start = now - timedelta(days=30)

        recent_resolution_stmt = select(
            func.avg(
                func.extract(
                    "epoch",
                    Grievance.resolved_at - Grievance.submitted_at
                ) / 86400
            )
        ).where(
            and_(
                Grievance.resolved_at >= recent_15_start,
                Grievance.resolved_at.isnot(None),
                Grievance.deleted_at.is_(None),
            )
        )
        recent_resolution_result = await self.db.execute(recent_resolution_stmt)
        recent_avg = recent_resolution_result.scalar() or 0.0

        prev_resolution_stmt = select(
            func.avg(
                func.extract(
                    "epoch",
                    Grievance.resolved_at - Grievance.submitted_at
                ) / 86400
            )
        ).where(
            and_(
                Grievance.resolved_at >= prev_15_start,
                Grievance.resolved_at < recent_15_start,
                Grievance.resolved_at.isnot(None),
                Grievance.deleted_at.is_(None),
            )
        )
        prev_resolution_result = await self.db.execute(prev_resolution_stmt)
        prev_avg = prev_resolution_result.scalar() or 0.0

        trend = "stable"
        if recent_avg < prev_avg * 0.95:
            trend = "down"  # Improving
        elif recent_avg > prev_avg * 1.05:
            trend = "up"  # Worsening

        resolution = ResolutionStats(
            avg_time_days=round(float(avg_resolution_days), 1),
            trend=trend,
            fastest_dept=fastest_dept,
            slowest_dept=slowest_dept,
        )

        # Empathy statistics
        critical_stmt = select(func.count(GrievanceSentiment.grievance_id)).where(
            GrievanceSentiment.distress_level == "CRITICAL"
        )
        critical_result = await self.db.execute(critical_stmt)
        critical_cases = critical_result.scalar() or 0

        high_stmt = select(func.count(GrievanceSentiment.grievance_id)).where(
            GrievanceSentiment.distress_level == "HIGH"
        )
        high_result = await self.db.execute(high_stmt)
        high_cases = high_result.scalar() or 0

        avg_distress_stmt = select(
            func.avg(GrievanceSentiment.distress_score)
        )
        avg_distress_result = await self.db.execute(avg_distress_stmt)
        avg_distress = avg_distress_result.scalar() or 0.0

        # Calculate SLA compliance for high-distress cases
        high_distress_sla_stmt = (
            select(
                func.count(Grievance.id).label("total"),
                func.count(
                    func.case(
                        (Grievance.resolved_at <= Grievance.due_date, 1),
                        else_=None
                    )
                ).label("compliant"),
            )
            .join(GrievanceSentiment, Grievance.grievance_id == GrievanceSentiment.grievance_id)
            .where(
                and_(
                    GrievanceSentiment.distress_level.in_(["CRITICAL", "HIGH"]),
                    Grievance.resolved_at.isnot(None),
                    Grievance.deleted_at.is_(None),
                )
            )
        )
        high_distress_sla_result = await self.db.execute(high_distress_sla_stmt)
        high_distress_sla = high_distress_sla_result.one()

        sla_compliance = (
            high_distress_sla.compliant / high_distress_sla.total
            if high_distress_sla.total > 0 else 0.0
        )

        empathy = EmpathyStats(
            critical_cases=critical_cases,
            high_cases=high_cases,
            avg_distress_score=round(float(avg_distress), 1),
            sla_compliance=round(sla_compliance, 2),
        )

        # Verification statistics
        pending_stmt = select(func.count(Verification.id)).where(
            Verification.status == "pending"
        )
        pending_result = await self.db.execute(pending_stmt)
        pending_verifications = pending_result.scalar() or 0

        verified_stmt = select(
            func.count(Verification.id).label("total"),
            func.count(
                func.case(
                    (Verification.verified == True, 1),
                    else_=None
                )
            ).label("verified"),
        ).where(Verification.status != "pending")
        verified_result = await self.db.execute(verified_stmt)
        verified_data = verified_result.one()

        verified_rate = (
            verified_data.verified / verified_data.total
            if verified_data.total > 0 else 0.0
        )

        # Mock disputed rate (add disputed status tracking in future)
        disputed_rate = 0.03

        verification = VerificationStats(
            pending=pending_verifications,
            verified_rate=round(verified_rate, 2),
            disputed_rate=disputed_rate,
        )

        # Growth chart (last 30 days)
        growth_chart = []
        for i in range(30):
            date = (now - timedelta(days=29-i)).replace(hour=0, minute=0, second=0, microsecond=0)
            next_date = date + timedelta(days=1)

            day_stmt = (
                select(
                    func.count(Grievance.id).label("total"),
                    func.count(
                        func.case(
                            (Grievance.resolved_at.isnot(None), 1),
                            else_=None
                        )
                    ).label("resolved"),
                )
                .where(
                    and_(
                        Grievance.submitted_at >= date,
                        Grievance.submitted_at < next_date,
                        Grievance.deleted_at.is_(None),
                    )
                )
            )
            day_result = await self.db.execute(day_stmt)
            day_data = day_result.one()

            growth_chart.append(
                GrowthChartPoint(
                    date=date.strftime("%Y-%m-%d"),
                    grievances=day_data.total,
                    resolved=day_data.resolved,
                    pending=day_data.total - day_data.resolved,
                )
            )

        return {
            "grievances": grievances,
            "users": users,
            "resolution": resolution,
            "empathy": empathy,
            "verification": verification,
            "growth_chart": growth_chart,
        }

    # ===== Helper Methods =====

    def _mock_photo_similarity(self, resolution_time: float) -> float:
        """Mock photo similarity score based on resolution time.

        In production, this should fetch actual similarity scores from
        the verification table.

        Args:
            resolution_time: Resolution time in days

        Returns:
            Photo similarity score (0.0 to 1.0)
        """
        # Simulate pattern: faster resolutions sometimes have higher similarity
        # (potential fraud indicator)
        if resolution_time < 2.0:
            return min(0.75 + (2.0 - resolution_time) * 0.15, 1.0)
        return min(0.65 + (resolution_time * 0.02), 0.95)

    def _calculate_box_plot_stats(self, data: List[float]) -> dict:
        """Calculate box plot statistics (min, Q1, median, Q3, max, outliers).

        Args:
            data: List of numeric values

        Returns:
            Dict with box plot statistics
        """
        sorted_data = sorted(data)
        n = len(sorted_data)

        # Calculate quartiles
        q1_idx = n // 4
        q2_idx = n // 2
        q3_idx = (3 * n) // 4

        q1 = sorted_data[q1_idx]
        median = sorted_data[q2_idx]
        q3 = sorted_data[q3_idx]

        # Calculate IQR and outlier boundaries
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        # Find outliers
        outliers = [x for x in sorted_data if x < lower_bound or x > upper_bound]

        # Min and max (excluding outliers for whiskers)
        non_outliers = [x for x in sorted_data if lower_bound <= x <= upper_bound]
        min_val = min(non_outliers) if non_outliers else sorted_data[0]
        max_val = max(non_outliers) if non_outliers else sorted_data[-1]

        return {
            "min": round(min_val, 2),
            "q1": round(q1, 2),
            "median": round(median, 2),
            "q3": round(q3, 2),
            "max": round(max_val, 2),
            "outliers": [round(x, 2) for x in outliers],
        }

    def _calculate_benford_analysis(self, values: List[float]) -> List[BenfordDigitData]:
        """Calculate Benford's Law analysis on first digits.

        Benford's Law states that in many naturally occurring datasets,
        the leading digit is more likely to be small. This can detect
        fabricated data.

        Args:
            values: List of numeric values

        Returns:
            List of BenfordDigitData for digits 1-9
        """
        # Count first digits
        digit_counts = defaultdict(int)
        total = 0

        for value in values:
            if value > 0:
                first_digit = int(str(int(value))[0])
                if 1 <= first_digit <= 9:
                    digit_counts[first_digit] += 1
                    total += 1

        # Benford's Law expected frequencies
        benford_expected = {
            1: 0.301,
            2: 0.176,
            3: 0.125,
            4: 0.097,
            5: 0.079,
            6: 0.067,
            7: 0.058,
            8: 0.051,
            9: 0.046,
        }

        result = []
        for digit in range(1, 10):
            expected = benford_expected[digit]
            actual = digit_counts[digit] / total if total > 0 else 0.0
            deviation = abs(actual - expected)

            result.append(
                BenfordDigitData(
                    digit=digit,
                    expected=round(expected, 3),
                    actual=round(actual, 3),
                    deviation=round(deviation, 3),
                )
            )

        return result
