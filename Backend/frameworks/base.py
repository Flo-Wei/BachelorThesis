"""
Base competency framework interface and data structures.

This module defines the abstract base class for competency frameworks and
the core data structures used to represent competencies across different
framework implementations.

Classes:
    Competency: Data class representing a single competency
    CompetencyFramework: Abstract interface for competency framework implementations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
import uuid


@dataclass
class Competency:
    """
    Represents a single competency within a competency framework.
    
    A competency defines a specific skill, knowledge area, or ability that
    can be possessed and demonstrated by individuals. Competencies are the
    building blocks of competency frameworks and serve as standardized
    references for skill assessment and development.
    
    Attributes:
        id: Unique identifier for the competency within its framework
        name: Human-readable name of the competency
        description: Detailed description of what the competency represents
        framework_id: Internal ID used by the framework system
        category: Category or domain this competency belongs to
        level: Optional proficiency level indicator
        prerequisites: List of competency IDs that are prerequisites
        related_competencies: List of related or similar competency IDs
        keywords: Set of keywords associated with this competency for search
        metadata: Additional framework-specific metadata
    """
    
    id: str = ""
    name: str = ""
    description: str = ""
    framework_id: str = ""
    category: str = ""
    level: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    related_competencies: List[str] = field(default_factory=list)
    keywords: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate competency data after initialization."""
        if not self.id:
            raise ValueError("Competency ID is required")
        if not self.name:
            raise ValueError("Competency name is required")
    
    def add_keyword(self, keyword: str) -> bool:
        """
        Add a keyword to this competency for improved searchability.
        
        Args:
            keyword: Keyword to add
            
        Returns:
            bool: True if keyword was added successfully, False otherwise
        """
        try:
            self.keywords.add(keyword.lower().strip())
            return True
        except Exception:
            return False
    
    def add_related_competency(self, competency_id: str) -> bool:
        """
        Add a related competency reference.
        
        Args:
            competency_id: ID of the related competency
            
        Returns:
            bool: True if relation was added successfully, False otherwise
        """
        try:
            if competency_id not in self.related_competencies and competency_id != self.id:
                self.related_competencies.append(competency_id)
            return True
        except Exception:
            return False
    
    def matches_keyword(self, search_term: str) -> bool:
        """
        Check if this competency matches a search term.
        
        Args:
            search_term: Term to search for
            
        Returns:
            bool: True if competency matches the search term, False otherwise
        """
        search_term = search_term.lower().strip()
        
        # Check name and description
        if search_term in self.name.lower() or search_term in self.description.lower():
            return True
        
        # Check keywords
        return search_term in self.keywords
    
    def get_similarity_score(self, other: 'Competency') -> float:
        """
        Calculate similarity score with another competency.
        
        Args:
            other: Another competency to compare with
            
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        if not isinstance(other, Competency):
            return 0.0
        
        # Check if they're the same competency
        if self.id == other.id:
            return 1.0
        
        # Check if they're directly related
        if other.id in self.related_competencies or self.id in other.related_competencies:
            return 0.8
        
        # Check category similarity
        category_score = 0.5 if self.category == other.category else 0.0
        
        # Check keyword overlap
        if self.keywords and other.keywords:
            common_keywords = self.keywords.intersection(other.keywords)
            total_keywords = self.keywords.union(other.keywords)
            keyword_score = len(common_keywords) / len(total_keywords) if total_keywords else 0.0
        else:
            keyword_score = 0.0
        
        # Check name similarity (simple word overlap)
        self_words = set(self.name.lower().split())
        other_words = set(other.name.lower().split())
        if self_words and other_words:
            common_words = self_words.intersection(other_words)
            total_words = self_words.union(other_words)
            name_score = len(common_words) / len(total_words) if total_words else 0.0
        else:
            name_score = 0.0
        
        # Weighted combination
        return (category_score * 0.3 + keyword_score * 0.4 + name_score * 0.3)
    
    def __str__(self) -> str:
        """Return string representation of the competency."""
        return f"Competency(id={self.id}, name={self.name}, category={self.category})"
    
    def __hash__(self) -> int:
        """Make competency hashable based on ID."""
        return hash(self.id)
    
    def __eq__(self, other) -> bool:
        """Check equality based on competency ID."""
        if not isinstance(other, Competency):
            return False
        return self.id == other.id


class CompetencyFramework(ABC):
    """
    Abstract base class defining the interface for competency frameworks.
    
    This interface establishes the contract that all competency framework
    implementations must follow. It provides standardized methods for
    accessing, searching, and retrieving competencies from various
    frameworks such as ESCO, national qualifications frameworks, or
    organization-specific competency models.
    
    Implementing classes should provide concrete implementations for
    all abstract methods, handling framework-specific data sources,
    formats, and retrieval mechanisms.
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of this competency framework.
        
        Returns:
            str: Human-readable name of the framework
        """
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """
        Get the version of this competency framework.
        
        Returns:
            str: Version identifier for the framework
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        Get a description of this competency framework.
        
        Returns:
            str: Description of the framework's purpose and scope
        """
        pass
    
    @abstractmethod
    def get_competencies(self) -> List[Competency]:
        """
        Retrieve all competencies available in this framework.
        
        Returns:
            List[Competency]: Complete list of competencies in the framework
            
        Raises:
            FrameworkError: If there's an error loading competencies
        """
        pass
    
    @abstractmethod
    def find_by_id(self, competency_id: str) -> Optional[Competency]:
        """
        Find a specific competency by its unique identifier.
        
        Args:
            competency_id: Unique identifier for the competency
            
        Returns:
            Optional[Competency]: Competency if found, None otherwise
            
        Raises:
            FrameworkError: If there's an error during the search
        """
        pass
    
    @abstractmethod
    def search_by_keyword(self, keyword: str, limit: Optional[int] = None) -> List[Competency]:
        """
        Search for competencies matching a keyword or phrase.
        
        Args:
            keyword: Search term to match against competency data
            limit: Optional maximum number of results to return
            
        Returns:
            List[Competency]: List of matching competencies, sorted by relevance
            
        Raises:
            FrameworkError: If there's an error during the search
        """
        pass
    
    @abstractmethod
    def get_categories(self) -> List[str]:
        """
        Get all available categories in this framework.
        
        Returns:
            List[str]: List of category names
            
        Raises:
            FrameworkError: If there's an error retrieving categories
        """
        pass
    
    @abstractmethod
    def get_competencies_by_category(self, category: str) -> List[Competency]:
        """
        Get all competencies belonging to a specific category.
        
        Args:
            category: Category name to filter by
            
        Returns:
            List[Competency]: List of competencies in the specified category
            
        Raises:
            FrameworkError: If there's an error during the query
        """
        pass
    
    @abstractmethod
    def find_similar_competencies(self, competency_id: str, 
                                threshold: float = 0.5,
                                limit: Optional[int] = None) -> List[Competency]:
        """
        Find competencies similar to a given competency.
        
        Args:
            competency_id: Reference competency ID
            threshold: Minimum similarity score (0.0 to 1.0)
            limit: Optional maximum number of results to return
            
        Returns:
            List[Competency]: List of similar competencies, sorted by similarity
            
        Raises:
            FrameworkError: If there's an error during the similarity search
        """
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """
        Check if the framework data has been loaded successfully.
        
        Returns:
            bool: True if framework is loaded and ready for use, False otherwise
        """
        pass
    
    @abstractmethod
    def reload(self) -> bool:
        """
        Reload the framework data from its source.
        
        This method is useful for refreshing the framework data when
        the underlying source has been updated.
        
        Returns:
            bool: True if reload was successful, False otherwise
            
        Raises:
            FrameworkError: If there's an error during the reload
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistical information about this framework.
        
        Returns:
            Dict[str, Any]: Dictionary containing framework statistics
            
        Raises:
            FrameworkError: If there's an error calculating statistics
        """
        pass
    
    def validate_competency_id(self, competency_id: str) -> bool:
        """
        Validate that a competency ID exists in this framework.
        
        Args:
            competency_id: Competency ID to validate
            
        Returns:
            bool: True if competency exists, False otherwise
        """
        try:
            return self.find_by_id(competency_id) is not None
        except Exception:
            return False
    
    def search_competencies(self, query: str, 
                          category_filter: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Competency]:
        """
        Advanced search for competencies with optional filtering.
        
        Args:
            query: Search query string
            category_filter: Optional category to filter results
            limit: Optional maximum number of results
            
        Returns:
            List[Competency]: List of matching competencies
        """
        try:
            # Get initial search results
            results = self.search_by_keyword(query, limit)
            
            # Apply category filter if specified
            if category_filter:
                results = [comp for comp in results if comp.category == category_filter]
            
            return results
        except Exception:
            return []
    
    def get_competency_count(self) -> int:
        """
        Get the total number of competencies in this framework.
        
        Returns:
            int: Total number of competencies
        """
        try:
            return len(self.get_competencies())
        except Exception:
            return 0
    
    def __str__(self) -> str:
        """Return string representation of the framework."""
        return f"{self.get_name()} v{self.get_version()}"


class FrameworkError(Exception):
    """
    Base exception class for competency framework-related errors.
    
    This exception should be raised when there are errors specific to
    competency framework operations, such as loading framework data,
    parsing competency information, or performing framework-specific queries.
    """
    
    def __init__(self, message: str, framework_name: Optional[str] = None, 
                 cause: Optional[Exception] = None):
        """
        Initialize the framework error.
        
        Args:
            message: Error message describing what went wrong
            framework_name: Optional name of the framework where error occurred
            cause: Optional underlying exception that caused this error
        """
        if framework_name:
            message = f"[{framework_name}] {message}"
        super().__init__(message)
        self.framework_name = framework_name
        self.cause = cause


class FrameworkNotLoadedException(FrameworkError):
    """
    Exception raised when trying to use a framework that hasn't been loaded.
    
    This exception indicates that framework operations are being attempted
    before the framework data has been properly initialized and loaded.
    """
    
    def __init__(self, framework_name: str):
        """
        Initialize the not loaded exception.
        
        Args:
            framework_name: Name of the framework that is not loaded
        """
        message = f"Framework '{framework_name}' has not been loaded yet. Call load() first."
        super().__init__(message, framework_name)


class CompetencyNotFoundException(FrameworkError):
    """
    Exception raised when a requested competency is not found.
    
    This exception indicates that a search for a specific competency
    (by ID or other criteria) did not find any matching records in the framework.
    """
    
    def __init__(self, competency_id: str, framework_name: Optional[str] = None):
        """
        Initialize the competency not found exception.
        
        Args:
            competency_id: The competency ID that was not found
            framework_name: Optional name of the framework where search was performed
        """
        message = f"Competency with ID '{competency_id}' was not found"
        super().__init__(message, framework_name)
        self.competency_id = competency_id 