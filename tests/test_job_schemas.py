from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import JobCreate, JobListResponse, JobRead, JobUpdate


def _valid_job_payload() -> dict[str, object]:
    """Return one complete valid payload for Job schema tests."""

    return {
        "source": "company_careers",
        "external_id": "job-123",
        "title": "Generative AI Engineer",
        "company_name": "Swiss AI Bank",
        "location": "Geneva, Switzerland",
        "description": "Build secure production-grade LLM systems.",
        "employment_type": "full_time",
        "seniority_level": "senior",
        "workplace_type": "hybrid",
        "url": "https://example.com/jobs/job-123",
        "posted_at": "2026-07-23T08:00:00+02:00",
    }


def test_job_create_accepts_valid_payload() -> None:
    """Verify that valid public Job input is normalized and accepted."""

    job = JobCreate.model_validate(_valid_job_payload())

    assert job.title == "Generative AI Engineer"
    assert job.employment_type == "full_time"
    assert job.workplace_type == "hybrid"
    assert str(job.url) == "https://example.com/jobs/job-123"


def test_job_create_strips_surrounding_whitespace() -> None:
    """Verify that public text input is normalized before business processing."""

    payload = _valid_job_payload()
    payload["title"] = "   LLM Engineer   "

    job = JobCreate.model_validate(payload)

    assert job.title == "LLM Engineer"


def test_job_create_rejects_invalid_employment_type() -> None:
    """Verify that unsupported business categories are rejected early."""

    payload = _valid_job_payload()
    payload["employment_type"] = "permanent_super_contract"

    with pytest.raises(ValidationError):
        JobCreate.model_validate(payload)


def test_job_create_rejects_invalid_url() -> None:
    """Verify that malformed job source URLs are rejected."""

    payload = _valid_job_payload()
    payload["url"] = "not-a-valid-url"

    with pytest.raises(ValidationError):
        JobCreate.model_validate(payload)


def test_job_create_rejects_unknown_fields() -> None:
    """Verify that accidental or unauthorized input fields are rejected."""

    payload = _valid_job_payload()
    payload["admin_override"] = True

    with pytest.raises(ValidationError):
        JobCreate.model_validate(payload)


def test_job_create_rejects_blank_required_text() -> None:
    """Verify that whitespace-only required values are rejected."""

    payload = _valid_job_payload()
    payload["title"] = "   "

    with pytest.raises(ValidationError):
        JobCreate.model_validate(payload)


def test_job_update_accepts_partial_payload() -> None:
    """Verify that a Job update can contain only the modified fields."""

    update = JobUpdate.model_validate(
        {
            "title": "Senior LLM Engineer",
            "is_active": False,
        }
    )

    assert update.title == "Senior LLM Engineer"
    assert update.is_active is False
    assert update.company_name is None


def test_job_update_rejects_unknown_fields() -> None:
    """Verify that unsupported update fields are rejected."""

    with pytest.raises(ValidationError):
        JobUpdate.model_validate(
            {
                "unknown_field": "value",
            }
        )


def test_job_read_accepts_attribute_based_object() -> None:
    """Verify conversion from an ORM-like object into the public response schema."""

    class JobObject:
        source = "company_careers"
        external_id = "job-read-123"
        title = "AI Engineer"
        company_name = "Swiss Read Bank"
        location = "Basel, Switzerland"
        description = "Build intelligent job-search systems."
        employment_type = "full_time"
        seniority_level = "mid"
        workplace_type = "hybrid"
        url = "https://example.com/jobs/job-read-123"
        posted_at = datetime(2026, 7, 23, 8, 0, tzinfo=UTC)
        id = uuid4()
        discovered_at = datetime.now(UTC)
        is_active = True
        created_at = datetime.now(UTC)
        updated_at = datetime.now(UTC)

    response = JobRead.model_validate(JobObject())

    assert response.id == JobObject.id
    assert response.title == "AI Engineer"
    assert response.is_active is True


def test_job_create_rejects_naive_posted_at() -> None:
    """Verify that publication datetimes require explicit timezone information."""

    payload = _valid_job_payload()
    payload["posted_at"] = "2026-07-24T09:00:00"

    with pytest.raises(
        ValidationError,
        match="posted_at must include timezone information",
    ):
        JobCreate.model_validate(payload)


def test_job_update_rejects_empty_payload() -> None:
    """Verify that partial updates contain at least one actual field."""

    with pytest.raises(
        ValidationError,
        match="At least one field must be provided",
    ):
        JobUpdate.model_validate({})


@pytest.mark.parametrize(
    "field_name",
    [
        "source",
        "title",
        "company_name",
        "description",
        "url",
    ],
)
def test_job_update_rejects_null_required_fields(
    field_name: str,
) -> None:
    """Verify that required database fields cannot be explicitly cleared."""

    with pytest.raises(
        ValidationError,
        match="Required job fields cannot be null",
    ):
        JobUpdate.model_validate(
            {
                field_name: None,
            }
        )


def test_job_update_allows_null_optional_fields() -> None:
    """Verify that nullable database fields can be explicitly cleared."""

    update = JobUpdate.model_validate(
        {
            "location": None,
            "external_id": None,
            "employment_type": None,
        }
    )

    update_data = update.model_dump(exclude_unset=True)

    assert update_data == {
        "location": None,
        "external_id": None,
        "employment_type": None,
    }


def test_job_update_dump_contains_only_provided_fields() -> None:
    """Verify that the future Service receives only explicitly updated fields."""

    update = JobUpdate.model_validate(
        {
            "title": "Senior Agentic AI Engineer",
            "is_active": False,
        }
    )

    update_data = update.model_dump(exclude_unset=True)

    assert update_data == {
        "title": "Senior Agentic AI Engineer",
        "is_active": False,
    }


def test_job_read_serializes_real_orm_job(
    db_session,
    job_repository,
) -> None:
    """Verify conversion from a real SQLAlchemy Job into the public schema."""

    from app.models import Job
    from tests.constants import TEST_JOB_SOURCE

    job = Job(
        source=TEST_JOB_SOURCE,
        external_id="job-read-real-orm",
        title="Production LLM Engineer",
        company_name="Swiss ORM Bank",
        location="Zurich, Switzerland",
        description="Build secure and observable AI systems.",
        employment_type="full_time",
        seniority_level="senior",
        workplace_type="hybrid",
        url="https://example.com/jobs/job-read-real-orm",
    )

    job_repository.create(job)
    db_session.commit()
    db_session.refresh(job)

    response = JobRead.model_validate(job)
    response_json = response.model_dump(mode="json")

    assert response.id == job.id
    assert response.title == job.title
    assert response.created_at == job.created_at
    assert response_json["id"] == str(job.id)
    assert response_json["url"] == job.url


def test_job_list_response_accepts_valid_pagination() -> None:
    """Verify that a valid paginated Job response is accepted."""

    current_time = datetime.now(UTC)

    response = JobRead.model_validate(
        {
            **_valid_job_payload(),
            "id": uuid4(),
            "discovered_at": current_time,
            "is_active": True,
            "created_at": current_time,
            "updated_at": current_time,
        }
    )

    page = JobListResponse.model_validate(
        {
            "items": [response],
            "total": 1,
            "offset": 0,
            "limit": 20,
        }
    )

    assert len(page.items) == 1
    assert page.total == 1
    assert page.offset == 0
    assert page.limit == 20


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("total", -1),
        ("offset", -1),
        ("limit", 0),
        ("limit", 501),
    ],
)
def test_job_list_response_rejects_invalid_pagination(
    field_name: str,
    invalid_value: int,
) -> None:
    """Verify that invalid pagination metadata is rejected."""

    payload = {
        "items": [],
        "total": 0,
        "offset": 0,
        "limit": 20,
    }
    payload[field_name] = invalid_value

    with pytest.raises(ValidationError):
        JobListResponse.model_validate(payload)


def test_job_list_response_serializes_to_json() -> None:
    """Verify that paginated responses can be serialized for FastAPI clients."""

    page = JobListResponse(
        items=[],
        total=0,
        offset=0,
        limit=20,
    )

    page_json = page.model_dump(mode="json")

    assert page_json == {
        "items": [],
        "total": 0,
        "offset": 0,
        "limit": 20,
    }
