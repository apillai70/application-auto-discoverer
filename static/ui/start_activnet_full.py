# start_activnet_full.py
import subprocess
import sys
import os
import time
import threading
from pathlib import Path

def start_api_server():
    """Start FastAPI server on port 8001"""
    print("🚀 Starting API server (port 8001)...")
    os.environ['ENVIRONMENT'] = 'production'
    
    try:
        # Get correct paths
        current_dir = Path.cwd()  # static/ui
        app_root = current_dir.parent.parent  # Go up to app root
        services_dir = app_root / "services"
        
        print(f"📁 Current: {current_dir}")
        print(f"📁 App root: {app_root}")
        print(f"📁 Services: {services_dir}")
        
        if not services_dir.exists():
            print(f"❌ Services directory not found: {services_dir}")
            return
            
        if not (services_dir / "main.py").exists():
            print(f"❌ main.py not found in: {services_dir}")
            return
        
        # Set Python path to include app_root so imports work
        env = os.environ.copy()
        env['PYTHONPATH'] = str(app_root)
        
        print(f"🔧 Setting PYTHONPATH: {app_root}")
        print(f"📄 Running: {services_dir / 'main.py'}")
        
        # Start the API server using uvicorn command with reload
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "services.main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload",
            "--reload-dir", str(app_root),
            "--log-level", "info"
        ], cwd=str(app_root), env=env)
        
    except KeyboardInterrupt:
        print("🛑 API server stopped")
    except Exception as e:
        print(f"❌ Error starting API: {e}")

def start_combined_proxy():
    """Start combined proxy on port 9000 for ngrok"""
    print("🔗 Starting combined proxy (port 9000) for ngrok...")
    time.sleep(5)  # Give both servers time to start
    
    try:
        import requests
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class CombinedHandler(BaseHTTPRequestHandler):
            def handle_request(self, method):
                # Route API calls to FastAPI (port 8001), everything else to frontend (port 8002)
                if (self.path.startswith('/api') or 
                    self.path.startswith('/docs') or 
                    self.path.startswith('/redoc') or
                    self.path.startswith('/openapi.json') or  # Fix: Route OpenAPI schema to API server
                    self.path.startswith('/health')):
                    target = f"http://127.0.0.1:8001{self.path}"
                else:
                    target = f"http://127.0.0.1:8002{self.path}"
                
                try:
                    if method == 'GET':
                        response = requests.get(target)
                    elif method == 'POST':
                        content_length = int(self.headers.get('content-length', 0))
                        post_data = self.rfile.read(content_length) if content_length > 0 else b''
                        response = requests.post(target, data=post_data, headers=dict(self.headers))
                    
                    self.send_response(response.status_code)
                    for header, value in response.headers.items():
                        if header.lower() not in ['content-encoding', 'transfer-encoding', 'connection']:
                            self.send_header(header, value)
                    self.end_headers()
                    self.wfile.write(response.content)
                    
                except requests.exceptions.ConnectionError:
                    self.send_response(502)
                    self.end_headers()
                    self.wfile.write(b"Service unavailable")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f"Proxy Error: {e}".encode())

            def do_GET(self): self.handle_request('GET')
            def do_POST(self): self.handle_request('POST')

        server = HTTPServer(('127.0.0.1', 9000), CombinedHandler)
        print("🔗 Combined proxy ready on http://127.0.0.1:9000")
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("🛑 Combined proxy stopped")
    except Exception as e:
        print(f"❌ Error starting proxy: {e}")
        

def start_frontend_server():
    """Start frontend server on port 8002"""
    print("🌐 Starting frontend server (port 8002)...")
    time.sleep(3)  # Give API server more time to start
    
    try:
        import http.server
        import socketserver
        from pathlib import Path
        
        # STAY in current directory (static/ui)
        frontend_dir = Path.cwd()
        print(f"📁 Frontend serving from: {frontend_dir}")
        
        # Check structure
        html_dir = frontend_dir / "html"
        css_dir = frontend_dir / "css"
        js_dir = frontend_dir / "js"
        
        print(f"📁 Checking structure:")
        print(f"   HTML: {'✅' if html_dir.exists() else '❌'} {html_dir}")
        print(f"   CSS:  {'✅' if css_dir.exists() else '❌'} {css_dir}")
        print(f"   JS:   {'✅' if js_dir.exists() else '❌'} {js_dir}")
        
        if html_dir.exists():
            html_files = list(html_dir.glob("*.html"))
            print(f"   📄 HTML files: {[f.name for f in html_files]}")
        
        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(frontend_dir), **kwargs)
            
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                super().end_headers()
            
            def do_GET(self):
                print(f"Request: {self.path}")
                
                # Handle root path - redirect to /html/index.html
                if self.path == '/':
                    self.send_response(302)
                    self.send_header('Location', '/html/index.html')
                    self.end_headers()
                    return
                
                return super().do_GET()

        PORT = 8002
        HOST = '0.0.0.0'

        print(f"🌐 Frontend URLs:")
        print(f"   http://localhost:{PORT}/html/index.html")

        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        

def main():
    print("🚀 Starting ACTIVnet Full Application")
    print("=" * 50)
    
    current_dir = Path.cwd()
    
    # Verify we're in the right place (should be static/ui)
    if not current_dir.name == 'ui' or not current_dir.parent.name == 'static':
        print(f"⚠️ Warning: Expected to run from static/ui, but in: {current_dir}")
        print("   Make sure you're running this from: <app_root>/static/ui/")
    
    app_root = current_dir.parent.parent
    services_dir = app_root / "services"
    
    print(f"📁 Directory structure:")
    print(f"   Current: {current_dir}")
    print(f"   App root: {app_root}")
    print(f"   Services: {services_dir}")
    
    # Verify structure
    checks = [
        ("Services directory", services_dir.exists()),
        ("main.py", (services_dir / "main.py").exists()),
        ("HTML directory", (current_dir / "html").exists()),
        ("CSS directory", (current_dir / "css").exists()),
        ("JS directory", (current_dir / "js").exists()),
    ]
    
    print(f"📋 Structure check:")
    for name, exists in checks:
        print(f"   {name}: {'✅' if exists else '❌'}")
    
    # Start all three servers
    api_thread = threading.Thread(target=start_api_server)
    frontend_thread = threading.Thread(target=start_frontend_server)
    proxy_thread = threading.Thread(target=start_combined_proxy)
    
    api_thread.daemon = True
    frontend_thread.daemon = True
    proxy_thread.daemon = True
    
    api_thread.start()
    frontend_thread.start()
    proxy_thread.start()
    
    print("\n🌐 ACTIVnet Application URLs:")
    print("   Frontend Direct: http://localhost:8002/html/index.html")
    print("   API Direct: http://localhost:8001/docs")
    print("   🔗 NGROK: http://127.0.0.1:9000 (expose this port!)")
    print("   🔗 FINAL: http://activnet.prutech:8000/html/index.html (via redirect)")
    print("\n🛑 Press Ctrl+C to stop all servers")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down ACTIVnet...")

if __name__ == "__main__":
    main()