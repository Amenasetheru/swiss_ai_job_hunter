from collections.abc import (
    Generator,
)  # Import the generator type used by yield-based dependencies

from sqlalchemy.orm import Session  # Import the SQLAlchemy ORM session type

from app.db.database import (
    SessionFactory,
)  # Import the configured project session factory


def get_db_session() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy session and always close it after use."""

    session = SessionFactory()  # Create one independent database session

    try:
        yield session  # Provide the open session to the current FastAPI request
    finally:
        session.close()  # Return the connection to the pool even when request processing fails
