import uuid  # Import UUID typing and validation support

import pytest  # Import the pytest framework and exception assertions
from sqlalchemy import (
    inspect,
    select,
)  # Import schema inspection and typed SELECT construction
from sqlalchemy.exc import (
    IntegrityError,
)  # Import the database integrity exception type

from app.db.database import (
    SessionFactory,
    engine,
)  # Import the production database infrastructure
from app.models import Job  # Import the ORM model under test


def test_job_model_maps_to_expected_table() -> None:
    """Verify the central table and column contract of the Job ORM model."""

    assert Job.__tablename__ == "jobs"

    assert list(Job.__table__.columns.keys()) == [
        "id",
        "source",
        "external_id",
        "title",
        "company_name",
        "location",
        "description",
        "employment_type",
        "seniority_level",
        "workplace_type",
        "url",
        "posted_at",
        "discovered_at",
        "is_active",
        "created_at",
        "updated_at",
    ]

    assert [column.name for column in Job.__table__.primary_key.columns] == ["id"]


def test_jobs_table_contains_expected_indexes_and_constraints() -> None:
    """Verify the PostgreSQL schema generated from the Job model."""

    inspector = inspect(engine)

    index_names = {index["name"] for index in inspector.get_indexes("jobs")}
    unique_constraint_names = {
        constraint["name"] for constraint in inspector.get_unique_constraints("jobs")
    }
    check_constraint_names = {
        constraint["name"] for constraint in inspector.get_check_constraints("jobs")
    }

    assert "ix_jobs_location" in index_names
    assert "ix_jobs_active_posted_at" in index_names

    assert "uq_jobs_url" in unique_constraint_names
    assert "uq_jobs_source_external_id" in unique_constraint_names

    assert "ck_jobs_employment_type_allowed" in check_constraint_names
    assert "ck_jobs_seniority_level_allowed" in check_constraint_names
    assert "ck_jobs_workplace_type_allowed" in check_constraint_names


def test_job_can_be_persisted_with_generated_values() -> None:
    """Verify UUID generation, PostgreSQL defaults, and ORM persistence."""

    test_url = "https://example.com/jobs/test-job-model-persistence"

    with SessionFactory() as session:
        existing_job = session.scalar(select(Job).where(Job.url == test_url))

        if existing_job is not None:
            session.delete(existing_job)
            session.commit()

        job = Job(
            source="test_suite",
            external_id="job-model-persistence",
            title="LLM Engineer",
            company_name="Swiss Test Bank",
            location="Zurich, Switzerland",
            description="Build and operate production-grade LLM systems.",
            employment_type="full_time",
            seniority_level="senior",
            workplace_type="hybrid",
            url=test_url,
        )

        session.add(job)
        session.commit()
        session.refresh(job)

        assert isinstance(job.id, uuid.UUID)
        assert job.is_active is True
        assert job.created_at is not None
        assert job.updated_at is not None
        assert job.discovered_at is not None

        persisted_job = session.scalar(select(Job).where(Job.id == job.id))

        assert persisted_job is not None
        assert persisted_job.title == "LLM Engineer"
        assert persisted_job.company_name == "Swiss Test Bank"

        session.delete(job)
        session.commit()


def test_job_rejects_invalid_employment_type() -> None:
    """Verify that PostgreSQL rejects unsupported employment categories."""

    job = Job(
        source="test_suite",
        external_id="invalid-employment-type",
        title="AI Engineer",
        company_name="Swiss Constraint Bank",
        description="Validate PostgreSQL domain constraints.",
        employment_type="permanent_super_contract",
        url="https://example.com/jobs/invalid-employment-type",
    )

    with SessionFactory() as session:
        session.add(job)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()
