# Web Diagram - AI Chatbot Application Architecture

This document contains a comprehensive web diagram showing the system architecture, data flow, and component interactions for the AI chatbot application.

## System Architecture Diagram

```mermaid
graph TB
    %% Frontend Layer
    subgraph "Frontend Layer"
        UI[User Interface<br/>HTML/CSS/JS]
        ChatUI[Chat Interface]
        UserUI[User Management]
        SkillsUI[Skills Display]
    end
    
    %% API Gateway Layer
    subgraph "API Gateway Layer"
        FastAPI[FastAPI Application<br/>Main Entry Point]
        CORS[CORS Middleware]
        Auth[Authentication<br/>JWT Tokens]
    end
    
    %% Router Layer
    subgraph "Router Layer"
        UsersRouter[Users Router<br/>/users/*]
        SessionsRouter[Sessions Router<br/>/sessions/*]
        ChatRouter[Chat Router<br/>/chat/*]
        SkillsRouter[Skills Router<br/>/skills/*]
        UtilsRouter[Utils Router]
    end
    
    %% Business Logic Layer
    subgraph "Business Logic Layer"
        LLMService[LLM Service<br/>OpenAI Integration]
        SkillService[Skill Extraction<br/>& Mapping Service]
        ChatService[Chat Processing<br/>Service]
        UserService[User Management<br/>Service]
    end
    
    %% Data Layer
    subgraph "Data Layer"
        Database[(SQLite Database<br/>SQLModel)]
        UserModel[User Models]
        ChatModels[Chat Models]
        SkillModels[Skill Models]
    end
    
    %% External Services
    subgraph "External Services"
        OpenAI[OpenAI API<br/>GPT Models]
        ESCOAPI[ESCO API<br/>Skills Database]
    end
    
    %% Data Flow
    UI --> FastAPI
    ChatUI --> ChatRouter
    UserUI --> UsersRouter
    SkillsUI --> SkillsRouter
    
    FastAPI --> CORS
    FastAPI --> Auth
    FastAPI --> UsersRouter
    FastAPI --> SessionsRouter
    FastAPI --> ChatRouter
    FastAPI --> SkillsRouter
    FastAPI --> UtilsRouter
    
    UsersRouter --> UserService
    SessionsRouter --> ChatService
    ChatRouter --> ChatService
    ChatRouter --> LLMService
    ChatRouter --> SkillService
    SkillsRouter --> SkillService
    
    UserService --> UserModel
    ChatService --> ChatModels
    SkillService --> SkillModels
    
    UserModel --> Database
    ChatModels --> Database
    SkillModels --> Database
    
    LLMService --> OpenAI
    SkillService --> ESCOAPI
    
    %% Authentication Flow
    Auth --> UserModel
    Auth --> Database
    
    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef api fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef router fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef service fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef data fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef external fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class UI,ChatUI,UserUI,SkillsUI frontend
    class FastAPI,CORS,Auth api
    class UsersRouter,SessionsRouter,ChatRouter,SkillsRouter,UtilsRouter router
    class LLMService,SkillService,ChatService,UserService service
    class Database,UserModel,ChatModels,SkillModels data
    class OpenAI,ESCOAPI external
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as FastAPI
    participant Auth as Auth Service
    participant CR as Chat Router
    participant LLM as LLM Service
    participant Skill as Skill Service
    participant DB as Database
    participant OpenAI as OpenAI API
    participant ESCO as ESCO API
    
    %% User Authentication
    U->>F: Login with username
    F->>API: POST /users/login
    API->>Auth: Verify credentials
    Auth->>DB: Query user
    DB-->>Auth: User data
    Auth-->>API: JWT token
    API-->>F: Token response
    F-->>U: Store token & redirect
    
    %% Chat Session Creation
    U->>F: Start new chat
    F->>API: POST /users/{id}/sessions
    API->>Auth: Verify JWT token
    Auth-->>API: User authenticated
    API->>CR: Create session
    CR->>DB: Save session
    DB-->>CR: Session created
    CR-->>API: Session response
    API-->>F: Session data
    F-->>U: Chat interface
    
    %% Chat Message Processing
    U->>F: Send message
    F->>API: POST /users/{id}/chat
    API->>Auth: Verify JWT token
    Auth-->>API: User authenticated
    API->>CR: Process chat
    CR->>DB: Save user message
    DB-->>CR: Message saved
    CR->>LLM: Generate response
    LLM->>OpenAI: API call
    OpenAI-->>LLM: AI response
    LLM->>DB: Save AI message
    DB-->>LLM: Message saved
    
    %% Skill Extraction
    CR->>Skill: Extract skills
    Skill->>LLM: Extract skills from message
    LLM->>OpenAI: Skill extraction API call
    OpenAI-->>LLM: Extracted skills
    LLM-->>Skill: Skills list
    Skill->>ESCO: Search matching skills
    ESCO-->>Skill: Available skills
    Skill->>LLM: Map skills
    LLM->>OpenAI: Skill mapping API call
    OpenAI-->>LLM: Mapped skills
    LLM-->>Skill: Mapped skills
    Skill->>DB: Save mapped skills
    DB-->>Skill: Skills saved
    
    %% Response to User
    CR-->>API: Chat response with skills
    API-->>F: Response data
    F-->>U: Display AI response & skills
```

## Component Interaction Diagram

```mermaid
flowchart LR
    subgraph "User Interface"
        A[User Input]
        B[Chat Display]
        C[Skills Visualization]
    end
    
    subgraph "API Layer"
        D[FastAPI App]
        E[Authentication]
        F[Request Validation]
    end
    
    subgraph "Business Logic"
        G[Chat Processing]
        H[LLM Integration]
        I[Skill Extraction]
        J[Skill Mapping]
    end
    
    subgraph "Data Storage"
        K[User Data]
        L[Chat Sessions]
        M[Messages]
        N[Skills]
    end
    
    subgraph "External APIs"
        O[OpenAI GPT]
        P[ESCO Skills]
    end
    
    A --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> O
    O --> H
    H --> I
    I --> J
    J --> P
    P --> J
    
    G --> K
    G --> L
    G --> M
    I --> N
    
    H --> M
    J --> N
    
    B --> M
    C --> N
```

## Technology Stack Overview

### Frontend
- **HTML/CSS/JavaScript**: Static web interface
- **Chat Interface**: Real-time chat functionality
- **User Management**: Registration, login, profile
- **Skills Display**: Visual representation of extracted skills

### Backend
- **FastAPI**: Modern Python web framework
- **SQLModel**: SQL database ORM with Pydantic
- **JWT Authentication**: Secure user authentication
- **CORS Middleware**: Cross-origin resource sharing

### AI Integration
- **OpenAI API**: GPT model integration
- **Custom Prompts**: Skill extraction and mapping
- **Response Parsing**: Structured output handling

### Data Management
- **SQLite Database**: Local data storage
- **ESCO API**: European Skills/Competences database
- **Skill Mapping**: AI-powered skill matching

### Architecture Patterns
- **RESTful API**: Standard HTTP endpoints
- **Dependency Injection**: Service layer management
- **Repository Pattern**: Data access abstraction
- **Middleware Architecture**: Request/response processing

## Key Features

1. **User Authentication**: JWT-based secure login
2. **Chat Sessions**: Persistent conversation management
3. **AI Integration**: OpenAI GPT model integration
4. **Skill Extraction**: Automatic skill identification from conversations
5. **ESCO Mapping**: Professional skill classification
6. **Real-time Processing**: Immediate AI responses
7. **Data Persistence**: Complete conversation history
8. **Scalable Architecture**: Modular component design
```

## System Flow Summary

The application follows a **layered architecture** pattern:

1. **Frontend Layer**: User interface for interaction
2. **API Gateway**: FastAPI application with middleware
3. **Router Layer**: Endpoint organization and routing
4. **Business Logic**: Core application services
5. **Data Layer**: Database models and persistence
6. **External Services**: OpenAI and ESCO API integration

**Data flows** from user input through authentication, processing, AI integration, skill extraction, and back to the user with enriched responses and skill mappings.
