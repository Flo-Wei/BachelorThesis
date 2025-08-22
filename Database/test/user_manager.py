# Import necessary modules for database operations and utilities
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError  # For handling database constraint violations
from .models import User
from .database import SessionLocal
import hashlib  # For password hashing
import re  # For email validation using regular expressions
from typing import List, Optional, Dict, Any

class UserManager:
    """
    User management class with CRUD operations
    
    This class provides a high-level interface for managing users in the database.
    It handles all the common operations you'd need for user management:
    - Creating new users
    - Reading user information
    - Updating user details
    - Deleting users (soft delete)
    - Authentication
    - Searching users
    
    CRUD stands for Create, Read, Update, Delete - the four basic database operations.
    """
    
    def __init__(self):
        """
        Initialize the UserManager with a database session
        
        The session is like a "workspace" where we can make changes to the database.
        All database operations (queries, inserts, updates, deletes) happen within a session.
        """
        self.db = SessionLocal()
    
    def __enter__(self):
        """
        Context manager entry point
        
        This allows us to use UserManager with the 'with' statement:
        with UserManager() as user_manager:
            user_manager.create_user(...)
        
        The session will be automatically closed when we exit the 'with' block.
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point
        
        This ensures the database session is properly closed, even if an error occurs.
        This is important to prevent memory leaks and connection pool exhaustion.
        """
        self.db.close()
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password using SHA-256
        
        We never store plain text passwords in the database for security reasons.
        Instead, we hash them using a cryptographic hash function.
        
        Note: In a real application, you should use more secure hashing like bcrypt
        with salt, but SHA-256 is used here for simplicity.
        
        Args:
            password: The plain text password to hash
            
        Returns:
            The hashed password as a hexadecimal string
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate email format using regular expressions
        
        This is a basic email validation. In a real application, you might want
        to use a more sophisticated validation library or send verification emails.
        
        Args:
            email: The email address to validate
            
        Returns:
            True if the email format is valid, False otherwise
        """
        # Regular expression pattern for basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def create_user(self, username: str, email: str, password: str, 
                   first_name: str = None, last_name: str = None, 
                   bio: str = None, is_admin: bool = False) -> Dict[str, Any]:
        """
        Create a new user in the database
        
        This method demonstrates several important SQLAlchemy concepts:
        - Creating new model instances
        - Adding objects to the session
        - Committing changes to the database
        - Error handling with rollback
        - Input validation
        
        Args:
            username: Unique username for the user
            email: Unique email address for the user
            password: Plain text password (will be hashed)
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            bio: User biography (optional)
            is_admin: Whether the user has admin privileges
            
        Returns:
            Dictionary with success status and either user data or error message
        """
        try:
            # Input validation - check email format
            if not self._validate_email(email):
                return {"success": False, "error": "Invalid email format"}
            
            # Check for existing users with same username or email
            # This prevents duplicate entries and demonstrates SQLAlchemy queries
            if self.get_user_by_username(username):
                return {"success": False, "error": "Username already exists"}
            
            if self.get_user_by_email(email):
                return {"success": False, "error": "Email already exists"}
            
            # Create a new User object (this doesn't save it to the database yet)
            # This demonstrates how to instantiate SQLAlchemy model classes
            user = User(
                username=username,
                email=email,
                password_hash=self._hash_password(password),  # Hash the password
                first_name=first_name,
                last_name=last_name,
                bio=bio,
                is_admin=is_admin
            )
            
            # Add the user object to the session
            # This tells SQLAlchemy that we want to save this object to the database
            self.db.add(user)
            
            # Commit the changes to the database
            # This actually executes the INSERT statement
            self.db.commit()
            
            # Refresh the user object to get the auto-generated ID and timestamps
            # This is important because the database assigns the ID and timestamps
            self.db.refresh(user)
            
            # Return success with user data
            return {"success": True, "user": user.to_dict()}
            
        except IntegrityError:
            # Handle database constraint violations (e.g., duplicate unique values)
            # Rollback undoes any changes made in this session
            self.db.rollback()
            return {"success": False, "error": "Database integrity error"}
        except Exception as e:
            # Handle any other unexpected errors
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by their ID
        
        This demonstrates a simple SQLAlchemy query using filter().
        The query translates to: SELECT * FROM users WHERE id = user_id LIMIT 1
        
        Args:
            user_id: The unique ID of the user
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by their username
        
        Args:
            username: The username to search for
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by their email address
        
        Args:
            email: The email address to search for
            
        Returns:
            User object if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all_users(self) -> List[User]:
        """
        Get all users from the database
        
        This demonstrates a query without filters - it returns all records.
        The query translates to: SELECT * FROM users
        
        Returns:
            List of all User objects
        """
        return self.db.query(User).all()
    
    def get_active_users(self) -> List[User]:
        """
        Get only active users
        
        This demonstrates filtering with a boolean condition.
        The query translates to: SELECT * FROM users WHERE is_active = True
        
        Returns:
            List of active User objects
        """
        return self.db.query(User).filter(User.is_active == True).all()
    
    def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update user information
        
        This method demonstrates how to update existing database records.
        It shows dynamic field updates and proper error handling.
        
        Args:
            user_id: The ID of the user to update
            **kwargs: Keyword arguments for fields to update (e.g., first_name="John")
            
        Returns:
            Dictionary with success status and updated user data or error message
        """
        try:
            # First, get the user we want to update
            user = self.get_user_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Define which fields are allowed to be updated
            # This is a security measure to prevent updating sensitive fields
            allowed_fields = ['first_name', 'last_name', 'bio', 'is_active', 'is_admin']
            
            # Update each field that was provided and is allowed
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    # setattr() dynamically sets an attribute on an object
                    setattr(user, field, value)
            
            # Commit the changes to the database
            self.db.commit()
            
            return {"success": True, "user": user.to_dict()}
            
        except Exception as e:
            # Rollback on any error
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change a user's password
        
        This method demonstrates password verification and secure password updates.
        
        Args:
            user_id: The ID of the user
            old_password: The current password (for verification)
            new_password: The new password to set
            
        Returns:
            Dictionary with success status and message
        """
        try:
            # Get the user
            user = self.get_user_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Verify the old password by comparing hashes
            if user.password_hash != self._hash_password(old_password):
                return {"success": False, "error": "Incorrect old password"}
            
            # Update the password hash
            user.password_hash = self._hash_password(new_password)
            self.db.commit()
            
            return {"success": True, "message": "Password changed successfully"}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """
        Delete a user (soft delete)
        
        Instead of actually deleting the record from the database, we set is_active to False.
        This is called a "soft delete" and is useful for:
        - Maintaining data integrity
        - Allowing data recovery
        - Preserving audit trails
        - Avoiding foreign key constraint issues
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            Dictionary with success status and message
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Soft delete by setting is_active to False
            user.is_active = False
            self.db.commit()
            
            return {"success": True, "message": "User deactivated successfully"}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user with username and password
        
        This method demonstrates user authentication by:
        1. Finding the user by username
        2. Checking if the account is active
        3. Verifying the password hash
        
        Args:
            username: The username to authenticate
            password: The password to verify
            
        Returns:
            Dictionary with success status and user data or error message
        """
        # Find the user by username
        user = self.get_user_by_username(username)
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Check if the account is active
        if not user.is_active:
            return {"success": False, "error": "User account is deactivated"}
        
        # Verify the password by comparing hashes
        if user.password_hash == self._hash_password(password):
            return {"success": True, "user": user.to_dict()}
        else:
            return {"success": False, "error": "Incorrect password"}
    
    def search_users(self, query: str) -> List[User]:
        """
        Search users by username, email, first_name, or last_name
        
        This demonstrates more complex SQLAlchemy queries using:
        - Multiple filter conditions with OR logic
        - String containment searches
        
        The query translates to something like:
        SELECT * FROM users WHERE 
            username LIKE '%query%' OR 
            email LIKE '%query%' OR 
            first_name LIKE '%query%' OR 
            last_name LIKE '%query%'
        
        Args:
            query: The search term to look for
            
        Returns:
            List of User objects that match the search criteria
        """
        return self.db.query(User).filter(
            (User.username.contains(query)) |
            (User.email.contains(query)) |
            (User.first_name.contains(query)) |
            (User.last_name.contains(query))
        ).all()
