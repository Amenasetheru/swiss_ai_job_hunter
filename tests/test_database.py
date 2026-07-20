from sqlalchemy import text  # Import SQLAlchemy's explicit textual SQL wrapper
from sqlalchemy.orm import Session  # Import the ORM session type

from app.db.base import (
    Base,
    NAMING_CONVENTION,
)  # Import the shared ORM base and naming rules
from app.db.database import (
    SessionFactory,
    engine,
)  # Import the production engine and session factory


def test_engine_uses_postgresql_dialect() -> None:
    """Verify that the project engine targets PostgreSQL."""

    assert engine.dialect.name == "postgresql"


def test_base_uses_expected_naming_convention() -> None:
    """Verify that ORM metadata uses deterministic database object names."""

    assert Base.metadata.naming_convention == NAMING_CONVENTION
    assert Base.metadata.naming_convention["pk"] == "pk_%(table_name)s"
    assert Base.metadata.naming_convention["fk"] == (
        "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    )


def test_session_factory_creates_sqlalchemy_session() -> None:
    """Verify that the configured factory creates ORM Session instances."""

    session = SessionFactory()

    try:
        assert isinstance(session, Session)
        assert session.bind is engine
    finally:
        session.close()


def test_database_session_reaches_project_database() -> None:
    """Verify the complete SQLAlchemy connection to the Docker PostgreSQL database."""

    with SessionFactory() as session:
        database_user = session.scalar(text("SELECT current_user"))
        database_name = session.scalar(text("SELECT current_database()"))

    assert database_user == "swiss_ai_job_hunter_user"
    assert database_name == "swiss_ai_job_hunter"
