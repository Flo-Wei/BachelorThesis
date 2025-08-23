from enum import Enum
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Literal, TYPE_CHECKING
from datetime import datetime
from openai.types.responses.response import Response as OpenAIResponse

if TYPE_CHECKING:
    from Backend.database.models.users import User
    from Backend.database.models.skills import ESCOSkillModel


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_session"
    
    session_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.user_id", index=True)
    session_name: Optional[str] = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    user: "User" = Relationship(back_populates="chat_sessions")
    chat_messages: List["ChatMessage"] = Relationship(back_populates="chat_session")
    esco_skills: List["ESCOSkillModel"] = Relationship(back_populates="chat_session")

    # Methods
    def __str__(self):
        return f"ChatSession(session_id={self.session_id}, user_id={self.user_id}, session_name={self.session_name})"
    
    def __repr__(self):
        return f"ChatSession(session_id={self.session_id}, user_id={self.user_id}, session_name={self.session_name}, created_at={self.created_at})"

    def add_message(self, session, message: "ChatMessage") -> None:
        """Add a message to this chat session and persist to database"""
        message.session_id = self.session_id
        session.add(message)
        self.updated_at = datetime.now()
        session.add(self)  # Update the session's updated_at timestamp
        session.commit()
        session.refresh(message)
        session.refresh(self)  # Refresh the session to update relationships

    def get_messages(self, role: MessageType | Literal["all"] = "all") -> List["ChatMessage"]:
        """Get messages filtered by role from loaded relationship"""
        if role == "all":
            return sorted(self.chat_messages, key=lambda x: x.timestamp)
        else:
            return sorted(
                [message for message in self.chat_messages if message.role == role],
                key=lambda x: x.timestamp
            )

    def get_last_message(self, role: MessageType | Literal["all"] = "all") -> Optional["ChatMessage"]:
        """Get the last message filtered by role from loaded relationship"""
        messages = self.get_messages(role)
        return messages[-1] if messages else None

    def get_total_usage(self) -> int:
        """Get total token usage for this session from loaded relationship"""
        return sum(message.usage for message in self.chat_messages if message.usage)
    
    def to_openai_input(self) -> List[dict]:
        """Convert session messages to OpenAI API input format"""
        messages = self.get_messages("all")
        return [
            {
                "role": message.role.value,  # Convert enum to string
                "content": message.message_content  # Simple string format
            }
            for message in messages
        ]


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"
    
    message_id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_session.session_id", index=True)
    role: MessageType = Field(index=True)
    message_content: str
    usage: int = Field(default=0)
    model: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    
    # Relationships
    chat_session: "ChatSession" = Relationship(back_populates="chat_messages")
    derived_skills_esco: List["ESCOSkillModel"] = Relationship(back_populates="origin_message")

    # Methods
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} {self.role}: {self.message_content}"
    
    def __repr__(self):
        return f"ChatMessage(role={self.role}, message_content={self.message_content}, timestamp={self.timestamp})"

    @classmethod
    def from_openai_message(cls,session: "ChatSession", message: OpenAIResponse):
        return cls(
            session_id=session.session_id,
            role=message.output[0].role,
            message_content=message.output[0].content[0].text, # TODO: reasoning models don work yet because of multiple content objects
            timestamp=datetime.fromtimestamp(message.created_at),
            usage=message.usage.total_tokens,
            model=message.model,
        )

