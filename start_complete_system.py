#!/usr/bin/env python3
# ACTIVnet Combined Startup (File Processor + Web Server)

import sys
import os
import subprocess
import threading
from pathlib import Path

project_root = Path(__file__).parent
os.chdir(project_root)

def start_file_processor():
    """Start the file processor in a separate process"""
    try:
        subprocess.run([sys.executable, "start_file_processor.py"])
    except Exception as e:
        print(f"File processor error: {e}")

def start_web_server():
    """Start the web server in a separate process"""
    try:
        subprocess.run([sys.executable, "start_web_server.py"])
    except Exception as e:
        print(f"Web server error: {e}")

if __name__ == "__main__":
    print("🚀 Starting ACTIVnet Complete System")
    print("=" * 50)
    
    # Start file processor in background thread
    processor_thread = threading.Thread(target=start_file_processor, daemon=True)
    processor_thread.start()
    
    # Start web server in main thread  
    start_web_server()
