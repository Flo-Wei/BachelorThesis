"""
Example usage of the database layer for the competency assessment system.

This module demonstrates how to use the database layer components including
configuration, connection management, repositories, and migrations. It provides
practical examples for common operations and patterns.

Run this file to see the database layer in action with sample data.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the parent directory to the Python path to import Backend modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from Backend.database import (
    DatabaseConfig, DatabaseManager, setup_database, create_repositories,
    initialize_database, MigrationManager, create_initial_migration
)
from Backend.domain.models import User, Profile, Skill, Assessment
from Backend.enums import UserRole, ProficiencyLevel, AssessmentStatus


def setup_logging():
    """Set up logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def example_basic_setup():
    """Example 1: Basic database setup and connection."""
    print("\n=== Example 1: Basic Database Setup ===")
    
    # Create configuration for SQLite database
    config = DatabaseConfig.sqlite("example_competency.db", echo=True)
    print(f"Database config: {config}")
    
    # Create database manager
    db_manager = DatabaseManager(config)
    
    # Test connection
    if db_manager.test_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
        return None
    
    # Create tables
    if db_manager.create_tables():
        print("✓ Database tables created successfully")
    else:
        print("✗ Failed to create database tables")
        return None
    
    print(f"Engine info: {db_manager.get_engine_info()}")
    return db_manager


def example_migration_system(db_manager: DatabaseManager):
    """Example 2: Using the migration system."""
    print("\n=== Example 2: Migration System ===")
    
    # Create migration manager
    migration_manager = MigrationManager(db_manager)
    
    # Add initial migration
    initial_migration = create_initial_migration()
    migration_manager.add_migration(initial_migration)
    
    # Check migration status
    status = migration_manager.get_migration_status()
    print(f"Migration status: {status}")
    
    # Apply pending migrations
    if migration_manager.apply_all_pending():
        print("✓ All migrations applied successfully")
    else:
        print("✗ Migration application failed")
    
    # Validate migrations
    validation = migration_manager.validate_migrations()
    print(f"Migration validation: {validation}")


def example_repository_operations(db_manager: DatabaseManager):
    """Example 3: Repository operations with sample data."""
    print("\n=== Example 3: Repository Operations ===")
    
    # Create repositories
    repositories = create_repositories(db_manager)
    user_repo = repositories['user']
    assessment_repo = repositories['assessment']
    skill_repo = repositories['skill']
    
    # Create sample user
    print("Creating sample user...")
    sample_user = User(
        email="john.doe@example.com",
        password_hash="$2b$12$sample_hash_here",
        role=UserRole.USER
    )
    
    # Create profile for user
    sample_profile = Profile(
        user_id=sample_user.id,
        first_name="John",
        last_name="Doe",
        preferred_language="en",
        volunteering_background="Volunteer at local community center for 3 years"
    )
    sample_user.profile = sample_profile
    
    # Add some skills to profile
    skills = [
        Skill(
            name="Project Management",
            description="Planning and executing community projects",
            level=ProficiencyLevel.INTERMEDIATE,
            framework_source="ESCO",
            framework_id="S2.1.1",
            user_id=sample_user.id
        ),
        Skill(
            name="Team Leadership",
            description="Leading volunteer teams",
            level=ProficiencyLevel.ADVANCED,
            framework_source="Freiwilligenpass",
            framework_id="FP003",
            user_id=sample_user.id
        )
    ]
    sample_profile.skills = skills
    
    # Save user (should cascade to profile and skills)
    if user_repo.save(sample_user):
        print(f"✓ User saved: {sample_user.email}")
    else:
        print("✗ Failed to save user")
        return
    
    # Test user retrieval
    retrieved_user = user_repo.find_by_email("john.doe@example.com")
    if retrieved_user:
        print(f"✓ User retrieved: {retrieved_user.profile.full_name if retrieved_user.profile else 'No profile'}")
        print(f"  Skills count: {len(retrieved_user.profile.skills) if retrieved_user.profile else 0}")
    else:
        print("✗ Failed to retrieve user")
    
    # Create sample assessment
    print("\nCreating sample assessment...")
    sample_assessment = Assessment(user_id=sample_user.id)
    sample_assessment.start()
    
    if assessment_repo.save(sample_assessment):
        print(f"✓ Assessment saved: {sample_assessment.id}")
    else:
        print("✗ Failed to save assessment")
    
    # Test assessment queries
    user_assessments = assessment_repo.find_by_user_id(sample_user.id)
    print(f"✓ Found {len(user_assessments)} assessments for user")
    
    active_assessments = assessment_repo.find_by_status(AssessmentStatus.IN_PROGRESS)
    print(f"✓ Found {len(active_assessments)} active assessments")
    
    # Test skill operations
    print("\nTesting skill operations...")
    user_skills = skill_repo.find_by_user_id(sample_user.id)
    print(f"✓ Found {len(user_skills)} skills for user")
    
    esco_skills = skill_repo.find_by_framework("ESCO")
    print(f"✓ Found {len(esco_skills)} ESCO skills")
    
    # Test search functionality
    project_skills = skill_repo.search_by_name("project", exact_match=False)
    print(f"✓ Found {len(project_skills)} skills matching 'project'")


def example_session_management(db_manager: DatabaseManager):
    """Example 4: Session management patterns."""
    print("\n=== Example 4: Session Management ===")
    
    # Using session scope for transactions
    try:
        with db_manager.session_scope() as session:
            # Query within transaction
            from Backend.database.models import UserModel
            users = session.query(UserModel).all()
            print(f"✓ Found {len(users)} users in database")
            
            # Example of transaction rollback on error
            # raise Exception("Simulated error")  # Uncomment to test rollback
            
    except Exception as e:
        print(f"Transaction rolled back due to error: {e}")
    
    # Using session manager context
    from Backend.database.connection import SessionManager
    
    with SessionManager(db_manager) as session:
        from Backend.database.models import SkillModel
        skills = session.query(SkillModel).all()
        print(f"✓ Found {len(skills)} skills in database")


def example_statistics_and_analytics(db_manager: DatabaseManager):
    """Example 5: Statistics and analytics operations."""
    print("\n=== Example 5: Statistics and Analytics ===")
    
    repositories = create_repositories(db_manager)
    user_repo = repositories['user']
    assessment_repo = repositories['assessment']
    skill_repo = repositories['skill']
    
    # User statistics
    total_users = user_repo.count()
    print(f"Total users: {total_users}")
    
    # Assessment statistics
    assessment_stats = assessment_repo.get_statistics()
    print(f"Assessment statistics: {assessment_stats}")
    
    # Skill statistics
    skill_stats = skill_repo.get_skill_statistics()
    print(f"Skill statistics: {skill_stats}")
    
    # Popular skills
    popular_skills = skill_repo.find_popular_skills(limit=5)
    print(f"Popular skills: {popular_skills}")


def example_configuration_patterns():
    """Example 6: Different configuration patterns."""
    print("\n=== Example 6: Configuration Patterns ===")
    
    # SQLite configuration
    sqlite_config = DatabaseConfig.sqlite("test.db")
    print(f"SQLite config: {sqlite_config.get_connection_url()}")
    
    # PostgreSQL configuration (for production)
    postgres_config = DatabaseConfig.postgresql(
        host="localhost",
        database="competency_db",
        username="app_user",
        password="secure_password"
    )
    print(f"PostgreSQL config: {postgres_config.get_connection_url()}")
    
    # Configuration from environment variables
    import os
    os.environ['DB_TYPE'] = 'sqlite'
    os.environ['DB_DATABASE'] = 'env_test.db'
    env_config = DatabaseConfig.from_environment()
    print(f"Environment config: {env_config.get_connection_url()}")
    
    # Configuration validation
    configs = [sqlite_config, postgres_config, env_config]
    for i, config in enumerate(configs, 1):
        if config.validate():
            print(f"✓ Configuration {i} is valid")
        else:
            print(f"✗ Configuration {i} is invalid")


def cleanup_example_data():
    """Clean up example database files."""
    print("\n=== Cleanup ===")
    
    import os
    files_to_remove = ["example_competency.db", "test.db", "env_test.db"]
    
    for filename in files_to_remove:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"✓ Removed {filename}")


def main():
    """Run all examples."""
    setup_logging()
    
    print("🚀 Competency Assessment Database Layer Examples")
    print("=" * 50)
    
    try:
        # Example 1: Basic setup
        db_manager = example_basic_setup()
        if not db_manager:
            print("Failed to set up database, exiting...")
            return
        
        # Example 2: Migration system
        example_migration_system(db_manager)
        
        # Example 3: Repository operations
        example_repository_operations(db_manager)
        
        # Example 4: Session management
        example_session_management(db_manager)
        
        # Example 5: Statistics
        example_statistics_and_analytics(db_manager)
        
        # Example 6: Configuration patterns
        example_configuration_patterns()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        cleanup_example_data()


if __name__ == "__main__":
    main() 