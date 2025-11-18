from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from Backend.classes.Skill_Classes import ESCOSkill, BaseSkill, CustomSkill

if TYPE_CHECKING:
    from Backend.database.models.messages import ChatMessage, ChatSession

class SkillSystem(str, Enum):
    CUSTOM = "CUSTOM"
    ESCO = "ESCO"
    # FREIWILLIGENPASS = "Freiwilligenpass"

class SkillType(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    DOMAIN_SPECIFIC = "domain-specific"
    OTHER = "other"

class ChatSkillBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_session.session_id", index=True)
    origin_message_id: int = Field(foreign_key="chat_message.message_id", index=True)
    skill_system: SkillSystem = Field(index=True)

    @classmethod
    def from_pydantic(cls, skill: BaseSkill) -> "ChatSkillBase":
        pass

class CustomSkillModel(SQLModel, table=True):
    __tablename__ = "custom_skill"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_session.session_id", index=True)
    origin_message_id: int = Field(foreign_key="chat_message.message_id", index=True)
    name: str = Field(max_length=255)
    type: SkillType = Field(index=True)
    confidence: float = Field(ge=0, le=1)
    evidence: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    chat_session: "ChatSession" = Relationship(back_populates="custom_skills")
    origin_message: "ChatMessage" = Relationship(back_populates="derived_skills_custom")
    esco_skill: Optional["ESCOSkillModel"] = Relationship(
        back_populates="custom_skill",
        sa_relationship_kwargs={"uselist": False}
    )
    
    # Methods
    def __repr__(self) -> str:
        return self.name
    
    def __str__(self) -> str:
        return self.name
    
    @classmethod
    def from_pydantic(cls, skill: CustomSkill, session_id: int, origin_message_id: int) -> "CustomSkillModel":
        # Convert string type to SkillType enum
        skill_type = SkillType(skill.type)
        return cls(
            session_id=session_id,
            origin_message_id=origin_message_id,
            name=skill.name,
            type=skill_type,
            confidence=skill.confidence,
            evidence=skill.evidence
        )

class ESCOSkillModel(SQLModel, table=True):
    __tablename__ = "esco_skill"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_session.session_id", index=True)
    custom_skill_id: int = Field(foreign_key="custom_skill.id", unique=True, index=True)
    skill_system: SkillSystem = Field(default=SkillSystem.ESCO, index=True)
    
    uri: str = Field(max_length=255)
    title: str = Field(max_length=255)
    reference_language: str = Field(max_length=255)
    preferred_label: Dict[str, str] = Field(sa_column=Column(JSON))
    description: Dict[str, str] = Field(sa_column=Column(JSON))
    links: Dict[str, Any] = Field(sa_column=Column(JSON))
    evidence: Optional[str] = Field(default=None)
    
    # Relationships
    chat_session: "ChatSession" = Relationship(back_populates="esco_skills")
    custom_skill: "CustomSkillModel" = Relationship(
        back_populates="esco_skill",
        sa_relationship_kwargs={"uselist": False}
    )
    
    # Methods
    def __repr__(self) -> str:
        return self.title
    
    def __str__(self) -> str:
        return self.title
    
    def get_preferred_label(self, language: str) -> str:
        """Get the preferred label for a specific language, fallback to title if not available"""
        return self.preferred_label.get(language, self.title)
    
    def get_description(self, language: str) -> str:
        """Get the description for a specific language, fallback to default message if not available"""
        return self.description.get(language, "No description available")
    
    @classmethod
    def from_pydantic(cls, skill: ESCOSkill, custom_skill_id: Optional[int] = None, session_id: Optional[int] = None, evidence: Optional[str] = None) -> "ESCOSkillModel":
        return cls(
            session_id=session_id or 0,  # Will be set later if None
            custom_skill_id=custom_skill_id or 0,  # Will be set later if None
            uri=skill.uri,
            title=skill.title,
            reference_language=skill.reference_language,
            preferred_label=skill.preferred_label,
            description=skill.description,
            links=skill.links,
            evidence=evidence
        )