"""Database utility functions for common operations."""

from sqlmodel import Session
from typing import Optional, List
import logging

from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, ChatMessage, MessageType
from Backend.database.models.skills import ESCOSkill
from .init import get_db_session, db_manager

logger = logging.getLogger(__name__)


def create_database_engine(database_url: str = None):
    """Deprecated: Use init_database() instead."""
    import warnings
    warnings.warn(
        "create_database_engine() is deprecated. Use init_database() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from .init import init_database
    init_database()
    return db_manager.engine


# Example usage functions
def create_user(session: Session, username: str, email: str) -> User:
    """Create a new user"""
    user = User(username=username, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_chat_session(session: Session, user: User, session_name: str = None) -> ChatSession:
    """Create a new chat session for a user"""
    chat_session = ChatSession(user_id=user.user_id, session_name=session_name)
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return chat_session


def add_message(
    session: Session, 
    chat_session: ChatSession, 
    content: str, 
    message_type: MessageType
) -> ChatMessage:
    """Add a message to a chat session"""
    message = ChatMessage(
        session_id=chat_session.session_id,
        message_content=content,
        message_type=message_type
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    session.refresh(chat_session)  # Refresh to update chat_messages relationship
    return message


def add_esco_skill(
    session: Session,
    chat_session: ChatSession,
    origin_message: ChatMessage,
    uri: str,
    title: str,
    reference_language: str = "en",
    preferred_label: dict = None,
    description: dict = None,
    links: dict = None
) -> ESCOSkill:
    """Add an ESCO skill identified from a message"""
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
    session.add(skill)
    session.commit()
    session.refresh(skill)
    session.refresh(chat_session)  # Refresh to update esco_skills relationship
    session.refresh(origin_message)  # Refresh to update derived_skills_esco relationship
    return skill


# Context manager versions for better session management
def create_user_with_session(username: str, email: str) -> User:
    """Create a new user using automatic session management."""
    try:
        with get_db_session() as session:
            return create_user(session, username, email)
    except Exception as e:
        logger.error(f"Failed to create user {username}: {e}")
        raise


def create_chat_session_with_session(user: User, session_name: str = None) -> ChatSession:
    """Create a new chat session using automatic session management."""
    try:
        with get_db_session() as session:
            return create_chat_session(session, user, session_name)
    except Exception as e:
        logger.error(f"Failed to create chat session for user {user.user_id}: {e}")
        raise


def add_message_with_session(
    chat_session: ChatSession, 
    content: str, 
    message_type: MessageType
) -> ChatMessage:
    """Add a message using automatic session management."""
    try:
        with get_db_session() as session:
            return add_message(session, chat_session, content, message_type)
    except Exception as e:
        logger.error(f"Failed to add message to session {chat_session.session_id}: {e}")
        raise


def add_esco_skill_with_session(
    chat_session: ChatSession,
    origin_message: ChatMessage,
    uri: str,
    title: str,
    reference_language: str = "en",
    preferred_label: dict = None,
    description: dict = None,
    links: dict = None
) -> ESCOSkill:
    """Add an ESCO skill using automatic session management."""
    try:
        with get_db_session() as session:
            return add_esco_skill(
                session, chat_session, origin_message, uri, title,
                reference_language, preferred_label, description, links
            )
    except Exception as e:
        logger.error(f"Failed to add ESCO skill {title}: {e}")
        raise


