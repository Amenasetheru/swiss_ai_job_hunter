import uuid  # Import UUID generation and typing support
from datetime import datetime  # Import the datetime type used by temporal columns

from sqlalchemy import (  # Import SQLAlchemy column types and database constraints
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import (
    UUID,
)  # Import PostgreSQL's native UUID column type
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)  # Import SQLAlchemy 2 typed ORM mapping tools

from app.db.base import Base  # Import the shared declarative base and metadata registry


class Job(Base):  # Define the persistent ORM representation of a job opportunity
    """Represent one job opportunity collected by Swiss AI Job Hunter."""

    __tablename__ = "jobs"  # Define the PostgreSQL table name

    __table_args__ = (  # Define table-level constraints and indexes
        UniqueConstraint(  # Prevent duplicate records from the same external source
            "source",
            "external_id",
            name="uq_jobs_source_external_id",
        ),
        CheckConstraint(  # Restrict employment types to supported business values
            (
                "employment_type IS NULL OR employment_type IN "
                "('full_time', 'part_time', 'contract', 'temporary', "
                "'internship', 'freelance', 'apprenticeship')"
            ),
            name="employment_type_allowed",
        ),
        CheckConstraint(  # Restrict workplace types to supported business values
            (
                "workplace_type IS NULL OR workplace_type IN "
                "('onsite', 'hybrid', 'remote')"
            ),
            name="workplace_type_allowed",
        ),
        CheckConstraint(  # Restrict seniority levels to supported business values
            (
                "seniority_level IS NULL OR seniority_level IN "
                "('internship', 'entry', 'junior', 'mid', 'senior', "
                "'lead', 'manager', 'director', 'executive')"
            ),
            name="seniority_level_allowed",
        ),
        Index(  # Accelerate filtering by location
            "ix_jobs_location",
            "location",
        ),
        Index(  # Accelerate filtering by active status and publication date
            "ix_jobs_active_posted_at",
            "is_active",
            "posted_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(  # Define the internal primary identifier
        UUID(as_uuid=True),  # Convert PostgreSQL UUID values into Python UUID objects
        primary_key=True,  # Mark the column as the table's primary key
        default=uuid.uuid4,  # Generate a UUID automatically before insertion
    )

    source: Mapped[str] = (
        mapped_column(  # Store the platform or website that provided the job
            String(100),  # Limit the source name to one hundred characters
            nullable=False,  # Require every job to have an identified source
        )
    )

    external_id: Mapped[str | None] = (
        mapped_column(  # Store the source-specific job identifier
            String(255),  # Support identifiers from different external platforms
            nullable=True,  # Allow sources that do not expose a stable identifier
        )
    )

    title: Mapped[str] = mapped_column(  # Store the public job title
        String(255),  # Limit the title to a practical database size
        nullable=False,  # Require every opportunity to have a title
    )

    company_name: Mapped[str] = (
        mapped_column(  # Store the raw company name found in the source
            String(255),  # Support long legal and commercial company names
            nullable=False,  # Require every opportunity to identify an employer
        )
    )

    location: Mapped[str | None] = mapped_column(  # Store the raw location text
        String(255),  # Support city, canton, country, or combined location values
        nullable=True,  # Allow jobs whose source does not expose a location
    )

    description: Mapped[str] = mapped_column(  # Store the complete job description
        Text,  # Use an unrestricted text-oriented database type
        nullable=False,  # Require content for matching and LLM analysis
    )

    employment_type: Mapped[str | None] = (
        mapped_column(  # Store the normalized contract category
            String(50),  # Keep enough space for supported normalized values
            nullable=True,  # Allow classification to happen after ingestion
        )
    )

    seniority_level: Mapped[str | None] = (
        mapped_column(  # Store the normalized experience level
            String(50),  # Keep enough space for supported normalized values
            nullable=True,  # Allow the AI pipeline to infer the level later
        )
    )

    workplace_type: Mapped[str | None] = (
        mapped_column(  # Store onsite, hybrid, or remote status
            String(50),  # Keep enough space for normalized workplace values
            nullable=True,  # Allow unknown workplace arrangements
        )
    )

    url: Mapped[str] = mapped_column(  # Store the original public job URL
        Text,  # Avoid arbitrary URL length limitations
        nullable=False,  # Require traceability back to the original posting
        unique=True,  # Prevent the same source URL from being stored twice
    )

    posted_at: Mapped[datetime | None] = (
        mapped_column(  # Store the publication datetime if available
            DateTime(timezone=True),  # Preserve timezone-aware timestamps
            nullable=True,  # Allow sources that do not expose a publication date
        )
    )

    discovered_at: Mapped[datetime] = (
        mapped_column(  # Store when our platform first found the job
            DateTime(timezone=True),  # Preserve timezone information
            nullable=False,  # Require operational traceability
            server_default=func.now(),  # Let PostgreSQL generate the initial timestamp
        )
    )

    is_active: Mapped[bool] = (
        mapped_column(  # Track whether the opportunity is still open
            Boolean,  # Use PostgreSQL's boolean type
            nullable=False,  # Require an explicit lifecycle state
            server_default="true",  # Mark newly collected opportunities as active
        )
    )

    created_at: Mapped[datetime] = (
        mapped_column(  # Store when the database record was created
            DateTime(timezone=True),  # Preserve timezone-aware timestamps
            nullable=False,  # Require auditing information
            server_default=func.now(),  # Let PostgreSQL generate the creation timestamp
        )
    )

    updated_at: Mapped[datetime] = (
        mapped_column(  # Store the most recent record update time
            DateTime(timezone=True),  # Preserve timezone-aware timestamps
            nullable=False,  # Require auditing information
            server_default=func.now(),  # Generate the timestamp when the record is inserted
            onupdate=func.now(),  # Update the timestamp during ORM-managed updates
        )
    )

    def __repr__(self) -> str:  # Define a safe developer-friendly object representation
        return (  # Return only non-sensitive identifying information
            f"Job(id={self.id!r}, title={self.title!r}, "
            f"company_name={self.company_name!r}, source={self.source!r})"
        )
