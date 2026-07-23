from collections.abc import (
    Generator,
)  # Import the generator type used by yield-based fixtures

import pytest  # Import the pytest testing framework
from sqlalchemy import delete  # Import a set-based SQL DELETE statement
from sqlalchemy.orm import Session  # Import the SQLAlchemy ORM session type

from app.db.database import SessionFactory  # Import the production session factory
from app.models import Job  # Import the Job ORM entity
from app.repositories import JobRepository  # Import the repository under test
from tests.constants import TEST_JOB_SOURCE  # Import the shared test source marker


def _remove_repository_test_jobs(session: Session) -> None:
    """Delete every temporary Job row created by repository tests."""

    session.execute(  # Execute one efficient SQL DELETE statement
        delete(Job).where(  # Delete only rows created by repository tests
            Job.source == TEST_JOB_SOURCE
        )
    )
    session.commit()  # Persist the cleanup operation


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide one database session and always close it after the test."""

    with SessionFactory() as session:  # Create one isolated SQLAlchemy session
        _remove_repository_test_jobs(
            session
        )  # Start from a clean repository-test state

        try:
            yield session  # Provide the open session to the requesting test
        finally:
            session.rollback()  # Cancel any unfinished transaction
            _remove_repository_test_jobs(session)  # Remove every temporary test record


@pytest.fixture
def job_repository(db_session: Session) -> JobRepository:
    """Provide a JobRepository connected to the current test session."""

    return JobRepository(db_session)  # Inject the test session into the repository
