#!/usr/bin/env python3
"""
Example usage of the User Management Database System

This script demonstrates all the basic operations you can perform with the user management system.
It's designed to be educational - each section shows different SQLAlchemy concepts and patterns.

Key SQLAlchemy concepts demonstrated:
- Database initialization and table creation
- Creating new records (INSERT operations)
- Querying records (SELECT operations)
- Updating existing records (UPDATE operations)
- Soft deleting records (setting flags instead of actual deletion)
- Error handling and validation
- Session management with context managers
- Complex queries with filters and search
"""

# Import the necessary components from our database system
from Database.database import init_db
from Database.user_manager import UserManager
import json

def print_separator(title):
    """
    Print a visual separator with a title for better output organization
    
    This is just a helper function to make the output more readable
    when running the example script.
    """
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)

def print_user(user):
    """
    Print user information in a formatted way
    
    This function demonstrates how to work with SQLAlchemy model objects
    and convert them to dictionaries for display.
    
    Args:
        user: Either a User object or a dictionary containing user data
    """
    if user:
        # Check if it's a User object (has to_dict method) or already a dictionary
        user_dict = user.to_dict() if hasattr(user, 'to_dict') else user
        print(f"ID: {user_dict['id']}")
        print(f"Username: {user_dict['username']}")
        print(f"Email: {user_dict['email']}")
        print(f"Name: {user_dict['first_name']} {user_dict['last_name']}")
        print(f"Active: {user_dict['is_active']}")
        print(f"Admin: {user_dict['is_admin']}")
        print(f"Bio: {user_dict['bio']}")
        print(f"Created: {user_dict['created_at']}")
    else:
        print("User not found")

def main():
    """
    Main function demonstrating user management operations
    
    This function is organized into sections, each demonstrating different
    aspects of SQLAlchemy and database operations.
    """
    
    # ============================================================================
    # SECTION 1: DATABASE INITIALIZATION
    # ============================================================================
    print_separator("INITIALIZING DATABASE")
    
    # Initialize the database - this creates all tables defined in our models
    # This is equivalent to running CREATE TABLE statements in SQL
    init_db()
    
    # ============================================================================
    # SECTION 2: CREATING USERS (INSERT operations)
    # ============================================================================
    print_separator("CREATING USERS")
    
    # Use the UserManager as a context manager
    # This ensures the database session is properly closed when we're done
    with UserManager() as user_manager:
        
        # Create an admin user
        # This demonstrates the create_user method and shows how SQLAlchemy
        # handles INSERT operations behind the scenes
        result = user_manager.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            first_name="Admin",
            last_name="User",
            bio="System administrator",
            is_admin=True
        )
        print(f"Admin user creation: {result['success']}")
        if result['success']:
            print_user(result['user'])
        
        # Create a regular user
        # This shows how the same method can be used with different parameters
        result = user_manager.create_user(
            username="john_doe",
            email="john.doe@example.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            bio="Software developer"
        )
        print(f"\nRegular user creation: {result['success']}")
        if result['success']:
            print_user(result['user'])
        
        # Create another user
        result = user_manager.create_user(
            username="jane_smith",
            email="jane.smith@example.com",
            password="secure456",
            first_name="Jane",
            last_name="Smith",
            bio="Data scientist"
        )
        print(f"\nAnother user creation: {result['success']}")
        if result['success']:
            print_user(result['user'])
        
        # ============================================================================
        # SECTION 3: ERROR HANDLING AND VALIDATION
        # ============================================================================
        print_separator("ERROR HANDLING")
        
        # Try to create a user with an existing username
        # This demonstrates how SQLAlchemy handles unique constraint violations
        # and how our application provides meaningful error messages
        result = user_manager.create_user(
            username="admin",  # This username already exists
            email="new@example.com",
            password="password"
        )
        print(f"Duplicate username: {result['error']}")
        
        # Try to create a user with an invalid email format
        # This demonstrates input validation before database operations
        result = user_manager.create_user(
            username="invalid",
            email="invalid-email",  # Invalid email format
            password="password"
        )
        print(f"Invalid email: {result['error']}")
        
        # ============================================================================
        # SECTION 4: AUTHENTICATION
        # ============================================================================
        print_separator("AUTHENTICATION")
        
        # Successful authentication
        # This demonstrates how password hashing and verification works
        result = user_manager.authenticate_user("admin", "admin123")
        print(f"Admin login: {result['success']}")
        if result['success']:
            print(f"Welcome, {result['user']['username']}!")
        
        # Failed authentication with wrong password
        # This shows how password verification prevents unauthorized access
        result = user_manager.authenticate_user("admin", "wrongpassword")
        print(f"Wrong password: {result['error']}")
        
        # Authentication with non-existent user
        # This demonstrates how the system handles missing users
        result = user_manager.authenticate_user("nonexistent", "password")
        print(f"Non-existent user: {result['error']}")
        
        # ============================================================================
        # SECTION 5: USER RETRIEVAL (SELECT operations)
        # ============================================================================
        print_separator("USER RETRIEVAL")
        
        # Get user by ID
        # This demonstrates a simple SQLAlchemy query with a primary key filter
        user = user_manager.get_user_by_id(1)
        print("User with ID 1:")
        print_user(user)
        
        # Get user by username
        # This shows querying by a unique field
        user = user_manager.get_user_by_username("john_doe")
        print("\nUser with username 'john_doe':")
        print_user(user)
        
        # Get user by email
        # This demonstrates another unique field query
        user = user_manager.get_user_by_email("jane.smith@example.com")
        print("\nUser with email 'jane.smith@example.com':")
        print_user(user)
        
        # ============================================================================
        # SECTION 6: LISTING ALL USERS
        # ============================================================================
        print_separator("ALL USERS")
        
        # Get all users from the database
        # This demonstrates a query without filters - returns all records
        users = user_manager.get_all_users()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"- {user.username} ({user.email}) - Active: {user.is_active}")
        
        # ============================================================================
        # SECTION 7: UPDATING USERS (UPDATE operations)
        # ============================================================================
        print_separator("UPDATING USER")
        
        # Update user information
        # This demonstrates how to modify existing database records
        result = user_manager.update_user(
            user_id=2,  # Update john_doe
            first_name="Johnny",
            bio="Senior software developer with 5 years experience"
        )
        print(f"Update result: {result['success']}")
        if result['success']:
            print("Updated user:")
            print_user(result['user'])
        
        # ============================================================================
        # SECTION 8: PASSWORD MANAGEMENT
        # ============================================================================
        print_separator("CHANGING PASSWORD")
        
        # Change a user's password
        # This demonstrates secure password updates with verification
        result = user_manager.change_password(2, "password123", "newpassword456")
        print(f"Password change: {result['success']}")
        if result['success']:
            print(result['message'])
            
            # Test the new password
            # This verifies that the password change worked correctly
            auth_result = user_manager.authenticate_user("john_doe", "newpassword456")
            print(f"Login with new password: {auth_result['success']}")
        
        # ============================================================================
        # SECTION 9: SEARCHING USERS
        # ============================================================================
        print_separator("SEARCHING USERS")
        
        # Search for users containing "john" in any field
        # This demonstrates complex SQLAlchemy queries with OR conditions
        search_results = user_manager.search_users("john")
        print(f"Users containing 'john': {len(search_results)}")
        for user in search_results:
            print(f"- {user.username} ({user.first_name} {user.last_name})")
        
        # ============================================================================
        # SECTION 10: SOFT DELETE
        # ============================================================================
        print_separator("SOFT DELETE USER")
        
        # Soft delete a user (deactivate instead of actually deleting)
        # This demonstrates the concept of soft deletes for data integrity
        result = user_manager.delete_user(3)  # Deactivate jane_smith
        print(f"Delete result: {result['success']}")
        if result['success']:
            print(result['message'])
            
            # Verify the user is deactivated
            # The record still exists in the database, but is_active is False
            user = user_manager.get_user_by_id(3)
            print(f"User active status: {user.is_active}")
            
            # Try to authenticate the deactivated user
            # This shows how soft deletes affect authentication
            auth_result = user_manager.authenticate_user("jane_smith", "secure456")
            print(f"Login deactivated user: {auth_result['error']}")
        
        # ============================================================================
        # SECTION 11: FILTERED QUERIES
        # ============================================================================
        print_separator("ACTIVE USERS ONLY")
        
        # Get only active users
        # This demonstrates filtering queries to show only specific records
        active_users = user_manager.get_active_users()
        print(f"Active users: {len(active_users)}")
        for user in active_users:
            print(f"- {user.username} ({user.email})")

# This is a Python idiom that ensures the main() function only runs
# when the script is executed directly (not when imported as a module)
if __name__ == "__main__":
    main()
