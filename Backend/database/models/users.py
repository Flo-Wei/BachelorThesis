from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from Backend.database.models.messages import ChatSession


class User(SQLModel, table=True):
    __tablename__ = "user"
    
    user_id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=100, unique=True, index=True)
    email: str = Field(max_length=255, unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")