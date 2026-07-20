from pydantic import (
    SecretStr,
)  # Import the protected string type used by database configuration

from app.core.settings import (
    Settings,
    get_settings,
)  # Import the settings model and cached provider


def test_settings_load_expected_defaults() -> (
    None
):  # Verify the stable non-secret default configuration
    settings = get_settings()  # Load the cached application settings

    assert (
        settings.app_name == "Swiss AI Job Hunter V1"
    )  # Verify the public application name
    assert settings.app_version == "0.1.0"  # Verify the initial semantic version
    assert (
        settings.app_environment == "development"
    )  # Verify the default runtime environment
    assert settings.debug is False  # Verify that debugging is disabled by default


def test_database_url_is_protected() -> (
    None
):  # Verify that the database URL is stored as sensitive data
    settings = get_settings()  # Load the cached application settings

    assert isinstance(
        settings.database_url, SecretStr
    )  # Confirm that Pydantic protects the value
    assert (
        str(settings.database_url) == "**********"
    )  # Confirm that regular display hides the secret


def test_settings_can_be_created_from_explicit_values() -> (
    None
):  # Verify deterministic settings construction
    settings = (
        Settings(  # Create isolated settings without relying on the local .env values
            database_url="postgresql+psycopg://user:password@localhost:5432/database",
        )
    )

    assert settings.database_url.get_secret_value().startswith(  # Read the secret only for this test
        "postgresql+psycopg://"
    )
