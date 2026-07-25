from fastapi import APIRouter  # Import FastAPI's modular router

from app.api.health import router as health_router  # Import the health endpoint router
from app.api.jobs import router as jobs_router  # Import the Job CRUD router


api_router = APIRouter()  # Create the root application router

api_router.include_router(health_router)  # Register infrastructure health endpoints
api_router.include_router(jobs_router)  # Register Job business endpoints
