from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlmodel import Session
import logging

from Backend.database.init import init_database, get_db

# Set up logging
logging.basicConfig(level=logging.INFO)
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

@app.get("/")
async def root():
    """Root endpoint for basic health check."""
    return {"message": "Bachelor Thesis Chatbot API is running"}
