"""
Core domain models for the competency assessment system.

This module contains all the core business entities that represent the main
concepts in the competency assessment domain. These classes form the backbone
of the system and define the structure and behavior of key business objects.

Classes:
    User: Represents a system user with authentication and profile information
    Profile: Contains detailed user profile information and skills
    Skill: Represents a specific competency or skill with evidence
    Evidence: Documents supporting evidence for skills
    Assessment: Represents a competency assessment session
    Conversation: Contains the conversational interaction data
    Message: Individual messages within conversations
    MappedCompetency: Links discovered competencies to framework standards
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from ..enums import (
    UserRole, ProficiencyLevel, AssessmentStatus, MessageType, 
    ConversationState, EvidenceType
)


@dataclass
class User:
    """
    Represents a system user with authentication and profile management capabilities.
    
    The User class is the central entity for authentication and authorization,
    containing all necessary information for user management, security, and
    access to the competency assessment system.
    
    Attributes:
        id: Unique identifier for the user
        email: User's email address used for authentication
        password_hash: Securely hashed password for authentication
        role: User's role determining system permissions
        profile: Detailed profile information (can be None for new users)
        assessments: List of completed assessments
        created_at: Timestamp when the user account was created
        last_login: Timestamp of the user's last login (None if never logged in)
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    password_hash: str = ""
    role: UserRole = UserRole.USER
    profile: Optional['Profile'] = None
    assessments: List['Assessment'] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.email:
            raise ValueError("Email is required for user creation")
        if not self.password_hash:
            raise ValueError("Password hash is required for user creation")
    
    def login(self) -> bool:
        """
        Perform user login operation.
        
        Updates the last_login timestamp and performs any necessary
        login-related operations.
        
        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            self.last_login = datetime.now(timezone.utc)
            return True
        except Exception:
            return False
    
    def logout(self) -> bool:
        """
        Perform user logout operation.
        
        Cleans up any active sessions and performs logout-related operations.
        
        Returns:
            bool: True if logout was successful, False otherwise
        """
        # In a real implementation, this would clean up sessions, tokens, etc.
        return True
    
    def update_profile(self, profile_data: Dict[str, Any]) -> bool:
        """
        Update the user's profile information.
        
        Args:
            profile_data: Dictionary containing profile update information
            
        Returns:
            bool: True if profile was successfully updated, False otherwise
        """
        try:
            if self.profile is None:
                self.profile = Profile(user_id=self.id)
            
            # Update profile fields based on provided data
            for field_name, value in profile_data.items():
                if hasattr(self.profile, field_name):
                    setattr(self.profile, field_name, value)
            
            return True
        except Exception:
            return False
    
    def get_assessments(self, status: Optional[AssessmentStatus] = None) -> List['Assessment']:
        """
        Retrieve user's assessments, optionally filtered by status.
        
        Args:
            status: Optional status filter for assessments
            
        Returns:
            List[Assessment]: List of matching assessments
        """
        if status is None:
            return self.assessments.copy()
        
        return [assessment for assessment in self.assessments if assessment.status == status]
    
    def add_assessment(self, assessment: 'Assessment') -> bool:
        """
        Add a new assessment to the user's assessment list.
        
        Args:
            assessment: Assessment instance to add
            
        Returns:
            bool: True if assessment was added successfully, False otherwise
        """
        try:
            if assessment.user_id != self.id:
                raise ValueError("Assessment user_id must match current user")
            
            self.assessments.append(assessment)
            return True
        except Exception:
            return False
    
    @property
    def is_admin(self) -> bool:
        """Check if user has administrative privileges."""
        return self.role in UserRole.get_admin_roles()
    
    @property
    def has_profile(self) -> bool:
        """Check if user has a complete profile."""
        return self.profile is not None and self.profile.is_complete
    
    def __str__(self) -> str:
        """Return string representation of the user."""
        return f"User(id={self.id}, email={self.email}, role={self.role})"


@dataclass
class Profile:
    """
    Contains detailed user profile information including skills and background.
    
    The Profile class stores comprehensive information about a user including
    personal details, skills, and background information relevant to competency
    assessment and professional development.
    
    Attributes:
        user_id: Reference to the associated user
        first_name: User's first name
        last_name: User's last name
        preferred_language: User's preferred language for interface and content
        skills: List of user's skills and competencies
        volunteering_background: Description of user's volunteering experience
    """
    
    user_id: str
    first_name: str = ""
    last_name: str = ""
    preferred_language: str = "en"
    skills: List['Skill'] = field(default_factory=list)
    volunteering_background: str = ""
    
    def update_skills(self, new_skills: List['Skill']) -> bool:
        """
        Update the user's skills list.
        
        Args:
            new_skills: List of new skill objects to replace existing skills
            
        Returns:
            bool: True if skills were updated successfully, False otherwise
        """
        try:
            # Validate that all skills belong to this user
            for skill in new_skills:
                if not hasattr(skill, 'user_id') or skill.user_id != self.user_id:
                    skill.user_id = self.user_id
            
            self.skills = new_skills
            return True
        except Exception:
            return False
    
    def add_skill(self, skill: 'Skill') -> bool:
        """
        Add a new skill to the user's profile.
        
        Args:
            skill: Skill object to add
            
        Returns:
            bool: True if skill was added successfully, False otherwise
        """
        try:
            # Ensure skill belongs to this user
            skill.user_id = self.user_id
            
            # Check for duplicates based on skill name and framework
            existing_skill = self.find_skill_by_name(skill.name)
            if existing_skill:
                # Update existing skill instead of creating duplicate
                existing_skill.level = skill.level
                existing_skill.description = skill.description
                return True
            
            self.skills.append(skill)
            return True
        except Exception:
            return False
    
    def find_skill_by_name(self, skill_name: str) -> Optional['Skill']:
        """
        Find a skill by name in the user's skills list.
        
        Args:
            skill_name: Name of the skill to find
            
        Returns:
            Optional[Skill]: The skill if found, None otherwise
        """
        for skill in self.skills:
            if skill.name.lower() == skill_name.lower():
                return skill
        return None
    
    def get_skills_by_level(self, level: ProficiencyLevel) -> List['Skill']:
        """
        Get all skills matching a specific proficiency level.
        
        Args:
            level: Proficiency level to filter by
            
        Returns:
            List[Skill]: List of skills at the specified level
        """
        return [skill for skill in self.skills if skill.level == level]
    
    def export_profile(self) -> Dict[str, Any]:
        """
        Export profile data to a dictionary format.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the profile
        """
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "preferred_language": self.preferred_language,
            "volunteering_background": self.volunteering_background,
            "skills": [
                {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "level": skill.level.value,
                    "framework_source": skill.framework_source,
                    "framework_id": skill.framework_id,
                    "acquired_date": skill.acquired_date.isoformat() if skill.acquired_date else None,
                    "evidence_count": len(skill.evidences)
                }
                for skill in self.skills
            ]
        }
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_complete(self) -> bool:
        """Check if the profile has minimum required information."""
        return bool(self.first_name and self.last_name)
    
    @property
    def skill_count(self) -> int:
        """Get the total number of skills in the profile."""
        return len(self.skills)
    
    def __str__(self) -> str:
        """Return string representation of the profile."""
        return f"Profile(user_id={self.user_id}, name={self.full_name}, skills={self.skill_count})"


@dataclass
class Skill:
    """
    Represents a specific competency or skill with associated evidence and metadata.
    
    The Skill class captures individual competencies that a user possesses,
    including proficiency level, supporting evidence, and links to competency
    frameworks for standardized assessment and comparison.
    
    Attributes:
        id: Unique identifier for the skill
        name: Human-readable name of the skill
        description: Detailed description of the skill
        level: Current proficiency level for this skill
        framework_source: Source framework (e.g., "ESCO", "Freiwilligenpass")
        framework_id: Identifier within the source framework
        evidences: List of supporting evidence for this skill
        acquired_date: Date when the skill was first acquired or recognized
        user_id: Reference to the user who possesses this skill
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    level: ProficiencyLevel = ProficiencyLevel.BEGINNER
    framework_source: str = ""
    framework_id: str = ""
    evidences: List['Evidence'] = field(default_factory=list)
    acquired_date: Optional[datetime] = None
    user_id: str = ""
    
    def __post_init__(self):
        """Validate skill data after initialization."""
        if not self.name:
            raise ValueError("Skill name is required")
        if not self.user_id:
            raise ValueError("User ID is required for skill")
    
    def validate(self) -> bool:
        """
        Validate the skill data for completeness and consistency.
        
        Returns:
            bool: True if skill data is valid, False otherwise
        """
        try:
            # Check required fields
            if not self.name or not self.user_id:
                return False
            
            # Validate evidence consistency
            for evidence in self.evidences:
                if evidence.skill_id != self.id:
                    return False
            
            # Validate framework reference if provided
            if self.framework_source and not self.framework_id:
                return False
            
            return True
        except Exception:
            return False
    
    def update_level(self, new_level: ProficiencyLevel, evidence: Optional['Evidence'] = None) -> bool:
        """
        Update the proficiency level for this skill.
        
        Args:
            new_level: New proficiency level to set
            evidence: Optional evidence supporting the level change
            
        Returns:
            bool: True if level was updated successfully, False otherwise
        """
        try:
            old_level = self.level
            self.level = new_level
            
            # Add evidence if provided
            if evidence:
                evidence.skill_id = self.id
                evidence.description = f"Level updated from {old_level.value} to {new_level.value}"
                self.evidences.append(evidence)
            
            return True
        except Exception:
            self.level = old_level  # Rollback on error
            return False
    
    def add_evidence(self, evidence: 'Evidence') -> bool:
        """
        Add supporting evidence for this skill.
        
        Args:
            evidence: Evidence object to add
            
        Returns:
            bool: True if evidence was added successfully, False otherwise
        """
        try:
            evidence.skill_id = self.id
            self.evidences.append(evidence)
            return True
        except Exception:
            return False
    
    def get_evidence_by_type(self, evidence_type: EvidenceType) -> List['Evidence']:
        """
        Get all evidence of a specific type for this skill.
        
        Args:
            evidence_type: Type of evidence to filter by
            
        Returns:
            List[Evidence]: List of matching evidence
        """
        return [evidence for evidence in self.evidences if evidence.type == evidence_type]
    
    @property
    def evidence_strength(self) -> float:
        """
        Calculate the overall evidence strength for this skill.
        
        Returns:
            float: Evidence strength score between 0.0 and 1.0
        """
        if not self.evidences:
            return 0.0
        
        total_score = sum(evidence.type.reliability_score for evidence in self.evidences)
        max_possible_score = len(self.evidences) * 1.0  # Maximum reliability is 1.0
        
        return min(total_score / max_possible_score, 1.0)
    
    @property
    def is_framework_linked(self) -> bool:
        """Check if skill is linked to a competency framework."""
        return bool(self.framework_source and self.framework_id)
    
    def __str__(self) -> str:
        """Return string representation of the skill."""
        return f"Skill(id={self.id}, name={self.name}, level={self.level})"


@dataclass
class Evidence:
    """
    Documents supporting evidence for skills and competencies.
    
    The Evidence class captures various types of supporting documentation
    and information that validate a user's claimed skills and competencies.
    Evidence can come from conversations, documents, certifications, or other sources.
    
    Attributes:
        id: Unique identifier for the evidence
        description: Human-readable description of the evidence
        date: Date when the evidence was created or occurred
        conversation_id: Reference to conversation where evidence was extracted (if applicable)
        type: Category of evidence (conversation, document, certification, etc.)
        extracted_text: Raw text content extracted for this evidence
        skill_id: Reference to the skill this evidence supports
        metadata: Additional metadata specific to the evidence type
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    conversation_id: Optional[str] = None
    type: EvidenceType = EvidenceType.CONVERSATION_EXTRACT
    extracted_text: str = ""
    skill_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate evidence data after initialization."""
        if not self.description and not self.extracted_text:
            raise ValueError("Either description or extracted_text is required")
        if not self.skill_id:
            raise ValueError("Skill ID is required for evidence")
    
    @property
    def requires_verification(self) -> bool:
        """Check if this evidence requires additional verification."""
        return self.type.requires_verification
    
    @property
    def reliability_score(self) -> float:
        """Get the reliability score for this evidence."""
        return self.type.reliability_score
    
    @property
    def is_conversation_based(self) -> bool:
        """Check if evidence was extracted from a conversation."""
        return self.conversation_id is not None
    
    def update_metadata(self, new_metadata: Dict[str, Any]) -> bool:
        """
        Update the evidence metadata.
        
        Args:
            new_metadata: Dictionary of metadata to update
            
        Returns:
            bool: True if metadata was updated successfully, False otherwise
        """
        try:
            self.metadata.update(new_metadata)
            return True
        except Exception:
            return False
    
    def __str__(self) -> str:
        """Return string representation of the evidence."""
        return f"Evidence(id={self.id}, type={self.type}, skill_id={self.skill_id})"


@dataclass
class Assessment:
    """
    Represents a competency assessment session with conversation and results.
    
    The Assessment class manages the entire assessment process, from initiation
    through completion, including the conversational interaction, competency
    mapping, and result generation.
    
    Attributes:
        id: Unique identifier for the assessment
        user_id: Reference to the user taking the assessment
        framework: Competency framework used for mapping (can be None initially)
        status: Current status of the assessment
        started_at: Timestamp when assessment was started
        completed_at: Timestamp when assessment was completed (None if not completed)
        conversation: Conversational interaction data
        mapped_competencies: List of competencies mapped during assessment
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    framework: Optional['CompetencyFramework'] = None
    status: AssessmentStatus = AssessmentStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    conversation: Optional['Conversation'] = None
    mapped_competencies: List['MappedCompetency'] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate assessment data after initialization."""
        if not self.user_id:
            raise ValueError("User ID is required for assessment")
    
    def start(self) -> bool:
        """
        Start the assessment process.
        
        Returns:
            bool: True if assessment was started successfully, False otherwise
        """
        try:
            if self.status != AssessmentStatus.NOT_STARTED:
                return False
            
            self.status = AssessmentStatus.IN_PROGRESS
            self.started_at = datetime.now(timezone.utc)
            
            # Initialize conversation
            if self.conversation is None:
                self.conversation = Conversation(assessment_id=self.id)
            
            return True
        except Exception:
            return False
    
    def pause(self) -> bool:
        """
        Pause the assessment process.
        
        Returns:
            bool: True if assessment was paused successfully, False otherwise
        """
        try:
            if self.status != AssessmentStatus.IN_PROGRESS:
                return False
            
            self.status = AssessmentStatus.PAUSED
            return True
        except Exception:
            return False
    
    def resume(self) -> bool:
        """
        Resume a paused assessment.
        
        Returns:
            bool: True if assessment was resumed successfully, False otherwise
        """
        try:
            if self.status != AssessmentStatus.PAUSED:
                return False
            
            self.status = AssessmentStatus.IN_PROGRESS
            return True
        except Exception:
            return False
    
    def complete(self) -> bool:
        """
        Complete the assessment process.
        
        Returns:
            bool: True if assessment was completed successfully, False otherwise
        """
        try:
            if self.status not in [AssessmentStatus.IN_PROGRESS, AssessmentStatus.PAUSED]:
                return False
            
            self.status = AssessmentStatus.COMPLETED
            self.completed_at = datetime.now(timezone.utc)
            
            # Finalize conversation
            if self.conversation:
                self.conversation.state = ConversationState.COMPLETED
            
            return True
        except Exception:
            return False
    
    def add_mapped_competency(self, competency: 'MappedCompetency') -> bool:
        """
        Add a mapped competency to the assessment results.
        
        Args:
            competency: MappedCompetency object to add
            
        Returns:
            bool: True if competency was added successfully, False otherwise
        """
        try:
            competency.assessment_id = self.id
            self.mapped_competencies.append(competency)
            return True
        except Exception:
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive assessment report.
        
        Returns:
            Dict[str, Any]: Dictionary containing the assessment report
        """
        if self.status != AssessmentStatus.COMPLETED:
            raise ValueError("Cannot generate report for incomplete assessment")
        
        duration = None
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
        
        return {
            "assessment_id": self.id,
            "user_id": self.user_id,
            "framework": self.framework.get_name() if self.framework else None,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": duration,
            "mapped_competencies": [
                {
                    "competency_id": comp.competency_id,
                    "competency_name": comp.competency_name,
                    "confidence_score": comp.confidence_score,
                    "supporting_evidence_count": len(comp.supporting_evidence)
                }
                for comp in self.mapped_competencies
            ],
            "conversation_summary": {
                "message_count": len(self.conversation.messages) if self.conversation else 0,
                "final_state": self.conversation.state.value if self.conversation else None
            }
        }
    
    @property
    def duration(self) -> Optional[float]:
        """Get the assessment duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if the assessment is currently active."""
        return self.status.is_active
    
    @property
    def is_completed(self) -> bool:
        """Check if the assessment is completed."""
        return self.status.is_finished
    
    def __str__(self) -> str:
        """Return string representation of the assessment."""
        return f"Assessment(id={self.id}, user_id={self.user_id}, status={self.status})"


@dataclass
class Conversation:
    """
    Contains the conversational interaction data for an assessment.
    
    The Conversation class manages the back-and-forth dialogue between the user
    and the AI system during competency assessment, tracking conversation state,
    messages, and current phase progression.
    
    Attributes:
        id: Unique identifier for the conversation
        assessment_id: Reference to the parent assessment
        messages: List of messages in the conversation
        state: Current state/phase of the conversation
        current_phase: Human-readable description of current phase
        metadata: Additional conversation metadata
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assessment_id: str = ""
    messages: List['Message'] = field(default_factory=list)
    state: ConversationState = ConversationState.INITIALIZING
    current_phase: str = "Initializing conversation"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate conversation data after initialization."""
        if not self.assessment_id:
            raise ValueError("Assessment ID is required for conversation")
    
    def add_message(self, message: 'Message') -> bool:
        """
        Add a new message to the conversation.
        
        Args:
            message: Message object to add
            
        Returns:
            bool: True if message was added successfully, False otherwise
        """
        try:
            message.conversation_id = self.id
            self.messages.append(message)
            return True
        except Exception:
            return False
    
    def get_messages_by_type(self, message_type: MessageType) -> List['Message']:
        """
        Get all messages of a specific type.
        
        Args:
            message_type: Type of messages to retrieve
            
        Returns:
            List[Message]: List of matching messages
        """
        return [msg for msg in self.messages if msg.type == message_type]
    
    def get_user_messages(self) -> List['Message']:
        """Get all user messages in the conversation."""
        return self.get_messages_by_type(MessageType.USER_MESSAGE)
    
    def get_bot_messages(self) -> List['Message']:
        """Get all bot messages in the conversation."""
        return self.get_messages_by_type(MessageType.BOT_MESSAGE)
    
    def transition_to_next_state(self) -> bool:
        """
        Transition the conversation to the next logical state.
        
        Returns:
            bool: True if transition was successful, False otherwise
        """
        try:
            if self.state == ConversationState.COMPLETED:
                return False
            
            next_state = self.state.get_next_state()
            self.state = next_state
            self.current_phase = self._get_phase_description(next_state)
            return True
        except Exception:
            return False
    
    def _get_phase_description(self, state: ConversationState) -> str:
        """
        Get human-readable description for a conversation state.
        
        Args:
            state: Conversation state
            
        Returns:
            str: Human-readable phase description
        """
        descriptions = {
            ConversationState.INITIALIZING: "Initializing conversation",
            ConversationState.MODE_SELECTION: "Selecting assessment mode",
            ConversationState.CONTEXT_GATHERING: "Gathering background information",
            ConversationState.COMPETENCY_DISCOVERY: "Discovering competencies",
            ConversationState.VALIDATION: "Validating competencies",
            ConversationState.MAPPING: "Mapping to framework",
            ConversationState.REVIEW: "Reviewing results",
            ConversationState.COMPLETED: "Assessment completed"
        }
        return descriptions.get(state, "Unknown phase")
    
    @property
    def message_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return len(self.messages)
    
    @property
    def user_message_count(self) -> int:
        """Get the number of user messages in the conversation."""
        return len(self.get_user_messages())
    
    @property
    def is_active(self) -> bool:
        """Check if the conversation is still active."""
        return self.state.is_active
    
    @property
    def latest_message(self) -> Optional['Message']:
        """Get the most recent message in the conversation."""
        return self.messages[-1] if self.messages else None
    
    def __str__(self) -> str:
        """Return string representation of the conversation."""
        return f"Conversation(id={self.id}, state={self.state}, messages={self.message_count})"


@dataclass
class Message:
    """
    Individual messages within conversations.
    
    The Message class represents individual communication units in the
    conversation between users and the AI system, including metadata
    for proper processing and display.
    
    Attributes:
        id: Unique identifier for the message
        type: Type of message (user, bot, system)
        content: Text content of the message
        sender: Identifier of the message sender
        timestamp: When the message was created
        metadata: Additional message-specific metadata
        conversation_id: Reference to the parent conversation
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.USER_MESSAGE
    content: str = ""
    sender: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    conversation_id: str = ""
    
    def __post_init__(self):
        """Validate message data after initialization."""
        if not self.content:
            raise ValueError("Message content is required")
        if not self.conversation_id:
            raise ValueError("Conversation ID is required for message")
    
    @property
    def is_user_message(self) -> bool:
        """Check if this message was sent by a user."""
        return self.type.is_user_generated
    
    @property
    def is_automated(self) -> bool:
        """Check if this message was automatically generated."""
        return self.type.is_automated
    
    @property
    def word_count(self) -> int:
        """Get the word count of the message content."""
        return len(self.content.split())
    
    @property
    def character_count(self) -> int:
        """Get the character count of the message content."""
        return len(self.content)
    
    def add_metadata(self, key: str, value: Any) -> bool:
        """
        Add metadata to the message.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            bool: True if metadata was added successfully, False otherwise
        """
        try:
            self.metadata[key] = value
            return True
        except Exception:
            return False
    
    def __str__(self) -> str:
        """Return string representation of the message."""
        return f"Message(id={self.id}, type={self.type}, sender={self.sender})"


@dataclass
class MappedCompetency:
    """
    Links discovered competencies to framework standards.
    
    The MappedCompetency class represents the connection between competencies
    discovered during assessment and standardized competency frameworks,
    including confidence scores and supporting evidence.
    
    Attributes:
        id: Unique identifier for the mapped competency
        competency_id: Identifier from the competency framework
        competency_name: Human-readable name of the competency
        confidence_score: Confidence level of the mapping (0.0 to 1.0)
        supporting_evidence: List of evidence IDs that support this mapping
        assessment_id: Reference to the assessment that produced this mapping
        framework_source: Source framework for this competency
        metadata: Additional mapping-specific metadata
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    competency_id: str = ""
    competency_name: str = ""
    confidence_score: float = 0.0
    supporting_evidence: List[str] = field(default_factory=list)
    assessment_id: str = ""
    framework_source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate mapped competency data after initialization."""
        if not self.competency_id:
            raise ValueError("Competency ID is required")
        if not self.competency_name:
            raise ValueError("Competency name is required")
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
    
    def add_supporting_evidence(self, evidence_id: str) -> bool:
        """
        Add supporting evidence for this competency mapping.
        
        Args:
            evidence_id: Identifier of the supporting evidence
            
        Returns:
            bool: True if evidence was added successfully, False otherwise
        """
        try:
            if evidence_id not in self.supporting_evidence:
                self.supporting_evidence.append(evidence_id)
            return True
        except Exception:
            return False
    
    def remove_supporting_evidence(self, evidence_id: str) -> bool:
        """
        Remove supporting evidence from this competency mapping.
        
        Args:
            evidence_id: Identifier of the evidence to remove
            
        Returns:
            bool: True if evidence was removed successfully, False otherwise
        """
        try:
            if evidence_id in self.supporting_evidence:
                self.supporting_evidence.remove(evidence_id)
            return True
        except Exception:
            return False
    
    def update_confidence_score(self, new_score: float) -> bool:
        """
        Update the confidence score for this mapping.
        
        Args:
            new_score: New confidence score (0.0 to 1.0)
            
        Returns:
            bool: True if score was updated successfully, False otherwise
        """
        try:
            if not (0.0 <= new_score <= 1.0):
                raise ValueError("Confidence score must be between 0.0 and 1.0")
            
            self.confidence_score = new_score
            return True
        except Exception:
            return False
    
    @property
    def evidence_count(self) -> int:
        """Get the number of supporting evidence items."""
        return len(self.supporting_evidence)
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this mapping has high confidence (>= 0.8)."""
        return self.confidence_score >= 0.8
    
    @property
    def is_low_confidence(self) -> bool:
        """Check if this mapping has low confidence (< 0.5)."""
        return self.confidence_score < 0.5
    
    @property
    def confidence_level(self) -> str:
        """Get a human-readable confidence level description."""
        if self.confidence_score >= 0.8:
            return "High"
        elif self.confidence_score >= 0.6:
            return "Medium"
        elif self.confidence_score >= 0.4:
            return "Low"
        else:
            return "Very Low"
    
    def __str__(self) -> str:
        """Return string representation of the mapped competency."""
        return f"MappedCompetency(id={self.id}, name={self.competency_name}, confidence={self.confidence_score:.2f})"


# Forward reference resolution
from ..frameworks.base import CompetencyFramework 