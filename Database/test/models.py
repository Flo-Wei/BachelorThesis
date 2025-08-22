# Import necessary SQLAlchemy components
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

# declarative_base() creates a base class that all our models will inherit from
# This is part of SQLAlchemy's "Declarative" system, which allows us to define
# database tables as Python classes
Base = declarative_base()

class User(Base):
    """
    User model - This class represents a database table called 'users'
    
    In SQLAlchemy, you define database tables by creating classes that inherit from Base.
    Each class attribute becomes a database column, and the class itself becomes a table.
    
    This is called the "Object-Relational Mapping" (ORM) pattern - it lets you work with
    database records as Python objects instead of writing raw SQL.
    """
    
    # __tablename__ tells SQLAlchemy what to name the database table
    # If you don't specify this, SQLAlchemy will use the class name (User -> user)
    __tablename__ = 'users'
    
    # Column definitions - each Column() creates a database column
    
    # Integer primary key that auto-increments
    # primary_key=True makes this the primary key (unique identifier for each row)
    # autoincrement=True means the database will automatically assign the next available number
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # String column for username (max 50 characters)
    # unique=True means no two users can have the same username
    # nullable=False means this field cannot be empty (required field)
    # index=True creates a database index for faster lookups by username
    username = Column(String(50), unique=True, nullable=False, index=True)
    
    # Email column with similar constraints
    email = Column(String(100), unique=True, nullable=False, index=True)
    
    # Password hash column - we store hashed passwords, never plain text
    password_hash = Column(String(255), nullable=False)
    
    # Optional name fields - nullable=True means these can be empty
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    
    # Boolean columns for user status
    # default=True means new users are active by default
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # DateTime columns with automatic timestamps
    # func.now() is a SQLAlchemy function that gets the current timestamp
    # onupdate=func.now() means this field updates automatically when the record is modified
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Text column for longer content (no length limit)
    bio = Column(Text, nullable=True)
    
    def __repr__(self):
        """
        __repr__ is a special Python method that defines how the object is displayed
        when you print it or convert it to a string. This is useful for debugging.
        """
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """
        Convert the User object to a dictionary for easy serialization (e.g., for JSON)
        
        This is useful when you want to send user data over an API or save it to a file.
        We exclude the password_hash for security reasons.
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            # Convert datetime objects to ISO format strings for JSON serialization
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'bio': self.bio
        }
