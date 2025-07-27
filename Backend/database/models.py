"""
SQLAlchemy database models for the competency assessment system.

This module defines the database schema using SQLAlchemy ORM models that map
to the domain entities. The models are designed to be database-agnostic and
support the full functionality of the domain layer while maintaining proper
relationships and constraints.

Models:
    BaseModel: Abstract base class with common fields
    UserModel: User accounts and authentication
    ProfileModel: User profile information
    SkillModel: Individual skills and competencies
    EvidenceModel: Supporting evidence for skills
    AssessmentModel: Competency assessment sessions
    ConversationModel: Chat conversations within assessments
    MessageModel: Individual messages in conversations
    MappedCompetencyModel: Framework-mapped competencies
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, Boolean, Enum as SQLEnum,
    ForeignKey, Table, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy import String as SQLString

from ..enums import (
    UserRole, ProficiencyLevel, AssessmentStatus, MessageType,
    ConversationState, EvidenceType
)


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses
    CHAR(36) to store string representation of UUIDs.
    """
    impl = CHAR
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


# Create the declarative base
Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model with common fields and functionality.
    
    This base class provides common fields that are used across multiple
    models, such as ID, creation timestamp, and update timestamp. It also
    provides utility methods for converting to domain objects.
    
    Attributes:
        id: Primary key using UUID
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    
    __abstract__ = True
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            elif hasattr(value, 'value'):  # Handle enums
                result[column.name] = value.value
            else:
                result[column.name] = value
        return result


class UserModel(BaseModel):
    """
    SQLAlchemy model for User entity.
    
    Maps to the User domain model and stores user account information,
    authentication data, and relationships to other entities.
    
    Attributes:
        email: User's email address (unique)
        password_hash: Hashed password for authentication
        role: User's system role
        last_login: Timestamp of last login
        is_active: Whether the user account is active
        profile: Related profile information (one-to-one)
        assessments: Related assessments (one-to-many)
    """
    
    __tablename__ = 'users'
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    profile = relationship("ProfileModel", back_populates="user", uselist=False)
    assessments = relationship("AssessmentModel", back_populates="user", 
                             cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserModel(id={self.id}, email={self.email}, role={self.role})>"


class ProfileModel(BaseModel):
    """
    SQLAlchemy model for Profile entity.
    
    Stores detailed user profile information including personal details
    and skills collection.
    
    Attributes:
        user_id: Foreign key to user
        first_name: User's first name
        last_name: User's last name
        preferred_language: User's preferred language code
        volunteering_background: Text description of volunteering experience
        user: Related user (many-to-one)
        skills: Related skills (one-to-many)
    """
    
    __tablename__ = 'profiles'
    
    user_id = Column(GUID(), ForeignKey('users.id'), nullable=False, unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    preferred_language = Column(String(10), default='en', nullable=False)
    volunteering_background = Column(Text, default='')
    
    # Relationships
    user = relationship("UserModel", back_populates="profile")
    skills = relationship("SkillModel", back_populates="profile", 
                         cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ProfileModel(id={self.id}, name={self.first_name} {self.last_name})>"


class SkillModel(BaseModel):
    """
    SQLAlchemy model for Skill entity.
    
    Represents individual skills and competencies with proficiency levels
    and framework linkages.
    
    Attributes:
        profile_id: Foreign key to profile
        name: Skill name
        description: Detailed skill description
        level: Proficiency level
        framework_source: Source framework name
        framework_id: ID within source framework
        acquired_date: When skill was acquired
        profile: Related profile (many-to-one)
        evidences: Related evidence items (one-to-many)
    """
    
    __tablename__ = 'skills'
    
    profile_id = Column(GUID(), ForeignKey('profiles.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default='')
    level = Column(SQLEnum(ProficiencyLevel), nullable=False, default=ProficiencyLevel.BEGINNER)
    framework_source = Column(String(100), default='')
    framework_id = Column(String(100), default='')
    acquired_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    profile = relationship("ProfileModel", back_populates="skills")
    evidences = relationship("EvidenceModel", back_populates="skill", 
                           cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SkillModel(id={self.id}, name={self.name}, level={self.level})>"


class EvidenceModel(BaseModel):
    """
    SQLAlchemy model for Evidence entity.
    
    Stores supporting evidence for skills with various evidence types
    and metadata.
    
    Attributes:
        skill_id: Foreign key to skill
        description: Evidence description
        date: Evidence date
        conversation_id: Related conversation ID (optional)
        type: Evidence type
        extracted_text: Raw extracted text
        metadata: Additional metadata as JSON
        skill: Related skill (many-to-one)
    """
    
    __tablename__ = 'evidences'
    
    skill_id = Column(GUID(), ForeignKey('skills.id'), nullable=False)
    description = Column(Text, nullable=False)
    date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    conversation_id = Column(GUID(), nullable=True)
    type = Column(SQLEnum(EvidenceType), nullable=False, default=EvidenceType.CONVERSATION_EXTRACT)
    extracted_text = Column(Text, default='')
    metadata = Column(JSON, default=dict)
    
    # Relationships
    skill = relationship("SkillModel", back_populates="evidences")
    
    def __repr__(self):
        return f"<EvidenceModel(id={self.id}, type={self.type}, skill_id={self.skill_id})>"


class AssessmentModel(BaseModel):
    """
    SQLAlchemy model for Assessment entity.
    
    Represents competency assessment sessions with status tracking
    and results.
    
    Attributes:
        user_id: Foreign key to user
        framework_name: Name of competency framework used
        status: Current assessment status
        started_at: When assessment was started
        completed_at: When assessment was completed
        user: Related user (many-to-one)
        conversation: Related conversation (one-to-one)
        mapped_competencies: Related mapped competencies (one-to-many)
    """
    
    __tablename__ = 'assessments'
    
    user_id = Column(GUID(), ForeignKey('users.id'), nullable=False)
    framework_name = Column(String(100), nullable=True)
    status = Column(SQLEnum(AssessmentStatus), nullable=False, default=AssessmentStatus.NOT_STARTED)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("UserModel", back_populates="assessments")
    conversation = relationship("ConversationModel", back_populates="assessment", uselist=False)
    mapped_competencies = relationship("MappedCompetencyModel", back_populates="assessment",
                                     cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AssessmentModel(id={self.id}, status={self.status}, user_id={self.user_id})>"


class ConversationModel(BaseModel):
    """
    SQLAlchemy model for Conversation entity.
    
    Stores conversation data for chat-based assessments including
    state management and messages.
    
    Attributes:
        assessment_id: Foreign key to assessment
        state: Current conversation state
        current_phase: Human-readable current phase
        metadata: Additional conversation metadata as JSON
        assessment: Related assessment (many-to-one)
        messages: Related messages (one-to-many)
    """
    
    __tablename__ = 'conversations'
    
    assessment_id = Column(GUID(), ForeignKey('assessments.id'), nullable=False, unique=True)
    state = Column(SQLEnum(ConversationState), nullable=False, default=ConversationState.INITIALIZING)
    current_phase = Column(String(100), default='Initializing conversation')
    metadata = Column(JSON, default=dict)
    
    # Relationships
    assessment = relationship("AssessmentModel", back_populates="conversation")
    messages = relationship("MessageModel", back_populates="conversation",
                          cascade="all, delete-orphan", order_by="MessageModel.created_at")
    
    def __repr__(self):
        return f"<ConversationModel(id={self.id}, state={self.state})>"


class MessageModel(BaseModel):
    """
    SQLAlchemy model for Message entity.
    
    Stores individual messages within conversations with type
    classification and metadata.
    
    Attributes:
        conversation_id: Foreign key to conversation
        type: Message type (user, bot, system)
        content: Message text content
        sender: Message sender identifier
        metadata: Additional message metadata as JSON
        conversation: Related conversation (many-to-one)
    """
    
    __tablename__ = 'messages'
    
    conversation_id = Column(GUID(), ForeignKey('conversations.id'), nullable=False)
    type = Column(SQLEnum(MessageType), nullable=False, default=MessageType.USER_MESSAGE)
    content = Column(Text, nullable=False)
    sender = Column(String(100), nullable=False)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    conversation = relationship("ConversationModel", back_populates="messages")
    
    def __repr__(self):
        return f"<MessageModel(id={self.id}, type={self.type}, sender={self.sender})>"


class MappedCompetencyModel(BaseModel):
    """
    SQLAlchemy model for MappedCompetency entity.
    
    Stores mappings between discovered competencies and framework
    standards with confidence scores and evidence links.
    
    Attributes:
        assessment_id: Foreign key to assessment
        competency_id: Framework competency ID
        competency_name: Framework competency name
        confidence_score: Mapping confidence (0.0 to 1.0)
        framework_source: Source framework name
        supporting_evidence: Evidence IDs as JSON array
        metadata: Additional mapping metadata as JSON
        assessment: Related assessment (many-to-one)
    """
    
    __tablename__ = 'mapped_competencies'
    
    assessment_id = Column(GUID(), ForeignKey('assessments.id'), nullable=False)
    competency_id = Column(String(100), nullable=False)
    competency_name = Column(String(200), nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.0)
    framework_source = Column(String(100), nullable=False)
    supporting_evidence = Column(JSON, default=list)  # List of evidence IDs
    metadata = Column(JSON, default=dict)
    
    # Relationships
    assessment = relationship("AssessmentModel", back_populates="mapped_competencies")
    
    def __repr__(self):
        return f"<MappedCompetencyModel(id={self.id}, competency={self.competency_name}, confidence={self.confidence_score})>"


# Association tables for many-to-many relationships (if needed in future)

# Example: Skills can be associated with multiple frameworks
skill_framework_association = Table(
    'skill_framework_associations',
    Base.metadata,
    Column('skill_id', GUID(), ForeignKey('skills.id'), primary_key=True),
    Column('framework_competency_id', String(100), primary_key=True),
    Column('framework_name', String(100), primary_key=True),
    Column('confidence_score', Float, default=0.0),
    Column('created_at', DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
)


# Database utility functions

def create_all_tables(engine):
    """
    Create all database tables.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine):
    """
    Drop all database tables.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.drop_all(bind=engine)


def get_table_names():
    """
    Get list of all table names.
    
    Returns:
        List[str]: List of table names
    """
    return list(Base.metadata.tables.keys())


def get_model_by_tablename(tablename: str):
    """
    Get model class by table name.
    
    Args:
        tablename: Name of the database table
        
    Returns:
        Model class or None if not found
    """
    for mapper in Base.registry.mappers:
        model = mapper.class_
        if hasattr(model, '__tablename__') and model.__tablename__ == tablename:
            return model
    return None 