import pytest  # Import pytest exception assertions and parameterized tests
from sqlalchemy.orm import Session  # Import the SQLAlchemy Session type

from app.models import Job  # Import the persistent Job ORM entity
from app.repositories import (
    DuplicateJobError,
    JobRepository,
)  # Import repository components
from tests.conftest import (
    TEST_JOB_SOURCE,
)  # Import the shared repository-test source marker


def _build_job(
    *,
    external_id: str,
    title: str,
    url: str,
) -> Job:
    """Build one valid Job object for repository tests."""

    return Job(
        source=TEST_JOB_SOURCE,
        external_id=external_id,
        title=title,
        company_name="Swiss Repository Bank",
        location="Geneva, Switzerland",
        description="Test the Job Repository persistence operations.",
        employment_type="full_time",
        seniority_level="senior",
        workplace_type="hybrid",
        url=url,
    )


def test_repository_creates_job_without_committing(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify that create flushes the entity but leaves commit control to the caller."""

    job = _build_job(
        external_id="create-job",
        title="Generative AI Repository Engineer",
        url="https://example.com/jobs/repository-create",
    )

    created_job = job_repository.create(job)

    assert created_job is job
    assert created_job.id is not None
    assert created_job.created_at is not None

    db_session.rollback()

    persisted_job = job_repository.get_by_url(
        "https://example.com/jobs/repository-create"
    )

    assert persisted_job is None


def test_repository_creates_and_persists_job_after_commit(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify that the caller can commit a Job created by the repository."""

    job = _build_job(
        external_id="committed-job",
        title="Committed LLM Engineer",
        url="https://example.com/jobs/repository-committed",
    )

    job_repository.create(job)
    db_session.commit()

    persisted_job = job_repository.get_by_id(job.id)

    assert persisted_job is not None
    assert persisted_job.title == "Committed LLM Engineer"


def test_repository_gets_job_by_id_and_url(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify primary-key and unique-URL repository lookups."""

    job = _build_job(
        external_id="lookup-job",
        title="LLM Repository Engineer",
        url="https://example.com/jobs/repository-lookup",
    )

    job_repository.create(job)
    db_session.commit()

    job_by_id = job_repository.get_by_id(job.id)
    job_by_url = job_repository.get_by_url(job.url)

    assert job_by_id is not None
    assert job_by_id.id == job.id
    assert job_by_url is not None
    assert job_by_url.url == job.url


def test_repository_returns_none_for_missing_job(
    job_repository: JobRepository,
) -> None:
    """Verify that absent records return None instead of raising an error."""

    missing_job = job_repository.get_by_url("https://example.com/jobs/does-not-exist")

    assert missing_job is None


def test_repository_lists_jobs_with_limit(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify deterministic listing and technical pagination."""

    jobs = [
        _build_job(
            external_id=f"list-job-{index}",
            title=f"AI Engineer {index}",
            url=f"https://example.com/jobs/repository-list-{index}",
        )
        for index in range(3)
    ]

    for job in jobs:
        job_repository.create(job)

    db_session.commit()

    listed_jobs = job_repository.list(
        offset=0,
        limit=2,
    )

    assert len(listed_jobs) <= 2


def test_repository_updates_job_without_committing(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify that update flushes changes while the caller controls the transaction."""

    job = _build_job(
        external_id="update-job",
        title="Original AI Engineer",
        url="https://example.com/jobs/repository-update",
    )

    job_repository.create(job)
    db_session.commit()

    job.title = "Updated AI Engineer"
    updated_job = job_repository.update(job)

    assert updated_job is job
    assert updated_job.title == "Updated AI Engineer"

    db_session.rollback()
    db_session.expire_all()

    persisted_job = job_repository.get_by_url(
        "https://example.com/jobs/repository-update"
    )

    assert persisted_job is not None
    assert persisted_job.title == "Original AI Engineer"


def test_repository_deletes_job_after_caller_commit(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify that delete removes a Job only when the caller commits."""

    job = _build_job(
        external_id="delete-job",
        title="Temporary AI Engineer",
        url="https://example.com/jobs/repository-delete",
    )

    job_repository.create(job)
    db_session.commit()

    job_id = job.id

    job_repository.delete(job)
    db_session.commit()

    deleted_job = job_repository.get_by_id(job_id)

    assert deleted_job is None


def test_repository_delete_can_be_rolled_back(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify that deletion remains reversible before the caller commits."""

    job = _build_job(
        external_id="rollback-delete-job",
        title="Rollback AI Engineer",
        url="https://example.com/jobs/repository-delete-rollback",
    )

    job_repository.create(job)
    db_session.commit()

    job_id = job.id

    job_repository.delete(job)
    db_session.rollback()
    db_session.expire_all()

    persisted_job = job_repository.get_by_id(job_id)

    assert persisted_job is not None


def test_repository_rejects_duplicate_url(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify that a duplicate URL becomes a clear repository exception."""

    duplicate_url = "https://example.com/jobs/repository-duplicate-url"

    first_job = _build_job(
        external_id="duplicate-url-first",
        title="First Duplicate URL Job",
        url=duplicate_url,
    )
    second_job = _build_job(
        external_id="duplicate-url-second",
        title="Second Duplicate URL Job",
        url=duplicate_url,
    )

    job_repository.create(first_job)
    db_session.commit()

    with pytest.raises(DuplicateJobError) as error_info:
        job_repository.create(second_job)

    assert error_info.value.constraint_name == "uq_jobs_url"
    assert str(error_info.value) == "A job with the same URL already exists."

    db_session.rollback()


def test_repository_rejects_duplicate_source_external_id(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify that duplicate external source identities are translated."""

    first_job = _build_job(
        external_id="shared-external-id",
        title="First External Identity Job",
        url="https://example.com/jobs/external-identity-first",
    )
    second_job = _build_job(
        external_id="shared-external-id",
        title="Second External Identity Job",
        url="https://example.com/jobs/external-identity-second",
    )

    job_repository.create(first_job)
    db_session.commit()

    with pytest.raises(DuplicateJobError) as error_info:
        job_repository.create(second_job)

    assert error_info.value.constraint_name == "uq_jobs_source_external_id"
    assert str(error_info.value) == (
        "A job with the same source and external ID already exists."
    )

    db_session.rollback()


@pytest.mark.parametrize(
    ("offset", "limit", "expected_message"),
    [
        (-1, 10, "offset must be greater than or equal to 0."),
        (0, 0, "limit must be greater than or equal to 1."),
        (0, 501, "limit must be less than or equal to 500."),
    ],
)
def test_repository_rejects_invalid_pagination(
    job_repository: JobRepository,
    offset: int,
    limit: int,
    expected_message: str,
) -> None:
    """Verify that invalid pagination values fail before querying PostgreSQL."""

    with pytest.raises(ValueError, match=expected_message):
        job_repository.list(
            offset=offset,
            limit=limit,
        )


def test_repository_counts_jobs(
    db_session: Session,
    job_repository: JobRepository,
) -> None:
    """Verify that count returns the complete number of persisted Jobs."""

    jobs = [
        _build_job(
            external_id=f"count-job-{index}",
            title=f"Counted AI Engineer {index}",
            url=f"https://example.com/jobs/repository-count-{index}",
        )
        for index in range(3)
    ]

    for job in jobs:
        job_repository.create(job)

    db_session.commit()

    assert job_repository.count() == 3


def test_repository_count_returns_zero_when_empty(
    job_repository: JobRepository,
) -> None:
    """Verify that count returns zero when no Job records exist."""

    assert job_repository.count() == 0
