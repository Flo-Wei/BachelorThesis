# Database System

This directory contains the improved database initialization and management system for the Bachelor Thesis chatbot application.

## Overview

The database system provides:

- **Centralized Configuration**: Environment-based configuration management
- **Proper Session Management**: Context managers for automatic session cleanup
- **Error Handling**: Comprehensive error handling and logging
- **Simple API**: Clean and straightforward database operations

## Architecture

```
Backend/database/
├── __init__.py           # Package initialization
├── config.py            # Database configuration management
├── init.py              # Core database initialization and session management
├── utils.py             # Database utility functions
├── example_usage.py     # Usage examples
├── README.md            # This file
└── models/              # SQLModel database models
    ├── __init__.py
    ├── users.py         # User model
    ├── messages.py      # Chat session and message models
    └── skills.py        # ESCO skill models
```

## Key Components

### 1. Configuration (`config.py`)

Handles database configuration with environment variable support:

```python
from Backend.database.config import db_config

print(db_config.database_url)  # Get configured database URL
print(db_config.is_sqlite)     # Check if using SQLite
```

### 2. Database Manager (`init.py`)

Core database management functionality:

```python
from Backend.database.init import init_database, get_db_session

# Initialize database
init_database()

# Use session with automatic cleanup
with get_db_session() as session:
    # Database operations here
    pass
```

### 3. Utility Functions (`utils.py`)

High-level database operations:

```python
from Backend.database.utils import (
    create_user_with_session,
    create_chat_session_with_session,
    add_message_with_session
)

# Create user (session managed automatically)
user = create_user_with_session("username", "email@example.com")

# Create chat session
chat_session = create_chat_session_with_session(user, "Session Name")

# Add message
message = add_message_with_session(chat_session, "Hello!", MessageType.USER)
```

## Environment Configuration

Set environment variables to configure the database:

```bash
# SQLite (default)
export DATABASE_URL="sqlite:///./Database/app_database.db"

# PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"

# Additional settings
export DB_ECHO=true           # Show SQL queries in logs
export DB_POOL_SIZE=10        # Connection pool size
export DB_MAX_OVERFLOW=20     # Maximum overflow connections
export DB_POOL_TIMEOUT=30     # Connection timeout (seconds)
```

## Usage Examples

### Basic Usage

```python
from Backend.database.init import init_database
from Backend.database.utils import create_user_with_session

# Initialize database
init_database()

# Create a user
user = create_user_with_session("john_doe", "john@example.com")
print(f"Created user: {user.username}")
```

### Manual Session Management

```python
from Backend.database.init import get_db_session
from Backend.database.models.users import User

# Use context manager for automatic cleanup
with get_db_session() as session:
    users = session.query(User).all()
    print(f"Total users: {len(users)}")
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from Backend.database.init import get_db

app = FastAPI()

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```



## Running Examples

```bash
# Run the example
uv run python Backend/database/example_usage.py

# Start the API server
uv run uvicorn Backend.api:app --reload
```



## Error Handling

The system includes comprehensive error handling:

```python
from Backend.database.utils import create_user_with_session
import logging

try:
    user = create_user_with_session("username", "email@example.com")
except Exception as e:
    logging.error(f"Failed to create user: {e}")
    # Handle error appropriately
```



## Best Practices

1. **Always use context managers** for session management
2. **Initialize the database** at application startup
3. **Handle exceptions** appropriately
4. **Use the utility functions** for common operations
5. **Use environment variables** for configuration

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root
2. **Database Lock (SQLite)**: Use context managers to ensure sessions are closed
3. **Connection Errors**: Check DATABASE_URL environment variable
4. **Permission Errors**: Ensure write permissions for SQLite database directory

### Debug Mode

Enable SQL query logging:

```bash
export DB_ECHO=true
```

Or in code:

```python
from Backend.database.config import db_config
db_config.echo_sql = True
```

## Future Enhancements

- Async database support
- Connection pooling optimization
