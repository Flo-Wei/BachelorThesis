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
        subprocess.run([sys.executable, "websocket_server.py"])
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
