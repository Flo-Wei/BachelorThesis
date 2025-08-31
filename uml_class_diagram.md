# UML Class Diagram - AI Chatbot Application

This document contains the UML class diagram for the AI chatbot application backend, showing the main classes, their relationships, and structure.

## Class Diagram

```mermaid
classDiagram
    %% Database Models
    class User {
        +int user_id
        +str username
        +str email
        +datetime created_at
        +List~ChatSession~ chat_sessions
    }
    
    class ChatSession {
        +int session_id
        +int user_id
        +str session_name
        +datetime created_at
        +datetime updated_at
        +User user
        +List~ChatMessage~ chat_messages
        +List~ESCOSkillModel~ esco_skills
        +add_message(session, message)
        +get_messages(role)
        +get_last_message(role)
        +get_total_usage()
        +to_openai_input()
    }
    
    class ChatMessage {
        +int message_id
        +int session_id
        +MessageType role
        +str message_content
        +int usage
        +str model
        +datetime timestamp
        +ChatSession chat_session
        +List~ESCOSkillModel~ derived_skills_esco
        +from_openai_message(session, message)
    }
    
    class ESCOSkillModel {
        +int id
        +int session_id
        +int origin_message_id
        +SkillSystem skill_system
        +str uri
        +str title
        +str reference_language
        +Dict~str,str~ preferred_label
        +Dict~str,str~ description
        +Dict~str,Any~ links
        +ChatSession chat_session
        +ChatMessage origin_message
        +get_preferred_label(language)
        +get_description(language)
        +from_pydantic(skill)
    }
    
    class ChatSkillBase {
        +int id
        +int session_id
        +int origin_message_id
        +SkillSystem skill_system
        +from_pydantic(skill)
    }
    
    %% Enums
    class MessageType {
        <<enumeration>>
        USER
        ASSISTANT
        SYSTEM
    }
    
    class SkillSystem {
        <<enumeration>>
        ESCO
    }
    
    %% LLM Classes
    class BaseLLM {
        <<abstract>>
        +str model_name
        +ModelConfig config
        +chat(chat_session, db_session)*
        +extract_skills(instruction, message)*
        +map_skill(instruction, skill, available_skills)*
    }
    
    class OpenAILLM {
        +OpenAI client
        +chat(chat_session, db_session)
        +extract_skills(instruction, message)
        +map_skill(instruction, skill, available_skills)
    }
    
    %% Skill Classes
    class BaseSkill {
        <<abstract>>
    }
    
    class CustomSkill {
        +str name
        +Literal type
        +float confidence
        +str evidence
    }
    
    class ESCOSkill {
        +str uri
        +str title
        +str reference_language
        +Dict~str,str~ preferred_label
        +Dict~str,str~ description
        +dict links
        +get_preferred_label(language)
        +get_description(language)
    }
    
    class SkillList {
        +List~BaseSkill~ skills
        +get_skill_by_id(id)
    }
    
    class CustomSkillList {
        +List~CustomSkill~ skills
        +get_skill_by_id(id)
    }
    
    %% Model Configuration
    class ModelConfig {
        +float temperature
        +int max_tokens
        +float top_p
        +List~str~ stop
        +to_dict()
    }
    
    class ModelConfigOpenAI {
        +str response_format
        +int seed
        +List~dict~ tools
        +str tool_choice
        +str user
        +Dict~int,float~ logit_bias
        +bool logprobs
        +int top_logprobs
    }
    
    %% Database Handlers
    class BaseSkillDatabaseHandler {
        <<abstract>>
        +str url
    }
    
    class ESCODatabase {
        +str language
        +search_skills(text, limit)
    }
    
    %% FastAPI Application
    class FastAPI {
        +lifespan()
        +add_middleware()
        +include_router()
    }
    
    %% Router Classes
    class UsersRouter {
        +register_user()
        +login_user()
        +get_user()
        +list_users()
    }
    
    class SessionsRouter {
        +create_session()
        +get_user_sessions()
        +get_session()
        +update_session()
        +get_session_messages()
        +get_session_skills()
        +get_all_session_skills()
    }
    
    class ChatRouter {
        +chat_with_user()
        +set_dependencies()
        +get_llm()
        +get_esco_database_handler()
    }
    
    class SkillsRouter {
        +get_skill_systems()
    }
    
    %% Authentication
    class Auth {
        +create_access_token()
        +verify_token()
        +get_current_user()
    }
    
    %% Relationships
    User --o ChatSession : "has"
    ChatSession --o ChatMessage : "contains"
    ChatSession --o ESCOSkillModel : "has"
    ChatMessage --o ESCOSkillModel : "derives"
    ChatSkillBase <|-- ESCOSkillModel : "inherits"
    BaseLLM <|-- OpenAILLM : "implements"
    BaseSkill <|-- CustomSkill : "inherits"
    BaseSkill <|-- ESCOSkill : "inherits"
    SkillList <|-- CustomSkillList : "inherits"
    ModelConfig <|-- ModelConfigOpenAI : "inherits"
    BaseSkillDatabaseHandler <|-- ESCODatabase : "inherits"
    
    FastAPI --> UsersRouter : "includes"
    FastAPI --> SessionsRouter : "includes"
    FastAPI --> ChatRouter : "includes"
    FastAPI --> SkillsRouter : "includes"
    
    ChatRouter --> BaseLLM : "uses"
    ChatRouter --> ESCODatabase : "uses"
    OpenAILLM --> ModelConfigOpenAI : "configures"
    OpenAILLM --> ChatMessage : "creates"
    OpenAILLM --> ESCOSkillModel : "maps to"
```

## Class Descriptions

### Database Models
- **User**: Represents application users with authentication and chat session management
- **ChatSession**: Manages chat conversations and their associated messages and skills
- **ChatMessage**: Individual messages within chat sessions with metadata
- **ESCOSkillModel**: ESCO skill mappings extracted from chat conversations
- **ChatSkillBase**: Abstract base class for different skill system implementations

### Core Classes
- **BaseLLM**: Abstract base class for LLM implementations
- **OpenAILLM**: Concrete OpenAI API implementation
- **BaseSkill**: Abstract base for skill representations
- **ESCOSkill**: ESCO skill data structure
- **CustomSkill**: User-defined skill extraction

### Configuration & Handlers
- **ModelConfig**: Base configuration for LLM models
- **ModelConfigOpenAI**: OpenAI-specific configuration options
- **BaseSkillDatabaseHandler**: Abstract base for skill database handlers
- **ESCODatabase**: ESCO API integration for skill search

### FastAPI Components
- **FastAPI**: Main application instance
- **UsersRouter**: User management endpoints
- **SessionsRouter**: Chat session management
- **ChatRouter**: Core chat functionality
- **SkillsRouter**: Skill-related endpoints
- **Auth**: JWT authentication and user verification

## Relationships

- **Composition**: Users have chat sessions, sessions contain messages and skills
- **Inheritance**: Multiple classes extend abstract base classes
- **Association**: Routers use LLM and database handlers
- **Dependency**: FastAPI includes various router modules
