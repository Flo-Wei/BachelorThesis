#!/usr/bin/env python3
"""Example usage of the database system."""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Backend.database.init import init_database, get_db_session
from Backend.database.utils import (
    create_user_with_session,
    create_chat_session_with_session,
    add_message_with_session,
    add_esco_skill_with_session
)
from Backend.database.models.messages import MessageType


def main():
    """Demonstrate the database system."""
    print("🚀 Database System Example")
    print("=" * 50)
    
    # Initialize database
    print("1. Initializing database...")
    init_database()
    print("   ✅ Database initialized")
    
    # Create a user
    print("\n2. Creating a user...")
    try:
        user = create_user_with_session(
            username="john_doe",
            email="john.doe@example.com"
        )
        print(f"   ✅ Created user: {user.username} (ID: {user.user_id})")
    except Exception as e:
        print(f"   ⚠️  User might already exist: {e}")
        # Try to find the user manually
        with get_db_session() as session:
            from Backend.database.models.users import User
            user = session.query(User).filter(User.username == "john_doe").first()
            if user:
                print(f"   ℹ️  Using existing user: {user.username} (ID: {user.user_id})")
            else:
                print("   ❌ Failed to create or find user")
                return
    
    # Create a chat session
    print("\n3. Creating a chat session...")
    chat_session = create_chat_session_with_session(
        user=user,
        session_name="Skill Assessment Chat"
    )
    print(f"   ✅ Created chat session: {chat_session.session_name} (ID: {chat_session.session_id})")
    
    # Add messages to the chat session
    print("\n4. Adding messages...")
    
    # User message
    user_message = add_message_with_session(
        chat_session=chat_session,
        content="Hi! I have 5 years of experience in Python programming, machine learning, and data analysis.",
        message_type=MessageType.USER
    )
    print(f"   ✅ Added user message (ID: {user_message.message_id})")
    
    # Assistant message
    assistant_message = add_message_with_session(
        chat_session=chat_session,
        content="That's great! I can identify several valuable skills from your background.",
        message_type=MessageType.ASSISTANT
    )
    print(f"   ✅ Added assistant message (ID: {assistant_message.message_id})")
    
    # Add ESCO skills
    print("\n5. Adding ESCO skills...")
    
    # Python programming skill
    python_skill = add_esco_skill_with_session(
        chat_session=chat_session,
        origin_message=user_message,
        uri="http://data.europa.eu/esco/skill/python-programming",
        title="Python Programming",
        reference_language="en",
        preferred_label={"en": "Python Programming", "de": "Python-Programmierung"},
        description={"en": "Ability to write programs using Python programming language"}
    )
    print(f"   ✅ Added Python skill (ID: {python_skill.id})")
    
    # Machine learning skill
    ml_skill = add_esco_skill_with_session(
        chat_session=chat_session,
        origin_message=user_message,
        uri="http://data.europa.eu/esco/skill/machine-learning",
        title="Machine Learning",
        reference_language="en",
        preferred_label={"en": "Machine Learning", "de": "Maschinelles Lernen"},
        description={"en": "Knowledge of machine learning algorithms and techniques"}
    )
    print(f"   ✅ Added Machine Learning skill (ID: {ml_skill.id})")
    
    # Demonstrate manual session management
    print("\n6. Querying data with manual session management...")
    with get_db_session() as session:
        from Backend.database.models.users import User
        from Backend.database.models.messages import ChatSession, ChatMessage
        from Backend.database.models.skills import ESCOSkill
        
        # Count records
        user_count = session.query(User).count()
        session_count = session.query(ChatSession).count()
        message_count = session.query(ChatMessage).count()
        skill_count = session.query(ESCOSkill).count()
        
        print(f"   📊 Total users: {user_count}")
        print(f"   📊 Total chat sessions: {session_count}")
        print(f"   📊 Total messages: {message_count}")
        print(f"   📊 Total ESCO skills: {skill_count}")
        
        # Display messages from our session
        messages = session.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.session_id
        ).order_by(ChatMessage.timestamp).all()
        
        print(f"\n   Conversation in session {chat_session.session_id}:")
        for message in messages:
            role = message.role.value.upper()
            content = message.message_content[:100] + "..." if len(message.message_content) > 100 else message.message_content
            print(f"   {role}: {content}")
        
        # Display skills from our session
        skills = session.query(ESCOSkill).filter(
            ESCOSkill.session_id == chat_session.session_id
        ).all()
        
        print(f"\n   Identified skills:")
        for skill in skills:
            print(f"   🎯 {skill.title}")
    
    print("\n🎉 Example completed successfully!")
    print("\nYou can now:")
    print("- Run the API server: uv run uvicorn Backend.api:app --reload")
    print("- Access the database directly through the utilities")


if __name__ == "__main__":
    main()
