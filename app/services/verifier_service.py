"""Verifier Service for community verification gamification.

This service handles the business logic for the verifier portal including:
- Verification queue management
- Submission processing and point calculation
- Verifier statistics and leaderboards
- Streak tracking and badge awarding
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.district import District
from app.models.grievance import Grievance
from app.models.verifier_activity import VerifierActivity
from app.models.verifier_profile import VerifierProfile
from app.schemas.verifier import (
    Badge,
    GrievanceQueueItem,
    LeaderboardEntry,
    LeaderboardPeriod,
    LeaderboardResponse,
    QueueStatus,
    VerificationQueueResponse,
    VerificationResult,
    VerificationSubmitRequest,
    VerificationSubmitResponse,
    VerifierStatsResponse,
)

logger = logging.getLogger(__name__)


# Point calculation constants
POINTS_VERIFIED = 10
POINTS_DISPUTED = 5
POINTS_INCONCLUSIVE = 3
STREAK_BONUS_MULTIPLIER = 1.5
HIGH_CONFIDENCE_BONUS = 5  # Bonus for confidence >= 0.8

# Badge thresholds
BADGE_THRESHOLDS = {
    Badge.BRONZE: 0,
    Badge.SILVER: 100,
    Badge.GOLD: 500,
    Badge.CHAMPION: 1000,
}


class VerifierService:
    """Service for verifier portal operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the service with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def get_verification_queue(
        self,
        status: Optional[QueueStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> VerificationQueueResponse:
        """Get verification queue for community verifiers.

        Args:
            status: Optional status filter (pending/in_progress)
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            VerificationQueueResponse with queue items
        """
        # Base query: resolved grievances awaiting verification
        query = (
            select(Grievance)
            .where(
                and_(
                    Grievance.status == "resolved",
                    Grievance.resolved_at.isnot(None),
                    Grievance.deleted_at.is_(None),
                )
            )
            .order_by(Grievance.resolved_at.asc())
        )

        # Count total items
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await self.db.execute(query)
        grievances = result.scalars().all()

        # Build response items
        items = []
        for g in grievances:
            # Calculate days since resolution
            days_since = 0
            if g.resolved_at:
                days_since = (datetime.utcnow() - g.resolved_at.replace(tzinfo=None)).days

            # Mask citizen phone for privacy
            masked_phone = g.citizen_phone[:3] + "****" + g.citizen_phone[-2:]

            items.append(
                GrievanceQueueItem(
                    grievance_id=g.grievance_id,
                    subject=g.subject or "No subject",
                    district_name=g.district.district_name if g.district else "Unknown",
                    department_name=g.department.dept_name if g.department else "Unknown",
                    resolved_at=g.resolved_at,
                    days_since_resolution=days_since,
                    priority=g.priority or "normal",
                    citizen_phone=masked_phone,
                )
            )

        return VerificationQueueResponse(
            items=items,
            total=total,
            has_more=(offset + limit) < total,
        )

    async def submit_verification(
        self, request: VerificationSubmitRequest
    ) -> VerificationSubmitResponse:
        """Submit verification result and update verifier profile.

        Args:
            request: Verification submission request

        Returns:
            VerificationSubmitResponse with points and badge info
        """
        # Get or create verifier profile
        profile = await self._get_or_create_profile(request.verifier_phone)

        # Calculate points for this verification
        points = self._calculate_points(
            request.verification_result,
            request.confidence_score,
            profile.current_streak,
        )

        # Update profile statistics
        old_badge = profile.badge
        await self._update_profile_stats(
            profile,
            request.verification_result,
            points,
        )

        # Create activity record
        activity = VerifierActivity(
            verifier_id=profile.id,
            grievance_id=request.grievance_id,
            result=request.verification_result.value,
            points_earned=points,
            bonus_applied=(profile.current_streak >= 3),
            location_lat=request.location_lat,
            location_lng=request.location_lng,
            notes=request.notes,
        )
        self.db.add(activity)

        # Check for badge level up
        new_badge = self._get_badge_for_points(profile.total_points)
        badge_earned = None
        if new_badge != old_badge:
            profile.badge = new_badge
            badge_earned = Badge(new_badge)
            # Add to badges_json if not already present
            if new_badge not in profile.badges_json:
                profile.badges_json = profile.badges_json + [new_badge]

        # Commit changes
        await self.db.commit()
        await self.db.refresh(profile)

        logger.info(
            f"Verification submitted: {request.grievance_id} by {request.verifier_phone}, "
            f"result={request.verification_result.value}, points={points}"
        )

        return VerificationSubmitResponse(
            success=True,
            points_earned=points,
            total_points=profile.total_points,
            badge_earned=badge_earned,
        )

    async def get_verifier_stats(self, phone: str) -> Optional[VerifierStatsResponse]:
        """Get statistics for a verifier by phone number.

        Args:
            phone: Verifier phone number

        Returns:
            VerifierStatsResponse or None if not found
        """
        # Get profile
        stmt = select(VerifierProfile).where(VerifierProfile.phone == phone)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            return None

        # Calculate rank
        rank = await self._get_verifier_rank(profile.total_points)

        return VerifierStatsResponse(
            verifier_phone=profile.phone,
            display_name=profile.display_name,
            total_verifications=profile.total_verifications,
            verified_count=profile.verified_count,
            disputed_count=profile.disputed_count,
            accuracy_rate=float(profile.accuracy_rate),
            points=profile.total_points,
            rank=rank,
            badge=Badge(profile.badge),
            badges_earned=profile.badges_json,
            streak_days=profile.current_streak,
            joined_at=profile.created_at,
        )

    async def get_leaderboard(
        self,
        period: LeaderboardPeriod = LeaderboardPeriod.ALL_TIME,
        district: Optional[str] = None,
        limit: int = 20,
    ) -> LeaderboardResponse:
        """Get verifier leaderboard.

        Args:
            period: Time period filter (weekly/monthly/all_time)
            district: Optional district name filter
            limit: Maximum number of entries

        Returns:
            LeaderboardResponse with rankings
        """
        # Calculate period boundaries
        period_start, period_end = self._get_period_boundaries(period)

        # Base query
        query = select(VerifierProfile).order_by(
            VerifierProfile.total_points.desc(),
            VerifierProfile.created_at.asc(),
        )

        # Apply district filter if specified
        if district:
            district_obj = await self._get_district_by_name(district)
            if district_obj:
                query = query.where(VerifierProfile.district_id == district_obj.id)

        # For period filters, we would need to filter based on activities
        # For now, keeping it simple with all-time rankings
        # TODO: Implement period-specific rankings using verifier_activities

        # Apply limit
        query = query.limit(limit)

        # Execute
        result = await self.db.execute(query)
        profiles = result.scalars().all()

        # Build leaderboard entries
        leaders = []
        for rank, profile in enumerate(profiles, start=1):
            # Mask phone number
            masked_phone = profile.phone[:3] + "****" + profile.phone[-2:]

            leaders.append(
                LeaderboardEntry(
                    rank=rank,
                    verifier_phone=masked_phone,
                    display_name=profile.display_name,
                    total_points=profile.total_points,
                    total_verifications=profile.total_verifications,
                    accuracy_rate=float(profile.accuracy_rate),
                    badge=Badge(profile.badge),
                    district_name=profile.district.district_name if profile.district else None,
                )
            )

        # Count total participants
        count_query = select(func.count()).select_from(VerifierProfile)
        if district:
            district_obj = await self._get_district_by_name(district)
            if district_obj:
                count_query = count_query.where(
                    VerifierProfile.district_id == district_obj.id
                )

        total_result = await self.db.execute(count_query)
        total_participants = total_result.scalar() or 0

        return LeaderboardResponse(
            period=period,
            period_start=period_start,
            period_end=period_end,
            leaders=leaders,
            total_participants=total_participants,
        )

    # Helper methods

    async def _get_or_create_profile(self, phone: str) -> VerifierProfile:
        """Get existing profile or create new one.

        Args:
            phone: Verifier phone number

        Returns:
            VerifierProfile instance
        """
        stmt = select(VerifierProfile).where(VerifierProfile.phone == phone)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = VerifierProfile(
                phone=phone,
                total_points=0,
                total_verifications=0,
                verified_count=0,
                disputed_count=0,
                inconclusive_count=0,
                accuracy_rate=0.0,
                current_streak=0,
                longest_streak=0,
                badge="BRONZE",
                badges_json=["BRONZE"],
            )
            self.db.add(profile)
            await self.db.flush()
            logger.info(f"Created new verifier profile: {phone}")

        return profile

    def _calculate_points(
        self,
        result: VerificationResult,
        confidence: float,
        current_streak: int,
    ) -> int:
        """Calculate points for a verification.

        Args:
            result: Verification result type
            confidence: Confidence score (0.0-1.0)
            current_streak: Current streak days

        Returns:
            Points earned
        """
        # Base points by result type
        base_points = {
            VerificationResult.VERIFIED: POINTS_VERIFIED,
            VerificationResult.DISPUTED: POINTS_DISPUTED,
            VerificationResult.INCONCLUSIVE: POINTS_INCONCLUSIVE,
        }.get(result, 0)

        # Apply streak bonus (3+ day streak)
        if current_streak >= 3:
            base_points = int(base_points * STREAK_BONUS_MULTIPLIER)

        # Apply high confidence bonus
        if confidence >= 0.8:
            base_points += HIGH_CONFIDENCE_BONUS

        return base_points

    async def _update_profile_stats(
        self,
        profile: VerifierProfile,
        result: VerificationResult,
        points: int,
    ) -> None:
        """Update verifier profile statistics.

        Args:
            profile: VerifierProfile to update
            result: Verification result
            points: Points earned
        """
        # Update totals
        profile.total_points += points
        profile.total_verifications += 1

        # Update result counts
        if result == VerificationResult.VERIFIED:
            profile.verified_count += 1
        elif result == VerificationResult.DISPUTED:
            profile.disputed_count += 1
        elif result == VerificationResult.INCONCLUSIVE:
            profile.inconclusive_count += 1

        # Calculate accuracy rate (verified / total)
        if profile.total_verifications > 0:
            profile.accuracy_rate = (
                profile.verified_count / profile.total_verifications * 100
            )

        # Update streak
        now = datetime.utcnow()
        if profile.last_verification_at:
            last_verification = profile.last_verification_at.replace(tzinfo=None)
            days_diff = (now - last_verification).days

            if days_diff == 1:
                # Consecutive day - increment streak
                profile.current_streak += 1
            elif days_diff == 0:
                # Same day - no change to streak
                pass
            else:
                # Streak broken
                profile.current_streak = 1
        else:
            # First verification
            profile.current_streak = 1

        # Update longest streak
        if profile.current_streak > profile.longest_streak:
            profile.longest_streak = profile.current_streak

        # Update last verification timestamp
        profile.last_verification_at = now
        profile.updated_at = now

    def _get_badge_for_points(self, points: int) -> str:
        """Determine badge level based on points.

        Args:
            points: Total points

        Returns:
            Badge name
        """
        if points >= BADGE_THRESHOLDS[Badge.CHAMPION]:
            return Badge.CHAMPION.value
        elif points >= BADGE_THRESHOLDS[Badge.GOLD]:
            return Badge.GOLD.value
        elif points >= BADGE_THRESHOLDS[Badge.SILVER]:
            return Badge.SILVER.value
        else:
            return Badge.BRONZE.value

    async def _get_verifier_rank(self, points: int) -> int:
        """Calculate verifier's rank based on points.

        Args:
            points: Verifier's total points

        Returns:
            Rank position (1-based)
        """
        stmt = select(func.count()).where(VerifierProfile.total_points > points)
        result = await self.db.execute(stmt)
        higher_count = result.scalar() or 0
        return higher_count + 1

    def _get_period_boundaries(
        self, period: LeaderboardPeriod
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get start and end timestamps for a period.

        Args:
            period: Leaderboard period

        Returns:
            Tuple of (start, end) datetimes
        """
        now = datetime.utcnow()

        if period == LeaderboardPeriod.WEEKLY:
            # Last 7 days
            start = now - timedelta(days=7)
            return (start, now)
        elif period == LeaderboardPeriod.MONTHLY:
            # Last 30 days
            start = now - timedelta(days=30)
            return (start, now)
        else:
            # All time
            return (None, None)

    async def _get_district_by_name(self, district_name: str) -> Optional[District]:
        """Get district by name.

        Args:
            district_name: District name

        Returns:
            District instance or None
        """
        stmt = select(District).where(
            func.lower(District.district_name) == district_name.lower()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


def get_verifier_service(db: AsyncSession) -> VerifierService:
    """Factory function to create VerifierService instance.

    Args:
        db: SQLAlchemy async session

    Returns:
        VerifierService instance
    """
    return VerifierService(db)
