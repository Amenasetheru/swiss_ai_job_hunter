from functools import (
    lru_cache,
)  # Import a cache decorator to reuse one validated settings instance

from pydantic import (
    SecretStr,
)  # Import a protected string type for sensitive configuration values
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)  # Import Pydantic settings management tools


class Settings(BaseSettings):  # Define the complete validated application configuration
    model_config = SettingsConfigDict(  # Configure how environment variables are loaded
        env_file=".env",  # Load local environment variables from the private .env file
        env_file_encoding="utf-8",  # Decode the environment file using UTF-8
        case_sensitive=False,  # Accept environment variable names regardless of letter case
        extra="ignore",  # Ignore variables that belong to future features
    )

    app_name: str = "Swiss AI Job Hunter V1"  # Define the public application name
    app_version: str = "0.1.0"  # Define the current semantic application version
    app_environment: str = "development"  # Define the active runtime environment
    debug: bool = False  # Disable framework debugging by default

    database_url: SecretStr  # Require the private PostgreSQL connection URL


@lru_cache(
    maxsize=1
)  # Cache exactly one Settings instance for the current Python process
def get_settings() -> (
    Settings
):  # Build and return the validated application configuration
    return (
        Settings()
    )  # Read environment variables, validate them, and create the settings object
