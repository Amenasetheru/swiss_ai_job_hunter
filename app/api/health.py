from fastapi import (
    APIRouter,
)  # Import the FastAPI router used to group related endpoints

from app.core.settings import (
    get_settings,
)  # Import the cached application settings provider
from app.schemas.health import (
    HealthResponse,
)  # Import the validated health response schema


router = APIRouter(  # Create a router dedicated to operational health endpoints
    tags=["Health"],  # Group this endpoint under "Health" in the OpenAPI documentation
)


@router.get(  # Register an HTTP GET route on the router
    "/health",  # Define the public endpoint path
    response_model=HealthResponse,  # Validate and document the returned response structure
    status_code=200,  # Return HTTP status code 200 when the application is available
    summary="Check application health",  # Add a concise description to the API documentation
)
def health_check() -> (
    HealthResponse
):  # Define the endpoint function and its return type
    settings = (
        get_settings()
    )  # Retrieve the cached and validated application configuration

    return HealthResponse(  # Build a validated response object
        status="ok",  # Confirm that the application process is running
        application=settings.app_name,  # Return the configured application name
        version=settings.app_version,  # Return the configured application version
        environment=settings.app_environment,  # Return the configured runtime environment
    )
