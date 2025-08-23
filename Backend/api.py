from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from sqlmodel import Session, select
import logging
from pathlib import Path
from typing import List

from Backend.database.init import init_database, get_db_session
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, ChatMessage, MessageType
from Backend.database.utils import (
    create_user,
    create_chat_session,
    add_message
)
from Backend.schemas import (
    UserCreate, UserResponse, UserLogin,
    ChatSessionCreate, ChatSessionResponse,
    ChatRequest, ChatResponse, MessageResponse
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting up application...")
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title="Bachelor Thesis Chatbot API",
    description="API for skill-extraction chatbot with database integration",
    version="1.0.0",
    lifespan=lifespan
)

# ==============================================================================
# USER MANAGEMENT ENDPOINTS
# ==============================================================================

@app.post("/users/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db_session)):
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
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@app.post("/users/login", response_model=UserResponse)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db_session)):
    """Login user (simplified - just find by username)."""
    user = db.exec(select(User).where(User.username == login_data.username)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db_session)):
    """Get user by ID."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@app.get("/users", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db_session)):
    """List all users (for testing/admin purposes)."""
    users = db.exec(select(User)).all()
    return users


# ==============================================================================
# CHAT SESSION MANAGEMENT
# ==============================================================================

@app.post("/users/{user_id}/sessions", response_model=ChatSessionResponse)
async def create_session(
    user_id: int, 
    session_data: ChatSessionCreate, 
    db: Session = Depends(get_db_session)
):
    """Create a new chat session for a user."""
    # Verify user exists
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        session = create_chat_session(user, session_data.session_name)
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )


@app.get("/users/{user_id}/sessions", response_model=List[ChatSessionResponse])
async def get_user_sessions(user_id: int, db: Session = Depends(get_db_session)):
    """Get all chat sessions for a user."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    sessions = db.exec(
        select(ChatSession).where(ChatSession.user_id == user_id)
    ).all()
    return sessions


@app.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: int, db: Session = Depends(get_db_session)):
    """Get a specific chat session."""
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    return session


@app.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: int, db: Session = Depends(get_db_session)):
    """Get all messages for a chat session."""
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    messages = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
    ).all()
    return messages


# ==============================================================================
# CHAT PROCESSING
# ==============================================================================

@app.post("/users/{user_id}/chat", response_model=ChatResponse)
async def chat_with_user(
    user_id: int,
    chat_request: ChatRequest,
    db: Session = Depends(get_db_session)
):
    """Process a chat message for a user."""
    # Verify user exists
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get or create chat session
    if chat_request.session_id:
        # Use existing session
        session = db.get(ChatSession, chat_request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to this user"
            )
    else:
        # Create new session
        session = create_chat_session(user, "New Chat Session")
    
    try:
        # Add user message
        user_message = add_message(
            session, chat_request.message, MessageType.USER
        )
        
        # Generate assistant response (simplified for now)
        assistant_content = f"I received your message: '{chat_request.message}'. This is a placeholder response."
        
        assistant_message = add_message(
            session, assistant_content, MessageType.ASSISTANT
        )
        
        return ChatResponse(
            message=user_message,
            assistant_response=assistant_message,
            session_id=session.session_id
        )
        
    except Exception as e:
        logger.error(f"Failed to process chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )


# ==============================================================================
# UTILITY ENDPOINTS
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Serve the frontend HTML file."""
    frontend_path = Path("Frontend/index.html")
    if frontend_path.exists():
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Frontend not found</h1>")


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "message": "API is running"}