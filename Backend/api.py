from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from Backend.logging_config import setup_logging
from Backend.database.init import init_database
from Backend.classes.LLM import OpenAILLM
from Backend.classes.Skill_Database_Handler import ESCODatabase
from Backend.routers import users, sessions, chat, skills, utils

# Set up logging
setup_logging()
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

        # Initialize LLM and store in app state
        app.state.llm = OpenAILLM(model_name="gpt-4o-mini")
        logger.info("LLM initialized successfully")

        # Initialize available skills-Database Manager
        app.state.esco_database_handler = ESCODatabase()
        logger.info("ESCO database handler initialized successfully")

        # Set dependencies for chat router to avoid circular imports
        from Backend.routers.chat import set_dependencies
        set_dependencies(app.state.llm, app.state.esco_database_handler)

    except Exception as e:
        logger.exception(f"Failed to initialize application: {e}")
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

# Global exception handler to catch all unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that logs full stack traces."""
    logger.exception(f"Unhandled exception occurred: {exc}")
    
    # In production, you might want to hide the stack trace from the response
    # and just return a generic error message
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "message": str(exc)
        }
    )

# Include routers
app.include_router(users.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(skills.router)
app.include_router(utils.router)