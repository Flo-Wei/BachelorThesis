from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
import logging

from Backend.database.init import get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.utils import create_user
from Backend.schemas import UserCreate, UserResponse, UserLogin, Token
from Backend.auth import create_access_token

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
        user = create_user(user_data.username, user_data.email)
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
async def list_users(db: Session = Depends(get_db_session_dependency)):
    """List all users (for testing/admin purposes)."""
    users = db.exec(select(User)).all()
    return users
