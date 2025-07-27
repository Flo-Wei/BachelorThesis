"""
Backend package for the competency assessment system.

This package contains all the core components for a comprehensive competency
assessment system including domain models, services, repositories, and
competency frameworks.

Main Components:
    - Domain models: Core business entities (User, Assessment, Skill, etc.)
    - Enumerations: System-wide constants and status values
    - Services: Business logic and application services
    - Repositories: Data access interfaces
    - Frameworks: Competency framework implementations (ESCO, Freiwilligenpass)

Quick Start:
    from Backend import User, Assessment, ChatService, ESCOFramework
    
    # Create a user
    user = User(email="user@example.com", password_hash="hashed_password")
    
    # Initialize frameworks
    esco = ESCOFramework()
    esco.load_framework()
    
    # Start assessment
    # (Additional setup required for full service initialization)
"""

# Core domain models
from .domain.models import (
    User, Profile, Skill, Evidence, Assessment, 
    Conversation, Message, MappedCompetency
)

# Enumerations
from .enums import (
    UserRole, ProficiencyLevel, AssessmentStatus, 
    MessageType, ConversationState, EvidenceType
)

# Repository interfaces
from .repositories.interfaces import (
    UserRepository, AssessmentRepository, SkillRepository,
    RepositoryError, NotFoundException, ValidationError
)

# Framework components
from .frameworks.base import (
    Competency, CompetencyFramework, FrameworkError, 
    FrameworkNotLoadedException, CompetencyNotFoundException
)
from .frameworks.esco import ESCOFramework, ESCOCompetency
from .frameworks.freiwilligenpass import FreiwilligenpassFramework, FPCompetency

# Service components
from .services.chat_service import (
    ChatService, ConversationEngine, LLMService, 
    CompetencyMappingService, VisualizationService,
    QuestionStrategy, StateManager, PromptTemplate, LLMProvider
)

__version__ = "1.0.0"
__author__ = "Competency Assessment System Team"

# Package metadata
__all__ = [
    # Domain models
    "User", "Profile", "Skill", "Evidence", "Assessment", 
    "Conversation", "Message", "MappedCompetency",
    
    # Enumerations
    "UserRole", "ProficiencyLevel", "AssessmentStatus", 
    "MessageType", "ConversationState", "EvidenceType",
    
    # Repository interfaces
    "UserRepository", "AssessmentRepository", "SkillRepository",
    "RepositoryError", "NotFoundException", "ValidationError",
    
    # Framework components
    "Competency", "CompetencyFramework", "FrameworkError", 
    "FrameworkNotLoadedException", "CompetencyNotFoundException",
    "ESCOFramework", "ESCOCompetency",
    "FreiwilligenpassFramework", "FPCompetency",
    
    # Service components
    "ChatService", "ConversationEngine", "LLMService", 
    "CompetencyMappingService", "VisualizationService",
    "QuestionStrategy", "StateManager", "PromptTemplate", "LLMProvider"
]


def get_version():
    """Get the current version of the backend package."""
    return __version__


def create_sample_user():
    """Create a sample user for testing purposes."""
    return User(
        email="sample@example.com",
        password_hash="$2b$12$sample_hash",
        role=UserRole.USER
    )


def get_available_frameworks():
    """Get a list of available competency frameworks."""
    return ["ESCO", "Freiwilligenpass"]


def create_framework(framework_name: str):
    """
    Create and return a competency framework instance.
    
    Args:
        framework_name: Name of the framework to create
        
    Returns:
        CompetencyFramework: Framework instance
        
    Raises:
        ValueError: If framework name is not recognized
    """
    if framework_name.lower() == "esco":
        return ESCOFramework()
    elif framework_name.lower() == "freiwilligenpass":
        return FreiwilligenpassFramework()
    else:
        raise ValueError(f"Unknown framework: {framework_name}")


class BackendConfig:
    """Configuration class for backend components."""
    
    def __init__(self):
        """Initialize default configuration."""
        self.default_language = "en"
        self.max_conversation_length = 100
        self.confidence_threshold = 0.5
        self.supported_frameworks = ["ESCO", "Freiwilligenpass"]
        self.log_level = "INFO"
    
    def to_dict(self):
        """Convert configuration to dictionary."""
        return {
            "default_language": self.default_language,
            "max_conversation_length": self.max_conversation_length,
            "confidence_threshold": self.confidence_threshold,
            "supported_frameworks": self.supported_frameworks,
            "log_level": self.log_level
        }


# Default configuration instance
default_config = BackendConfig() 