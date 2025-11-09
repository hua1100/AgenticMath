"""
Custom SQLAlchemy types for cross-database compatibility.
"""

from sqlalchemy import String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
import uuid


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses String(36).
    This allows the same models to work with both PostgreSQL (production)
    and SQLite (testing).

    Example:
        >>> class MyModel(Base):
        ...     id = Column(GUID(), primary_key=True, default=uuid4)
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Return the appropriate type for the current database dialect."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        """Process value before binding to database."""
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            # PostgreSQL can handle UUID objects directly
            return value
        else:
            # SQLite needs string representation
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        """Process value after retrieving from database."""
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        # Convert string back to UUID object
        return uuid.UUID(value)
