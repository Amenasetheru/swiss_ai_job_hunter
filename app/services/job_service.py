import uuid  # Import the UUID type used by Job identifiers
from collections.abc import (
    Callable,
)  # Import the callable type used by transaction helpers
from typing import TypeVar  # Import a generic type variable for ORM entities

from sqlalchemy.orm import Session  # Import the SQLAlchemy transaction session

from app.models import Job  # Import the persistent Job ORM entity
from app.repositories import (
    DuplicateJobError,
    JobRepository,
)  # Import persistence components
from app.schemas import (  # Import validated public Job contracts
    JobCreate,
    JobListResponse,
    JobRead,
    JobUpdate,
)
from app.services.exceptions import (  # Import business-level Job exceptions
    JobAlreadyExistsError,
    JobNotFoundError,
)


EntityType = TypeVar("EntityType")  # Represent any ORM entity handled by a helper


class JobService:
    """Coordinate Job business rules and transaction boundaries."""

    def __init__(
        self,
        *,
        session: Session,
        repository: JobRepository,
    ) -> None:
        """Initialize the service with one transaction and one Job repository."""

        self._session = session  # Store the request-scoped transaction owner
        self._repository = repository  # Store the Job persistence abstraction

    def create_job(self, job_data: JobCreate) -> JobRead:
        """Create and persist one validated Job."""

        job = Job(  # Convert validated public input into an ORM entity
            source=job_data.source,
            external_id=job_data.external_id,
            title=job_data.title,
            company_name=job_data.company_name,
            location=job_data.location,
            description=job_data.description,
            employment_type=job_data.employment_type,
            seniority_level=job_data.seniority_level,
            workplace_type=job_data.workplace_type,
            url=str(job_data.url),
            posted_at=job_data.posted_at,
        )

        created_job = self._execute_write(  # Execute the persistence operation safely
            operation=lambda: self._repository.create(job),
            refresh=True,
        )

        return JobRead.model_validate(
            created_job
        )  # Convert ORM output to public schema

    def get_job(self, job_id: uuid.UUID) -> JobRead:
        """Return one Job or raise a business error when it does not exist."""

        job = self._get_job_entity(job_id)

        return JobRead.model_validate(job)

    def get_job_by_url(self, url: str) -> JobRead | None:
        """Return one Job by URL or None when no record exists."""

        job = self._repository.get_by_url(url)

        if job is None:
            return None

        return JobRead.model_validate(job)

    def list_jobs(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> JobListResponse:
        """Return one validated paginated collection of Jobs."""

        jobs = self._repository.list(
            offset=offset,
            limit=limit,
        )
        total = self._repository.count()

        return JobListResponse(
            items=[JobRead.model_validate(job) for job in jobs],
            total=total,
            offset=offset,
            limit=limit,
        )

    def update_job(
        self,
        job_id: uuid.UUID,
        job_data: JobUpdate,
    ) -> JobRead:
        """Apply a validated partial update to one existing Job."""

        job = self._get_job_entity(job_id)

        update_data = job_data.model_dump(
            exclude_unset=True,
        )

        if "url" in update_data:
            update_data["url"] = str(update_data["url"])

        for field_name, value in update_data.items():
            setattr(
                job,
                field_name,
                value,
            )

        updated_job = self._execute_write(
            operation=lambda: self._repository.update(job),
            refresh=True,
        )

        return JobRead.model_validate(updated_job)

    def delete_job(self, job_id: uuid.UUID) -> None:
        """Delete one existing Job and commit the transaction."""

        job = self._get_job_entity(job_id)

        self._execute_write(
            operation=lambda: self._repository.delete(job),
            refresh=False,
        )

    def _get_job_entity(self, job_id: uuid.UUID) -> Job:
        """Return one ORM Job entity or raise a business not-found error."""

        job = self._repository.get_by_id(job_id)

        if job is None:
            raise JobNotFoundError(job_id)

        return job

    def _execute_write(
        self,
        *,
        operation: Callable[[], EntityType],
        refresh: bool,
    ) -> EntityType:
        """Execute one write operation with consistent transaction handling."""

        try:
            result = operation()  # Execute the repository operation
            self._session.commit()  # Persist the complete business transaction

            if refresh:
                self._session.refresh(result)  # Reload database-generated values

            return result
        except DuplicateJobError as error:
            self._session.rollback()  # Restore the transaction after a duplicate conflict

            raise JobAlreadyExistsError(
                constraint_name=error.constraint_name,
            ) from error
        except Exception:
            self._session.rollback()  # Restore the transaction after any unexpected failure

            raise
