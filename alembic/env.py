from logging.config import fileConfig  # Import logging configuration support

from alembic import context  # Import the active Alembic migration context
from sqlalchemy import (
    engine_from_config,
    pool,
)  # Import migration engine and pooling tools

from app.core.settings import get_settings  # Import the validated project configuration
from app.db.base import Base
from app.models import Job  # noqa: F401  # Register ORM models in Base.metadata  # Import the shared ORM metadata registry


config = context.config  # Retrieve the Alembic configuration loaded from alembic.ini

if (
    config.config_file_name is not None
):  # Configure logging only when an INI file exists
    fileConfig(
        config.config_file_name
    )  # Apply the logging configuration from alembic.ini


settings = get_settings()  # Load the cached and validated project settings

config.set_main_option(  # Override Alembic's placeholder database URL
    "sqlalchemy.url",  # Select the SQLAlchemy connection setting
    settings.database_url.get_secret_value(),  # Provide the private PostgreSQL URL from .env
)

target_metadata = Base.metadata  # Expose all registered ORM table metadata to Alembic


def run_migrations_offline() -> None:
    """Run migrations without opening a live database connection."""

    database_url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations through a live PostgreSQL connection."""

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
