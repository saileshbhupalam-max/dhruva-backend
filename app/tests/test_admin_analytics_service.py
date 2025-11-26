"""Tests for Admin Analytics Service (Layer 2 - Dashboard Metrics).

Tests cover:
- Fraud detection metrics (scatter plot, box plot, Benford's Law)
- NLP performance metrics
- Department analytics (SLA, satisfaction)
- System overview metrics
- Helper function unit tests
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.admin_analytics_service import AdminAnalyticsService


class TestBoxPlotCalculation:
    """Tests for box plot statistics calculation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an AdminAnalyticsService with mock DB."""
        return AdminAnalyticsService(mock_db)

    def test_box_plot_basic_calculation(self, service):
        """Test basic box plot statistics calculation."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        result = service._calculate_box_plot_stats(data)

        assert result["min"] == 1.0
        assert result["max"] == 10.0
        # Median is at index n//2 = 5 in 0-indexed sorted list = 6.0
        assert result["median"] == 6.0
        assert "q1" in result
        assert "q3" in result
        assert "outliers" in result

    def test_box_plot_with_outliers(self, service):
        """Test box plot calculation identifies outliers."""
        # Include extreme values that should be outliers
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 100.0]
        result = service._calculate_box_plot_stats(data)

        assert 100.0 in result["outliers"]

    def test_box_plot_uniform_data(self, service):
        """Test box plot with uniform data."""
        data = [5.0, 5.0, 5.0, 5.0, 5.0]
        result = service._calculate_box_plot_stats(data)

        assert result["min"] == 5.0
        assert result["max"] == 5.0
        assert result["median"] == 5.0
        assert result["q1"] == 5.0
        assert result["q3"] == 5.0

    def test_box_plot_minimum_data(self, service):
        """Test box plot with minimum required data points."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = service._calculate_box_plot_stats(data)

        assert result["min"] == 1.0
        assert result["max"] == 5.0


class TestBenfordAnalysis:
    """Tests for Benford's Law analysis."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an AdminAnalyticsService with mock DB."""
        return AdminAnalyticsService(mock_db)

    def test_benford_analysis_basic(self, service):
        """Test Benford analysis returns all 9 digits."""
        data = [1.5, 2.3, 3.2, 4.1, 5.0, 6.8, 7.2, 8.9, 9.1]
        result = service._calculate_benford_analysis(data)

        assert len(result) == 9
        assert result[0].digit == 1
        assert result[8].digit == 9

    def test_benford_analysis_expected_values(self, service):
        """Test Benford analysis has correct expected values."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = service._calculate_benford_analysis(data)

        # Benford's Law expected frequencies
        assert result[0].expected == 0.301  # Digit 1
        assert result[1].expected == 0.176  # Digit 2
        assert result[2].expected == 0.125  # Digit 3

    def test_benford_analysis_deviation_calculation(self, service):
        """Test Benford analysis calculates deviation correctly."""
        # All values start with 1 - deviation from expected
        data = [1.0, 1.5, 1.9, 10.0, 11.0, 12.0]
        result = service._calculate_benford_analysis(data)

        # Digit 1 should have 100% actual vs 30.1% expected
        digit_1 = result[0]
        assert digit_1.actual == 1.0
        assert digit_1.deviation == pytest.approx(0.699, abs=0.001)

    def test_benford_analysis_empty_data(self, service):
        """Test Benford analysis with empty data."""
        result = service._calculate_benford_analysis([])

        assert len(result) == 9
        # All actual values should be 0
        assert all(d.actual == 0.0 for d in result)

    def test_benford_analysis_ignores_zero_and_negative(self, service):
        """Test Benford analysis ignores zero and negative values."""
        data = [0.0, -1.0, -5.0, 1.0, 2.0, 3.0]
        result = service._calculate_benford_analysis(data)

        # Only 1, 2, 3 should be counted (3 values)
        total_actual = sum(d.actual for d in result)
        assert total_actual == pytest.approx(1.0, abs=0.01)


class TestMockPhotoSimilarity:
    """Tests for mock photo similarity calculation."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an AdminAnalyticsService with mock DB."""
        return AdminAnalyticsService(mock_db)

    def test_fast_resolution_high_similarity(self, service):
        """Test fast resolution produces higher similarity score."""
        fast_score = service._mock_photo_similarity(0.5)  # 0.5 days
        slow_score = service._mock_photo_similarity(10.0)  # 10 days

        assert fast_score > slow_score

    def test_similarity_bounded_0_to_1(self, service):
        """Test similarity score is bounded between 0 and 1."""
        for time in [0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]:
            score = service._mock_photo_similarity(time)
            assert 0.0 <= score <= 1.0

    def test_very_fast_resolution_caps_at_1(self, service):
        """Test very fast resolution caps similarity at 1.0."""
        score = service._mock_photo_similarity(0.0)
        assert score <= 1.0


class TestFraudMetrics:
    """Tests for fraud detection metrics."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create an AdminAnalyticsService with mock DB."""
        return AdminAnalyticsService(mock_db)

    @pytest.mark.asyncio
    async def test_fraud_metrics_with_data(self, service, mock_db):
        """Test fraud metrics with resolved grievances."""
        # Create mock grievance data
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00001"
        mock_grievance.assigned_officer_id = "OFF001"
        mock_grievance.submitted_at = datetime.now(timezone.utc) - timedelta(days=10)
        mock_grievance.resolved_at = datetime.now(timezone.utc) - timedelta(days=5)
        mock_grievance.officer_name = "John Doe"

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_grievance]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_fraud_metrics()

        assert result.summary.total_analyzed >= 0
        assert isinstance(result.scatter_data, list)
        assert isinstance(result.benford_data, list)
        assert len(result.benford_data) == 9

    @pytest.mark.asyncio
    async def test_fraud_metrics_empty_data(self, service, mock_db):
        """Test fraud metrics with no resolved grievances."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_fraud_metrics()

        assert result.summary.total_analyzed == 0
        assert len(result.scatter_data) == 0
        assert len(result.flagged_cases) == 0


class TestNLPMetrics:
    """Tests for NLP performance metrics."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an AdminAnalyticsService with mock DB."""
        return AdminAnalyticsService(mock_db)

    @pytest.mark.asyncio
    async def test_nlp_metrics_language_distribution(self, service, mock_db):
        """Test NLP metrics returns language distribution."""
        mock_row_te = MagicMock()
        mock_row_te.language = "te"
        mock_row_te.count = 70

        mock_row_en = MagicMock()
        mock_row_en.language = "en"
        mock_row_en.count = 30

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row_te, mock_row_en]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_nlp_metrics()

        assert "language_distribution" in result
        assert "overall_accuracy" in result
        assert "confusion_matrix" in result
        assert "accuracy_trend" in result
        assert "model_info" in result

    @pytest.mark.asyncio
    async def test_nlp_metrics_accuracy_trend(self, service, mock_db):
        """Test NLP metrics returns 30-day accuracy trend."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_nlp_metrics()

        assert len(result["accuracy_trend"]) == 30

    @pytest.mark.asyncio
    async def test_nlp_metrics_confusion_matrix_structure(self, service, mock_db):
        """Test NLP metrics confusion matrix has correct structure."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_nlp_metrics()

        confusion = result["confusion_matrix"]
        assert len(confusion.labels) == len(confusion.matrix)
        # Each row should have same columns as labels
        for row in confusion.matrix:
            assert len(row) == len(confusion.labels)


class TestDepartmentAnalytics:
    """Tests for department analytics."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an AdminAnalyticsService with mock DB."""
        return AdminAnalyticsService(mock_db)

    @pytest.mark.asyncio
    async def test_department_analytics_30d_period(self, service, mock_db):
        """Test department analytics for 30-day period."""
        # Mock department data
        mock_dept = MagicMock()
        mock_dept.dept_name = "Revenue"
        mock_dept.sla_days = 14
        mock_dept.total_grievances = 100
        mock_dept.avg_resolution_days = 7.5

        mock_dept_result = MagicMock()
        mock_dept_result.all.return_value = [mock_dept]

        # Mock SLA data
        mock_sla_result = MagicMock()
        mock_sla_result.all.return_value = []

        # Mock satisfaction data
        mock_sat_result = MagicMock()
        mock_sat_result.all.return_value = []

        call_count = [0]
        async def mock_execute(stmt):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_dept_result
            elif call_count[0] == 2:
                return mock_sla_result
            return mock_sat_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        result = await service.get_department_analytics(period="30d")

        assert "sla_heatmap" in result
        assert "satisfaction_trends" in result
        assert "performance_ranking" in result

    @pytest.mark.asyncio
    async def test_department_analytics_period_parsing(self, service, mock_db):
        """Test department analytics parses period correctly."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Test different periods
        for period in ["30d", "90d", "1y"]:
            result = await service.get_department_analytics(period=period)
            assert result is not None


class TestSystemMetrics:
    """Tests for system-wide metrics.

    Note: The get_system_metrics() method has complex SQLAlchemy queries
    that are better tested via integration tests. These unit tests validate
    the service instantiation and helper method behavior.
    """

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create an AdminAnalyticsService with mock DB."""
        return AdminAnalyticsService(mock_db)

    def test_service_initialization(self, service, mock_db):
        """Test AdminAnalyticsService initializes with database session."""
        assert service.db == mock_db

    def test_service_has_required_methods(self, service):
        """Test AdminAnalyticsService has all required public methods."""
        assert hasattr(service, "get_fraud_metrics")
        assert hasattr(service, "get_nlp_metrics")
        assert hasattr(service, "get_department_analytics")
        assert hasattr(service, "get_system_metrics")
        assert callable(service.get_fraud_metrics)
        assert callable(service.get_nlp_metrics)
        assert callable(service.get_department_analytics)
        assert callable(service.get_system_metrics)


class TestSchemaStructures:
    """Tests for expected schema structures in analytics responses.

    These tests validate that the response schemas have the expected fields
    when properly constructed. The actual get_system_metrics() is better
    tested via integration tests due to complex SQLAlchemy queries.
    """

    def test_grievance_stats_schema_fields(self):
        """Test GrievanceStats schema has all required fields."""
        from app.schemas.admin import GrievanceStats

        stats = GrievanceStats(
            total=100,
            today=5,
            this_week=25,
            this_month=80,
            growth_rate=0.15,
        )

        assert stats.total == 100
        assert stats.today == 5
        assert stats.this_week == 25
        assert stats.this_month == 80
        assert stats.growth_rate == 0.15

    def test_user_stats_schema_fields(self):
        """Test UserStats schema has all required fields."""
        from app.schemas.admin import UserStats

        stats = UserStats(
            total_officers=50,
            active_officers=40,
            total_citizens=1000,
        )

        assert stats.total_officers == 50
        assert stats.active_officers == 40
        assert stats.total_citizens == 1000

    def test_resolution_stats_schema_fields(self):
        """Test ResolutionStats schema has all required fields."""
        from app.schemas.admin import ResolutionStats

        stats = ResolutionStats(
            avg_time_days=7.5,
            trend="down",
            fastest_dept="Revenue",
            slowest_dept="Police",
        )

        assert stats.avg_time_days == 7.5
        assert stats.trend == "down"
        assert stats.fastest_dept == "Revenue"
        assert stats.slowest_dept == "Police"

    def test_empathy_stats_schema_fields(self):
        """Test EmpathyStats schema has all required fields."""
        from app.schemas.admin import EmpathyStats

        stats = EmpathyStats(
            critical_cases=10,
            high_cases=25,
            avg_distress_score=6.5,
            sla_compliance=0.85,
        )

        assert stats.critical_cases == 10
        assert stats.high_cases == 25
        assert stats.avg_distress_score == 6.5
        assert stats.sla_compliance == 0.85

    def test_verification_stats_schema_fields(self):
        """Test VerificationStats schema has all required fields."""
        from app.schemas.admin import VerificationStats

        stats = VerificationStats(
            pending=15,
            verified_rate=0.92,
            disputed_rate=0.03,
        )

        assert stats.pending == 15
        assert stats.verified_rate == 0.92
        assert stats.disputed_rate == 0.03

    def test_growth_chart_point_schema_fields(self):
        """Test GrowthChartPoint schema has all required fields."""
        from app.schemas.admin import GrowthChartPoint

        point = GrowthChartPoint(
            date="2025-01-15",
            grievances=50,
            resolved=40,
            pending=10,
        )

        assert point.date == "2025-01-15"
        assert point.grievances == 50
        assert point.resolved == 40
        assert point.pending == 10


class TestSLAHeatmap:
    """Tests for SLA heatmap data schema."""

    def test_sla_heatmap_data_schema(self):
        """Test SLAHeatmapData schema has correct structure."""
        from app.schemas.admin import SLAHeatmapData

        heatmap = SLAHeatmapData(
            department="Revenue",
            within_sla=80,
            near_breach=15,
            breached=5,
        )

        assert heatmap.department == "Revenue"
        assert heatmap.within_sla == 80
        assert heatmap.near_breach == 15
        assert heatmap.breached == 5

    def test_satisfaction_trend_schema(self):
        """Test SatisfactionTrend schema has correct structure."""
        from app.schemas.admin import SatisfactionTrend

        trend = SatisfactionTrend(
            department="Revenue",
            date="2025-01",
            avg_satisfaction=4.2,
            feedback_count=150,
        )

        assert trend.department == "Revenue"
        assert trend.date == "2025-01"
        assert trend.avg_satisfaction == 4.2
        assert trend.feedback_count == 150

    def test_department_performance_schema(self):
        """Test DepartmentPerformance schema has correct structure."""
        from app.schemas.admin import DepartmentPerformance

        perf = DepartmentPerformance(
            department="Revenue",
            avg_resolution_days=7.5,
            sla_compliance_rate=0.85,
            total_grievances=100,
            satisfaction_score=4.2,
            rank=1,
        )

        assert perf.department == "Revenue"
        assert perf.avg_resolution_days == 7.5
        assert perf.sla_compliance_rate == 0.85
        assert perf.total_grievances == 100
        assert perf.satisfaction_score == 4.2
        assert perf.rank == 1
