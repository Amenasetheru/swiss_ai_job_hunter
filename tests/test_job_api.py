from collections.abc import Generator  # Import the generator type used by fixtures
from uuid import UUID, uuid4  # Import UUID typing and generation

import pytest  # Import the pytest framework
from fastapi.testclient import TestClient  # Import the synchronous FastAPI test client

from app.main import app  # Import the fully configured FastAPI application
from app.services import (  # Import business errors and the overridden dependency
    JobAlreadyExistsError,
    JobNotFoundError,
    get_job_service,
)


class FakeJobService:
    """Provide predictable Job API behavior without accessing PostgreSQL."""

    def __init__(self) -> None:
        """Initialize configurable method results and errors."""

        self.created_job = None
        self.list_response = None
        self.job_response = None
        self.updated_job = None

        self.create_error = None
        self.get_error = None
        self.update_error = None
        self.delete_error = None

        self.received_create_data = None
        self.received_offset = None
        self.received_limit = None
        self.received_job_id = None
        self.received_update_data = None
        self.deleted_job_id = None

    def create_job(self, job_data):
        """Return a configured response or raise a creation error."""

        self.received_create_data = job_data

        if self.create_error is not None:
            raise self.create_error

        return self.created_job

    def list_jobs(self, *, offset: int, limit: int):
        """Return the configured paginated response."""

        self.received_offset = offset
        self.received_limit = limit

        return self.list_response

    def get_job(self, job_id: UUID):
        """Return a configured Job response or raise a lookup error."""

        self.received_job_id = job_id

        if self.get_error is not None:
            raise self.get_error

        return self.job_response

    def update_job(self, job_id: UUID, job_data):
        """Return a configured update response or raise an update error."""

        self.received_job_id = job_id
        self.received_update_data = job_data

        if self.update_error is not None:
            raise self.update_error

        return self.updated_job

    def delete_job(self, job_id: UUID) -> None:
        """Record deletion or raise a configured deletion error."""

        self.deleted_job_id = job_id

        if self.delete_error is not None:
            raise self.delete_error


@pytest.fixture
def fake_job_service() -> FakeJobService:
    """Provide one fresh fake service for each API test."""

    return FakeJobService()


@pytest.fixture
def api_client(
    fake_job_service: FakeJobService,
) -> Generator[TestClient, None, None]:
    """Provide a TestClient with the JobService dependency overridden."""

    app.dependency_overrides[get_job_service] = lambda: fake_job_service

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def _valid_job_payload() -> dict[str, object]:
    """Return one valid HTTP request payload for Job creation."""

    return {
        "source": "company_careers",
        "external_id": "api-job-123",
        "title": "Generative AI Engineer",
        "company_name": "Swiss API Bank",
        "location": "Geneva, Switzerland",
        "description": "Build secure production-grade LLM systems.",
        "employment_type": "full_time",
        "seniority_level": "senior",
        "workplace_type": "hybrid",
        "url": "https://example.com/jobs/api-job-123",
        "posted_at": "2026-07-25T09:00:00+02:00",
    }


def _job_response_payload(
    *,
    job_id: UUID | None = None,
    title: str = "Generative AI Engineer",
) -> dict[str, object]:
    """Return one complete response compatible with JobRead."""

    return {
        **_valid_job_payload(),
        "id": str(job_id or uuid4()),
        "title": title,
        "discovered_at": "2026-07-25T07:10:00Z",
        "is_active": True,
        "created_at": "2026-07-25T07:10:00Z",
        "updated_at": "2026-07-25T07:10:00Z",
    }


def test_create_job_returns_http_201(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify successful Job creation through the HTTP boundary."""

    fake_job_service.created_job = _job_response_payload()

    response = api_client.post(
        "/jobs",
        json=_valid_job_payload(),
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Generative AI Engineer"
    assert response.json()["is_active"] is True
    assert fake_job_service.received_create_data.title == ("Generative AI Engineer")


def test_create_job_returns_http_409_for_duplicate(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify duplicate business conflicts become HTTP 409 responses."""

    fake_job_service.create_error = JobAlreadyExistsError(constraint_name="uq_jobs_url")

    response = api_client.post(
        "/jobs",
        json=_valid_job_payload(),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "A job with the same URL already exists."}


def test_list_jobs_returns_paginated_response(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify the public collection endpoint and pagination metadata."""

    fake_job_service.list_response = {
        "items": [_job_response_payload()],
        "total": 1,
        "offset": 20,
        "limit": 10,
    }

    response = api_client.get(
        "/jobs",
        params={
            "offset": 20,
            "limit": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert fake_job_service.received_offset == 20
    assert fake_job_service.received_limit == 10


def test_get_job_returns_http_200(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify retrieval of one Job by UUID."""

    job_id = uuid4()
    fake_job_service.job_response = _job_response_payload(job_id=job_id)

    response = api_client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(job_id)
    assert fake_job_service.received_job_id == job_id


def test_get_job_returns_http_404(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify missing Jobs become HTTP 404 responses."""

    job_id = uuid4()
    fake_job_service.get_error = JobNotFoundError(job_id)

    response = api_client.get(f"/jobs/{job_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": f"Job with ID '{job_id}' was not found."}


def test_get_job_rejects_invalid_uuid(
    api_client: TestClient,
) -> None:
    """Verify FastAPI rejects malformed path identifiers before the Service."""

    response = api_client.get("/jobs/not-a-valid-uuid")

    assert response.status_code == 422


def test_list_jobs_rejects_invalid_limit(
    api_client: TestClient,
) -> None:
    """Verify invalid HTTP pagination values are rejected."""

    response = api_client.get(
        "/jobs",
        params={
            "limit": 501,
        },
    )

    assert response.status_code == 422


def test_update_job_returns_http_200(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify successful partial Job updates."""

    job_id = uuid4()
    fake_job_service.updated_job = _job_response_payload(
        job_id=job_id,
        title="Senior Generative AI Engineer",
    )

    response = api_client.patch(
        f"/jobs/{job_id}",
        json={
            "title": "Senior Generative AI Engineer",
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Senior Generative AI Engineer"
    assert fake_job_service.received_job_id == job_id
    assert fake_job_service.received_update_data.title == (
        "Senior Generative AI Engineer"
    )
    assert fake_job_service.received_update_data.is_active is False


def test_update_job_returns_http_404(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify updates of missing Jobs become HTTP 404 responses."""

    job_id = uuid4()
    fake_job_service.update_error = JobNotFoundError(job_id)

    response = api_client.patch(
        f"/jobs/{job_id}",
        json={
            "title": "Missing Job",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (f"Job with ID '{job_id}' was not found.")


def test_update_job_returns_http_409(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify update uniqueness conflicts become HTTP 409 responses."""

    job_id = uuid4()
    fake_job_service.update_error = JobAlreadyExistsError(constraint_name="uq_jobs_url")

    response = api_client.patch(
        f"/jobs/{job_id}",
        json={
            "url": "https://example.com/jobs/already-existing",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == ("A job with the same URL already exists.")


def test_update_job_rejects_empty_payload(
    api_client: TestClient,
) -> None:
    """Verify Pydantic rejects empty PATCH requests."""

    response = api_client.patch(
        f"/jobs/{uuid4()}",
        json={},
    )

    assert response.status_code == 422


def test_delete_job_returns_http_204(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify successful deletion returns an empty HTTP 204 response."""

    job_id = uuid4()

    response = api_client.delete(f"/jobs/{job_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert fake_job_service.deleted_job_id == job_id


def test_delete_job_returns_http_404(
    api_client: TestClient,
    fake_job_service: FakeJobService,
) -> None:
    """Verify deletion of a missing Job becomes HTTP 404."""

    job_id = uuid4()
    fake_job_service.delete_error = JobNotFoundError(job_id)

    response = api_client.delete(f"/jobs/{job_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == (f"Job with ID '{job_id}' was not found.")
