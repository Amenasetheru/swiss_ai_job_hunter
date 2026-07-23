class RepositoryError(Exception):
    """Represent a generic failure raised by the persistence layer."""


class DuplicateJobError(RepositoryError):
    """Represent a Job that conflicts with an existing unique database record."""

    def __init__(
        self,
        *,
        constraint_name: str | None = None,
    ) -> None:
        """Initialize the duplicate error with the violated database constraint."""

        self.constraint_name = (
            constraint_name  # Store the violated unique constraint name
        )

        message = "A job with the same unique identity already exists."  # Define a safe default message

        if constraint_name == "uq_jobs_url":  # Detect a duplicate public job URL
            message = "A job with the same URL already exists."
        elif (
            constraint_name == "uq_jobs_source_external_id"
        ):  # Detect a duplicate source identifier
            message = "A job with the same source and external ID already exists."

        super().__init__(message)  # Initialize the standard Python exception message
