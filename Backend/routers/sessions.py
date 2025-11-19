from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from typing import List, Dict
import logging

from Backend.database.init import get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, ChatMessage
from Backend.database.models.skills import ESCOSkillModel, CustomSkillModel, SkillSystem
from Backend.database.utils import create_chat_session
from Backend.schemas import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionWithSkillsResponse,
    MessageResponse, SkillResponse, CustomSkillResponse
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
    
    # For each session, get skills count (ESCO and CUSTOM)
    sessions_with_skills = []
    for session in sessions:
        from sqlalchemy.orm import selectinload
        stmt = select(ESCOSkillModel).where(ESCOSkillModel.session_id == session.session_id).options(selectinload(ESCOSkillModel.custom_skill))
        esco_skills = db.exec(stmt).all()
        # Note: origin_message_id is now accessed through custom_skill relationship
        # We don't set it on the model since it's not a field anymore
        
        custom_skills = db.exec(
            select(CustomSkillModel).where(CustomSkillModel.session_id == session.session_id)
        ).all()
        
        # Convert ESCO skills to SkillResponse format
        from Backend.schemas import SkillResponse, CustomSkillResponse
        esco_skill_responses = []
        for skill in esco_skills:
            origin_message_id = skill.custom_skill.origin_message_id if skill.custom_skill else None
            custom_skill_id = skill.custom_skill_id if skill.custom_skill_id else None
            custom_skill_name = skill.custom_skill.name if skill.custom_skill else None
            skill_response = SkillResponse(
                id=skill.id,
                skill_system=skill.skill_system,
                uri=skill.uri,
                title=skill.title,
                reference_language=skill.reference_language,
                preferred_label=skill.preferred_label,
                description=skill.description,
                links=skill.links,
                origin_message_id=origin_message_id,
                custom_skill_id=custom_skill_id,
                custom_skill_name=custom_skill_name,
                session_id=skill.session_id,
                evidence=skill.evidence
            )
            esco_skill_responses.append(skill_response)
        
        # Convert CustomSkills to CustomSkillResponse format
        custom_skill_responses = []
        for custom_skill in custom_skills:
            # Convert enum to string for JSON serialization
            skill_type = custom_skill.type.value if hasattr(custom_skill.type, 'value') else str(custom_skill.type)
            custom_skill_response = CustomSkillResponse(
                id=custom_skill.id,
                skill_system=SkillSystem.CUSTOM,
                session_id=custom_skill.session_id,
                origin_message_id=custom_skill.origin_message_id,
                name=custom_skill.name,
                type=skill_type,
                confidence=custom_skill.confidence,
                evidence=custom_skill.evidence,
                created_at=custom_skill.created_at
            )
            custom_skill_responses.append(custom_skill_response)
        
        session_data = ChatSessionWithSkillsResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            session_name=session.session_name,
            created_at=session.created_at,
            updated_at=session.updated_at,
            esco_skills=esco_skill_responses,
            custom_skills=custom_skill_responses
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


@router.get("/sessions/{session_id}/skills/{skill_system}")
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
    
    if skill_system == SkillSystem.ESCO:
        # Query with relationship loading
        from sqlalchemy.orm import selectinload
        stmt = select(ESCOSkillModel).where(ESCOSkillModel.session_id == session_id).options(selectinload(ESCOSkillModel.custom_skill))
        skills = db.exec(stmt).all()
        # Convert to SkillResponse with origin_message_id from custom_skill
        from Backend.schemas import SkillResponse
        skill_responses = []
        for skill in skills:
            origin_message_id = skill.custom_skill.origin_message_id if skill.custom_skill else None
            custom_skill_id = skill.custom_skill_id if skill.custom_skill_id else None
            custom_skill_name = skill.custom_skill.name if skill.custom_skill else None
            skill_response = SkillResponse(
                id=skill.id,
                skill_system=skill.skill_system,
                uri=skill.uri,
                title=skill.title,
                reference_language=skill.reference_language,
                preferred_label=skill.preferred_label,
                description=skill.description,
                links=skill.links,
                origin_message_id=origin_message_id,
                custom_skill_id=custom_skill_id,
                custom_skill_name=custom_skill_name,
                session_id=skill.session_id,
                evidence=skill.evidence
            )
            skill_responses.append(skill_response)
        return skill_responses
    elif skill_system == SkillSystem.CUSTOM:
        skills = db.exec(
            select(CustomSkillModel)
            .where(CustomSkillModel.session_id == session_id)
        ).all()
        # Convert to CustomSkillResponse format
        from Backend.schemas import CustomSkillResponse
        skill_responses = []
        for skill in skills:
            # Convert enum to string for JSON serialization
            skill_type = skill.type.value if hasattr(skill.type, 'value') else str(skill.type)
            skill_response = CustomSkillResponse(
                id=skill.id,
                skill_system=SkillSystem.CUSTOM,
                session_id=skill.session_id,
                origin_message_id=skill.origin_message_id,
                name=skill.name,
                type=skill_type,
                confidence=skill.confidence,
                evidence=skill.evidence,
                created_at=skill.created_at
            )
            skill_responses.append(skill_response)
        return skill_responses
    else:
        # Future skill systems can be added here
        return []


@router.get("/sessions/{session_id}/skills")
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
    from sqlalchemy.orm import selectinload
    from Backend.schemas import SkillResponse
    stmt = select(ESCOSkillModel).where(ESCOSkillModel.session_id == session_id).options(selectinload(ESCOSkillModel.custom_skill))
    esco_skills = db.exec(stmt).all()
    # Convert to SkillResponse with origin_message_id from custom_skill
    skill_responses = []
    for skill in esco_skills:
        origin_message_id = skill.custom_skill.origin_message_id if skill.custom_skill else None
        custom_skill_id = skill.custom_skill_id if skill.custom_skill_id else None
        custom_skill_name = skill.custom_skill.name if skill.custom_skill else None
        skill_response = SkillResponse(
            id=skill.id,
            skill_system=skill.skill_system,
            uri=skill.uri,
            title=skill.title,
            reference_language=skill.reference_language,
            preferred_label=skill.preferred_label,
            description=skill.description,
            links=skill.links,
            origin_message_id=origin_message_id,
            custom_skill_id=custom_skill_id,
            custom_skill_name=custom_skill_name,
            session_id=skill.session_id,
            evidence=skill.evidence
        )
        skill_responses.append(skill_response)
    result["ESCO"] = skill_responses
    
    # Get CUSTOM skills
    from Backend.schemas import CustomSkillResponse
    custom_skills = db.exec(
        select(CustomSkillModel)
        .where(CustomSkillModel.session_id == session_id)
    ).all()
    # Convert to CustomSkillResponse format
    custom_skill_responses = []
    for skill in custom_skills:
        # Convert enum to string for JSON serialization
        skill_type = skill.type.value if hasattr(skill.type, 'value') else str(skill.type)
        skill_response = CustomSkillResponse(
            id=skill.id,
            skill_system=SkillSystem.CUSTOM,
            session_id=skill.session_id,
            origin_message_id=skill.origin_message_id,
            name=skill.name,
            type=skill_type,
            confidence=skill.confidence,
            evidence=skill.evidence,
            created_at=skill.created_at
        )
        custom_skill_responses.append(skill_response)
    result["CUSTOM"] = custom_skill_responses
    
    # Future skill systems can be added here
    result["Freiwilligenpass"] = []
    
    return result
