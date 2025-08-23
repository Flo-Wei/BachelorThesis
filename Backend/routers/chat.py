from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
import logging

from Backend.database.init import get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, MessageType
from Backend.database.utils import create_chat_session, add_message
from Backend.schemas import ChatRequest, ChatResponse
from Backend.auth import get_current_user
from Backend.classes.LLM import BaseLLM
from Backend.utils import get_prompt

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


# These will be set by the main app during startup
_llm_instance = None
_esco_database_handler = None


def set_dependencies(llm_instance, esco_database_handler):
    """Set the dependencies from the main app."""
    global _llm_instance, _esco_database_handler
    _llm_instance = llm_instance
    _esco_database_handler = esco_database_handler


def get_llm() -> BaseLLM:
    """Dependency to get the LLM instance."""
    if _llm_instance is None:
        raise HTTPException(status_code=500, detail="LLM not initialized")
    return _llm_instance


def get_esco_database_handler():
    """Dependency to get the ESCO database handler."""
    if _esco_database_handler is None:
        raise HTTPException(status_code=500, detail="ESCO database handler not initialized")
    return _esco_database_handler


@router.post("/users/{user_id}/chat", response_model=ChatResponse)
async def chat_with_user(
    user_id: int,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session_dependency),
    llm: BaseLLM = Depends(get_llm)
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
        # --- Chat logic ---
        # Add user message
        user_message = add_message(
            session, chat_request.message, MessageType.USER, db
        )
        
        # Get LLM response (this will automatically save the assistant message to the database)
        assistant_message = llm.chat(
            chat_session=session,
            db_session=db
        )

        # Extract skills from assistant message
        skills = llm.extract_skills(
            instruction=get_prompt("information_extractor"),
            message=assistant_message
        )

        # Map skills to available skills
        esco_database_handler = get_esco_database_handler()
        for skill in skills:
            mapped_skill = llm.map_skill(
                instruction=get_prompt("information_mapper"),
                skill=skill,
                available_skills=esco_database_handler.search_skills(
                    skill.name,
                    limit=20
                )
            )
            mapped_skill.session_id = session.session_id
            mapped_skill.origin_message_id = assistant_message.message_id
            db.add(mapped_skill)
            db.commit()
            db.refresh(mapped_skill)
            session.esco_skills.append(mapped_skill)
            db.add(session)
            db.commit()
            db.refresh(session)

        
        return ChatResponse(
            message=user_message,
            assistant_response=assistant_message,
            session_id=session.session_id
        )
        
    except Exception as e:
        logger.exception(f"Failed to process chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )
