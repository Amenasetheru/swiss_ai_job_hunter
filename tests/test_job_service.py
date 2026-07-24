import uuid  # Import UUID generation for missing-record tests

import pytest  # Import pytest exception assertions

from app.schemas import JobCreate, JobUpdate  # Import the validated creation contract
from app.services import (  # Import the Job service and its business exceptions
    JobAlreadyExistsError,
    JobNotFoundError,
    JobService,
)


def _build_job_create(
    *,
    external_id: str,
    title: str,
    url: str,
) -> JobCreate:
    """Build one valid JobCreate schema for service tests."""

    return JobCreate.model_validate(
        {
            "source": "job_repository_test",
            "external_id": external_id,
            "title": title,
            "company_name": "Swiss Service Bank",
            "location": "Geneva, Switzerland",
            "description": "Test the Job Service business operations.",
            "employment_type": "full_time",
            "seniority_level": "senior",
            "workplace_type": "hybrid",
            "url": url,
            "posted_at": "2026-07-24T09:00:00+02:00",
        }
    )


def test_service_creates_job_and_returns_public_schema(
    job_service: JobService,
) -> None:
    """Verify creation, transaction commit, and ORM-to-schema conversion."""

    job_data = _build_job_create(
        external_id="service-create",
        title="Agentic AI Engineer",
        url="https://example.com/jobs/service-create",
    )

    created_job = job_service.create_job(job_data)

    assert created_job.id is not None
    assert created_job.title == "Agentic AI Engineer"
    assert created_job.company_name == "Swiss Service Bank"
    assert created_job.is_active is True
    assert created_job.created_at is not None


def test_service_gets_existing_job(
    job_service: JobService,
) -> None:
    """Verify retrieval of a previously created Job."""

    created_job = job_service.create_job(
        _build_job_create(
            external_id="service-get",
            title="LLM Platform Engineer",
            url="https://example.com/jobs/service-get",
        )
    )

    retrieved_job = job_service.get_job(created_job.id)

    assert retrieved_job.id == created_job.id
    assert retrieved_job.title == "LLM Platform Engineer"


def test_service_raises_when_job_does_not_exist(
    job_service: JobService,
) -> None:
    """Verify that missing records become explicit business errors."""

    missing_id = uuid.uuid4()

    with pytest.raises(JobNotFoundError) as error_info:
        job_service.get_job(missing_id)

    assert error_info.value.job_id == missing_id
    assert str(error_info.value) == (f"Job with ID '{missing_id}' was not found.")


def test_service_returns_none_for_missing_url(
    job_service: JobService,
) -> None:
    """Verify optional lookup behavior for missing URLs."""

    job = job_service.get_job_by_url("https://example.com/jobs/service-missing-url")

    assert job is None


def test_service_translates_duplicate_url(
    job_service: JobService,
) -> None:
    """Verify that persistence duplicate errors become business exceptions."""

    duplicate_url = "https://example.com/jobs/service-duplicate"

    job_service.create_job(
        _build_job_create(
            external_id="service-duplicate-first",
            title="First AI Engineer",
            url=duplicate_url,
        )
    )

    with pytest.raises(JobAlreadyExistsError) as error_info:
        job_service.create_job(
            _build_job_create(
                external_id="service-duplicate-second",
                title="Second AI Engineer",
                url=duplicate_url,
            )
        )

    assert error_info.value.constraint_name == "uq_jobs_url"
    assert str(error_info.value) == ("A job with the same URL already exists.")


def test_service_lists_jobs_with_pagination(
    job_service: JobService,
) -> None:
    """Verify business pagination and total-count response construction."""

    for index in range(3):
        job_service.create_job(
            _build_job_create(
                external_id=f"service-list-{index}",
                title=f"Service AI Engineer {index}",
                url=f"https://example.com/jobs/service-list-{index}",
            )
        )

    page = job_service.list_jobs(
        offset=0,
        limit=2,
    )

    assert len(page.items) == 2
    assert page.total == 3
    assert page.offset == 0
    assert page.limit == 2


def test_service_updates_only_provided_fields(
    job_service: JobService,
) -> None:
    """Verify that partial updates preserve every omitted Job field."""

    created_job = job_service.create_job(
        _build_job_create(
            external_id="service-update",
            title="Original Service Engineer",
            url="https://example.com/jobs/service-update",
        )
    )

    updated_job = job_service.update_job(
        created_job.id,
        JobUpdate.model_validate(
            {
                "title": "Updated Service Engineer",
                "is_active": False,
            }
        ),
    )

    assert updated_job.title == "Updated Service Engineer"
    assert updated_job.is_active is False
    assert updated_job.company_name == "Swiss Service Bank"
    assert updated_job.url == created_job.url


def test_service_allows_clearing_optional_fields(
    job_service: JobService,
) -> None:
    """Verify that nullable fields can be explicitly cleared."""

    created_job = job_service.create_job(
        _build_job_create(
            external_id="service-clear-location",
            title="Location Service Engineer",
            url="https://example.com/jobs/service-clear-location",
        )
    )

    updated_job = job_service.update_job(
        created_job.id,
        JobUpdate.model_validate(
            {
                "location": None,
                "external_id": None,
            }
        ),
    )

    assert updated_job.location is None
    assert updated_job.external_id is None


def test_service_raises_when_updating_missing_job(
    job_service: JobService,
) -> None:
    """Verify that updates of absent records become not-found errors."""

    missing_id = uuid.uuid4()

    with pytest.raises(JobNotFoundError):
        job_service.update_job(
            missing_id,
            JobUpdate.model_validate(
                {
                    "title": "Missing Job",
                }
            ),
        )


def test_service_translates_duplicate_url_during_update(
    job_service: JobService,
) -> None:
    """Verify duplicate URLs are translated during partial updates."""

    first_job = job_service.create_job(
        _build_job_create(
            external_id="service-update-duplicate-first",
            title="First Update Job",
            url="https://example.com/jobs/service-update-duplicate-first",
        )
    )
    second_job = job_service.create_job(
        _build_job_create(
            external_id="service-update-duplicate-second",
            title="Second Update Job",
            url="https://example.com/jobs/service-update-duplicate-second",
        )
    )

    with pytest.raises(JobAlreadyExistsError) as error_info:
        job_service.update_job(
            second_job.id,
            JobUpdate.model_validate(
                {
                    "url": str(first_job.url),
                }
            ),
        )

    assert error_info.value.constraint_name == "uq_jobs_url"


def test_service_deletes_existing_job(
    job_service: JobService,
) -> None:
    """Verify that an existing Job is permanently deleted."""

    created_job = job_service.create_job(
        _build_job_create(
            external_id="service-delete",
            title="Delete Service Engineer",
            url="https://example.com/jobs/service-delete",
        )
    )

    job_service.delete_job(created_job.id)

    with pytest.raises(JobNotFoundError):
        job_service.get_job(created_job.id)


def test_service_raises_when_deleting_missing_job(
    job_service: JobService,
) -> None:
    """Verify that deleting an absent Job raises a not-found error."""

    missing_id = uuid.uuid4()

    with pytest.raises(JobNotFoundError):
        job_service.delete_job(missing_id)
