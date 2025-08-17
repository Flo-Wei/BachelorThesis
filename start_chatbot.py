#!/usr/bin/env python3
"""
Simple startup script for the chatbot
"""

import subprocess
import sys
import webbrowser
import time

def main():
    print("Starting simple chatbot...")
    
    # Start the FastAPI server
    try:
        print("Starting FastAPI server on http://localhost:8000")
        print("Open your browser and go to: http://localhost:8000")
        print("Press Ctrl+C to stop the server")
        
        # Use the module import string to avoid the reload warning
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "websocket_server:app", 
            "--host", "localhost", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
