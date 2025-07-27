"""
Database package for the competency assessment system.

This package provides database models, repositories, and connection management
using SQLAlchemy ORM. The implementation is database-agnostic, supporting
SQLite for development and easy migration to PostgreSQL, MySQL, or other
databases for production.

Main Components:
    - Models: SQLAlchemy ORM models mapped from domain entities
    - Repositories: Concrete implementations of repository interfaces
    - Configuration: Database connection and configuration management
    - Migrations: Database schema management and versioning

Quick Start:
    from Backend.database import DatabaseConfig, create_engine, UserModel
    
    # Initialize database
    config = DatabaseConfig()
    engine = create_engine(config)
    
    # Use repositories
    from Backend.database import SQLUserRepository
    user_repo = SQLUserRepository(engine)
"""

# Database models
from .models import (
    BaseModel, UserModel, ProfileModel, SkillModel, EvidenceModel,
    AssessmentModel, ConversationModel, MessageModel, MappedCompetencyModel
)

# Repository implementations
from .repositories import (
    SQLUserRepository, SQLAssessmentRepository, SQLSkillRepository
)

# Configuration and connection management
from .config import DatabaseConfig, DatabaseType
from .connection import DatabaseManager, create_engine, get_session

# Migration utilities
from .migrations import MigrationManager, initialize_database, create_tables

__version__ = "1.0.0"

# Package exports
__all__ = [
    # Models
    "BaseModel", "UserModel", "ProfileModel", "SkillModel", "EvidenceModel",
    "AssessmentModel", "ConversationModel", "MessageModel", "MappedCompetencyModel",
    
    # Repositories
    "SQLUserRepository", "SQLAssessmentRepository", "SQLSkillRepository",
    
    # Configuration
    "DatabaseConfig", "DatabaseType", "DatabaseManager", 
    "create_engine", "get_session",
    
    # Migrations
    "MigrationManager", "initialize_database", "create_tables"
]


def setup_database(database_url: str = "sqlite:///competency_assessment.db") -> DatabaseManager:
    """
    Quick setup function for database initialization.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        DatabaseManager: Configured database manager
    """
    config = DatabaseConfig.from_url(database_url)
    return DatabaseManager(config)


def create_repositories(db_manager: DatabaseManager) -> dict:
    """
    Create all repository instances with the given database manager.
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        dict: Dictionary containing all repository instances
    """
    return {
        'user': SQLUserRepository(db_manager),
        'assessment': SQLAssessmentRepository(db_manager),
        'skill': SQLSkillRepository(db_manager)
    } 