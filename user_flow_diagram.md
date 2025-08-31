# User Flow Diagram - AI Chatbot Application

This document contains comprehensive user flow diagrams showing the complete user journey through the AI chatbot application, including all major interactions, decision points, and user paths.

## Main User Flow Diagram

```mermaid
flowchart TD
    Start([User arrives at application]) --> Landing{First time user?}
    
    %% New User Path
    Landing -->|Yes| Register[Register new account]
    Register --> EnterDetails[Enter username & email]
    EnterDetails --> ValidateRegistration{Validation successful?}
    ValidateRegistration -->|No| ShowError[Show error message]
    ShowError --> EnterDetails
    ValidateRegistration -->|Yes| AccountCreated[Account created successfully]
    
    %% Existing User Path
    Landing -->|No| Login[Login with existing account]
    Login --> EnterCredentials[Enter username]
    EnterCredentials --> ValidateLogin{Valid credentials?}
    ValidateLogin -->|No| ShowLoginError[Show login error]
    ShowLoginError --> EnterCredentials
    ValidateLogin -->|Yes| GenerateToken[Generate JWT token]
    
    %% Common Path After Authentication
    AccountCreated --> GenerateToken
    GenerateToken --> Dashboard[User Dashboard]
    
    %% Dashboard Options
    Dashboard --> DashboardChoice{What would you like to do?}
    
    %% Start New Chat
    DashboardChoice -->|Start New Chat| NewChat[Create new chat session]
    NewChat --> EnterSessionName[Enter session name optional]
    EnterSessionName --> ChatInterface[Chat Interface]
    
    %% Continue Existing Chat
    DashboardChoice -->|Continue Chat| ViewSessions[View existing sessions]
    ViewSessions --> SelectSession[Select chat session]
    SelectSession --> ChatInterface
    
    %% View Skills
    DashboardChoice -->|View Skills| SkillsOverview[Skills Overview]
    SkillsOverview --> SkillsBySession[View skills by session]
    SkillsBySession --> SelectSessionForSkills[Select session]
    SelectSessionForSkills --> DisplaySkills[Display extracted skills]
    DisplaySkills --> BackToDashboard[Return to Dashboard]
    
    %% Profile Management
    DashboardChoice -->|Manage Profile| ProfileOptions{Profile action?}
    ProfileOptions -->|View Profile| ShowProfile[Display user profile]
    ProfileOptions -->|Edit Profile| EditProfile[Edit profile information]
    EditProfile --> SaveProfile[Save changes]
    SaveProfile --> ProfileUpdated[Profile updated]
    ShowProfile --> BackToDashboard
    ProfileUpdated --> BackToDashboard
    
    %% Chat Interface Flow
    ChatInterface --> ChatChoice{Chat action?}
    
    %% Send Message
    ChatChoice -->|Send Message| TypeMessage[Type message]
    TypeMessage --> ValidateMessage{Message valid?}
    ValidateMessage -->|No| ShowMessageError[Show validation error]
    ShowMessageError --> TypeMessage
    ValidateMessage -->|Yes| SendMessage[Send message to AI]
    
    %% AI Processing
    SendMessage --> AIProcessing[AI processing...]
    AIProcessing --> ExtractSkills[Extract skills from message]
    ExtractSkills --> MapSkills[Map to ESCO skills]
    MapSkills --> GenerateResponse[Generate AI response]
    
    %% Display Results
    GenerateResponse --> DisplayResponse[Display AI response]
    DisplayResponse --> DisplaySkillsInChat[Display extracted skills]
    DisplaySkillsInChat --> ContinueChat{Continue chatting?}
    
    %% Continue or End Chat
    ContinueChat -->|Yes| ChatChoice
    ContinueChat -->|No| EndChat[End chat session]
    EndChat --> SaveSession[Save session data]
    SaveSession --> SessionSaved[Session saved]
    SessionSaved --> BackToDashboard
    
    %% Session Management
    ViewSessions --> SessionAction{Session action?}
    SessionAction -->|Open Session| SelectSession
    SessionAction -->|Delete Session| ConfirmDelete[Confirm deletion]
    ConfirmDelete --> DeleteSession[Delete session]
    DeleteSession --> SessionDeleted[Session deleted]
    SessionDeleted --> ViewSessions
    SessionAction -->|Rename Session| RenameSession[Enter new name]
    RenameSession --> UpdateSessionName[Update session name]
    UpdateSessionName --> NameUpdated[Name updated]
    NameUpdated --> ViewSessions
    
    %% Return to Dashboard
    BackToDashboard --> DashboardChoice
    
    %% Logout
    DashboardChoice -->|Logout| ConfirmLogout[Confirm logout]
    ConfirmLogout --> Logout[Clear session & logout]
    Logout --> Start
    
    %% Styling
    classDef startEnd fill:#ff6b6b,stroke:#d63031,stroke-width:3px,color:#fff
    classDef process fill:#74b9ff,stroke:#0984e3,stroke-width:2px,color:#fff
    classDef decision fill:#fdcb6e,stroke:#e17055,stroke-width:2px,color:#000
    classDef data fill:#55a3ff,stroke:#2d3436,stroke-width:2px,color:#fff
    classDef error fill:#fd79a8,stroke:#e84393,stroke-width:2px,color:#fff
    classDef success fill:#00b894,stroke:#00a085,stroke-width:2px,color:#fff
    
    class Start,EndChat,Logout startEnd
    class Register,Login,EnterDetails,EnterCredentials,NewChat,EnterSessionName,ChatInterface,TypeMessage,SendMessage,AIProcessing,ExtractSkills,MapSkills,GenerateResponse,DisplayResponse,DisplaySkillsInChat,SaveSession,ViewSessions,SelectSession,SkillsOverview,SkillsBySession,SelectSessionForSkills,DisplaySkills,ShowProfile,EditProfile,SaveProfile,DeleteSession,RenameSession,UpdateSessionName process
    class Landing,ValidateRegistration,ValidateLogin,ValidateMessage,DashboardChoice,ContinueChat,SessionAction,ProfileOptions,ConfirmDelete,ConfirmLogout decision
    class Dashboard,AccountCreated,GenerateToken,ProfileUpdated,SessionSaved,SessionDeleted,NameUpdated data
    class ShowError,ShowLoginError,ShowMessageError error
    class ChatInterface,DisplayResponse,DisplaySkillsInChat success
```

## Detailed Chat Flow Diagram

```mermaid
flowchart TD
    StartChat([User starts chat]) --> InitSession{New or existing session?}
    
    %% New Session Flow
    InitSession -->|New| CreateSession[Create new session]
    CreateSession --> SetSessionName[Set session name]
    SetSessionName --> SessionReady[Session ready]
    
    %% Existing Session Flow
    InitSession -->|Existing| LoadSession[Load existing session]
    LoadSession --> LoadHistory[Load chat history]
    LoadHistory --> SessionReady
    
    %% Chat Loop
    SessionReady --> ChatLoop[Chat Loop]
    ChatLoop --> UserInput[User types message]
    UserInput --> ValidateInput{Message valid?}
    ValidateInput -->|No| ShowValidationError[Show validation error]
    ShowValidationError --> UserInput
    
    ValidateInput -->|Yes| SaveUserMessage[Save user message to DB]
    SaveUserMessage --> PrepareContext[Prepare chat context]
    PrepareContext --> CallOpenAI[Call OpenAI API]
    
    %% OpenAI Processing
    CallOpenAI --> AIResponse[Receive AI response]
    AIResponse --> ParseResponse[Parse AI response]
    ParseResponse --> SaveAIResponse[Save AI response to DB]
    SaveAIResponse --> UpdateSession[Update session timestamp]
    
    %% Skill Extraction Process
    UpdateSession --> StartSkillExtraction[Start skill extraction]
    StartSkillExtraction --> ExtractSkillsPrompt[Send skill extraction prompt]
    ExtractSkillsPrompt --> CallOpenAISkills[Call OpenAI for skills]
    CallOpenAISkills --> ParseSkills[Parse extracted skills]
    
    %% Skill Mapping Process
    ParseSkills --> MapToESCO[Map skills to ESCO]
    MapToESCO --> SearchESCO[Search ESCO database]
    SearchESCO --> GetESCOResults[Get ESCO results]
    GetESCOResults --> MapSkillsPrompt[Send skill mapping prompt]
    MapSkillsPrompt --> CallOpenAIMapping[Call OpenAI for mapping]
    CallOpenAIMapping --> ParseMapping[Parse skill mapping]
    ParseMapping --> SaveMappedSkills[Save mapped skills to DB]
    
    %% Display Results
    SaveMappedSkills --> DisplayAIResponse[Display AI response]
    DisplayAIResponse --> DisplaySkills[Display extracted skills]
    DisplaySkills --> UpdateUI[Update chat interface]
    
    %% Continue or End
    UpdateUI --> ContinueChat{Continue chatting?}
    ContinueChat -->|Yes| ChatLoop
    ContinueChat -->|No| EndSession[End chat session]
    EndSession --> SaveFinalState[Save final session state]
    SaveFinalState --> ReturnToDashboard[Return to dashboard]
    
    %% Error Handling
    CallOpenAI -->|Error| HandleAPIError[Handle API error]
    HandleAPIError --> ShowAPIError[Show error message]
    ShowAPIError --> ChatLoop
    
    CallOpenAISkills -->|Error| HandleSkillError[Handle skill extraction error]
    HandleSkillError --> SkipSkills[Skip skill extraction]
    SkipSkills --> DisplayAIResponse
    
    CallOpenAIMapping -->|Error| HandleMappingError[Handle mapping error]
    HandleMappingError --> SkipMapping[Skip skill mapping]
    SkipMapping --> DisplayAIResponse
    
    %% Styling
    classDef startEnd fill:#ff6b6b,stroke:#d63031,stroke-width:3px,color:#fff
    classDef process fill:#74b9ff,stroke:#0984e3,stroke-width:2px,color:#fff
    classDef decision fill:#fdcb6e,stroke:#e17055,stroke-width:2px,color:#000
    classDef data fill:#55a3ff,stroke:#2d3436,stroke-width:2px,color:#fff
    classDef error fill:#fd79a8,stroke:#e84393,stroke-width:2px,color:#fff
    classDef success fill:#00b894,stroke:#00a085,stroke-width:2px,color:#fff
    
    class StartChat,EndSession,ReturnToDashboard startEnd
    class CreateSession,SetSessionName,LoadSession,LoadHistory,UserInput,SaveUserMessage,PrepareContext,CallOpenAI,AIResponse,ParseResponse,SaveAIResponse,UpdateSession,StartSkillExtraction,ExtractSkillsPrompt,CallOpenAISkills,ParseSkills,MapToESCO,SearchESCO,GetESCOResults,MapSkillsPrompt,CallOpenAIMapping,ParseMapping,SaveMappedSkills,DisplayAIResponse,DisplaySkills,UpdateUI,SaveFinalState process
    class InitSession,ValidateInput,ContinueChat decision
    class SessionReady,ChatLoop,SessionReady data
    class ShowValidationError,HandleAPIError,ShowAPIError,HandleSkillError,HandleMappingError error
    class DisplayAIResponse,DisplaySkills success
```

## Authentication Flow Diagram

```mermaid
flowchart TD
    AuthStart([Authentication Start]) --> AuthMethod{Authentication method?}
    
    %% Registration Flow
    AuthMethod -->|Register| RegStart[Start registration]
    RegStart --> EnterRegData[Enter registration data]
    EnterRegData --> ValidateRegData{Data valid?}
    ValidateRegData -->|No| ShowRegErrors[Show validation errors]
    ShowRegErrors --> EnterRegData
    ValidateRegData -->|Yes| CheckUserExists{User exists?}
    CheckUserExists -->|Yes| ShowUserExists[Show user exists error]
    ShowUserExists --> EnterRegData
    CheckUserExists -->|No| CreateUser[Create user account]
    CreateUser --> UserCreated[User created successfully]
    
    %% Login Flow
    AuthMethod -->|Login| LoginStart[Start login]
    LoginStart --> EnterLoginData[Enter login credentials]
    EnterLoginData --> ValidateLoginData{Credentials valid?}
    ValidateLoginData -->|No| ShowLoginErrors[Show login errors]
    ShowLoginErrors --> EnterLoginData
    ValidateLoginData -->|Yes| VerifyUser{User exists?}
    VerifyUser -->|No| ShowUserNotFound[Show user not found]
    ShowUserNotFound --> EnterLoginData
    VerifyUser -->|Yes| GenerateJWT[Generate JWT token]
    
    %% Common Success Path
    UserCreated --> GenerateJWT
    GenerateJWT --> StoreToken[Store JWT token]
    StoreToken --> RedirectToApp[Redirect to application]
    RedirectToApp --> AuthComplete[Authentication complete]
    
    %% Token Validation Flow
    AuthComplete --> TokenValidation{Token valid?}
    TokenValidation -->|No| TokenExpired[Token expired/invalid]
    TokenExpired --> RedirectToLogin[Redirect to login]
    RedirectToLogin --> LoginStart
    TokenValidation -->|Yes| AccessGranted[Access granted]
    
    %% Logout Flow
    AccessGranted --> UserAction{User action?}
    UserAction -->|Logout| LogoutStart[Start logout]
    LogoutStart --> ClearToken[Clear JWT token]
    ClearToken --> ClearSession[Clear session data]
    ClearSession --> RedirectToAuth[Redirect to auth]
    RedirectToAuth --> AuthStart
    
    %% Styling
    classDef startEnd fill:#ff6b6b,stroke:#d63031,stroke-width:3px,color:#fff
    classDef process fill:#74b9ff,stroke:#0984e3,stroke-width:2px,color:#fff
    classDef decision fill:#fdcb6e,stroke:#e17055,stroke-width:2px,color:#000
    classDef data fill:#55a3ff,stroke:#2d3436,stroke-width:2px,color:#fff
    classDef error fill:#fd79a8,stroke:#e84393,stroke-width:2px,color:#fff
    classDef success fill:#00b894,stroke:#00a085,stroke-width:2px,color:#fff
    
    class AuthStart,AuthComplete,AccessGranted startEnd
    class RegStart,EnterRegData,CreateUser,LoginStart,EnterLoginData,GenerateJWT,StoreToken,RedirectToApp,ClearToken,ClearSession,RedirectToAuth process
    class AuthMethod,ValidateRegData,CheckUserExists,ValidateLoginData,VerifyUser,TokenValidation,UserAction decision
    class UserCreated data
    class ShowRegErrors,ShowUserExists,ShowLoginErrors,ShowUserNotFound,TokenExpired error
    class UserCreated,GenerateJWT,StoreToken success
```

## Skills Management Flow Diagram

```mermaid
flowchart TD
    SkillsStart([Skills Management Start]) --> SkillsAction{What to do with skills?}
    
    %% View Skills
    SkillsAction -->|View Skills| ViewSkillsStart[Start viewing skills]
    ViewSkillsStart --> SelectSessionForSkills[Select chat session]
    SelectSessionForSkills --> LoadSessionSkills[Load session skills]
    LoadSessionSkills --> DisplaySkillsList[Display skills list]
    DisplaySkillsList --> SkillsViewComplete[Skills viewing complete]
    
    %% Skills by Category
    SkillsAction -->|Skills by Category| CategoryView[View skills by category]
    CategoryView --> SelectCategory[Select skill category]
    SelectCategory --> FilterSkills[Filter skills by category]
    FilterSkills --> DisplayCategorySkills[Display category skills]
    DisplayCategorySkills --> CategoryViewComplete[Category view complete]
    
    %% Skills Analysis
    SkillsAction -->|Skills Analysis| AnalysisStart[Start skills analysis]
    AnalysisStart --> AnalyzeSkillPatterns[Analyze skill patterns]
    AnalyzeSkillPatterns --> GenerateInsights[Generate insights]
    GenerateInsights --> DisplayAnalysis[Display analysis results]
    DisplayAnalysis --> AnalysisComplete[Analysis complete]
    
    %% Export Skills
    SkillsAction -->|Export Skills| ExportStart[Start export]
    ExportStart --> SelectExportFormat{Export format?}
    SelectExportFormat -->|CSV| ExportCSV[Export to CSV]
    SelectExportFormat -->|PDF| ExportPDF[Export to PDF]
    SelectExportFormat -->|JSON| ExportJSON[Export to JSON]
    ExportCSV --> DownloadFile[Download file]
    ExportPDF --> DownloadFile
    ExportJSON --> DownloadFile
    DownloadFile --> ExportComplete[Export complete]
    
    %% Return to Main
    SkillsViewComplete --> ReturnToMain[Return to main menu]
    CategoryViewComplete --> ReturnToMain
    AnalysisComplete --> ReturnToMain
    ExportComplete --> ReturnToMain
    
    %% Styling
    classDef startEnd fill:#ff6b6b,stroke:#d63031,stroke-width:3px,color:#fff
    classDef process fill:#74b9ff,stroke:#0984e3,stroke-width:2px,color:#fff
    classDef decision fill:#fdcb6e,stroke:#e17055,stroke-width:2px,color:#000
    classDef data fill:#55a3ff,stroke:#2d3436,stroke-width:2px,color:#fff
    classDef success fill:#00b894,stroke:#00a085,stroke-width:2px,color:#fff
    
    class SkillsStart,ReturnToMain startEnd
    class ViewSkillsStart,SelectSessionForSkills,LoadSessionSkills,DisplaySkillsList,CategoryView,SelectCategory,FilterSkills,DisplayCategorySkills,AnalysisStart,AnalyzeSkillPatterns,GenerateInsights,DisplayAnalysis,ExportStart,ExportCSV,ExportPDF,ExportJSON,DownloadFile process
    class SkillsAction,SelectExportFormat decision
    class SkillsViewComplete,CategoryViewComplete,AnalysisComplete,ExportComplete data
    class DisplaySkillsList,DisplayCategorySkills,DisplayAnalysis,DownloadFile success
```

## User Journey Summary

### **1. Onboarding Journey**
- **First Visit**: User arrives and registers new account
- **Account Creation**: Username and email validation
- **Initial Setup**: Account created and JWT token generated

### **2. Authentication Journey**
- **Login Process**: Username-based authentication
- **Token Management**: JWT token generation and storage
- **Session Security**: Token validation on each request

### **3. Chat Experience Journey**
- **Session Management**: Create new or continue existing chats
- **Message Exchange**: Real-time chat with AI
- **Skill Extraction**: Automatic skill identification
- **ESCO Mapping**: Professional skill classification

### **4. Skills Management Journey**
- **Skills Viewing**: Browse extracted skills by session
- **Skills Analysis**: Pattern recognition and insights
- **Skills Export**: Multiple format export options

### **5. Profile Management Journey**
- **Profile Viewing**: Display user information
- **Profile Editing**: Update user details
- **Session History**: Manage chat sessions

### **6. Error Handling Journey**
- **Validation Errors**: Input validation feedback
- **API Errors**: Graceful error handling
- **Network Issues**: Connection error management

## Key User Experience Features

1. **Seamless Onboarding**: Simple registration and login process
2. **Intuitive Chat Interface**: Easy-to-use chat experience
3. **Real-time Processing**: Immediate AI responses and skill extraction
4. **Comprehensive Skills View**: Multiple ways to explore extracted skills
5. **Session Persistence**: Complete conversation history
6. **Error Recovery**: Clear error messages and recovery paths
7. **Responsive Design**: Works across different devices
8. **Export Functionality**: Multiple format options for skills data

## User Decision Points

- **Authentication Method**: Register new account vs. login existing
- **Session Management**: New chat vs. continue existing
- **Skills Exploration**: View by session vs. by category vs. analysis
- **Export Preferences**: CSV, PDF, or JSON format
- **Chat Continuation**: Continue chatting vs. end session
- **Profile Actions**: View vs. edit profile information
