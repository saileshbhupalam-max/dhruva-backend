"""Tests for Verifier Service (Layer 2 - Community Verification).

Tests cover:
- Point calculation with streak bonuses
- Badge level progression
- Verification queue retrieval
- Leaderboard generation
- Profile statistics
- Edge cases and error handling
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.verifier import (
    Badge,
    LeaderboardPeriod,
    QueueStatus,
    VerificationResult,
    VerificationSubmitRequest,
)
from app.services.verifier_service import (
    BADGE_THRESHOLDS,
    HIGH_CONFIDENCE_BONUS,
    POINTS_DISPUTED,
    POINTS_INCONCLUSIVE,
    POINTS_VERIFIED,
    STREAK_BONUS_MULTIPLIER,
    VerifierService,
    get_verifier_service,
)


class TestPointCalculation:
    """Tests for point calculation logic."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    def test_verified_base_points(self, service):
        """Test base points for VERIFIED result."""
        points = service._calculate_points(
            result=VerificationResult.VERIFIED,
            confidence=0.5,
            current_streak=0,
        )
        assert points == POINTS_VERIFIED

    def test_disputed_base_points(self, service):
        """Test base points for DISPUTED result."""
        points = service._calculate_points(
            result=VerificationResult.DISPUTED,
            confidence=0.5,
            current_streak=0,
        )
        assert points == POINTS_DISPUTED

    def test_inconclusive_base_points(self, service):
        """Test base points for INCONCLUSIVE result."""
        points = service._calculate_points(
            result=VerificationResult.INCONCLUSIVE,
            confidence=0.5,
            current_streak=0,
        )
        assert points == POINTS_INCONCLUSIVE

    def test_streak_bonus_applied_at_3_days(self, service):
        """Test streak bonus multiplier at 3+ day streak."""
        base_points = POINTS_VERIFIED
        points = service._calculate_points(
            result=VerificationResult.VERIFIED,
            confidence=0.5,
            current_streak=3,
        )
        expected = int(base_points * STREAK_BONUS_MULTIPLIER)
        assert points == expected

    def test_streak_bonus_not_applied_below_3_days(self, service):
        """Test no streak bonus for streaks below 3 days."""
        points_streak_2 = service._calculate_points(
            result=VerificationResult.VERIFIED,
            confidence=0.5,
            current_streak=2,
        )
        assert points_streak_2 == POINTS_VERIFIED

    def test_high_confidence_bonus(self, service):
        """Test high confidence bonus at >= 0.8."""
        points = service._calculate_points(
            result=VerificationResult.VERIFIED,
            confidence=0.8,
            current_streak=0,
        )
        assert points == POINTS_VERIFIED + HIGH_CONFIDENCE_BONUS

    def test_high_confidence_bonus_at_1_0(self, service):
        """Test high confidence bonus at 1.0."""
        points = service._calculate_points(
            result=VerificationResult.VERIFIED,
            confidence=1.0,
            current_streak=0,
        )
        assert points == POINTS_VERIFIED + HIGH_CONFIDENCE_BONUS

    def test_no_high_confidence_bonus_below_threshold(self, service):
        """Test no high confidence bonus below 0.8."""
        points = service._calculate_points(
            result=VerificationResult.VERIFIED,
            confidence=0.79,
            current_streak=0,
        )
        assert points == POINTS_VERIFIED

    def test_combined_streak_and_confidence_bonus(self, service):
        """Test combined streak and high confidence bonus."""
        points = service._calculate_points(
            result=VerificationResult.VERIFIED,
            confidence=0.9,
            current_streak=5,
        )
        base_with_streak = int(POINTS_VERIFIED * STREAK_BONUS_MULTIPLIER)
        expected = base_with_streak + HIGH_CONFIDENCE_BONUS
        assert points == expected


class TestBadgeLevelProgression:
    """Tests for badge level determination."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    def test_bronze_badge_at_zero_points(self, service):
        """Test BRONZE badge at 0 points."""
        badge = service._get_badge_for_points(0)
        assert badge == Badge.BRONZE.value

    def test_bronze_badge_at_99_points(self, service):
        """Test BRONZE badge below SILVER threshold."""
        badge = service._get_badge_for_points(99)
        assert badge == Badge.BRONZE.value

    def test_silver_badge_at_threshold(self, service):
        """Test SILVER badge at threshold (100 points)."""
        badge = service._get_badge_for_points(100)
        assert badge == Badge.SILVER.value

    def test_silver_badge_below_gold(self, service):
        """Test SILVER badge between thresholds."""
        badge = service._get_badge_for_points(499)
        assert badge == Badge.SILVER.value

    def test_gold_badge_at_threshold(self, service):
        """Test GOLD badge at threshold (500 points)."""
        badge = service._get_badge_for_points(500)
        assert badge == Badge.GOLD.value

    def test_gold_badge_below_champion(self, service):
        """Test GOLD badge between thresholds."""
        badge = service._get_badge_for_points(999)
        assert badge == Badge.GOLD.value

    def test_champion_badge_at_threshold(self, service):
        """Test CHAMPION badge at threshold (1000 points)."""
        badge = service._get_badge_for_points(1000)
        assert badge == Badge.CHAMPION.value

    def test_champion_badge_at_high_points(self, service):
        """Test CHAMPION badge at very high points."""
        badge = service._get_badge_for_points(10000)
        assert badge == Badge.CHAMPION.value


class TestPeriodBoundaries:
    """Tests for leaderboard period boundary calculation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    def test_weekly_period_boundaries(self, service):
        """Test weekly period returns 7-day range."""
        start, end = service._get_period_boundaries(LeaderboardPeriod.WEEKLY)

        assert start is not None
        assert end is not None
        assert (end - start).days == 7

    def test_monthly_period_boundaries(self, service):
        """Test monthly period returns 30-day range."""
        start, end = service._get_period_boundaries(LeaderboardPeriod.MONTHLY)

        assert start is not None
        assert end is not None
        assert (end - start).days == 30

    def test_all_time_period_boundaries(self, service):
        """Test all-time period returns None boundaries."""
        start, end = service._get_period_boundaries(LeaderboardPeriod.ALL_TIME)

        assert start is None
        assert end is None


class TestProfileManagement:
    """Tests for verifier profile creation and updates."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    @pytest.mark.asyncio
    async def test_create_new_profile(self, service, mock_db):
        """Test creating a new verifier profile."""
        # Mock no existing profile
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        profile = await service._get_or_create_profile("+919876543210")

        assert profile is not None
        assert profile.phone == "+919876543210"
        assert profile.total_points == 0
        assert profile.badge == "BRONZE"
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_profile(self, service, mock_db):
        """Test retrieving existing verifier profile."""
        mock_profile = MagicMock()
        mock_profile.phone = "+919876543210"
        mock_profile.total_points = 500
        mock_profile.badge = "GOLD"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        mock_db.execute = AsyncMock(return_value=mock_result)

        profile = await service._get_or_create_profile("+919876543210")

        assert profile.total_points == 500
        assert profile.badge == "GOLD"
        mock_db.add.assert_not_called()


class TestStreakTracking:
    """Tests for verification streak tracking."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    @pytest.mark.asyncio
    async def test_first_verification_starts_streak(self, service, mock_db):
        """Test first verification starts streak at 1."""
        mock_profile = MagicMock()
        mock_profile.last_verification_at = None
        mock_profile.current_streak = 0
        mock_profile.longest_streak = 0
        mock_profile.total_verifications = 0
        mock_profile.verified_count = 0
        mock_profile.disputed_count = 0
        mock_profile.inconclusive_count = 0
        mock_profile.total_points = 0

        await service._update_profile_stats(
            mock_profile,
            VerificationResult.VERIFIED,
            10,
        )

        assert mock_profile.current_streak == 1
        assert mock_profile.longest_streak == 1

    @pytest.mark.asyncio
    async def test_consecutive_day_increments_streak(self, service, mock_db):
        """Test consecutive day verification increments streak."""
        yesterday = datetime.utcnow() - timedelta(days=1)

        mock_profile = MagicMock()
        mock_profile.last_verification_at = yesterday
        mock_profile.current_streak = 5
        mock_profile.longest_streak = 5
        mock_profile.total_verifications = 10
        mock_profile.verified_count = 8
        mock_profile.disputed_count = 1
        mock_profile.inconclusive_count = 1
        mock_profile.total_points = 100

        await service._update_profile_stats(
            mock_profile,
            VerificationResult.VERIFIED,
            10,
        )

        assert mock_profile.current_streak == 6
        assert mock_profile.longest_streak == 6

    @pytest.mark.asyncio
    async def test_same_day_maintains_streak(self, service, mock_db):
        """Test same day verification maintains streak."""
        today = datetime.utcnow()

        mock_profile = MagicMock()
        mock_profile.last_verification_at = today
        mock_profile.current_streak = 5
        mock_profile.longest_streak = 5
        mock_profile.total_verifications = 10
        mock_profile.verified_count = 8
        mock_profile.disputed_count = 1
        mock_profile.inconclusive_count = 1
        mock_profile.total_points = 100

        await service._update_profile_stats(
            mock_profile,
            VerificationResult.VERIFIED,
            10,
        )

        # Streak should not change for same day
        assert mock_profile.current_streak == 5

    @pytest.mark.asyncio
    async def test_streak_broken_after_gap(self, service, mock_db):
        """Test streak resets after 2+ day gap."""
        two_days_ago = datetime.utcnow() - timedelta(days=2)

        mock_profile = MagicMock()
        mock_profile.last_verification_at = two_days_ago
        mock_profile.current_streak = 10
        mock_profile.longest_streak = 10
        mock_profile.total_verifications = 20
        mock_profile.verified_count = 15
        mock_profile.disputed_count = 3
        mock_profile.inconclusive_count = 2
        mock_profile.total_points = 200

        await service._update_profile_stats(
            mock_profile,
            VerificationResult.VERIFIED,
            10,
        )

        assert mock_profile.current_streak == 1
        # Longest streak should be preserved
        assert mock_profile.longest_streak == 10


class TestVerificationSubmission:
    """Tests for verification submission flow."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.flush = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    @pytest.mark.asyncio
    async def test_submit_verification_success(self, service, mock_db):
        """Test successful verification submission."""
        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.phone = "+919876543210"
        mock_profile.total_points = 100
        mock_profile.current_streak = 2
        mock_profile.longest_streak = 5
        mock_profile.badge = "SILVER"
        mock_profile.badges_json = ["BRONZE", "SILVER"]
        mock_profile.total_verifications = 20
        mock_profile.verified_count = 15
        mock_profile.disputed_count = 3
        mock_profile.inconclusive_count = 2
        mock_profile.accuracy_rate = 75.0
        mock_profile.last_verification_at = None

        service._get_or_create_profile = AsyncMock(return_value=mock_profile)

        request = VerificationSubmitRequest(
            grievance_id="PGRS-2025-GTR-00001",
            verifier_phone="+919876543210",
            verification_result=VerificationResult.VERIFIED,
            confidence_score=0.9,
            notes="Verified in person",
        )

        result = await service.submit_verification(request)

        assert result.success is True
        assert result.points_earned > 0
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_submit_verification_badge_level_up(self, service, mock_db):
        """Test verification that triggers badge level up."""
        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.phone = "+919876543210"
        mock_profile.total_points = 95  # Will go to 100+ with points earned
        mock_profile.current_streak = 0
        mock_profile.longest_streak = 0
        mock_profile.badge = "BRONZE"
        mock_profile.badges_json = ["BRONZE"]
        mock_profile.total_verifications = 9
        mock_profile.verified_count = 8
        mock_profile.disputed_count = 0
        mock_profile.inconclusive_count = 1
        mock_profile.accuracy_rate = 88.8
        mock_profile.last_verification_at = None

        service._get_or_create_profile = AsyncMock(return_value=mock_profile)

        request = VerificationSubmitRequest(
            grievance_id="PGRS-2025-GTR-00002",
            verifier_phone="+919876543210",
            verification_result=VerificationResult.VERIFIED,
            confidence_score=0.85,
        )

        result = await service.submit_verification(request)

        assert result.success is True
        # Badge earned should be SILVER after crossing 100 points
        assert result.badge_earned == Badge.SILVER


class TestVerifierStats:
    """Tests for verifier statistics retrieval."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    @pytest.mark.asyncio
    async def test_get_stats_existing_verifier(self, service, mock_db):
        """Test getting stats for existing verifier."""
        mock_profile = MagicMock()
        mock_profile.phone = "+919876543210"
        mock_profile.display_name = "Ravi Kumar"
        mock_profile.total_verifications = 50
        mock_profile.verified_count = 40
        mock_profile.disputed_count = 8
        mock_profile.accuracy_rate = 80.0
        mock_profile.total_points = 550
        mock_profile.badge = "GOLD"
        mock_profile.badges_json = ["BRONZE", "SILVER", "GOLD"]
        mock_profile.current_streak = 3
        mock_profile.created_at = datetime.utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_profile
        mock_db.execute = AsyncMock(return_value=mock_result)

        service._get_verifier_rank = AsyncMock(return_value=5)

        result = await service.get_verifier_stats("+919876543210")

        assert result is not None
        assert result.verifier_phone == "+919876543210"
        assert result.total_verifications == 50
        assert result.badge == Badge.GOLD
        assert result.rank == 5

    @pytest.mark.asyncio
    async def test_get_stats_nonexistent_verifier(self, service, mock_db):
        """Test getting stats for non-existent verifier."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_verifier_stats("+919999999999")

        assert result is None


class TestLeaderboard:
    """Tests for leaderboard generation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    @pytest.mark.asyncio
    async def test_get_leaderboard_all_time(self, service, mock_db):
        """Test all-time leaderboard retrieval."""
        mock_profile_1 = MagicMock()
        mock_profile_1.phone = "+919876543210"
        mock_profile_1.display_name = "Champion"
        mock_profile_1.total_points = 1500
        mock_profile_1.total_verifications = 150
        mock_profile_1.accuracy_rate = 95.0
        mock_profile_1.badge = "CHAMPION"
        mock_profile_1.district = MagicMock()
        mock_profile_1.district.district_name = "Guntur"

        mock_profile_2 = MagicMock()
        mock_profile_2.phone = "+919876543211"
        mock_profile_2.display_name = "Gold User"
        mock_profile_2.total_points = 600
        mock_profile_2.total_verifications = 60
        mock_profile_2.accuracy_rate = 85.0
        mock_profile_2.badge = "GOLD"
        mock_profile_2.district = None

        # Create mock result for profiles query
        mock_profiles_result = MagicMock()
        mock_profiles_result.scalars.return_value.all.return_value = [
            mock_profile_1,
            mock_profile_2,
        ]

        # Create mock result for count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        call_count = [0]

        async def mock_execute(stmt):
            call_count[0] += 1
            stmt_str = str(stmt).lower()
            # First call is profiles query, second is count
            if call_count[0] == 1:
                return mock_profiles_result
            return mock_count_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        result = await service.get_leaderboard(period=LeaderboardPeriod.ALL_TIME)

        assert result.period == LeaderboardPeriod.ALL_TIME
        assert result.period_start is None
        assert result.period_end is None
        assert len(result.leaders) == 2
        assert result.leaders[0].rank == 1
        assert result.leaders[0].badge == Badge.CHAMPION

    @pytest.mark.asyncio
    async def test_get_leaderboard_empty(self, service, mock_db):
        """Test leaderboard with no verifiers."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_leaderboard()

        assert len(result.leaders) == 0
        assert result.total_participants == 0


class TestVerificationQueue:
    """Tests for verification queue retrieval."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    @pytest.mark.asyncio
    async def test_get_queue_with_resolved_grievances(self, service, mock_db):
        """Test queue retrieval with resolved grievances."""
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00001"
        mock_grievance.subject = "Water supply issue"
        mock_grievance.citizen_phone = "+919876543210"
        mock_grievance.priority = "high"
        mock_grievance.resolved_at = datetime.utcnow() - timedelta(days=5)
        mock_grievance.district = MagicMock()
        mock_grievance.district.district_name = "Guntur"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "WRDS"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_grievance]
        mock_result.scalar.return_value = 1

        async def mock_execute(stmt):
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        result = await service.get_verification_queue()

        assert len(result.items) == 1
        assert result.items[0].grievance_id == "PGRS-2025-GTR-00001"
        assert result.items[0].days_since_resolution == 5
        # Phone should be masked
        assert "****" in result.items[0].citizen_phone

    @pytest.mark.asyncio
    async def test_get_queue_empty(self, service, mock_db):
        """Test queue retrieval with no resolved grievances."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_verification_queue()

        assert len(result.items) == 0
        assert result.total == 0
        assert result.has_more is False


class TestVerifierRank:
    """Tests for verifier rank calculation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    @pytest.mark.asyncio
    async def test_rank_with_no_higher_points(self, service, mock_db):
        """Test rank 1 when no one has higher points."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_result)

        rank = await service._get_verifier_rank(1000)

        assert rank == 1

    @pytest.mark.asyncio
    async def test_rank_with_higher_points_users(self, service, mock_db):
        """Test rank when others have higher points."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5  # 5 people with higher points
        mock_db.execute = AsyncMock(return_value=mock_result)

        rank = await service._get_verifier_rank(500)

        assert rank == 6


class TestServiceFactory:
    """Tests for service factory function."""

    def test_get_verifier_service_returns_instance(self):
        """Test that get_verifier_service returns a VerifierService."""
        mock_db = MagicMock()
        service = get_verifier_service(mock_db)

        assert isinstance(service, VerifierService)
        assert service.db == mock_db


class TestAccuracyRateCalculation:
    """Tests for accuracy rate calculation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create a VerifierService with mock DB."""
        return VerifierService(mock_db)

    @pytest.mark.asyncio
    async def test_accuracy_rate_calculation(self, service, mock_db):
        """Test accuracy rate is calculated correctly."""
        mock_profile = MagicMock()
        mock_profile.last_verification_at = None
        mock_profile.current_streak = 0
        mock_profile.longest_streak = 0
        mock_profile.total_verifications = 9
        mock_profile.verified_count = 7
        mock_profile.disputed_count = 1
        mock_profile.inconclusive_count = 1
        mock_profile.total_points = 100
        mock_profile.accuracy_rate = 77.78

        await service._update_profile_stats(
            mock_profile,
            VerificationResult.VERIFIED,
            10,
        )

        # After update: 8 verified out of 10 total = 80%
        assert mock_profile.total_verifications == 10
        assert mock_profile.verified_count == 8
        assert mock_profile.accuracy_rate == 80.0

    @pytest.mark.asyncio
    async def test_accuracy_rate_with_disputed(self, service, mock_db):
        """Test accuracy rate calculation with disputed result."""
        mock_profile = MagicMock()
        mock_profile.last_verification_at = None
        mock_profile.current_streak = 0
        mock_profile.longest_streak = 0
        mock_profile.total_verifications = 9
        mock_profile.verified_count = 7
        mock_profile.disputed_count = 1
        mock_profile.inconclusive_count = 1
        mock_profile.total_points = 100

        await service._update_profile_stats(
            mock_profile,
            VerificationResult.DISPUTED,
            5,
        )

        # Disputed count should increase
        assert mock_profile.disputed_count == 2
        assert mock_profile.total_verifications == 10
        # Accuracy rate: 7/10 = 70%
        assert mock_profile.accuracy_rate == 70.0
