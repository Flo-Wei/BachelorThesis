# Import SQLAlchemy components for database connection and session management
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from models import Base
import os

# Database URL - this tells SQLAlchemy how to connect to your database
# SQLite is used here for simplicity (no server setup required)
# The database file will be created as "user_management.db" in the current directory
DATABASE_URL = "sqlite:///./Database/user_management.db"

# For other databases, you would use URLs like:
# PostgreSQL: "postgresql://username:password@localhost/database_name"
# MySQL: "mysql+pymysql://username:password@localhost/database_name"
# SQL Server: "mssql+pyodbc://username:password@server/database_name"

# Create the database engine
# The engine is the core interface to the database - it manages connections and executes SQL
engine = create_engine(
    DATABASE_URL,
    # SQLite-specific configuration
    connect_args={"check_same_thread": False},  # Allows multiple threads to use the same connection
    poolclass=StaticPool,  # Uses a single connection for the entire application
    echo=True  # Set to True to see all SQL queries in the console (useful for debugging)
    # Set echo=False in production to disable SQL logging for better performance
)

# Create a session factory
# A session is like a "workspace" where you can make changes to database objects
# SessionLocal is a factory that creates new sessions
SessionLocal = sessionmaker(
    autocommit=False,  # Don't automatically commit changes (we'll do it manually)
    autoflush=False,   # Don't automatically flush changes to the database
    bind=engine        # Use our engine for database connections
)

def create_tables():
    """
    Create all tables defined in our models
    
    This function looks at all classes that inherit from Base (like our User class)
    and creates the corresponding database tables if they don't exist.
    
    This is equivalent to running CREATE TABLE statements in SQL.
    """
    # Base.metadata contains information about all our models
    # create_all() generates and executes the CREATE TABLE statements
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """
    Get a database session
    
    This is a generator function that creates a new database session.
    It's designed to be used with dependency injection (like in FastAPI).
    
    The 'yield' keyword means this function can be used as a context manager.
    """
    # Create a new session
    db = SessionLocal()
    try:
        # Return the session to the caller
        yield db
    finally:
        # Always close the session when done, even if an error occurs
        # This is important to prevent memory leaks and connection pool exhaustion
        db.close()

def init_db():
    """
    Initialize the database with all tables
    
    This is a convenience function that creates all tables and prints a success message.
    Call this function once when setting up your application.
    """
    create_tables()
    print("Database initialized successfully!")
