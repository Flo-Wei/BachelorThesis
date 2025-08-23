from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict
import logging

from Backend.database.init import get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession
from Backend.database.models.skills import ESCOSkillModel, SkillSystem
from Backend.schemas import SkillResponse
from Backend.auth import get_current_user

router = APIRouter(prefix="/skills", tags=["skills"])
logger = logging.getLogger(__name__)


@router.get("/systems", response_model=List[str])
async def get_skill_systems():
    """Get all available skill systems."""
    return [system.value for system in SkillSystem]


@router.get("/sessions/{session_id}/{skill_system}", response_model=List[SkillResponse])
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


@router.get("/sessions/{session_id}", response_model=Dict[str, List[SkillResponse]])
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
