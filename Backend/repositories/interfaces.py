"""
Repository interfaces for data access operations.

This module defines abstract base classes that establish contracts for data
persistence and retrieval operations. These interfaces follow the Repository
pattern to decouple business logic from data access implementation details.

Classes:
    UserRepository: Interface for user data operations
    AssessmentRepository: Interface for assessment data operations
    SkillRepository: Interface for skill data operations
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.models import User, Assessment, Skill
from ..enums import AssessmentStatus, UserRole


class UserRepository(ABC):
    """
    Abstract repository interface for user data operations.
    
    This interface defines the contract for user persistence operations,
    including CRUD operations and user-specific queries. Implementations
    of this interface handle the actual data storage and retrieval logic.
    
    The repository pattern allows for flexible data storage backends
    (database, file system, API, etc.) while maintaining a consistent
    interface for the business logic layer.
    """
    
    @abstractmethod
    def save(self, user: User) -> bool:
        """
        Save a user to the data store.
        
        This method handles both creating new users and updating existing ones.
        The implementation should handle ID generation for new users and
        proper conflict resolution for updates.
        
        Args:
            user: User object to save
            
        Returns:
            bool: True if save operation was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the save operation
        """
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Find a user by their unique identifier.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Optional[User]: User object if found, None otherwise
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their email address.
        
        This method is crucial for authentication and user lookup operations.
        Email addresses should be unique in the system.
        
        Args:
            email: Email address to search for
            
        Returns:
            Optional[User]: User object if found, None otherwise
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def find_by_role(self, role: UserRole) -> List[User]:
        """
        Find all users with a specific role.
        
        Args:
            role: User role to filter by
            
        Returns:
            List[User]: List of users with the specified role
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[User]:
        """
        Retrieve all users with optional pagination.
        
        Args:
            limit: Maximum number of users to return (None for no limit)
            offset: Number of users to skip
            
        Returns:
            List[User]: List of users
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def update(self, user: User) -> bool:
        """
        Update an existing user in the data store.
        
        Args:
            user: User object with updated information
            
        Returns:
            bool: True if update was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the update
            NotFoundException: If the user doesn't exist
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """
        Delete a user from the data store.
        
        This operation should also handle cascading deletes for related
        data (assessments, skills, etc.) according to business rules.
        
        Args:
            user_id: Unique identifier of the user to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the deletion
            NotFoundException: If the user doesn't exist
        """
        pass
    
    @abstractmethod
    def exists(self, user_id: str) -> bool:
        """
        Check if a user exists in the data store.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            bool: True if user exists, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the check
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        Get the total number of users in the data store.
        
        Returns:
            int: Total count of users
            
        Raises:
            RepositoryError: If there's an error during the count operation
        """
        pass
    
    @abstractmethod
    def find_by_last_login_before(self, date: datetime) -> List[User]:
        """
        Find users who haven't logged in since a specific date.
        
        This method is useful for identifying inactive users.
        
        Args:
            date: Cutoff date for last login
            
        Returns:
            List[User]: List of users with last login before the specified date
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass


class AssessmentRepository(ABC):
    """
    Abstract repository interface for assessment data operations.
    
    This interface defines the contract for assessment persistence operations,
    including CRUD operations and assessment-specific queries. Assessments
    are central to the competency evaluation process.
    """
    
    @abstractmethod
    def save(self, assessment: Assessment) -> bool:
        """
        Save an assessment to the data store.
        
        Args:
            assessment: Assessment object to save
            
        Returns:
            bool: True if save operation was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the save operation
        """
        pass
    
    @abstractmethod
    def find_by_id(self, assessment_id: str) -> Optional[Assessment]:
        """
        Find an assessment by its unique identifier.
        
        Args:
            assessment_id: Unique identifier for the assessment
            
        Returns:
            Optional[Assessment]: Assessment object if found, None otherwise
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def find_by_user_id(self, user_id: str) -> List[Assessment]:
        """
        Find all assessments for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List[Assessment]: List of assessments for the user
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def find_by_status(self, status: AssessmentStatus) -> List[Assessment]:
        """
        Find all assessments with a specific status.
        
        Args:
            status: Assessment status to filter by
            
        Returns:
            List[Assessment]: List of assessments with the specified status
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def find_by_user_and_status(self, user_id: str, status: AssessmentStatus) -> List[Assessment]:
        """
        Find assessments for a specific user with a specific status.
        
        Args:
            user_id: Unique identifier for the user
            status: Assessment status to filter by
            
        Returns:
            List[Assessment]: List of matching assessments
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def update_status(self, assessment_id: str, status: AssessmentStatus) -> bool:
        """
        Update the status of an assessment.
        
        This method provides a convenient way to update just the status
        without loading and saving the entire assessment object.
        
        Args:
            assessment_id: Unique identifier for the assessment
            status: New status to set
            
        Returns:
            bool: True if update was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the update
            NotFoundException: If the assessment doesn't exist
        """
        pass
    
    @abstractmethod
    def update(self, assessment: Assessment) -> bool:
        """
        Update an existing assessment in the data store.
        
        Args:
            assessment: Assessment object with updated information
            
        Returns:
            bool: True if update was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the update
            NotFoundException: If the assessment doesn't exist
        """
        pass
    
    @abstractmethod
    def delete(self, assessment_id: str) -> bool:
        """
        Delete an assessment from the data store.
        
        Args:
            assessment_id: Unique identifier of the assessment to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the deletion
            NotFoundException: If the assessment doesn't exist
        """
        pass
    
    @abstractmethod
    def find_completed_between_dates(self, start_date: datetime, end_date: datetime) -> List[Assessment]:
        """
        Find assessments completed within a specific date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            List[Assessment]: List of assessments completed in the date range
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistical information about assessments.
        
        Returns aggregated data such as total count, status distribution,
        average completion time, etc.
        
        Returns:
            Dict[str, Any]: Dictionary containing assessment statistics
            
        Raises:
            RepositoryError: If there's an error during the calculation
        """
        pass
    
    @abstractmethod
    def find_incomplete_older_than(self, days: int) -> List[Assessment]:
        """
        Find incomplete assessments older than a specified number of days.
        
        This method is useful for cleanup operations and identifying
        abandoned assessments.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List[Assessment]: List of old incomplete assessments
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass


class SkillRepository(ABC):
    """
    Abstract repository interface for skill data operations.
    
    This interface defines the contract for skill persistence operations,
    including CRUD operations and skill-specific queries. Skills are
    fundamental building blocks of user competency profiles.
    """
    
    @abstractmethod
    def save(self, skill: Skill) -> bool:
        """
        Save a skill to the data store.
        
        Args:
            skill: Skill object to save
            
        Returns:
            bool: True if save operation was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the save operation
        """
        pass
    
    @abstractmethod
    def find_by_id(self, skill_id: str) -> Optional[Skill]:
        """
        Find a skill by its unique identifier.
        
        Args:
            skill_id: Unique identifier for the skill
            
        Returns:
            Optional[Skill]: Skill object if found, None otherwise
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def find_by_user_id(self, user_id: str) -> List[Skill]:
        """
        Find all skills for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List[Skill]: List of skills belonging to the user
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def search_by_name(self, name: str, exact_match: bool = False) -> List[Skill]:
        """
        Search for skills by name.
        
        Args:
            name: Skill name to search for
            exact_match: Whether to perform exact match or fuzzy search
            
        Returns:
            List[Skill]: List of skills matching the search criteria
            
        Raises:
            RepositoryError: If there's an error during the search
        """
        pass
    
    @abstractmethod
    def find_by_framework(self, framework_source: str, framework_id: Optional[str] = None) -> List[Skill]:
        """
        Find skills linked to a specific competency framework.
        
        Args:
            framework_source: Name of the framework (e.g., "ESCO", "Freiwilligenpass")
            framework_id: Optional specific competency ID within the framework
            
        Returns:
            List[Skill]: List of skills linked to the framework
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def update(self, skill: Skill) -> bool:
        """
        Update an existing skill in the data store.
        
        Args:
            skill: Skill object with updated information
            
        Returns:
            bool: True if update was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the update
            NotFoundException: If the skill doesn't exist
        """
        pass
    
    @abstractmethod
    def delete(self, skill_id: str) -> bool:
        """
        Delete a skill from the data store.
        
        This operation should also handle cascading deletes for related
        evidence according to business rules.
        
        Args:
            skill_id: Unique identifier of the skill to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the deletion
            NotFoundException: If the skill doesn't exist
        """
        pass
    
    @abstractmethod
    def find_by_proficiency_level(self, level: 'ProficiencyLevel') -> List[Skill]:
        """
        Find all skills at a specific proficiency level.
        
        Args:
            level: Proficiency level to filter by
            
        Returns:
            List[Skill]: List of skills at the specified level
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def get_skill_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistical information about skills.
        
        Args:
            user_id: Optional user ID to get statistics for specific user
            
        Returns:
            Dict[str, Any]: Dictionary containing skill statistics
            
        Raises:
            RepositoryError: If there's an error during the calculation
        """
        pass
    
    @abstractmethod
    def find_popular_skills(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find the most popular skills across all users.
        
        Args:
            limit: Maximum number of skills to return
            
        Returns:
            List[Dict[str, Any]]: List of popular skills with count information
            
        Raises:
            RepositoryError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def find_similar_skills(self, skill_id: str, similarity_threshold: float = 0.7) -> List[Skill]:
        """
        Find skills similar to a given skill.
        
        This method can use various similarity algorithms (name similarity,
        framework relationships, etc.) to find related skills.
        
        Args:
            skill_id: Reference skill ID
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List[Skill]: List of similar skills
            
        Raises:
            RepositoryError: If there's an error during the similarity search
        """
        pass
    
    @abstractmethod
    def bulk_save(self, skills: List[Skill]) -> bool:
        """
        Save multiple skills in a single operation.
        
        This method provides better performance when saving many skills
        at once, such as during bulk import operations.
        
        Args:
            skills: List of skill objects to save
            
        Returns:
            bool: True if all saves were successful, False otherwise
            
        Raises:
            RepositoryError: If there's an error during the bulk save
        """
        pass


class RepositoryError(Exception):
    """
    Base exception class for repository-related errors.
    
    This exception should be raised when there are errors during
    data persistence operations that are not related to business logic.
    """
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        """
        Initialize the repository error.
        
        Args:
            message: Error message describing what went wrong
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.cause = cause


class NotFoundException(RepositoryError):
    """
    Exception raised when a requested entity is not found.
    
    This exception indicates that a query for a specific entity
    (by ID or other unique criteria) did not find any matching records.
    """
    
    def __init__(self, entity_type: str, identifier: str):
        """
        Initialize the not found exception.
        
        Args:
            entity_type: Type of entity that was not found (e.g., "User", "Assessment")
            identifier: The identifier that was used in the search
        """
        message = f"{entity_type} with identifier '{identifier}' was not found"
        super().__init__(message)
        self.entity_type = entity_type
        self.identifier = identifier


class ValidationError(RepositoryError):
    """
    Exception raised when entity validation fails during persistence.
    
    This exception indicates that the entity data doesn't meet
    the required validation criteria for persistence.
    """
    
    def __init__(self, entity_type: str, validation_errors: List[str]):
        """
        Initialize the validation error.
        
        Args:
            entity_type: Type of entity that failed validation
            validation_errors: List of validation error messages
        """
        message = f"{entity_type} validation failed: {', '.join(validation_errors)}"
        super().__init__(message)
        self.entity_type = entity_type
        self.validation_errors = validation_errors 