"""Database initialization and session management."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlmodel import Session, SQLModel, create_engine, Engine
from sqlalchemy.pool import StaticPool

from .config import db_config

# Set up logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database engine, sessions, and initialization."""
    
    def __init__(self):
        self._engine: Optional[Engine] = None
    
    @property
    def engine(self) -> Engine:
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    def _create_engine(self) -> Engine:
        """Create the database engine with proper configuration."""
        logger.info(f"Creating database engine for: {db_config.database_url}")
        
        engine_kwargs = {
            "echo": db_config.echo_sql,
            "connect_args": db_config.connect_args,
        }
        
        # SQLite-specific configuration
        if db_config.is_sqlite:
            engine_kwargs.update({
                "poolclass": StaticPool,
            })
        else:
            # PostgreSQL/MySQL configuration
            engine_kwargs.update({
                "pool_size": db_config.pool_size,
                "max_overflow": db_config.max_overflow,
                "pool_timeout": db_config.pool_timeout,
            })
        
        return create_engine(db_config.database_url, **engine_kwargs)
    
    def initialize_database(self) -> None:
        """Initialize database tables."""
        try:
            logger.info("Creating database tables")
            SQLModel.metadata.create_all(self.engine)
            logger.info("Database initialization completed successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = Session(self.engine)
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_session(self) -> Session:
        """Create a new database session (caller must close it)."""
        return Session(self.engine)


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions
def init_database() -> None:
    """Initialize the database."""
    db_manager.initialize_database()


def get_engine() -> Engine:
    """Get the database engine."""
    return db_manager.engine


def get_session() -> Session:
    """Get a new database session (caller must close it)."""
    return db_manager.create_session()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup."""
    with db_manager.get_session() as session:
        yield session


# FastAPI dependency for session injection
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session injection."""
    with db_manager.get_session() as session:
        yield session
