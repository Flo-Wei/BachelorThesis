from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session, select
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

from Backend.database.init import init_database, get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, ChatMessage, MessageType
from Backend.database.models.skills import ESCOSkill, SkillSystem
from Backend.database.utils import (
    create_user,
    create_chat_session,
    add_message
)
from Backend.schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    ChatSessionCreate, ChatSessionResponse, ChatSessionWithSkillsResponse,
    ChatRequest, ChatResponse, MessageResponse,
    SkillResponse
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# JWT utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def get_current_user(user_id: int = Depends(verify_token), db: Session = Depends(get_db_session_dependency)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# USER MANAGEMENT ENDPOINTS
# ==============================================================================

@app.post("/users/register", response_model=UserResponse)
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
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@app.post("/users/login", response_model=Token)
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


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db_session_dependency)):
    """Get user by ID."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@app.get("/users", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db_session_dependency)):
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
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )


@app.get("/users/{user_id}/sessions", response_model=List[ChatSessionWithSkillsResponse])
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
            select(ESCOSkill).where(ESCOSkill.session_id == session.session_id)
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


@app.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: int, db: Session = Depends(get_db_session_dependency)):
    """Get a specific chat session."""
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    return session


@app.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
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


# ==============================================================================
# CHAT PROCESSING
# ==============================================================================

@app.post("/users/{user_id}/chat", response_model=ChatResponse)
async def chat_with_user(
    user_id: int,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency)
):
    """Process a chat message for a user."""
    # Check if user is chatting as themselves
    if user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot chat as another user"
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
        session = create_chat_session(current_user, "New Chat Session")
    
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
# SKILLS ENDPOINTS
# ==============================================================================

@app.get("/skills/systems", response_model=List[str])
async def get_skill_systems():
    """Get all available skill systems."""
    return [system.value for system in SkillSystem]


@app.get("/sessions/{session_id}/skills/{skill_system}", response_model=List[SkillResponse])
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
            select(ESCOSkill)
            .where(ESCOSkill.session_id == session_id)
        ).all()
        return skills
    else:
        # Future skill systems can be added here
        return []


@app.get("/sessions/{session_id}/skills", response_model=Dict[str, List[SkillResponse]])
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
        select(ESCOSkill)
        .where(ESCOSkill.session_id == session_id)
    ).all()
    result["ESCO"] = esco_skills
    
    # Future skill systems can be added here
    result["Freiwilligenpass"] = []
    
    return result


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