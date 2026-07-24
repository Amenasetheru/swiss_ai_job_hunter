from unittest.mock import MagicMock  # Import configurable test doubles

from sqlalchemy.orm import (
    Session,
)  # Import the Session type used as a mock specification

from app.repositories import JobRepository  # Import the expected Repository dependency
from app.services import JobService, get_job_service  # Import the dependency factory


def test_get_job_service_builds_expected_dependencies() -> None:
    """Verify that one Session is shared by the Service and Repository."""

    session = MagicMock(spec=Session)

    service = get_job_service(session)

    assert isinstance(service, JobService)
    assert isinstance(service._repository, JobRepository)
    assert service._session is session
    assert service._repository._session is session
