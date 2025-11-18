from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
import logging

from Backend.database.init import get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, ChatMessage
from Backend.database.models.skills import ESCOSkillModel, CustomSkillModel
from Backend.database.utils import create_user
from Backend.schemas import UserCreate, UserResponse, UserLogin, Token, UserUpdate
from Backend.auth import create_access_token, get_admin_user

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db_session_dependency)):
    """Register a new user."""
    # Check if user already exists
    existing_user = db.exec(
        select(User).where(
            (User.username == user_data.username) | 
            (User.email == user_data.email)
        )
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Create new user
    try:
        user = create_user(user_data.username, user_data.email, user_data.is_admin)
        return user
    except Exception as e:
        logger.exception(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=Token)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db_session_dependency)):
    """Login user and return JWT token."""
    user = db.exec(select(User).where(User.username == login_data.username)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.user_id)})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db_session_dependency)):
    """Get user by ID."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db_session_dependency),
    admin_user: User = Depends(get_admin_user)
):
    """List all users (admin only)."""
    users = db.exec(select(User)).all()
    return users


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db_session_dependency),
    admin_user: User = Depends(get_admin_user)
):
    """Update a user (admin only)."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_update.username is not None:
        # Check if username is already taken by another user
        existing_user = db.exec(
            select(User).where(
                (User.username == user_update.username) & 
                (User.user_id != user_id)
            )
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        user.username = user_update.username
    
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_user = db.exec(
            select(User).where(
                (User.email == user_update.email) & 
                (User.user_id != user_id)
            )
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        user.email = user_update.email
    
    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db_session_dependency),
    admin_user: User = Depends(get_admin_user)
):
    """Delete a user and all related data (admin only)."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if user.user_id == admin_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Get all chat sessions for this user
    chat_sessions = db.exec(
        select(ChatSession).where(ChatSession.user_id == user_id)
    ).all()
    
    # Delete all related data in correct order (cascade delete)
    for session in chat_sessions:
        session_id = session.session_id
        
        # Delete ESCO skills FIRST (they have foreign key to custom_skills)
        # Must delete before custom skills since custom_skill_id is NOT NULL
        esco_skills = db.exec(
            select(ESCOSkillModel).where(ESCOSkillModel.session_id == session_id)
        ).all()
        for skill in esco_skills:
            db.delete(skill)
        
        # Delete custom skills (related to messages)
        # Delete after ESCO skills since ESCO skills reference them
        custom_skills = db.exec(
            select(CustomSkillModel).where(CustomSkillModel.session_id == session_id)
        ).all()
        for skill in custom_skills:
            db.delete(skill)
        
        # Delete chat messages (related to session)
        messages = db.exec(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        ).all()
        for message in messages:
            db.delete(message)
        
        # Delete the chat session
        db.delete(session)
    
    # Finally, delete the user
    db.delete(user)
    db.commit()
    return None
