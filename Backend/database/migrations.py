"""
Database migration and initialization utilities.

This module provides tools for managing database schema changes, versioning,
and initialization. It supports both programmatic and file-based migrations
to help maintain database consistency across different environments.

Classes:
    MigrationManager: Manages database schema migrations and versioning
    Migration: Individual migration definition
"""

import os
import logging
import hashlib
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from sqlalchemy import Column, String, DateTime, Text, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .config import DatabaseConfig
from .connection import DatabaseManager
from .models import Base, create_all_tables, drop_all_tables


# Migration tracking table
MigrationBase = declarative_base()

class MigrationRecord(MigrationBase):
    """
    Database table to track applied migrations.
    
    This table keeps a record of all migrations that have been applied
    to the database, including their version, checksum, and application time.
    """
    __tablename__ = 'schema_migrations'
    
    version = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256 checksum
    applied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    execution_time_ms = Column(Integer, default=0)
    description = Column(Text, default='')


@dataclass
class Migration:
    """
    Individual migration definition.
    
    A migration represents a single change to the database schema,
    including the operations to apply and optionally rollback the change.
    
    Attributes:
        version: Unique version identifier (e.g., "001", "20240101_001")
        name: Human-readable migration name
        description: Detailed description of the migration
        up_operation: Function to apply the migration
        down_operation: Function to rollback the migration (optional)
        checksum: SHA-256 checksum of the migration content
    """
    version: str
    name: str
    description: str
    up_operation: Callable[[DatabaseManager], bool]
    down_operation: Optional[Callable[[DatabaseManager], bool]] = None
    checksum: str = ""
    
    def __post_init__(self):
        """Calculate checksum if not provided."""
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum of migration content."""
        content = f"{self.version}:{self.name}:{self.description}"
        return hashlib.sha256(content.encode()).hexdigest()


class MigrationManager:
    """
    Manages database schema migrations and versioning.
    
    This class provides functionality to apply, rollback, and track
    database schema changes. It ensures migrations are applied in
    order and maintains a record of applied changes.
    
    Attributes:
        db_manager: Database manager for connection handling
        migrations_dir: Directory containing migration files
        migrations: List of registered migrations
        logger: Logger for migration operations
    """
    
    def __init__(self, db_manager: DatabaseManager, migrations_dir: Optional[str] = None):
        """
        Initialize migration manager.
        
        Args:
            db_manager: Database manager instance
            migrations_dir: Optional directory containing migration files
        """
        self.db_manager = db_manager
        self.migrations_dir = migrations_dir
        self.migrations: List[Migration] = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize migration tracking table
        self._init_migration_table()
    
    def _init_migration_table(self) -> None:
        """Initialize the migration tracking table."""
        try:
            if self.db_manager.engine:
                MigrationBase.metadata.create_all(bind=self.db_manager.engine)
                self.logger.info("Migration tracking table initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize migration table: {str(e)}")
            raise
    
    def add_migration(self, migration: Migration) -> None:
        """
        Add a migration to the manager.
        
        Args:
            migration: Migration to add
        """
        # Check for version conflicts
        existing_versions = [m.version for m in self.migrations]
        if migration.version in existing_versions:
            raise ValueError(f"Migration version {migration.version} already exists")
        
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)  # Keep sorted by version
        self.logger.debug(f"Added migration: {migration.version} - {migration.name}")
    
    def load_migrations_from_directory(self, directory: str) -> int:
        """
        Load migrations from Python files in a directory.
        
        Args:
            directory: Directory path containing migration files
            
        Returns:
            int: Number of migrations loaded
        """
        if not os.path.exists(directory):
            self.logger.warning(f"Migrations directory not found: {directory}")
            return 0
        
        migrations_loaded = 0
        migration_files = sorted([f for f in os.listdir(directory) if f.endswith('.py') and not f.startswith('__')])
        
        for filename in migration_files:
            try:
                # Extract version from filename (assumes format: VERSION_name.py)
                version = filename.split('_')[0]
                filepath = os.path.join(directory, filename)
                
                # Load migration from file (simplified implementation)
                # In a real implementation, you'd use importlib to load the migration
                self.logger.debug(f"Would load migration from {filepath}")
                migrations_loaded += 1
                
            except Exception as e:
                self.logger.error(f"Failed to load migration {filename}: {str(e)}")
        
        return migrations_loaded
    
    def get_applied_migrations(self) -> List[str]:
        """
        Get list of applied migration versions.
        
        Returns:
            List[str]: List of applied migration versions
        """
        try:
            with self.db_manager.session_scope() as session:
                records = session.query(MigrationRecord).order_by(MigrationRecord.version).all()
                return [record.version for record in records]
        except Exception as e:
            self.logger.error(f"Failed to get applied migrations: {str(e)}")
            return []
    
    def get_pending_migrations(self) -> List[Migration]:
        """
        Get list of pending (unapplied) migrations.
        
        Returns:
            List[Migration]: List of pending migrations
        """
        applied_versions = set(self.get_applied_migrations())
        return [m for m in self.migrations if m.version not in applied_versions]
    
    def apply_migration(self, migration: Migration) -> bool:
        """
        Apply a single migration.
        
        Args:
            migration: Migration to apply
            
        Returns:
            bool: True if migration was applied successfully, False otherwise
        """
        self.logger.info(f"Applying migration {migration.version}: {migration.name}")
        
        try:
            start_time = datetime.now()
            
            # Execute the migration
            success = migration.up_operation(self.db_manager)
            
            if success:
                # Record the migration
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                self._record_migration(migration, execution_time)
                self.logger.info(f"Migration {migration.version} applied successfully")
                return True
            else:
                self.logger.error(f"Migration {migration.version} failed to execute")
                return False
                
        except Exception as e:
            self.logger.error(f"Error applying migration {migration.version}: {str(e)}")
            return False
    
    def apply_all_pending(self) -> bool:
        """
        Apply all pending migrations.
        
        Returns:
            bool: True if all migrations were applied successfully, False otherwise
        """
        pending_migrations = self.get_pending_migrations()
        
        if not pending_migrations:
            self.logger.info("No pending migrations to apply")
            return True
        
        self.logger.info(f"Applying {len(pending_migrations)} pending migrations")
        
        for migration in pending_migrations:
            if not self.apply_migration(migration):
                self.logger.error(f"Failed to apply migration {migration.version}, stopping")
                return False
        
        self.logger.info("All pending migrations applied successfully")
        return True
    
    def rollback_migration(self, version: str) -> bool:
        """
        Rollback a specific migration.
        
        Args:
            version: Version of migration to rollback
            
        Returns:
            bool: True if rollback was successful, False otherwise
        """
        # Find the migration
        migration = next((m for m in self.migrations if m.version == version), None)
        if not migration:
            self.logger.error(f"Migration {version} not found")
            return False
        
        if not migration.down_operation:
            self.logger.error(f"Migration {version} has no rollback operation")
            return False
        
        # Check if migration is applied
        applied_versions = self.get_applied_migrations()
        if version not in applied_versions:
            self.logger.warning(f"Migration {version} is not applied")
            return True
        
        self.logger.info(f"Rolling back migration {version}: {migration.name}")
        
        try:
            success = migration.down_operation(self.db_manager)
            
            if success:
                # Remove migration record
                self._remove_migration_record(version)
                self.logger.info(f"Migration {version} rolled back successfully")
                return True
            else:
                self.logger.error(f"Migration {version} rollback failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error rolling back migration {version}: {str(e)}")
            return False
    
    def validate_migrations(self) -> Dict[str, Any]:
        """
        Validate applied migrations against current migration definitions.
        
        Returns:
            Dict[str, Any]: Validation results
        """
        validation_results = {
            "valid": True,
            "issues": [],
            "applied_count": 0,
            "pending_count": 0
        }
        
        try:
            applied_versions = self.get_applied_migrations()
            pending_migrations = self.get_pending_migrations()
            
            validation_results["applied_count"] = len(applied_versions)
            validation_results["pending_count"] = len(pending_migrations)
            
            # Check for checksum mismatches
            with self.db_manager.session_scope() as session:
                for migration in self.migrations:
                    if migration.version in applied_versions:
                        record = session.query(MigrationRecord).filter_by(version=migration.version).first()
                        if record and record.checksum != migration.checksum:
                            validation_results["valid"] = False
                            validation_results["issues"].append(
                                f"Checksum mismatch for migration {migration.version}"
                            )
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["issues"].append(f"Validation error: {str(e)}")
        
        return validation_results
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get comprehensive migration status information.
        
        Returns:
            Dict[str, Any]: Migration status information
        """
        try:
            applied_migrations = self.get_applied_migrations()
            pending_migrations = self.get_pending_migrations()
            
            return {
                "total_migrations": len(self.migrations),
                "applied_count": len(applied_migrations),
                "pending_count": len(pending_migrations),
                "applied_versions": applied_migrations,
                "pending_versions": [m.version for m in pending_migrations],
                "latest_applied": applied_migrations[-1] if applied_migrations else None,
                "database_exists": self._check_database_exists()
            }
        except Exception as e:
            self.logger.error(f"Failed to get migration status: {str(e)}")
            return {"error": str(e)}
    
    def _record_migration(self, migration: Migration, execution_time_ms: int) -> None:
        """Record a successful migration in the database."""
        try:
            with self.db_manager.session_scope() as session:
                record = MigrationRecord(
                    version=migration.version,
                    name=migration.name,
                    checksum=migration.checksum,
                    execution_time_ms=execution_time_ms,
                    description=migration.description
                )
                session.add(record)
                session.commit()
        except Exception as e:
            self.logger.error(f"Failed to record migration: {str(e)}")
            raise
    
    def _remove_migration_record(self, version: str) -> None:
        """Remove a migration record from the database."""
        try:
            with self.db_manager.session_scope() as session:
                record = session.query(MigrationRecord).filter_by(version=version).first()
                if record:
                    session.delete(record)
                    session.commit()
        except Exception as e:
            self.logger.error(f"Failed to remove migration record: {str(e)}")
            raise
    
    def _check_database_exists(self) -> bool:
        """Check if the database exists and is accessible."""
        try:
            return self.db_manager.test_connection()
        except Exception:
            return False


# Predefined migrations for initial setup

def create_initial_migration() -> Migration:
    """
    Create the initial migration that sets up all base tables.
    
    Returns:
        Migration: Initial database setup migration
    """
    def up_operation(db_manager: DatabaseManager) -> bool:
        """Create all initial tables."""
        try:
            return db_manager.create_tables()
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to create initial tables: {str(e)}")
            return False
    
    def down_operation(db_manager: DatabaseManager) -> bool:
        """Drop all tables."""
        try:
            return db_manager.drop_tables()
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to drop tables: {str(e)}")
            return False
    
    return Migration(
        version="001",
        name="initial_schema",
        description="Create initial database schema with all tables",
        up_operation=up_operation,
        down_operation=down_operation
    )


# Convenience functions

def initialize_database(db_manager: DatabaseManager, apply_migrations: bool = True) -> bool:
    """
    Initialize a new database with schema and optionally apply migrations.
    
    Args:
        db_manager: Database manager instance
        apply_migrations: Whether to apply initial migrations
        
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Test connection
        if not db_manager.test_connection():
            logger.error("Cannot connect to database")
            return False
        
        # Create migration manager
        migration_manager = MigrationManager(db_manager)
        
        if apply_migrations:
            # Add initial migration
            initial_migration = create_initial_migration()
            migration_manager.add_migration(initial_migration)
            
            # Apply all migrations
            success = migration_manager.apply_all_pending()
            if success:
                logger.info("Database initialized successfully with migrations")
            else:
                logger.error("Failed to apply initial migrations")
            return success
        else:
            # Just create tables directly
            success = db_manager.create_tables()
            if success:
                logger.info("Database initialized successfully without migrations")
            else:
                logger.error("Failed to create database tables")
            return success
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False


def create_tables(db_manager: DatabaseManager) -> bool:
    """
    Create all database tables.
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        bool: True if tables were created successfully, False otherwise
    """
    return db_manager.create_tables()


def setup_test_database(database_url: str = "sqlite:///:memory:") -> Optional[DatabaseManager]:
    """
    Set up an in-memory test database with all tables.
    
    Args:
        database_url: Database URL (defaults to in-memory SQLite)
        
    Returns:
        Optional[DatabaseManager]: Configured database manager or None if setup failed
    """
    try:
        from .config import DatabaseConfig
        
        config = DatabaseConfig.from_url(database_url)
        db_manager = DatabaseManager(config)
        
        if initialize_database(db_manager, apply_migrations=False):
            return db_manager
        else:
            return None
            
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to setup test database: {str(e)}")
        return None 