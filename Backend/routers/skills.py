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



