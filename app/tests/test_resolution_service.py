"""Unit tests for Smart Resolution Engine service.

Tests cover:
- Root cause detection for different signal patterns
- Template application and tracking
- Clarification question retrieval
- Edge cases and error handling
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.resolution import (
    ApplyTemplateRequest,
    ClarificationAnswer,
    ClarificationSubmission,
    InterventionResult,
    RootCause,
)
from app.services.resolution_service import SmartResolutionService


class TestRootCauseDetection:
    """Unit tests for root cause detection."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def resolution_service(self, mock_db):
        """Create a resolution service with mock DB."""
        return SmartResolutionService(mock_db)

    @pytest.mark.asyncio
    async def test_wrong_department_detection_english(self, resolution_service, mock_db):
        """Test WRONG_DEPARTMENT detection with English officer notes."""
        # Arrange
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00001"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "Revenue"
        mock_grievance.category = "Land Records"
        mock_grievance.officer_notes = "This belongs to Municipal, not my department"
        mock_grievance.resolution_notes = None
        mock_grievance.status = "assigned"
        mock_grievance.assigned_officer_id = "OFF001"
        mock_grievance.contact_attempts = 0

        resolution_service._get_grievance = AsyncMock(return_value=mock_grievance)
        resolution_service._get_officer_case_count = AsyncMock(return_value=20)
        resolution_service._check_duplicate = AsyncMock(return_value=False)
        resolution_service._get_matching_templates = AsyncMock(return_value=[])
        resolution_service.get_clarification_questions = AsyncMock(return_value=[])

        # Act
        result = await resolution_service.analyze_root_cause("PGRS-2025-GTR-00001")

        # Assert
        assert result.detected_root_cause == RootCause.WRONG_DEPARTMENT
        assert result.confidence_score >= Decimal("0.25")
        assert "Officer note:" in result.detection_signals[0]

    @pytest.mark.asyncio
    async def test_wrong_department_detection_telugu(self, resolution_service, mock_db):
        """Test WRONG_DEPARTMENT detection with Telugu officer notes."""
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00002"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "Revenue"
        mock_grievance.category = "Land Records"
        mock_grievance.officer_notes = "ఇది మా పరిధిలో లేదు, వేరే డిపార్ట్‌మెంట్"
        mock_grievance.resolution_notes = None
        mock_grievance.status = "assigned"
        mock_grievance.assigned_officer_id = "OFF001"
        mock_grievance.contact_attempts = 0

        resolution_service._get_grievance = AsyncMock(return_value=mock_grievance)
        resolution_service._get_officer_case_count = AsyncMock(return_value=20)
        resolution_service._check_duplicate = AsyncMock(return_value=False)
        resolution_service._get_matching_templates = AsyncMock(return_value=[])
        resolution_service.get_clarification_questions = AsyncMock(return_value=[])

        result = await resolution_service.analyze_root_cause("PGRS-2025-GTR-00002")

        assert result.detected_root_cause == RootCause.WRONG_DEPARTMENT
        assert result.confidence_score >= Decimal("0.25")

    @pytest.mark.asyncio
    async def test_officer_overload_detection(self, resolution_service, mock_db):
        """Test OFFICER_OVERLOAD detection when officer has 100+ cases."""
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00003"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "Pension"
        mock_grievance.category = "Pension Delay"
        mock_grievance.officer_notes = None
        mock_grievance.resolution_notes = None
        mock_grievance.status = "assigned"
        mock_grievance.assigned_officer_id = "OFF002"
        mock_grievance.contact_attempts = 0

        resolution_service._get_grievance = AsyncMock(return_value=mock_grievance)
        resolution_service._get_officer_case_count = AsyncMock(return_value=150)
        resolution_service._check_duplicate = AsyncMock(return_value=False)
        resolution_service._get_matching_templates = AsyncMock(return_value=[])
        resolution_service.get_clarification_questions = AsyncMock(return_value=[])

        result = await resolution_service.analyze_root_cause("PGRS-2025-GTR-00003")

        assert result.detected_root_cause == RootCause.OFFICER_OVERLOAD
        assert result.confidence_score >= Decimal("0.90")

    @pytest.mark.asyncio
    async def test_duplicate_case_detection(self, resolution_service, mock_db):
        """Test DUPLICATE_CASE detection with similar recent case."""
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00004"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "Pension"
        mock_grievance.category = "Pension Delay"
        mock_grievance.citizen_phone = "9876543210"
        mock_grievance.officer_notes = None
        mock_grievance.resolution_notes = None
        mock_grievance.status = "assigned"
        mock_grievance.assigned_officer_id = "OFF001"
        mock_grievance.contact_attempts = 0

        resolution_service._get_grievance = AsyncMock(return_value=mock_grievance)
        resolution_service._get_officer_case_count = AsyncMock(return_value=20)
        resolution_service._check_duplicate = AsyncMock(return_value=True)
        resolution_service._get_matching_templates = AsyncMock(return_value=[])
        resolution_service.get_clarification_questions = AsyncMock(return_value=[])

        result = await resolution_service.analyze_root_cause("PGRS-2025-GTR-00004")

        assert result.detected_root_cause == RootCause.DUPLICATE_CASE
        assert result.confidence_score >= Decimal("0.95")

    @pytest.mark.asyncio
    async def test_missing_info_detection_english(self, resolution_service, mock_db):
        """Test MISSING_INFORMATION detection with English request."""
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00005"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "Revenue"
        mock_grievance.category = "Land Survey"
        mock_grievance.officer_notes = "Please provide survey number, missing details"
        mock_grievance.resolution_notes = None
        mock_grievance.status = "assigned"
        mock_grievance.assigned_officer_id = "OFF001"
        mock_grievance.contact_attempts = 0

        resolution_service._get_grievance = AsyncMock(return_value=mock_grievance)
        resolution_service._get_officer_case_count = AsyncMock(return_value=20)
        resolution_service._check_duplicate = AsyncMock(return_value=False)
        resolution_service._get_matching_templates = AsyncMock(return_value=[])
        resolution_service.get_clarification_questions = AsyncMock(return_value=[])

        result = await resolution_service.analyze_root_cause("PGRS-2025-GTR-00005")

        assert result.detected_root_cause == RootCause.MISSING_INFORMATION

    @pytest.mark.asyncio
    async def test_citizen_unreachable_detection(self, resolution_service, mock_db):
        """Test CITIZEN_UNREACHABLE detection with multiple contact attempts."""
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00006"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "Pension"
        mock_grievance.category = "Pension Delay"
        mock_grievance.officer_notes = "Phone not reachable, tried 3 times"
        mock_grievance.resolution_notes = None
        mock_grievance.status = "assigned"
        mock_grievance.assigned_officer_id = "OFF001"
        mock_grievance.contact_attempts = 3

        resolution_service._get_grievance = AsyncMock(return_value=mock_grievance)
        resolution_service._get_officer_case_count = AsyncMock(return_value=20)
        resolution_service._check_duplicate = AsyncMock(return_value=False)
        resolution_service._get_matching_templates = AsyncMock(return_value=[])
        resolution_service.get_clarification_questions = AsyncMock(return_value=[])

        result = await resolution_service.analyze_root_cause("PGRS-2025-GTR-00006")

        assert result.detected_root_cause == RootCause.CITIZEN_UNREACHABLE
        assert "Contact attempts" in str(result.detection_signals)

    @pytest.mark.asyncio
    async def test_default_to_missing_info_on_no_signals(self, resolution_service, mock_db):
        """Test default to MISSING_INFORMATION when no clear signals."""
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00007"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "Pension"
        mock_grievance.category = "Pension Delay"
        mock_grievance.officer_notes = None
        mock_grievance.resolution_notes = None
        mock_grievance.status = "assigned"
        mock_grievance.assigned_officer_id = None
        mock_grievance.contact_attempts = 0

        resolution_service._get_grievance = AsyncMock(return_value=mock_grievance)
        resolution_service._get_officer_case_count = AsyncMock(return_value=0)
        resolution_service._check_duplicate = AsyncMock(return_value=False)
        resolution_service._get_matching_templates = AsyncMock(return_value=[])
        resolution_service.get_clarification_questions = AsyncMock(return_value=[])

        result = await resolution_service.analyze_root_cause("PGRS-2025-GTR-00007")

        assert result.detected_root_cause == RootCause.MISSING_INFORMATION
        assert result.confidence_score == Decimal("0.50")

    @pytest.mark.asyncio
    async def test_grievance_not_found(self, resolution_service, mock_db):
        """Test error when grievance not found."""
        resolution_service._get_grievance = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await resolution_service.analyze_root_cause("PGRS-2025-GTR-99999")


class TestTemplateApplication:
    """Unit tests for template application."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.execute = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def resolution_service(self, mock_db):
        """Create a resolution service with mock DB."""
        return SmartResolutionService(mock_db)

    @pytest.mark.asyncio
    async def test_template_application_success(self, resolution_service, mock_db):
        """Test successful template application."""
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_key = "pension_bank_mismatch_fix"
        mock_template.template_title = "Update Bank Account"
        mock_template.action_steps = [
            {"step": 1, "action": "VERIFY_AADHAAR", "description": "Verify Aadhaar"},
            {"step": 2, "action": "UPDATE_RECORD", "description": "Update record"},
        ]
        mock_template.similar_cases_resolved = 100

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock the application object after refresh
        def set_application_id(app):
            app.id = 999

        mock_db.refresh.side_effect = set_application_id

        request = ApplyTemplateRequest(template_key="pension_bank_mismatch_fix")

        result = await resolution_service.apply_template(
            "PGRS-2025-GTR-00001",
            request,
            "OFF001"
        )

        assert result.success is True
        assert result.application_id == 999
        assert len(result.actions_executed) == 2
        assert all(a.status == "COMPLETED" for a in result.actions_executed)

    @pytest.mark.asyncio
    async def test_template_not_found(self, resolution_service, mock_db):
        """Test error when template not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        request = ApplyTemplateRequest(template_key="nonexistent_template")

        with pytest.raises(ValueError, match="not found"):
            await resolution_service.apply_template(
                "PGRS-2025-GTR-00001",
                request,
                "OFF001"
            )


class TestClarificationQuestions:
    """Unit tests for clarification question retrieval."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def resolution_service(self, mock_db):
        """Create a resolution service with mock DB."""
        return SmartResolutionService(mock_db)

    @pytest.mark.asyncio
    async def test_get_questions_english(self, resolution_service, mock_db):
        """Test getting questions in English."""
        mock_question = MagicMock()
        mock_question.id = 1
        mock_question.question_text_en = "Please provide survey number"
        mock_question.question_text_te = "సర్వే నంబర్ అందించండి"
        mock_question.response_type = "TEXT"
        mock_question.response_options = None
        mock_question.is_required = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_question]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await resolution_service.get_clarification_questions(
            RootCause.MISSING_INFORMATION,
            department="Revenue",
            language="en",
        )

        assert len(result) == 1
        assert result[0].question_text == "Please provide survey number"

    @pytest.mark.asyncio
    async def test_get_questions_telugu(self, resolution_service, mock_db):
        """Test getting questions in Telugu."""
        mock_question = MagicMock()
        mock_question.id = 1
        mock_question.question_text_en = "Please provide survey number"
        mock_question.question_text_te = "సర్వే నంబర్ అందించండి"
        mock_question.response_type = "TEXT"
        mock_question.response_options = None
        mock_question.is_required = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_question]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await resolution_service.get_clarification_questions(
            RootCause.MISSING_INFORMATION,
            department="Revenue",
            language="te",
        )

        assert len(result) == 1
        assert result[0].question_text == "సర్వే నంబర్ అందించండి"


class TestClarificationSubmission:
    """Unit tests for clarification submission."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def resolution_service(self, mock_db):
        """Create a resolution service with mock DB."""
        return SmartResolutionService(mock_db)

    @pytest.mark.asyncio
    async def test_submit_clarification_success(self, resolution_service, mock_db):
        """Test successful clarification submission."""
        submission = ClarificationSubmission(
            responses=[
                ClarificationAnswer(
                    question_id=1,
                    response_text="Survey number: 123/456",
                ),
                ClarificationAnswer(
                    question_id=2,
                    response_text="Village: Anantapur",
                ),
            ]
        )

        result = await resolution_service.submit_clarification(
            "PGRS-2025-GTR-00001",
            submission,
        )

        assert result.success is True
        assert result.responses_saved == 2
        assert result.next_action == "RE_ANALYZE"
        assert mock_db.add.call_count == 2


class TestApplicationResultUpdate:
    """Unit tests for updating application results."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def resolution_service(self, mock_db):
        """Create a resolution service with mock DB."""
        return SmartResolutionService(mock_db)

    @pytest.mark.asyncio
    async def test_update_result_success(self, resolution_service, mock_db):
        """Test successful result update."""
        mock_application = MagicMock()
        mock_application.id = 1
        mock_application.template_id = 5

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_application
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock the stats update
        mock_stats = MagicMock()
        mock_stats.one.return_value = MagicMock(total=10, successes=8)

        async def mock_execute(stmt):
            if "count" in str(stmt).lower():
                return mock_stats
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        await resolution_service.update_application_result(
            application_id=1,
            result=InterventionResult.SUCCESS,
            notes="Resolved successfully",
        )

        assert mock_application.result == "SUCCESS"
        assert mock_application.notes == "Resolved successfully"

    @pytest.mark.asyncio
    async def test_update_result_not_found(self, resolution_service, mock_db):
        """Test error when application not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="not found"):
            await resolution_service.update_application_result(
                application_id=999,
                result=InterventionResult.SUCCESS,
            )


class TestGetSuggestedTemplates:
    """Unit tests for get_suggested_templates()."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def resolution_service(self, mock_db):
        """Create a resolution service with mock DB."""
        return SmartResolutionService(mock_db)

    @pytest.mark.asyncio
    async def test_get_suggested_templates_with_analysis(self, resolution_service, mock_db):
        """Test getting suggested templates when analysis exists."""
        # Arrange
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00001"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "Pension"
        mock_grievance.category = "Pension Delay"

        mock_analysis = MagicMock()
        mock_analysis.detected_root_cause = "MISSING_INFORMATION"

        resolution_service._get_grievance = AsyncMock(return_value=mock_grievance)

        # First call returns analysis, second returns templates
        mock_analysis_result = MagicMock()
        mock_analysis_result.scalar_one_or_none.return_value = mock_analysis

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_key = "pension_bank_mismatch_fix"
        mock_template.department = "Pension"
        mock_template.category = "Pension Delay"
        mock_template.root_cause = "MISSING_INFORMATION"
        mock_template.template_title = "Update Bank Account"
        mock_template.template_description = "Fix bank mismatch"
        mock_template.action_steps = [{"step": 1, "action": "TEST", "description": "Test"}]
        mock_template.success_rate = Decimal("95.20")
        mock_template.avg_resolution_hours = 4
        mock_template.similar_cases_resolved = 100
        mock_template.is_active = True

        mock_templates_result = MagicMock()
        mock_templates_result.scalars.return_value.all.return_value = [mock_template]

        call_count = [0]
        async def mock_execute(stmt):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_analysis_result
            return mock_templates_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        # Act
        result = await resolution_service.get_suggested_templates("PGRS-2025-GTR-00001")

        # Assert
        assert len(result) == 1
        assert result[0].template_key == "pension_bank_mismatch_fix"

    @pytest.mark.asyncio
    async def test_get_suggested_templates_no_grievance(self, resolution_service, mock_db):
        """Test returns empty list when grievance not found."""
        resolution_service._get_grievance = AsyncMock(return_value=None)

        result = await resolution_service.get_suggested_templates("PGRS-2025-GTR-99999")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_suggested_templates_no_analysis(self, resolution_service, mock_db):
        """Test getting templates without prior analysis."""
        mock_grievance = MagicMock()
        mock_grievance.grievance_id = "PGRS-2025-GTR-00001"
        mock_grievance.department = MagicMock()
        mock_grievance.department.dept_name = "Revenue"
        mock_grievance.category = "Land Records"

        resolution_service._get_grievance = AsyncMock(return_value=mock_grievance)

        # No analysis exists
        mock_analysis_result = MagicMock()
        mock_analysis_result.scalar_one_or_none.return_value = None

        mock_templates_result = MagicMock()
        mock_templates_result.scalars.return_value.all.return_value = []

        call_count = [0]
        async def mock_execute(stmt):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_analysis_result
            return mock_templates_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        result = await resolution_service.get_suggested_templates("PGRS-2025-GTR-00001")

        assert result == []


class TestListTemplates:
    """Unit tests for list_templates()."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def resolution_service(self, mock_db):
        """Create a resolution service with mock DB."""
        return SmartResolutionService(mock_db)

    @pytest.mark.asyncio
    async def test_list_templates_no_filters(self, resolution_service, mock_db):
        """Test listing all active templates."""
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_key = "pension_bank_mismatch_fix"
        mock_template.department = "Pension"
        mock_template.category = "Pension Delay"
        mock_template.root_cause = "MISSING_INFORMATION"
        mock_template.template_title = "Update Bank Account"
        mock_template.template_description = "Fix bank mismatch"
        mock_template.action_steps = [{"step": 1, "action": "TEST", "description": "Test"}]
        mock_template.success_rate = Decimal("95.20")
        mock_template.avg_resolution_hours = 4
        mock_template.similar_cases_resolved = 100
        mock_template.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_template]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await resolution_service.list_templates()

        assert len(result) == 1
        assert result[0].template_key == "pension_bank_mismatch_fix"
        assert result[0].success_rate == Decimal("95.20")

    @pytest.mark.asyncio
    async def test_list_templates_with_department_filter(self, resolution_service, mock_db):
        """Test listing templates filtered by department."""
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_key = "pension_verification_pending"
        mock_template.department = "Pension"
        mock_template.category = "Pension Delay"
        mock_template.root_cause = "EXTERNAL_DEPENDENCY"
        mock_template.template_title = "Fast-track Verification"
        mock_template.template_description = "Expedite verification"
        mock_template.action_steps = [{"step": 1, "action": "TEST", "description": "Test"}]
        mock_template.success_rate = Decimal("87.50")
        mock_template.avg_resolution_hours = 24
        mock_template.similar_cases_resolved = 50
        mock_template.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_template]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await resolution_service.list_templates(department="Pension")

        assert len(result) == 1
        assert result[0].department == "Pension"

    @pytest.mark.asyncio
    async def test_list_templates_with_root_cause_filter(self, resolution_service, mock_db):
        """Test listing templates filtered by root cause."""
        mock_template = MagicMock()
        mock_template.id = 5
        mock_template.template_key = "duplicate_merge"
        mock_template.department = "General"
        mock_template.category = "All"
        mock_template.root_cause = "DUPLICATE_CASE"
        mock_template.template_title = "Merge Duplicate Cases"
        mock_template.template_description = "Merge duplicate grievance"
        mock_template.action_steps = [{"step": 1, "action": "TEST", "description": "Test"}]
        mock_template.success_rate = Decimal("96.70")
        mock_template.avg_resolution_hours = 1
        mock_template.similar_cases_resolved = 200
        mock_template.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_template]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await resolution_service.list_templates(root_cause=RootCause.DUPLICATE_CASE)

        assert len(result) == 1
        assert result[0].root_cause == RootCause.DUPLICATE_CASE

    @pytest.mark.asyncio
    async def test_list_templates_empty_result(self, resolution_service, mock_db):
        """Test listing templates returns empty list when none match."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await resolution_service.list_templates(
            department="NonExistent",
            category="Unknown",
        )

        assert result == []
