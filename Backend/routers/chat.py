from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
import logging

from Backend.database.init import get_db_session_dependency
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, MessageType
from Backend.database.utils import create_chat_session, add_message
from Backend.schemas import ChatRequest, ChatResponse
from Backend.auth import get_current_user
from Backend.classes.Skill_Database_Handler import ESCODatabase
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


def get_esco_database_handler() -> ESCODatabase:
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
    logger.debug(f"Starting chat request for user_id={user_id}, current_user={current_user.user_id}, "
                f"session_id={chat_request.session_id}, message_length={len(chat_request.message)}")
    
    # Check if user is chatting as themselves
    if user_id != current_user.user_id:
        logger.debug(f"Authorization failed: user_id={user_id} != current_user.user_id={current_user.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot chat as another user"
        )
    logger.debug(f"Authorization passed: user is chatting as themselves")
    
    # Get or create chat session
    if chat_request.session_id:
        logger.debug(f"Looking up existing session with ID: {chat_request.session_id}")
        # Use existing session
        session = db.get(ChatSession, chat_request.session_id)
        if not session:
            logger.debug(f"Session {chat_request.session_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        if session.user_id != user_id:
            logger.debug(f"Session ownership failed: session.user_id={session.user_id} != user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to this user"
            )
        logger.debug(f"Using existing session: {session.session_id}, title='{session.session_name}', "
                    f"message_count={len(session.chat_messages)}")
    else:
        logger.debug(f"Creating new chat session for user {user_id}")
        # Create new session
        session = create_chat_session(current_user, "New Chat Session")
        logger.debug(f"Created new session: {session.session_id}")
    
    try:
        # --- Chat logic ---
        logger.debug(f"Starting chat processing for session {session.session_id}")
        
        # Add user message
        logger.debug(f"Adding user message: '{chat_request.message[:100]}{'...' if len(chat_request.message) > 100 else ''}'")
        user_message = add_message(
            session, chat_request.message, MessageType.USER, db
        )
        logger.debug(f"User message added with ID: {user_message.message_id}")
        
        # Get LLM response (this will automatically save the assistant message to the database)
        logger.debug(f"Requesting LLM response for session {session.session_id}")
        assistant_message = llm.chat(
            chat_session=session,
            db_session=db
        )
        logger.debug(f"LLM response received: message_id={assistant_message.message_id}, "
                    f"content_length={len(assistant_message.message_content)}, "
                    f"preview='{assistant_message.message_content[:100]}{'...' if len(assistant_message.message_content) > 100 else ''}'")

        # Extract skills from assistant message
        logger.debug(f"Extracting skills from assistant message {assistant_message.message_id}")
        skills = llm.extract_skills(
            instruction=get_prompt("information_extractor"),
            message=assistant_message
        )
        logger.debug(f"Extracted {len(skills)} skills: {[skill.model_dump() for skill in skills]}")

        # Map skills to available skills
        logger.debug(f"Starting skill mapping process for {len(skills)} skills")
        esco_database_handler = get_esco_database_handler()
        mapped_skills_count = 0
        
        for i, skill in enumerate(skills):
            logger.debug(f"Processing skill {i+1}/{len(skills)}: '{skill.name}'")
            
            # Search for available skills
            available_skills = esco_database_handler.search_skills(skill.name, limit=20)
            logger.debug(f"Found {len(available_skills)} potential matches for '{skill.name}': {[skill.title for skill in available_skills]}")
            
            if len(available_skills) > 0:
                mapped_skill = llm.map_skill(
                    instruction=get_prompt("information_mapper"),
                    skill=skill,
                    available_skills=available_skills
                )
                logger.debug(f"Mapped '{skill.name}' to '{mapped_skill.title}' (URI: {mapped_skill.uri})")

                # Save mapped skill to database
                mapped_skill.session_id = session.session_id
                mapped_skill.origin_message_id = assistant_message.message_id
                db.add(mapped_skill)
                db.commit()
                db.refresh(mapped_skill)
                logger.debug(f"Saved mapped skill to database with ID: {mapped_skill.id}")
                # Add to session
                session.esco_skills.append(mapped_skill)
            else:
                logger.debug(f"No available skills found for '{skill.name}'")
                mapped_skill = None
            
            db.add(session)
            db.commit()
            db.refresh(session)
            mapped_skills_count += 1
            logger.debug(f"Added mapped skill to session. Total skills in session: {len(session.esco_skills)}")

        logger.debug(f"Skill mapping completed. Mapped {mapped_skills_count} skills for session {session.session_id}")
        
        response = ChatResponse(
            message=user_message,
            assistant_response=assistant_message,
            session_id=session.session_id
        )
        logger.debug(f"Chat processing completed successfully for session {session.session_id}")
        return response
        
    except Exception as e:
        logger.exception(f"Failed to process chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )
