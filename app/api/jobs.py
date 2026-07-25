import uuid  # Import the UUID type used by public Job route identifiers

from fastapi import (  # Import FastAPI routing, dependency, and HTTP response tools
    APIRouter,
    HTTPException,
    Query,
    Response,
    status,
)

from app.schemas import (  # Import validated public Job request and response contracts
    JobCreate,
    JobListResponse,
    JobRead,
    JobUpdate,
)
from app.services import (  # Import the business service dependency and service exceptions
    JobAlreadyExistsError,
    JobNotFoundError,
    JobServiceDependency,
)


router = APIRouter(  # Create the HTTP router dedicated to Job operations
    prefix="/jobs",  # Prefix every route in this module with /jobs
    tags=["Jobs"],  # Group these endpoints under Jobs in OpenAPI
)


@router.post(
    "",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job",
    description=("Create one validated job posting and persist it in PostgreSQL."),
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "A job with the same unique identity already exists."
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "The submitted job payload is invalid."
        },
    },
)
def create_job(
    job_data: JobCreate,
    service: JobServiceDependency,
) -> JobRead:
    """Create and return one persisted Job."""

    try:
        return service.create_job(job_data)
    except JobAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=JobListResponse,
    status_code=status.HTTP_200_OK,
    summary="List jobs",
    description="Return a paginated collection of persisted job postings.",
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "The pagination parameters are invalid."
        }
    },
)
def list_jobs(
    service: JobServiceDependency,
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of matching jobs to skip.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of jobs to return.",
    ),
) -> JobListResponse:
    """Return one paginated collection of Jobs."""

    return service.list_jobs(
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{job_id}",
    response_model=JobRead,
    status_code=status.HTTP_200_OK,
    summary="Get a job",
    description="Return one persisted job posting by its UUID identifier.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "The requested job does not exist."},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "The supplied job identifier is not a valid UUID."
        },
    },
)
def get_job(
    job_id: uuid.UUID,
    service: JobServiceDependency,
) -> JobRead:
    """Return one Job by identifier."""

    try:
        return service.get_job(job_id)
    except JobNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.patch(
    "/{job_id}",
    response_model=JobRead,
    status_code=status.HTTP_200_OK,
    summary="Update a job",
    description=("Apply a validated partial update to an existing job posting."),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "The requested job does not exist."},
        status.HTTP_409_CONFLICT: {
            "description": "The update conflicts with another existing job."
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "The identifier or update payload is invalid."
        },
    },
)
def update_job(
    job_id: uuid.UUID,
    job_data: JobUpdate,
    service: JobServiceDependency,
) -> JobRead:
    """Partially update and return one persisted Job."""

    try:
        return service.update_job(
            job_id,
            job_data,
        )
    except JobNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except JobAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job",
    description="Permanently delete one persisted job posting.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "The requested job does not exist."},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "The supplied job identifier is not a valid UUID."
        },
    },
)
def delete_job(
    job_id: uuid.UUID,
    service: JobServiceDependency,
) -> Response:
    """Delete one Job and return an empty HTTP response."""

    try:
        service.delete_job(job_id)
    except JobNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
