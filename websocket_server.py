# This file creates a simple web server that can handle real-time chat using WebSockets
# WebSockets allow the browser and server to talk to each other in real-time (like a phone call)
# Regular web pages can only send requests and get responses (like sending letters back and forth)

# Import the tools we need
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # FastAPI is a modern web framework, WebSocket handles real-time connections
from fastapi.middleware.cors import CORSMiddleware  # CORS allows your frontend to talk to your backend (security thing)
from fastapi.responses import HTMLResponse  # Lets us send HTML pages to the browser
import uvicorn  # This is the server that actually runs our FastAPI app
import json  # For converting data between Python and text format
import logging  # For keeping track of what's happening (like a diary)
from pathlib import Path  # For working with file paths
from Backend.classes.LLM import OpenAILLM
from Backend.classes.Model_Config import ModelConfigOpenAI
from Backend.classes.LLM_Message import ChatHistory, LLMMessage
from Backend.classes.Skill_Classes import BaseSkill, CustomSkill, CustomSkillList
from Backend.classes.Skill_Database_Handler import ESCODatabase
from Backend.utils import get_prompt

# Set up logging - this creates a diary of what's happening in your server
logging.basicConfig(level=logging.INFO)  # INFO level means "tell me about important stuff"
logger = logging.getLogger(__name__)  # Create a logger object to write diary entries

# Create our web application - this is like creating a new website
app = FastAPI(
    title="Simple Chatbot API",  # The name that shows up in the API docs
    description="Minimal FastAPI server for testing",  # Description of what this does
    version="1.0.0"  # Version number
)

# CORS middleware - this is like a security guard that decides who can talk to your server
# In development, we allow everyone ("*") but in production you'd restrict this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any website to connect to your server
    allow_credentials=True,  # Allow cookies and authentication
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all types of headers
)

# This class manages all the people connected to your chat
class ConnectionManager:
    def __init__(self):
        # Keep track of everyone who's currently connected to the chat
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        # When someone wants to join the chat
        await websocket.accept()  # Say "yes, you can join"
        self.active_connections.append(websocket)  # Add them to our list of connected people
        logger.info(f"Client connected. Total clients: {len(self.active_connections)}")  # Write in our diary
    
    def disconnect(self, websocket: WebSocket):
        # When someone leaves the chat
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)  # Remove them from our list
            logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")  # Write in our diary
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        # Send a message to one specific person
        try:
            await websocket.send_text(message)  # Send the message
        except Exception as e:
            # If something goes wrong (like they disconnected), remove them from our list
            logger.error(f"Error sending message: {e}")  # Write the error in our diary
            self.disconnect(websocket)

# Create one manager to handle all connections
manager = ConnectionManager()
llm = OpenAILLM(model_name="gpt-4.1-2025-04-14") # TODO: Add config

# This route serves the main webpage when someone visits your website
@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Serve the frontend HTML file"""
    # Look for the HTML file that contains your chat interface
    frontend_path = Path("Frontend/index.html")
    if frontend_path.exists():
        # If the file exists, read it and send it to the browser
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        # If the file doesn't exist, send a simple error message
        return HTMLResponse(content="<h1>Frontend not found</h1>")

# This route lets other programs check if your server is working
@app.get("/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "ok",  # Server is working fine
        "connections": len(manager.active_connections),  # How many people are currently chatting
        "llm_available": llm is not None  # Whether the AI model is working
    }

# This is the main chat endpoint - it handles real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for chat"""
    # When someone connects to the chat
    await manager.connect(websocket)  # Add them to our list
    
    try:
        chat_history = ChatHistory()
        chat_history.add_message(LLMMessage(role="system", content=get_prompt("interviewer")))

        # Keep listening for messages from this person
        while True:
            # Wait for them to send a message
            data = await websocket.receive_text()
            
            try:
                # Try to understand what they sent (convert from text to Python data)
                message_data = json.loads(data)
                message_type = message_data.get('type')  # What kind of message is this?
                content = message_data.get('content', '')  # What did they actually say?
                
                if message_type == 'message':
                    # If they sent a chat message
                    chat_history.add_message(LLMMessage(role="user", content=content))

                    # RIGHT NOW: We just echo back what they said
                    # THIS IS WHERE YOU PUT YOUR LLM CODE!
                    # Instead of echoing, you'd call your AI model here
                    
                    response_message = llm.chat(chat_history)
                    chat_history.add_message(response_message)
                    
                    response = {
                        'type': 'message',  # This is a chat message
                        'content': response_message.content,  # Right now just repeats what they said
                        'timestamp': message_data.get('timestamp', '')  # When they sent it
                    }
                    
                    # Send the response back to them
                    await manager.send_personal_message(json.dumps(response), websocket)
                    
            except json.JSONDecodeError:
                # If they sent something that's not valid JSON (like random text)
                logger.warning("Invalid JSON received")  # Write in our diary
                await manager.send_personal_message(json.dumps({
                    'type': 'error',
                    'content': 'Invalid JSON format'  # Tell them they sent bad data
                }), websocket)
                
    except WebSocketDisconnect:
        # If they close their browser or lose connection
        manager.disconnect(websocket)  # Remove them from our list
    except Exception as e:
        # If something else goes wrong
        logger.error(f"WebSocket error: {e}")  # Write the error in our diary
        manager.disconnect(websocket)  # Remove them from our list

# This runs when you start the file directly (not when importing it)
if __name__ == "__main__":
    # Start the web server
    uvicorn.run(
        app,  # Use our FastAPI app
        host="localhost",  # Only allow connections from your own computer
        port=8000,  # Use port 8000 (like a specific phone number)
        reload=True  # Automatically restart when you change the code (good for development)
    )
