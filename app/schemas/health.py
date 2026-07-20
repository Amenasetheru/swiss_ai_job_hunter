from typing import Literal  # Import Literal to restrict a value to predefined constants

from pydantic import (
    BaseModel,
    ConfigDict,
)  # Import the Pydantic model base class and configuration object


class HealthResponse(
    BaseModel
):  # Define the validated response returned by the health endpoint
    model_config = ConfigDict(  # Configure how Pydantic handles this response model
        frozen=True,  # Prevent response objects from being modified after creation
        extra="forbid",  # Reject unexpected fields that are not declared below
    )

    status: Literal["ok"]  # Restrict the health status to the exact string "ok"
    application: str  # Store the public application name
    version: str  # Store the current application version
    environment: str  # Store the active runtime environment
