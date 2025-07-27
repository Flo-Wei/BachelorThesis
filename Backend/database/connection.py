"""
Database connection management for the competency assessment system.

This module provides utilities for managing SQLAlchemy database connections,
sessions, and engine configuration. It supports connection pooling, transaction
management, and provides a clean abstraction over SQLAlchemy's session handling.

Classes:
    DatabaseManager: Main database connection and session manager
    SessionManager: Context manager for database sessions
"""

import logging
from typing import Optional, Generator, Any
from contextlib import contextmanager
from sqlalchemy import create_engine as sa_create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError

from .config import DatabaseConfig, DatabaseType
from .models import Base


class DatabaseManager:
    """
    Database connection and session manager.
    
    This class manages SQLAlchemy engines, session factories, and provides
    utilities for database operations. It supports connection pooling,
    transaction management, and handles database-specific configurations.
    
    Attributes:
        config: Database configuration
        engine: SQLAlchemy engine instance
        session_factory: Session factory for creating database sessions
        scoped_session_factory: Scoped session factory for thread-safe operations
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize database manager with configuration.
        
        Args:
            config: Database configuration instance
        """
        self.config = config
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.scoped_session_factory: Optional[scoped_session] = None
        self._logger = logging.getLogger(__name__)
        
        # Initialize the engine and session factory
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the database engine and session factory."""
        try:
            self.engine = self._create_engine()
            self.session_factory = sessionmaker(bind=self.engine)
            self.scoped_session_factory = scoped_session(self.session_factory)
            self._logger.info(f"Database manager initialized for {self.config.database_type.value}")
        except Exception as e:
            self._logger.error(f"Failed to initialize database manager: {str(e)}")
            raise
    
    def _create_engine(self) -> Engine:
        """
        Create SQLAlchemy engine with appropriate configuration.
        
        Returns:
            Engine: Configured SQLAlchemy engine
        """
        url = self.config.get_connection_url()
        engine_options = self.config.get_engine_options()
        
        # Special handling for SQLite
        if self.config.database_type == DatabaseType.SQLITE:
            # For SQLite, we need special configuration for threading
            engine_options.update({
                'poolclass': StaticPool,
                'connect_args': {
                    'check_same_thread': False,  # Allow SQLite to be used in multiple threads
                    'timeout': 20  # Set connection timeout
                }
            })
        
        self._logger.debug(f"Creating engine with URL: {url}")
        return sa_create_engine(url, **engine_options)
    
    def create_session(self) -> Session:
        """
        Create a new database session.
        
        Returns:
            Session: New SQLAlchemy session instance
        """
        if not self.session_factory:
            raise RuntimeError("Database manager not initialized")
        
        return self.session_factory()
    
    def get_scoped_session(self) -> scoped_session:
        """
        Get a scoped session (thread-safe).
        
        Returns:
            scoped_session: Thread-safe scoped session
        """
        if not self.scoped_session_factory:
            raise RuntimeError("Database manager not initialized")
        
        return self.scoped_session_factory
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.
        
        This context manager automatically handles session creation, transaction
        management, and cleanup. If an exception occurs, the transaction is
        rolled back; otherwise, it's committed.
        
        Yields:
            Session: Database session within transaction scope
        """
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_tables(self) -> bool:
        """
        Create all database tables.
        
        Returns:
            bool: True if tables were created successfully, False otherwise
        """
        try:
            if not self.engine:
                raise RuntimeError("Database engine not initialized")
            
            Base.metadata.create_all(bind=self.engine)
            self._logger.info("Database tables created successfully")
            return True
        except Exception as e:
            self._logger.error(f"Failed to create tables: {str(e)}")
            return False
    
    def drop_tables(self) -> bool:
        """
        Drop all database tables.
        
        Returns:
            bool: True if tables were dropped successfully, False otherwise
        """
        try:
            if not self.engine:
                raise RuntimeError("Database engine not initialized")
            
            Base.metadata.drop_all(bind=self.engine)
            self._logger.info("Database tables dropped successfully")
            return True
        except Exception as e:
            self._logger.error(f"Failed to drop tables: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            if not self.engine:
                return False
            
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            
            self._logger.info("Database connection test successful")
            return True
        except Exception as e:
            self._logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    def get_engine_info(self) -> dict:
        """
        Get information about the database engine.
        
        Returns:
            dict: Engine information including URL, driver, and pool status
        """
        if not self.engine:
            return {"status": "not_initialized"}
        
        info = {
            "url": str(self.engine.url),
            "dialect": self.engine.dialect.name,
            "driver": self.engine.dialect.driver,
            "pool_size": getattr(self.engine.pool, 'size', lambda: None)(),
            "checked_out": getattr(self.engine.pool, 'checkedout', lambda: None)(),
            "overflow": getattr(self.engine.pool, 'overflow', lambda: None)(),
            "checked_in": getattr(self.engine.pool, 'checkedin', lambda: None)()
        }
        
        return info
    
    def close(self) -> None:
        """Close the database connection and clean up resources."""
        try:
            if self.scoped_session_factory:
                self.scoped_session_factory.remove()
            
            if self.engine:
                self.engine.dispose()
            
            self._logger.info("Database manager closed successfully")
        except Exception as e:
            self._logger.error(f"Error closing database manager: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()


class SessionManager:
    """
    Context manager for database sessions with automatic cleanup.
    
    This class provides a convenient way to manage database sessions
    with automatic transaction handling and resource cleanup.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize session manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.session: Optional[Session] = None
    
    def __enter__(self) -> Session:
        """
        Enter context manager and create session.
        
        Returns:
            Session: Database session
        """
        self.session = self.db_manager.create_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager and handle cleanup.
        
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.session:
            try:
                if exc_type is None:
                    # No exception occurred, commit the transaction
                    self.session.commit()
                else:
                    # Exception occurred, rollback the transaction
                    self.session.rollback()
            except Exception as e:
                logging.getLogger(__name__).error(f"Error during session cleanup: {str(e)}")
                self.session.rollback()
            finally:
                self.session.close()


# Convenience functions for common operations

def create_engine(config: DatabaseConfig) -> Engine:
    """
    Create a SQLAlchemy engine from configuration.
    
    Args:
        config: Database configuration
        
    Returns:
        Engine: Configured SQLAlchemy engine
    """
    manager = DatabaseManager(config)
    return manager.engine


def get_session(db_manager: DatabaseManager) -> SessionManager:
    """
    Get a session manager for the given database manager.
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        SessionManager: Session manager context
    """
    return SessionManager(db_manager)


@contextmanager
def transaction_scope(db_manager: DatabaseManager) -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.
    
    This is a convenience function that wraps DatabaseManager.session_scope().
    
    Args:
        db_manager: Database manager instance
        
    Yields:
        Session: Database session within transaction scope
    """
    with db_manager.session_scope() as session:
        yield session


def create_database_manager(
    database_url: str = "sqlite:///competency_assessment.db",
    echo: bool = False
) -> DatabaseManager:
    """
    Create a database manager with simple configuration.
    
    Args:
        database_url: Database connection URL
        echo: Whether to echo SQL statements
        
    Returns:
        DatabaseManager: Configured database manager
    """
    config = DatabaseConfig.from_url(database_url, echo=echo)
    return DatabaseManager(config)


class ConnectionPool:
    """
    Connection pool manager for handling multiple database connections.
    
    This class is useful for applications that need to manage multiple
    databases or connection configurations.
    """
    
    def __init__(self):
        """Initialize connection pool."""
        self._managers: dict[str, DatabaseManager] = {}
        self._logger = logging.getLogger(__name__)
    
    def add_manager(self, name: str, config: DatabaseConfig) -> DatabaseManager:
        """
        Add a database manager to the pool.
        
        Args:
            name: Unique name for the manager
            config: Database configuration
            
        Returns:
            DatabaseManager: Created database manager
        """
        if name in self._managers:
            raise ValueError(f"Manager with name '{name}' already exists")
        
        manager = DatabaseManager(config)
        self._managers[name] = manager
        self._logger.info(f"Added database manager '{name}' to pool")
        return manager
    
    def get_manager(self, name: str) -> Optional[DatabaseManager]:
        """
        Get a database manager by name.
        
        Args:
            name: Manager name
            
        Returns:
            DatabaseManager: Manager instance or None if not found
        """
        return self._managers.get(name)
    
    def remove_manager(self, name: str) -> bool:
        """
        Remove a database manager from the pool.
        
        Args:
            name: Manager name
            
        Returns:
            bool: True if manager was removed, False if not found
        """
        manager = self._managers.pop(name, None)
        if manager:
            manager.close()
            self._logger.info(f"Removed database manager '{name}' from pool")
            return True
        return False
    
    def close_all(self) -> None:
        """Close all database managers in the pool."""
        for name, manager in self._managers.items():
            try:
                manager.close()
                self._logger.info(f"Closed database manager '{name}'")
            except Exception as e:
                self._logger.error(f"Error closing manager '{name}': {str(e)}")
        
        self._managers.clear()
    
    def get_manager_names(self) -> list[str]:
        """Get list of all manager names in the pool."""
        return list(self._managers.keys())
    
    def __len__(self) -> int:
        """Get number of managers in the pool."""
        return len(self._managers)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close_all() 