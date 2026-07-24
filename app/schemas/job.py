import uuid  # Import the UUID type used by public Job identifiers
from datetime import datetime  # Import the datetime type used by temporal fields
from typing import Literal  # Import Literal to restrict fields to predefined values

from pydantic import (  # Import Pydantic validation and schema configuration tools
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


EmploymentType = Literal[  # Define the supported normalized employment categories
    "full_time",
    "part_time",
    "contract",
    "temporary",
    "internship",
    "freelance",
    "apprenticeship",
]

SeniorityLevel = Literal[  # Define the supported normalized experience levels
    "internship",
    "entry",
    "junior",
    "mid",
    "senior",
    "lead",
    "manager",
    "director",
    "executive",
]

WorkplaceType = Literal[  # Define the supported workplace arrangements
    "onsite",
    "hybrid",
    "remote",
]


class JobBase(BaseModel):
    """Define the shared validated fields of a Job."""

    model_config = ConfigDict(  # Configure strict public data validation
        extra="forbid",  # Reject fields that are not explicitly declared
        str_strip_whitespace=True,  # Remove surrounding spaces from string inputs
    )

    source: str = Field(  # Store the platform or website that provided the job
        min_length=1,  # Reject empty source names
        max_length=100,  # Match the database column size
    )
    external_id: str | None = Field(  # Store the source-specific job identifier
        default=None,  # Allow sources without a stable external identifier
        min_length=1,  # Reject empty identifiers when a value is provided
        max_length=255,  # Match the database column size
    )
    title: str = Field(  # Store the public job title
        min_length=1,  # Reject empty titles
        max_length=255,  # Match the database column size
    )
    company_name: str = Field(  # Store the employer name collected from the source
        min_length=1,  # Reject empty company names
        max_length=255,  # Match the database column size
    )
    location: str | None = Field(  # Store the raw job location
        default=None,  # Allow jobs whose source does not expose a location
        min_length=1,  # Reject empty location strings when provided
        max_length=255,  # Match the database column size
    )
    description: str = Field(  # Store the full job description
        min_length=1,  # Require content for search, matching, and AI analysis
    )
    employment_type: EmploymentType | None = None  # Store the normalized contract type
    seniority_level: SeniorityLevel | None = (
        None  # Store the normalized experience level
    )
    workplace_type: WorkplaceType | None = (
        None  # Store the normalized workplace arrangement
    )
    url: HttpUrl  # Validate that the original source URL is structurally valid
    posted_at: datetime | None = None  # Store the publication datetime when available

    @field_validator(  # Register a custom validator for required text fields
        "source",
        "title",
        "company_name",
        "description",
    )
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        """Reject values that contain only whitespace."""

        if not value.strip():  # Detect values such as spaces or line breaks only
            raise ValueError("The value must not be blank.")

        return value  # Return the validated and normalized string

    @field_validator("posted_at")  # Register a validator for publication datetimes
    @classmethod
    def require_timezone_for_posted_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require explicit timezone information when posted_at is provided."""

        if value is not None and value.utcoffset() is None:
            raise ValueError("posted_at must include timezone information.")

        return value


class JobCreate(JobBase):
    """Define the validated data required to create a Job."""

    model_config = ConfigDict(  # Configure creation validation and OpenAPI documentation
        extra="forbid",  # Reject fields that are not explicitly declared
        str_strip_whitespace=True,  # Remove surrounding spaces from string inputs
        json_schema_extra={  # Provide one realistic request example for API documentation
            "example": {
                "source": "company_careers",
                "external_id": "ai-engineer-123",
                "title": "Generative AI Engineer",
                "company_name": "Swiss AI Bank",
                "location": "Geneva, Switzerland",
                "description": "Build secure production-grade LLM and RAG systems.",
                "employment_type": "full_time",
                "seniority_level": "senior",
                "workplace_type": "hybrid",
                "url": "https://example.com/jobs/ai-engineer-123",
                "posted_at": "2026-07-24T09:00:00+02:00",
            }
        },
    )


class JobUpdate(BaseModel):
    """Define a partial set of fields used to update an existing Job."""

    model_config = ConfigDict(  # Configure strict partial-update validation
        extra="forbid",  # Reject unknown update fields
        str_strip_whitespace=True,  # Remove surrounding spaces from string inputs
        json_schema_extra={  # Provide one realistic partial-update example
            "example": {
                "title": "Senior Generative AI Engineer",
                "workplace_type": "hybrid",
                "is_active": True,
            }
        },
    )

    source: str | None = Field(default=None, min_length=1, max_length=100)
    external_id: str | None = Field(default=None, min_length=1, max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    employment_type: EmploymentType | None = None
    seniority_level: SeniorityLevel | None = None
    workplace_type: WorkplaceType | None = None
    url: HttpUrl | None = None
    posted_at: datetime | None = None
    is_active: bool | None = None

    @field_validator(  # Register validation for optional text fields
        "source",
        "title",
        "company_name",
        "description",
    )
    @classmethod
    def reject_blank_optional_strings(
        cls,
        value: str | None,
    ) -> str | None:
        """Reject blank strings while allowing omitted values."""

        if value is not None and not value.strip():
            raise ValueError("The value must not be blank.")

        return value

    @field_validator("posted_at")  # Validate update publication datetimes
    @classmethod
    def require_timezone_for_updated_posted_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """Require timezone information when posted_at is updated."""

        if value is not None and value.utcoffset() is None:
            raise ValueError("posted_at must include timezone information.")

        return value

    @model_validator(mode="after")  # Validate relationships between update fields
    def validate_partial_update(self) -> "JobUpdate":
        """Reject empty updates and null values for required persistent fields."""

        if not self.model_fields_set:  # Detect a payload that contains no fields
            raise ValueError("At least one field must be provided for an update.")

        required_persistent_fields = {  # Define fields that cannot be cleared in PostgreSQL
            "source",
            "title",
            "company_name",
            "description",
            "url",
        }

        null_required_fields = sorted(  # Collect required fields explicitly set to null
            field_name
            for field_name in required_persistent_fields
            if field_name in self.model_fields_set and getattr(self, field_name) is None
        )

        if null_required_fields:
            joined_fields = ", ".join(null_required_fields)

            raise ValueError(f"Required job fields cannot be null: {joined_fields}.")

        return self


class JobRead(JobBase):
    """Define the public representation returned for a persisted Job."""

    model_config = ConfigDict(  # Configure ORM conversion and response documentation
        from_attributes=True,  # Read values directly from SQLAlchemy object attributes
        extra="forbid",  # Reject unexpected fields during direct validation
        str_strip_whitespace=True,  # Normalize surrounding whitespace
        json_schema_extra={  # Provide one realistic API response example
            "example": {
                "id": "96a4a260-832e-4fff-af5b-3f25ec77da93",
                "source": "company_careers",
                "external_id": "ai-engineer-123",
                "title": "Generative AI Engineer",
                "company_name": "Swiss AI Bank",
                "location": "Geneva, Switzerland",
                "description": "Build secure production-grade LLM and RAG systems.",
                "employment_type": "full_time",
                "seniority_level": "senior",
                "workplace_type": "hybrid",
                "url": "https://example.com/jobs/ai-engineer-123",
                "posted_at": "2026-07-24T09:00:00+02:00",
                "discovered_at": "2026-07-24T07:10:00Z",
                "is_active": True,
                "created_at": "2026-07-24T07:10:00Z",
                "updated_at": "2026-07-24T07:10:00Z",
            }
        },
    )

    id: uuid.UUID  # Expose the generated persistent identifier
    discovered_at: datetime  # Expose when the platform first discovered the job
    is_active: bool  # Expose whether the opportunity remains active
    created_at: datetime  # Expose when the database row was created
    updated_at: datetime  # Expose when the database row was last updated


class JobListResponse(BaseModel):
    """Define the paginated public response returned for Job collections."""

    model_config = ConfigDict(  # Configure strict pagination response validation
        extra="forbid",  # Reject unexpected pagination response fields
        json_schema_extra={  # Provide one realistic paginated response example
            "example": {
                "items": [
                    {
                        "id": "96a4a260-832e-4fff-af5b-3f25ec77da93",
                        "source": "company_careers",
                        "external_id": "ai-engineer-123",
                        "title": "Generative AI Engineer",
                        "company_name": "Swiss AI Bank",
                        "location": "Geneva, Switzerland",
                        "description": "Build secure production-grade LLM systems.",
                        "employment_type": "full_time",
                        "seniority_level": "senior",
                        "workplace_type": "hybrid",
                        "url": "https://example.com/jobs/ai-engineer-123",
                        "posted_at": "2026-07-24T09:00:00+02:00",
                        "discovered_at": "2026-07-24T07:10:00Z",
                        "is_active": True,
                        "created_at": "2026-07-24T07:10:00Z",
                        "updated_at": "2026-07-24T07:10:00Z",
                    }
                ],
                "total": 1,
                "offset": 0,
                "limit": 20,
            }
        },
    )

    items: list[JobRead]  # Store the validated Job records returned on the current page
    total: int = Field(ge=0)  # Store the total number of matching Job records
    offset: int = Field(ge=0)  # Store the number of matching rows skipped
    limit: int = Field(ge=1, le=500)  # Store the validated page-size limit
