from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from typing import List, Dict, Optional
import logging

from Backend.database.init import get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession
from Backend.database.models.skills import ESCOSkillModel, CustomSkillModel, SkillSystem, SkillType
from Backend.schemas import SkillResponse, CustomSkillResponse, CustomSkillUpdate, ESCOSkillUpdate
from Backend.auth import get_current_user

router = APIRouter(prefix="/skills", tags=["skills"])
logger = logging.getLogger(__name__)


@router.get("/systems", response_model=List[str])
async def get_skill_systems():
    """Get all available skill systems."""
    return [system.value for system in SkillSystem]


@router.get("/search/esco", response_model=List[SkillResponse])
async def search_esco_skills(
    query: str, 
    request: Request,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Search for skills in the ESCO database."""
    try:
        esco_handler = request.app.state.esco_database_handler
        skills = esco_handler.search_skills(query, limit=limit)
        
        # Convert to SkillResponse
        response = []
        for skill in skills:
            response.append(SkillResponse(
                id=0, # Temporary ID as it's not in DB yet
                skill_system=SkillSystem.ESCO,
                uri=skill.uri,
                title=skill.title,
                reference_language=skill.reference_language,
                preferred_label=skill.preferred_label,
                description=skill.description,
                links=skill.links,
                session_id=0 # No session context for search
            ))
        return response
    except Exception as e:
        logger.exception(f"Failed to search ESCO skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search ESCO skills"
        )


@router.put("/custom/{skill_id}", response_model=CustomSkillResponse)
async def update_custom_skill(
    skill_id: int,
    skill_data: CustomSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency)
):
    """Update a custom skill."""
    skill = db.get(CustomSkillModel, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
        
    # Check ownership via session
    session = db.get(ChatSession, skill.session_id)
    if not session or session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
        
    # Update fields
    if skill_data.name is not None:
        skill.name = skill_data.name
    if skill_data.type is not None:
        try:
            skill.type = SkillType(skill_data.type)
        except ValueError:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid skill type: {skill_data.type}"
            )
    if skill_data.confidence is not None:
        skill.confidence = skill_data.confidence
    if skill_data.evidence is not None:
        skill.evidence = skill_data.evidence
        
    db.add(skill)
    db.commit()
    db.refresh(skill)
    
    return CustomSkillResponse(
        id=skill.id,
        skill_system=SkillSystem.CUSTOM,
        session_id=skill.session_id,
        origin_message_id=skill.origin_message_id,
        name=skill.name,
        type=skill.type.value,
        confidence=skill.confidence,
        evidence=skill.evidence,
        created_at=skill.created_at
    )


@router.put("/esco/{skill_id}", response_model=SkillResponse)
async def update_esco_skill(
    skill_id: int,
    skill_data: ESCOSkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency)
):
    """Update an ESCO skill (remapping)."""
    skill = db.get(ESCOSkillModel, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
        
    # Check ownership via session
    session = db.get(ChatSession, skill.session_id)
    if not session or session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
        
    # Update fields
    if skill_data.title is not None:
        skill.title = skill_data.title
    if skill_data.uri is not None:
        skill.uri = skill_data.uri
    if skill_data.reference_language is not None:
        skill.reference_language = skill_data.reference_language
    if skill_data.preferred_label is not None:
        skill.preferred_label = skill_data.preferred_label
    if skill_data.description is not None:
        skill.description = skill_data.description
    if skill_data.evidence is not None:
        skill.evidence = skill_data.evidence
        
    db.add(skill)
    db.commit()
    db.refresh(skill)
    
    # Access relationships
    # Use simple property access, hoping it triggers lazy load if attached to session, 
    # or manually get it if needed.
    custom_skill_id = skill.custom_skill_id
    origin_message_id = None
    
    # If custom_skill is not loaded, try to load it
    if custom_skill_id and not skill.custom_skill:
        skill.custom_skill = db.get(CustomSkillModel, custom_skill_id)
        
    if skill.custom_skill:
        origin_message_id = skill.custom_skill.origin_message_id

    return SkillResponse(
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
        session_id=skill.session_id,
        evidence=skill.evidence
    )
