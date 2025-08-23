"""Database utility functions for common operations."""

from sqlmodel import Session
from typing import Optional
import logging

from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, ChatMessage, MessageType
from Backend.database.models.skills import ESCOSkill
from .init import get_db_session

logger = logging.getLogger(__name__)


def create_user(username: str, email: str, session: Optional[Session] = None) -> User:
    """Create a new user.
    
    Args:
        username: The username for the new user
        email: The email for the new user
        session: Optional database session. If None, creates and manages session automatically.
    
    Returns:
        The created User object
    """
    def _create_user(db_session: Session) -> User:
        user = User(username=username, email=email)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    if session is not None:
        return _create_user(session)
    
    try:
        with get_db_session() as db_session:
            return _create_user(db_session)
    except Exception as e:
        logger.error(f"Failed to create user {username}: {e}")
        raise


def create_chat_session(user: User, session_name: str = None, session: Optional[Session] = None) -> ChatSession:
    """Create a new chat session for a user.
    
    Args:
        user: The user to create the session for
        session_name: Optional name for the session
        session: Optional database session. If None, creates and manages session automatically.
    
    Returns:
        The created ChatSession object
    """
    def _create_chat_session(db_session: Session) -> ChatSession:
        chat_session = ChatSession(user_id=user.user_id, session_name=session_name)
        db_session.add(chat_session)
        db_session.commit()
        db_session.refresh(chat_session)
        return chat_session
    
    if session is not None:
        return _create_chat_session(session)
    
    try:
        with get_db_session() as db_session:
            return _create_chat_session(db_session)
    except Exception as e:
        logger.error(f"Failed to create chat session for user {user.user_id}: {e}")
        raise


def add_message(
    chat_session: ChatSession, 
    content: str, 
    message_type: MessageType,
    session: Optional[Session] = None
) -> ChatMessage:
    """Add a message to a chat session.
    
    Args:
        chat_session: The chat session to add the message to
        content: The message content
        message_type: The type of message (USER, ASSISTANT, SYSTEM)
        session: Optional database session. If None, creates and manages session automatically.
    
    Returns:
        The created ChatMessage object
    """
    def _add_message(db_session: Session) -> ChatMessage:
        message = ChatMessage(
            session_id=chat_session.session_id,
            message_content=content,
            role=message_type
        )
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)
        db_session.refresh(chat_session)  # Refresh to update chat_messages relationship
        return message
    
    if session is not None:
        return _add_message(session)
    
    try:
        with get_db_session() as db_session:
            return _add_message(db_session)
    except Exception as e:
        logger.error(f"Failed to add message to session {chat_session.session_id}: {e}")
        raise


def add_esco_skill(
    chat_session: ChatSession,
    origin_message: ChatMessage,
    uri: str,
    title: str,
    reference_language: str = "en",
    preferred_label: dict = None,
    description: dict = None,
    links: dict = None,
    session: Optional[Session] = None
) -> ESCOSkill:
    """Add an ESCO skill identified from a message.
    
    Args:
        chat_session: The chat session the skill was identified in
        origin_message: The message the skill was identified from
        uri: The ESCO URI for the skill
        title: The skill title
        reference_language: The reference language (default: "en")
        preferred_label: Dict of preferred labels by language
        description: Dict of descriptions by language
        links: Dict of related links
        session: Optional database session. If None, creates and manages session automatically.
    
    Returns:
        The created ESCOSkill object
    """
    def _add_esco_skill(db_session: Session) -> ESCOSkill:
        skill = ESCOSkill(
            session_id=chat_session.session_id,
            origin_message_id=origin_message.message_id,
            uri=uri,
            title=title,
            reference_language=reference_language,
            preferred_label=preferred_label or {},
            description=description or {},
            links=links or {}
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)
        db_session.refresh(chat_session)  # Refresh to update esco_skills relationship
        db_session.refresh(origin_message)  # Refresh to update derived_skills_esco relationship
        return skill
    
    if session is not None:
        return _add_esco_skill(session)
    
    try:
        with get_db_session() as db_session:
            return _add_esco_skill(db_session)
    except Exception as e:
        logger.error(f"Failed to add ESCO skill {title}: {e}")
        raise


# Backward compatibility aliases
create_user_with_session = create_user
create_chat_session_with_session = create_chat_session
add_message_with_session = add_message
add_esco_skill_with_session = add_esco_skill