"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str


# Chat session schemas
class ChatSessionCreate(BaseModel):
    session_name: Optional[str] = None


class ChatSessionResponse(BaseModel):
    session_id: int
    user_id: int
    session_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Message schemas
class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    message_id: int
    session_id: int
    role: str
    message_content: str
    usage: int
    model: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Chat request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None  # If None, create new session


class ChatResponse(BaseModel):
    message: MessageResponse
    assistant_response: MessageResponse
    session_id: int


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# Skills schemas
from Backend.database.models.skills import SkillSystem

class SkillResponse(BaseModel):
    id: int
    skill_system: SkillSystem
    uri: str
    title: str
    reference_language: str
    preferred_label: Dict[str, str]
    description: Dict[str, str]
    links: Dict[str, Any]
    origin_message_id: int
    session_id: int
    
    class Config:
        from_attributes = True


class ChatSessionWithSkillsResponse(ChatSessionResponse):
    esco_skills: List[SkillResponse] = []
    
    class Config:
        from_attributes = True
