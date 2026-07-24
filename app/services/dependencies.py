from typing import Annotated  # Import metadata-based FastAPI type annotations

from fastapi import Depends  # Import FastAPI dependency injection
from sqlalchemy.orm import Session  # Import the SQLAlchemy session type

from app.db.dependencies import (
    get_db_session,
)  # Import the request-scoped database session
from app.repositories import JobRepository  # Import the Job persistence abstraction
from app.services.job_service import JobService  # Import the Job business service


def get_job_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> JobService:
    """Build one request-scoped JobService with its repository dependencies."""

    repository = JobRepository(session)  # Connect the Repository to the request session

    return JobService(  # Build the business service with the same transaction
        session=session,
        repository=repository,
    )


JobServiceDependency = Annotated[  # Define a reusable FastAPI dependency annotation
    JobService,
    Depends(get_job_service),
]
