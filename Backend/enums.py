"""
Enumeration classes for the competency assessment system.

This module contains all the enumeration classes that define the possible
values for various attributes throughout the system. These enums ensure
type safety and provide clear, predefined options for status tracking,
user roles, proficiency levels, and more.

Classes:
    UserRole: Defines the different roles a user can have in the system
    ProficiencyLevel: Defines skill proficiency levels from beginner to expert
    AssessmentStatus: Tracks the current status of an assessment
    MessageType: Categorizes different types of messages in conversations
    ConversationState: Tracks the current phase of a conversation
    EvidenceType: Categorizes different types of evidence for skills
"""

from enum import Enum, auto
from typing import List


class UserRole(Enum):
    """
    Enumeration defining the different roles a user can have in the system.
    
    This enum is used to control access permissions and determine what
    actions a user can perform within the application.
    
    Attributes:
        USER: Standard user with basic assessment and profile management permissions
        ADMIN: Administrator with full system access and user management capabilities
        MODERATOR: Moderator with limited administrative capabilities for content management
    """
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    
    def __str__(self) -> str:
        """Return the string representation of the user role."""
        return self.value.capitalize()
    
    @classmethod
    def get_admin_roles(cls) -> List['UserRole']:
        """
        Get all roles that have administrative privileges.
        
        Returns:
            List[UserRole]: List of roles with administrative access
        """
        return [cls.ADMIN, cls.MODERATOR]


class ProficiencyLevel(Enum):
    """
    Enumeration defining skill proficiency levels from beginner to expert.
    
    This enum provides a standardized way to assess and represent skill
    competency levels across different domains and frameworks.
    
    Attributes:
        BEGINNER: Basic understanding with limited practical experience
        INTERMEDIATE: Good understanding with some practical experience
        ADVANCED: Strong competency with extensive practical experience
        EXPERT: Mastery level with ability to teach and lead others
    """
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    
    def __str__(self) -> str:
        """Return the string representation of the proficiency level."""
        return self.value.capitalize()
    
    @property
    def numeric_value(self) -> int:
        """
        Get the numeric representation of the proficiency level.
        
        Returns:
            int: Numeric value (1-4) representing the proficiency level
        """
        mapping = {
            self.BEGINNER: 1,
            self.INTERMEDIATE: 2,
            self.ADVANCED: 3,
            self.EXPERT: 4
        }
        return mapping[self]
    
    @classmethod
    def from_numeric(cls, value: int) -> 'ProficiencyLevel':
        """
        Create a ProficiencyLevel from a numeric value.
        
        Args:
            value: Numeric value (1-4)
            
        Returns:
            ProficiencyLevel: Corresponding proficiency level
            
        Raises:
            ValueError: If the numeric value is not valid (1-4)
        """
        mapping = {
            1: cls.BEGINNER,
            2: cls.INTERMEDIATE,
            3: cls.ADVANCED,
            4: cls.EXPERT
        }
        if value not in mapping:
            raise ValueError(f"Invalid proficiency level value: {value}. Must be 1-4.")
        return mapping[value]


class AssessmentStatus(Enum):
    """
    Enumeration tracking the current status of an assessment.
    
    This enum provides clear state management for assessments as they
    progress through different phases of completion.
    
    Attributes:
        NOT_STARTED: Assessment has been created but not yet begun
        IN_PROGRESS: Assessment is currently active and ongoing
        PAUSED: Assessment has been temporarily suspended by the user
        COMPLETED: Assessment has been finished and results are available
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    
    def __str__(self) -> str:
        """Return the string representation of the assessment status."""
        return self.value.replace("_", " ").title()
    
    @property
    def is_active(self) -> bool:
        """
        Check if the assessment is in an active state.
        
        Returns:
            bool: True if assessment is in progress, False otherwise
        """
        return self == self.IN_PROGRESS
    
    @property
    def is_finished(self) -> bool:
        """
        Check if the assessment has been completed.
        
        Returns:
            bool: True if assessment is completed, False otherwise
        """
        return self == self.COMPLETED
    
    @property
    def can_resume(self) -> bool:
        """
        Check if the assessment can be resumed.
        
        Returns:
            bool: True if assessment can be resumed, False otherwise
        """
        return self in [self.NOT_STARTED, self.PAUSED]


class MessageType(Enum):
    """
    Enumeration categorizing different types of messages in conversations.
    
    This enum helps distinguish between different types of messages to
    enable proper processing, display, and analysis of conversation data.
    
    Attributes:
        USER_MESSAGE: Message sent by the user/participant
        BOT_MESSAGE: Message generated by the AI system
        SYSTEM_MESSAGE: System-generated notifications or status updates
    """
    USER_MESSAGE = "user_message"
    BOT_MESSAGE = "bot_message"
    SYSTEM_MESSAGE = "system_message"
    
    def __str__(self) -> str:
        """Return the string representation of the message type."""
        return self.value.replace("_", " ").title()
    
    @property
    def is_user_generated(self) -> bool:
        """
        Check if the message was generated by a user.
        
        Returns:
            bool: True if message is from user, False otherwise
        """
        return self == self.USER_MESSAGE
    
    @property
    def is_automated(self) -> bool:
        """
        Check if the message was automatically generated.
        
        Returns:
            bool: True if message is from bot or system, False otherwise
        """
        return self in [self.BOT_MESSAGE, self.SYSTEM_MESSAGE]


class ConversationState(Enum):
    """
    Enumeration tracking the current phase of a conversation.
    
    This enum manages the conversation flow and ensures proper sequencing
    of different phases in the competency assessment process.
    
    Attributes:
        INITIALIZING: Setting up the conversation and initial parameters
        MODE_SELECTION: User selecting assessment mode or preferences
        CONTEXT_GATHERING: Collecting background information from user
        COMPETENCY_DISCOVERY: Active discovery of skills and competencies
        VALIDATION: Validating and confirming discovered competencies
        MAPPING: Mapping competencies to framework standards
        REVIEW: Final review of results with user
        COMPLETED: Conversation has finished successfully
    """
    INITIALIZING = "initializing"
    MODE_SELECTION = "mode_selection"
    CONTEXT_GATHERING = "context_gathering"
    COMPETENCY_DISCOVERY = "competency_discovery"
    VALIDATION = "validation"
    MAPPING = "mapping"
    REVIEW = "review"
    COMPLETED = "completed"
    
    def __str__(self) -> str:
        """Return the string representation of the conversation state."""
        return self.value.replace("_", " ").title()
    
    @property
    def is_active(self) -> bool:
        """
        Check if the conversation is in an active state.
        
        Returns:
            bool: True if conversation is ongoing, False if completed
        """
        return self != self.COMPLETED
    
    @property
    def is_assessment_phase(self) -> bool:
        """
        Check if the conversation is in the main assessment phase.
        
        Returns:
            bool: True if in competency discovery or validation, False otherwise
        """
        return self in [self.COMPETENCY_DISCOVERY, self.VALIDATION]
    
    def get_next_state(self) -> 'ConversationState':
        """
        Get the next logical state in the conversation flow.
        
        Returns:
            ConversationState: The next state in the typical flow
            
        Raises:
            ValueError: If already in completed state
        """
        state_flow = [
            self.INITIALIZING,
            self.MODE_SELECTION,
            self.CONTEXT_GATHERING,
            self.COMPETENCY_DISCOVERY,
            self.VALIDATION,
            self.MAPPING,
            self.REVIEW,
            self.COMPLETED
        ]
        
        if self == self.COMPLETED:
            raise ValueError("Cannot transition from completed state")
        
        current_index = state_flow.index(self)
        return state_flow[current_index + 1]
    
    @classmethod
    def get_initial_state(cls) -> 'ConversationState':
        """
        Get the initial state for a new conversation.
        
        Returns:
            ConversationState: The starting state for conversations
        """
        return cls.INITIALIZING


class EvidenceType(Enum):
    """
    Enumeration categorizing different types of evidence for skills.
    
    This enum helps classify the sources and types of evidence that
    support skill claims and competency assessments.
    
    Attributes:
        CONVERSATION_EXTRACT: Evidence extracted from conversation text
        DOCUMENT_UPLOAD: Evidence from uploaded documents or certificates
        SELF_ASSESSMENT: Evidence from user's self-reported assessments
        PEER_VALIDATION: Evidence from peer reviews or endorsements
        PROJECT_DEMONSTRATION: Evidence from demonstrated projects or work
        FORMAL_CERTIFICATION: Evidence from formal certifications or credentials
    """
    CONVERSATION_EXTRACT = "conversation_extract"
    DOCUMENT_UPLOAD = "document_upload"
    SELF_ASSESSMENT = "self_assessment"
    PEER_VALIDATION = "peer_validation"
    PROJECT_DEMONSTRATION = "project_demonstration"
    FORMAL_CERTIFICATION = "formal_certification"
    
    def __str__(self) -> str:
        """Return the string representation of the evidence type."""
        return self.value.replace("_", " ").title()
    
    @property
    def reliability_score(self) -> float:
        """
        Get the relative reliability score for this evidence type.
        
        Returns:
            float: Reliability score between 0.0 and 1.0
        """
        reliability_mapping = {
            self.FORMAL_CERTIFICATION: 1.0,
            self.PROJECT_DEMONSTRATION: 0.9,
            self.PEER_VALIDATION: 0.8,
            self.DOCUMENT_UPLOAD: 0.7,
            self.CONVERSATION_EXTRACT: 0.6,
            self.SELF_ASSESSMENT: 0.5
        }
        return reliability_mapping[self]
    
    @property
    def requires_verification(self) -> bool:
        """
        Check if this evidence type typically requires additional verification.
        
        Returns:
            bool: True if verification is recommended, False otherwise
        """
        verification_required = [
            self.SELF_ASSESSMENT,
            self.CONVERSATION_EXTRACT
        ]
        return self in verification_required 