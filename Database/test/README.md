# User Management Database System

A simple user management system built with SQLAlchemy for learning purposes. This system provides basic CRUD operations for user management with authentication capabilities.

## Features

- **User Registration**: Create new users with validation
- **Authentication**: Login with username and password
- **User Management**: Update, delete, and search users
- **Password Management**: Secure password hashing and change functionality
- **Soft Delete**: Users are deactivated rather than permanently deleted
- **Search**: Search users by username, email, or name
- **Admin Support**: Admin user flag for role-based access

## Database Schema

### User Table
- `id`: Primary key (auto-increment)
- `username`: Unique username (indexed)
- `email`: Unique email address (indexed)
- `password_hash`: Hashed password (SHA-256)
- `first_name`: User's first name
- `last_name`: User's last name
- `is_active`: Account status (True/False)
- `is_admin`: Admin privileges (True/False)
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp
- `bio`: User biography/description

## Files Structure

```
Database/
├── __init__.py          # Package initialization
├── models.py            # SQLAlchemy models
├── database.py          # Database connection and setup
├── user_manager.py      # User management operations
├── example_usage.py     # Example usage script
└── README.md           # This file
```

## Quick Start

1. **Run the example script** to see the system in action:
   ```bash
   uv run Database/example_usage.py
   ```

2. **Use in your own code**:
   ```python
   from Database.database import init_db
   from Database.user_manager import UserManager
   
   # Initialize database
   init_db()
   
   # Use the user manager
   with UserManager() as user_manager:
       # Create a user
       result = user_manager.create_user(
           username="testuser",
           email="test@example.com",
           password="password123",
           first_name="Test",
           last_name="User"
       )
       
       # Authenticate user
       auth_result = user_manager.authenticate_user("testuser", "password123")
   ```

## API Reference

### UserManager Class

#### Creating Users
```python
create_user(username, email, password, first_name=None, last_name=None, bio=None, is_admin=False)
```
- Returns: `{"success": bool, "user": dict}` or `{"success": bool, "error": str}`

#### Authentication
```python
authenticate_user(username, password)
```
- Returns: `{"success": bool, "user": dict}` or `{"success": bool, "error": str}`

#### User Retrieval
```python
get_user_by_id(user_id)
get_user_by_username(username)
get_user_by_email(email)
get_all_users()
get_active_users()
```

#### User Updates
```python
update_user(user_id, **kwargs)
change_password(user_id, old_password, new_password)
```

#### User Deletion
```python
delete_user(user_id)  # Soft delete (sets is_active to False)
```

#### Search
```python
search_users(query)  # Search by username, email, first_name, or last_name
```

## Security Features

- **Password Hashing**: Passwords are hashed using SHA-256
- **Email Validation**: Basic email format validation
- **Unique Constraints**: Username and email must be unique
- **Soft Delete**: Users are deactivated rather than deleted
- **Input Validation**: Basic validation for user inputs

## Database

The system uses SQLite by default for simplicity. The database file (`user_management.db`) will be created automatically in the project root when you first run the system.

To use a different database (PostgreSQL, MySQL, etc.), modify the `DATABASE_URL` in `database.py`:

```python
# PostgreSQL example
DATABASE_URL = "postgresql://user:password@localhost/dbname"

# MySQL example  
DATABASE_URL = "mysql+pymysql://user:password@localhost/dbname"
```

## Learning Points

This system demonstrates:

1. **SQLAlchemy ORM**: Model definition, relationships, and queries
2. **Database Sessions**: Proper session management with context managers
3. **Error Handling**: Database integrity errors and validation
4. **CRUD Operations**: Create, Read, Update, Delete operations
5. **Authentication**: Basic user authentication system
6. **Data Validation**: Input validation and business logic
7. **Soft Deletes**: Maintaining data integrity while allowing "deletion"

## Next Steps

To extend this system, consider adding:

- **Password Reset**: Email-based password reset functionality
- **User Roles**: More sophisticated role-based access control
- **Session Management**: JWT tokens or session handling
- **Audit Logging**: Track user actions and changes
- **Profile Pictures**: File upload and storage
- **Email Verification**: Email confirmation for new accounts
- **Rate Limiting**: Prevent brute force attacks
- **Two-Factor Authentication**: Additional security layer
