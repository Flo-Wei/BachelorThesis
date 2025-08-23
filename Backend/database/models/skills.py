from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from Backend.database.models.messages import ChatMessage, ChatSession

class SkillSystem(str, Enum):
    ESCO = "ESCO"
    FREIWILLIGENPASS = "Freiwilligenpass"

class ChatSkillBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_session.session_id", index=True)
    origin_message_id: int = Field(foreign_key="chat_message.message_id", index=True)
    skill_system: SkillSystem = Field(index=True)

class ESCOSkill(ChatSkillBase, table=True):
    __tablename__ = "esco_skill"
    
    uri: str = Field(max_length=255)
    title: str = Field(max_length=255)
    reference_language: str = Field(max_length=255)
    preferred_label: Dict[str, str] = Field(sa_column=Column(JSON))
    description: Dict[str, str] = Field(sa_column=Column(JSON))
    links: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    skill_system: SkillSystem = Field(default=SkillSystem.ESCO, index=True)
    
    # Relationships
    chat_session: "ChatSession" = Relationship(back_populates="esco_skills")
    origin_message: "ChatMessage" = Relationship(back_populates="derived_skills_esco")
    
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