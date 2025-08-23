from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict
import logging

from Backend.database.init import get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, ChatMessage
from Backend.database.models.skills import ESCOSkillModel, SkillSystem
from Backend.database.utils import create_chat_session
from Backend.schemas import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionWithSkillsResponse,
    MessageResponse, SkillResponse
)
from Backend.auth import get_current_user

router = APIRouter(tags=["sessions"])
logger = logging.getLogger(__name__)


@router.post("/users/{user_id}/sessions", response_model=ChatSessionResponse)
async def create_session(
    user_id: int, 
    session_data: ChatSessionCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency)
):
    """Create a new chat session for a user."""
    # Check if user is creating session for themselves
    if user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create session for other users"
        )
    
    try:
        session = create_chat_session(current_user, session_data.session_name)
        return session
    except Exception as e:
        logger.exception(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )


@router.get("/users/{user_id}/sessions", response_model=List[ChatSessionWithSkillsResponse])
async def get_user_sessions(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db_session_dependency)):
    """Get all chat sessions for a user with skills count."""
    # Check if user is accessing their own sessions
    if user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to other user's sessions"
        )
    
    sessions = db.exec(
        select(ChatSession).where(ChatSession.user_id == user_id)
    ).all()
    
    # For each session, get skills count (for now just ESCO)
    sessions_with_skills = []
    for session in sessions:
        esco_skills = db.exec(
            select(ESCOSkillModel).where(ESCOSkillModel.session_id == session.session_id)
        ).all()
        
        session_data = ChatSessionWithSkillsResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            session_name=session.session_name,
            created_at=session.created_at,
            updated_at=session.updated_at,
            esco_skills=esco_skills
        )
        sessions_with_skills.append(session_data)
    
    return sessions_with_skills


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: int, db: Session = Depends(get_db_session_dependency)):
    """Get a specific chat session."""
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    return session


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: int, 
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency)
):
    """Update a chat session (currently only supports updating the name)."""
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if session belongs to current user
    if session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chat session"
        )
    
    try:
        # Update session name
        if session_data.session_name is not None:
            session.session_name = session_data.session_name
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
        
    except Exception as e:
        logger.exception(f"Failed to update session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat session"
        )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db_session_dependency)):
    """Get all messages for a chat session."""
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if session belongs to current user
    if session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chat session"
        )
    
    messages = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
    ).all()
    return messages


@router.get("/sessions/{session_id}/skills/{skill_system}", response_model=List[SkillResponse])
async def get_session_skills(
    session_id: int, 
    skill_system: SkillSystem,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency)
):
    """Get all skills for a chat session by skill system."""
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if session belongs to current user
    if session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chat session"
        )
    
    # For now, only ESCO skills are implemented
    if skill_system == SkillSystem.ESCO:
        skills = db.exec(
            select(ESCOSkillModel)
            .where(ESCOSkillModel.session_id == session_id)
        ).all()
        return skills
    else:
        # Future skill systems can be added here
        return []


@router.get("/sessions/{session_id}/skills", response_model=Dict[str, List[SkillResponse]])
async def get_all_session_skills(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency)
):
    """Get all skills for a chat session grouped by skill system."""
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Check if session belongs to current user
    if session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chat session"
        )
    
    result = {}
    
    # Get ESCO skills
    esco_skills = db.exec(
        select(ESCOSkillModel)
        .where(ESCOSkillModel.session_id == session_id)
    ).all()
    result["ESCO"] = esco_skills
    
    # Future skill systems can be added here
    result["Freiwilligenpass"] = []
    
    return result
