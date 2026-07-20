from sqlalchemy import (
    Engine,
    create_engine,
)  # Import the engine type and engine factory
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)  # Import ORM sessions and their configurable factory

from app.core.settings import (
    get_settings,
)  # Import the validated and cached application settings


settings = (
    get_settings()
)  # Load the shared validated configuration once for this module

engine: Engine = create_engine(  # Create the process-wide SQLAlchemy database engine
    settings.database_url.get_secret_value(),  # Reveal the protected database URL only to SQLAlchemy
    pool_pre_ping=True,  # Validate pooled connections before returning them to the application
    pool_size=5,  # Keep up to five persistent database connections in the main pool
    max_overflow=10,  # Allow up to ten temporary connections above the main pool size
    pool_timeout=30,  # Wait up to thirty seconds when the connection pool is exhausted
    pool_recycle=1800,  # Recreate connections that have existed for thirty minutes
)

SessionFactory = sessionmaker(  # Configure a reusable factory that creates independent ORM sessions
    bind=engine,  # Connect every created session to the shared SQLAlchemy engine
    class_=Session,  # Create standard synchronous SQLAlchemy Session objects
    autoflush=False,  # Avoid automatically sending pending changes before every query
    expire_on_commit=False,  # Keep loaded object attributes available after a successful commit
)
