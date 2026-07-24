import uuid  # Import the UUID type used by Job identifiers


class ServiceError(Exception):
    """Represent a generic failure raised by the business service layer."""


class JobNotFoundError(ServiceError):
    """Represent a requested Job that does not exist."""

    def __init__(self, job_id: uuid.UUID) -> None:
        """Initialize the error with the missing Job identifier."""

        self.job_id = job_id  # Store the missing persistent identifier

        super().__init__(  # Initialize the standard Python exception message
            f"Job with ID '{job_id}' was not found."
        )


class JobAlreadyExistsError(ServiceError):
    """Represent a Job that conflicts with an existing business record."""

    def __init__(
        self,
        *,
        constraint_name: str | None = None,
    ) -> None:
        """Initialize the error with the violated persistence constraint."""

        self.constraint_name = constraint_name  # Preserve the duplicate category

        message = "A job with the same unique identity already exists."

        if constraint_name == "uq_jobs_url":
            message = "A job with the same URL already exists."
        elif constraint_name == "uq_jobs_source_external_id":
            message = "A job with the same source and external ID already exists."

        super().__init__(message)  # Initialize the public business error message
