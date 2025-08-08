# static_server.py
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from current directory or specify your frontend folder
        super().__init__(*args, directory=str(Path.cwd()), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Handle root path
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

def start_frontend_server():
    PORT = 8000
    HOST = '0.0.0.0'  # Accept external connections
    
    # Check if running files exist
    frontend_files = ['index.html', 'topology.js', 'style.css']
    missing_files = [f for f in frontend_files if not Path(f).exists()]
    
    if missing_files:
        print(f"⚠️ Missing frontend files: {missing_files}")
        print("📁 Current directory:", Path.cwd())
        print("📄 Available files:", [f.name for f in Path.cwd().iterdir() if f.is_file()])
    
    try:
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            print(f"🌐 Frontend server running on:")
            print(f"   http://activnet.prutech:8000")
            print(f"   http://192.168.15.207:8000") 
            print(f"   http://localhost:8000")
            print(f"📁 Serving files from: {Path.cwd()}")
            print("🛑 Press Ctrl+C to stop")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    start_frontend_server()