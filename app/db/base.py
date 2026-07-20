from sqlalchemy import (
    MetaData,
)  # Import the registry that stores database table definitions
from sqlalchemy.orm import (
    DeclarativeBase,
)  # Import the modern SQLAlchemy 2 ORM base class


# Define deterministic names for database constraints and indexes
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):  # Define the shared parent class for every ORM model
    metadata = MetaData(  # Create the central registry of project table definitions
        naming_convention=NAMING_CONVENTION,  # Apply predictable names to constraints and indexes
    )
