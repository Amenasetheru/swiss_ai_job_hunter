import uuid  # Import the UUID type used by Job primary identifiers

from sqlalchemy import Select, func, select  # Import typed SELECT and aggregation tools
from sqlalchemy.exc import (
    IntegrityError,
)  # Import SQLAlchemy's database integrity exception
from sqlalchemy.orm import Session  # Import the SQLAlchemy unit-of-work session

from app.models import Job  # Import the ORM entity managed by this repository
from app.repositories.exceptions import (
    DuplicateJobError,
)  # Import the translated duplicate exception


class JobRepository:
    """Provide database persistence operations for Job entities."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with one active SQLAlchemy session."""

        self._session = session

    def create(self, job: Job) -> Job:
        """Add one Job entity to the current transaction."""

        self._session.add(job)

        try:
            self._session.flush()
        except IntegrityError as error:
            self._raise_translated_integrity_error(error)

        return job

    def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        """Return one job by primary key or None when it does not exist."""

        return self._session.get(
            Job,
            job_id,
        )

    def get_by_url(self, url: str) -> Job | None:
        """Return one job by its unique source URL or None when absent."""

        statement = select(Job).where(Job.url == url)

        return self._session.scalar(statement)

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Job]:
        """Return jobs ordered from most recently discovered to oldest."""

        self._validate_pagination(
            offset=offset,
            limit=limit,
        )

        statement: Select[tuple[Job]] = (
            select(Job)
            .order_by(
                Job.discovered_at.desc(),
                Job.id.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(self._session.scalars(statement).all())

    def count(self) -> int:
        """Return the total number of persisted Job records."""

        statement = select(func.count(Job.id))

        return self._session.scalar(statement) or 0

    def update(self, job: Job) -> Job:
        """Flush pending changes made to an already managed Job entity."""

        try:
            self._session.flush()
        except IntegrityError as error:
            self._raise_translated_integrity_error(error)

        return job

    def delete(self, job: Job) -> None:
        """Mark one Job entity for deletion in the current transaction."""

        self._session.delete(job)
        self._session.flush()

    def flush(self) -> None:
        """Flush every pending repository change without committing."""

        self._session.flush()

    @classmethod
    def _raise_translated_integrity_error(
        cls,
        error: IntegrityError,
    ) -> None:
        """Translate known unique-constraint failures and preserve unknown errors."""

        constraint_name = cls._extract_constraint_name(error)

        if constraint_name in {
            "uq_jobs_url",
            "uq_jobs_source_external_id",
        }:
            raise DuplicateJobError(
                constraint_name=constraint_name,
            ) from error

        raise error

    @staticmethod
    def _extract_constraint_name(
        error: IntegrityError,
    ) -> str | None:
        """Extract a PostgreSQL constraint name from an integrity error."""

        original_error = error.orig
        diagnostic = getattr(original_error, "diag", None)

        if diagnostic is None:
            return None

        return getattr(
            diagnostic,
            "constraint_name",
            None,
        )

    @staticmethod
    def _validate_pagination(
        *,
        offset: int,
        limit: int,
    ) -> None:
        """Reject invalid technical pagination values."""

        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0.")

        if limit < 1:
            raise ValueError("limit must be greater than or equal to 1.")

        if limit > 500:
            raise ValueError("limit must be less than or equal to 500.")
