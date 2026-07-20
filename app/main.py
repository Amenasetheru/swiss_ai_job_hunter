from fastapi import FastAPI  # Import the main FastAPI application class

from app.api.router import api_router  # Import the root API router
from app.core.settings import get_settings  # Import the cached settings provider


def create_application() -> (
    FastAPI
):  # Define an application factory for production and testing
    settings = get_settings()  # Load and validate the application configuration

    application = FastAPI(  # Create the FastAPI application instance
        title=settings.app_name,  # Set the title displayed in OpenAPI documentation
        version=settings.app_version,  # Set the public API version
        debug=settings.debug,  # Configure framework debugging from validated settings
        description=(  # Define a readable description for API consumers
            "Enterprise-grade AI platform for intelligent job searching "
            "and application strategy in Switzerland."
        ),
    )

    application.include_router(
        api_router
    )  # Register every endpoint from the root API router

    return application  # Return the fully configured FastAPI instance


app = create_application()  # Create the application object used by the ASGI server
