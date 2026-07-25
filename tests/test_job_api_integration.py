from fastapi.testclient import TestClient  # Import FastAPI's synchronous test client
from sqlalchemy import delete  # Import a set-based SQL DELETE statement

from app.db.database import SessionFactory  # Import the production session factory
from app.main import app  # Import the fully configured FastAPI application
from app.models import Job  # Import the persistent Job ORM entity
from tests.constants import TEST_JOB_SOURCE  # Import the shared test-data marker


def _cleanup_api_integration_jobs() -> None:
    """Delete every Job created by API integration tests."""

    with SessionFactory() as session:
        session.execute(delete(Job).where(Job.source == TEST_JOB_SOURCE))
        session.commit()


def _valid_job_payload() -> dict[str, object]:
    """Return one valid request payload for the real API integration flow."""

    return {
        "source": TEST_JOB_SOURCE,
        "external_id": "api-integration-job-123",
        "title": "Generative AI Integration Engineer",
        "company_name": "Swiss Integration Bank",
        "location": "Geneva, Switzerland",
        "description": "Validate the complete HTTP-to-PostgreSQL Job lifecycle.",
        "employment_type": "full_time",
        "seniority_level": "senior",
        "workplace_type": "hybrid",
        "url": "https://example.com/jobs/api-integration-job-123",
        "posted_at": "2026-07-25T09:00:00+02:00",
    }


def test_job_api_complete_postgresql_lifecycle() -> None:
    """Verify create, read, list, update, delete, and not-found behavior."""

    _cleanup_api_integration_jobs()

    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/jobs",
                json=_valid_job_payload(),
            )

            assert create_response.status_code == 201

            created_job = create_response.json()
            job_id = created_job["id"]

            assert created_job["title"] == ("Generative AI Integration Engineer")
            assert created_job["is_active"] is True

            get_response = client.get(f"/jobs/{job_id}")

            assert get_response.status_code == 200
            assert get_response.json()["id"] == job_id

            list_response = client.get(
                "/jobs",
                params={
                    "offset": 0,
                    "limit": 10,
                },
            )

            assert list_response.status_code == 200
            assert list_response.json()["total"] >= 1
            assert any(item["id"] == job_id for item in list_response.json()["items"])

            update_response = client.patch(
                f"/jobs/{job_id}",
                json={
                    "title": "Senior Generative AI Integration Engineer",
                    "is_active": False,
                },
            )

            assert update_response.status_code == 200
            assert update_response.json()["title"] == (
                "Senior Generative AI Integration Engineer"
            )
            assert update_response.json()["is_active"] is False

            delete_response = client.delete(f"/jobs/{job_id}")

            assert delete_response.status_code == 204
            assert delete_response.content == b""

            missing_response = client.get(f"/jobs/{job_id}")

            assert missing_response.status_code == 404
    finally:
        _cleanup_api_integration_jobs()
