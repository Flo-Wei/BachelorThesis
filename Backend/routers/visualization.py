from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from typing import Dict, Any, List
import logging

from Backend.database.init import get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession
from Backend.database.models.skills import ESCOSkillModel, CustomSkillModel, SkillType
from Backend.auth import get_current_user
from Backend.visualization.processor import VisualizationProcessor

router = APIRouter(prefix="/visualizations", tags=["visualizations"])
logger = logging.getLogger(__name__)

processor = VisualizationProcessor()

async def verify_session_access(
    session_id: int, 
    user: User, 
    db: Session
) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return session

@router.get("/session/{session_id}/custom")
async def get_custom_visualizations(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency)
):
    """Get data for Donut and Density charts based on Custom Skills."""
    await verify_session_access(session_id, current_user, db)
    
    # Fetch custom skills
    statement = select(CustomSkillModel).where(CustomSkillModel.session_id == session_id)
    results = db.exec(statement)
    custom_skills = results.all()
    
    # Convert to list of dicts to ensure clean types for processor
    skills_data = []
    for skill in custom_skills:
        skills_data.append({
            "type": skill.type.value if isinstance(skill.type, SkillType) else str(skill.type),
            "confidence": skill.confidence
        })
    
    data = processor.process_custom_skills(skills_data)
    return data

@router.get("/session/{session_id}/esco")
async def get_esco_visualizations(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency)
):
    """Get data for Sunburst, Occupation Match, and Radar charts based on ESCO Skills."""
    await verify_session_access(session_id, current_user, db)
    
    # Fetch ESCO skills with custom_skill relationship to get type
    statement = select(ESCOSkillModel).where(
        ESCOSkillModel.session_id == session_id
    ).options(joinedload(ESCOSkillModel.custom_skill))
    
    results = db.exec(statement)
    esco_skills = results.all()
    
    # Prepare data for processor
    skills_data = []
    for s in esco_skills:
        skill_dict = {
            "uri": s.uri,
            "title": s.title,
            "name": s.title, # Fallback
            "type": "Unknown",
            "links": s.links
        }
        
        if s.custom_skill:
             skill_dict["type"] = s.custom_skill.type.value if isinstance(s.custom_skill.type, SkillType) else str(s.custom_skill.type)
        
        skills_data.append(skill_dict)
    
    hierarchy = processor.process_esco_hierarchy(skills_data)
    occupations = processor.match_occupations(skills_data)
    radar = processor.process_radar_data(skills_data)
    
    return {
        "sunburst": hierarchy,
        "occupations": occupations,
        "radar": radar
    }

