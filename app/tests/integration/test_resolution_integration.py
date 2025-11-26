"""Integration tests for Smart Resolution Engine API.

Tests the full API flow from HTTP request to database.
Requires a running database with seed data.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.integration
class TestResolutionAPIIntegration:
    """Integration tests for Smart Resolution API.

    Note: These tests require:
    - A running PostgreSQL database
    - Seed data for templates and questions
    - Authentication tokens for protected endpoints
    """

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires running database and auth setup")
    async def test_analyze_endpoint_returns_root_cause(self, client, seeded_db, test_grievance, auth_headers):
        """Test POST /api/v1/resolution/analyze/{grievance_id}

        Should return:
        - detected_root_cause: One of the 10 root causes
        - confidence_score: 0.0 to 1.0
        - detection_signals: List of signals found
        - suggested_templates: List of matching templates
        """
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                f"/api/v1/resolution/analyze/{test_grievance.grievance_id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "detected_root_cause" in data
        assert "confidence_score" in data
        assert data["confidence_score"] >= 0.0
        assert data["confidence_score"] <= 1.0
        assert "detection_signals" in data
        assert isinstance(data["detection_signals"], list)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires running database and auth setup")
    async def test_list_templates_endpoint(self, auth_headers):
        """Test GET /api/v1/resolution/templates

        Should return list of active templates with success rates.
        """
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/resolution/templates",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            template = data[0]
            assert "template_key" in template
            assert "success_rate" in template
            assert "action_steps" in template

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires running database and auth setup")
    async def test_apply_template_endpoint(self, client, seeded_db, test_grievance, auth_headers):
        """Test POST /api/v1/resolution/apply/{grievance_id}

        Should execute template actions and return application ID.
        """
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                f"/api/v1/resolution/apply/{test_grievance.grievance_id}",
                json={"template_key": "pension_bank_mismatch_fix"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "application_id" in data
        assert "actions_executed" in data

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires running database and auth setup")
    async def test_get_questions_endpoint(self, auth_headers):
        """Test GET /api/v1/resolution/questions/{root_cause}

        Should return questions for the given root cause.
        """
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/resolution/questions/MISSING_INFORMATION",
                params={"language": "en"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            question = data[0]
            assert "question_text" in question
            assert "response_type" in question
            assert "is_required" in question

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires running database and auth setup")
    async def test_submit_clarification_endpoint(self, client, seeded_db, test_grievance):
        """Test POST /api/v1/resolution/clarify/{grievance_id}

        Should save clarification responses.
        """
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                f"/api/v1/resolution/clarify/{test_grievance.grievance_id}",
                json={
                    "responses": [
                        {"question_id": 1, "response_text": "Survey 123/456"},
                    ]
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["responses_saved"] == 1

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires running database and auth setup")
    async def test_update_application_result_endpoint(self, client, seeded_db, auth_headers):
        """Test POST /api/v1/resolution/applications/{application_id}/result

        Should update application result and template success rate.
        """
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/resolution/applications/1/result",
                json={"result": "SUCCESS", "notes": "Resolved successfully"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
