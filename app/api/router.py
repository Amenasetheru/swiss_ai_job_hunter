from fastapi import APIRouter  # Import the FastAPI router composition class

from app.api.health import (
    router as health_router,
)  # Import and rename the health-specific router


api_router = APIRouter()  # Create the root router that will aggregate every API module

api_router.include_router(
    health_router
)  # Attach the health endpoints to the root API router
