# start_activnet_full.py - Modified for Historical URL Structure
"""
ACTIVnet Full Application Launcher
==================================
Serves frontend from <app_root>/static/ on port 8000 with /ui/html/ structure
Runs FastAPI backend on port 8001
Optional proxy on port 9000 for ngrok

Historical URL: http://localhost:8000/ui/html/index.html
"""

import subprocess
import sys
import os
import time
import threading
import http.server
import socketserver
from pathlib import Path
from typing import Optional

class Config:
    """Application configuration"""
    FRONTEND_PORT = 8000  # Historical port
    API_PORT = 8001
    PROXY_PORT = 9000
    FRONTEND_HOST = '0.0.0.0'
    API_HOST = '0.0.0.0'
    PROXY_HOST = '127.0.0.1'

def get_paths():
    """Get application paths based on where script is run from"""
    current_dir = Path.cwd()
    
    # Determine app_root based on current location
    if current_dir.name == 'ui' and current_dir.parent.name == 'static':
        # Running from static/ui
        app_root = current_dir.parent.parent
        static_dir = current_dir.parent
    elif current_dir.name == 'static':
        # Running from static
        app_root = current_dir.parent
        static_dir = current_dir
    else:
        # Assume running from app root
        app_root = current_dir
        static_dir = app_root / 'static'
    
    services_dir = app_root / 'services'
    
    return {
        'app_root': app_root,
        'static_dir': static_dir,
        'services_dir': services_dir,
        'ui_dir': static_dir / 'ui'
    }

def verify_structure(paths):
    """Verify the application structure"""
    print("📁 Verifying Application Structure...")
    print(f"   App Root: {paths['app_root']}")
    print(f"   Static Dir: {paths['static_dir']}")
    print(f"   Services Dir: {paths['services_dir']}")
    print(f"   UI Dir: {paths['ui_dir']}")
    
    checks = {
        "Static directory": paths['static_dir'].exists(),
        "UI directory": paths['ui_dir'].exists(),
        "HTML directory": (paths['ui_dir'] / 'html').exists(),
        "CSS directory": (paths['ui_dir'] / 'css').exists(),
        "JS directory": (paths['ui_dir'] / 'js').exists(),
        "Services directory": paths['services_dir'].exists(),
        "Main.py": (paths['services_dir'] / 'main.py').exists(),
        "Index.html": (paths['ui_dir'] / 'html' / 'index.html').exists()
    }
    
    print("\n📋 Structure Check:")
    all_good = True
    for name, exists in checks.items():
        status = '✅' if exists else '❌'
        print(f"   {status} {name}")
        if not exists:
            all_good = False
    
    if not all_good:
        print("\n⚠️ Some components are missing!")
        print("   Make sure you have the correct directory structure:")
        print("   <app_root>/")
        print("   ├── static/")
        print("   │   └── ui/")
        print("   │       ├── html/")
        print("   │       ├── css/")
        print("   │       └── js/")
        print("   └── services/")
        print("       └── main.py")
        
    return all_good

def start_api_server(paths):
    """Start FastAPI server on port 8001"""
    print(f"\n🚀 Starting API server on port {Config.API_PORT}...")
    
    try:
        # Set environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(paths['app_root'])
        env['ENVIRONMENT'] = 'production'
        
        # Start uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "services.main:app",
            "--host", Config.API_HOST,
            "--port", str(Config.API_PORT),
            "--reload",
            "--reload-dir", str(paths['app_root']),
            "--log-level", "info"
        ], cwd=str(paths['app_root']), env=env)
        
    except KeyboardInterrupt:
        print("🛑 API server stopped")
    except Exception as e:
        print(f"❌ Error starting API: {e}")

def start_frontend_server(paths):
    """Start frontend server on port 8000 serving from static/ directory"""
    print(f"\n🌐 Starting frontend server on port {Config.FRONTEND_PORT}...")
    time.sleep(2)  # Give API time to start
    
    try:
        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            """Custom handler to serve from static directory with proper paths"""
            
            def __init__(self, *args, **kwargs):
                # Serve from static directory (NOT static/ui)
                super().__init__(*args, directory=str(paths['static_dir']), **kwargs)
            
            def end_headers(self):
                # Add CORS headers
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                super().end_headers()
            
            def do_GET(self):
                # Log the request
                print(f"📥 GET {self.path}")
                
                # Handle root redirect to historical URL
                if self.path == '/' or self.path == '/ui' or self.path == '/ui/':
                    self.send_response(302)
                    self.send_header('Location', '/ui/html/index.html')
                    self.end_headers()
                    return
                
                # Handle /ui/html/ directory listing redirect
                if self.path == '/ui/html' or self.path == '/ui/html/':
                    self.send_response(302)
                    self.send_header('Location', '/ui/html/index.html')
                    self.end_headers()
                    return
                
                # Serve the file normally
                return super().do_GET()
            
            def log_message(self, format, *args):
                # Custom logging format
                print(f"   {self.address_string()} - {format % args}")

        # Create server
        with socketserver.TCPServer(
            (Config.FRONTEND_HOST, Config.FRONTEND_PORT),
            CustomHTTPRequestHandler
        ) as httpd:
            print(f"✅ Frontend server ready on port {Config.FRONTEND_PORT}")
            print(f"📁 Serving from: {paths['static_dir']}")
            print(f"🌐 Historical URL: http://localhost:{Config.FRONTEND_PORT}/ui/html/index.html")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("🛑 Frontend server stopped")
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"❌ Port {Config.FRONTEND_PORT} is already in use!")
            print(f"   Try: lsof -i :{Config.FRONTEND_PORT} (Linux/Mac)")
            print(f"   Or:  netstat -ano | findstr :{Config.FRONTEND_PORT} (Windows)")
        else:
            print(f"❌ Error starting frontend: {e}")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")

def start_proxy_server(paths):
    """Optional proxy server for ngrok on port 9000"""
    print(f"\n🔗 Starting proxy server on port {Config.PROXY_PORT} (optional for ngrok)...")
    time.sleep(5)  # Give both servers time to start
    
    try:
        import requests
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class ProxyHandler(BaseHTTPRequestHandler):
            def handle_request(self, method):
                # Route API calls to FastAPI, everything else to frontend
                if (self.path.startswith('/api') or 
                    self.path.startswith('/docs') or 
                    self.path.startswith('/redoc') or
                    self.path.startswith('/openapi.json') or
                    self.path.startswith('/health')):
                    # Route to API server
                    target = f"http://127.0.0.1:{Config.API_PORT}{self.path}"
                else:
                    # Route to frontend server
                    target = f"http://127.0.0.1:{Config.FRONTEND_PORT}{self.path}"
                
                try:
                    # Forward the request
                    headers = dict(self.headers)
                    headers.pop('Host', None)  # Remove host header
                    
                    if method == 'GET':
                        response = requests.get(target, headers=headers, timeout=30)
                    elif method == 'POST':
                        content_length = int(self.headers.get('content-length', 0))
                        post_data = self.rfile.read(content_length) if content_length > 0 else b''
                        response = requests.post(target, data=post_data, headers=headers, timeout=30)
                    else:
                        response = requests.request(method, target, headers=headers, timeout=30)
                    
                    # Send response
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
                    self.wfile.write(f"Proxy error: {e}".encode())
            
            def do_GET(self): self.handle_request('GET')
            def do_POST(self): self.handle_request('POST')
            def do_PUT(self): self.handle_request('PUT')
            def do_DELETE(self): self.handle_request('DELETE')
            def do_OPTIONS(self): self.handle_request('OPTIONS')
            
            def log_message(self, format, *args):
                # Suppress proxy logs to reduce noise
                pass
        
        server = HTTPServer((Config.PROXY_HOST, Config.PROXY_PORT), ProxyHandler)
        print(f"✅ Proxy server ready on http://{Config.PROXY_HOST}:{Config.PROXY_PORT}")
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("🛑 Proxy server stopped")
    except ImportError:
        print("⚠️ Requests library not installed - proxy disabled")
        print("   Install with: pip install requests")
    except Exception as e:
        print(f"⚠️ Proxy server error: {e}")

def test_services(test_api=True, test_frontend=True):
    """Test if services are accessible"""
    print("\n🧪 Testing Services...")
    time.sleep(3)  # Give services time to fully start
    
    try:
        import requests
        
        if test_frontend:
            try:
                response = requests.get(f"http://localhost:{Config.FRONTEND_PORT}/ui/html/index.html", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ Frontend accessible at http://localhost:{Config.FRONTEND_PORT}/ui/html/index.html")
                else:
                    print(f"   ⚠️ Frontend returned status {response.status_code}")
            except Exception as e:
                print(f"   ❌ Frontend not accessible: {e}")
        
        if test_api:
            try:
                response = requests.get(f"http://localhost:{Config.API_PORT}/health", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ API accessible at http://localhost:{Config.API_PORT}")
                else:
                    print(f"   ⚠️ API returned status {response.status_code}")
            except Exception as e:
                print(f"   ❌ API not accessible: {e}")
                
    except ImportError:
        print("   ⚠️ Requests library not installed - skipping tests")

def main():
    """Main entry point"""
    print("=" * 60)
    print("🚀 ACTIVnet Full Application Launcher")
    print("=" * 60)
    
    # Get paths
    paths = get_paths()
    
    # Verify structure
    if not verify_structure(paths):
        response = input("\n⚠️ Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("❌ Startup cancelled")
            return
    
    # Check for running processes on our ports
    print("\n🔍 Checking ports...")
    ports_to_check = [Config.FRONTEND_PORT, Config.API_PORT]
    
    for port in ports_to_check:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                print(f"   ⚠️ Port {port} is already in use")
                print(f"      Kill process: lsof -ti:{port} | xargs kill -9 (Linux/Mac)")
                print(f"      Or: netstat -ano | findstr :{port} (Windows)")
        except:
            pass
    
    # Start services in threads
    print("\n🚀 Starting Services...")
    
    # Create threads
    api_thread = threading.Thread(target=start_api_server, args=(paths,), daemon=True)
    frontend_thread = threading.Thread(target=start_frontend_server, args=(paths,), daemon=True)
    
    # Optional proxy thread
    enable_proxy = '--proxy' in sys.argv or '--ngrok' in sys.argv
    proxy_thread = None
    if enable_proxy:
        proxy_thread = threading.Thread(target=start_proxy_server, args=(paths,), daemon=True)
    
    # Start threads
    api_thread.start()
    frontend_thread.start()
    if proxy_thread:
        proxy_thread.start()
    
    # Test services after a delay
    test_thread = threading.Thread(target=test_services, daemon=True)
    test_thread.start()
    
    # Print access information
    print("\n" + "=" * 60)
    print("🌐 ACTIVnet Application URLs:")
    print("=" * 60)
    print(f"📱 Frontend (Historical): http://localhost:{Config.FRONTEND_PORT}/ui/html/index.html")
    print(f"📱 Frontend (Direct):     http://localhost:{Config.FRONTEND_PORT}/ui/html/")
    print(f"🔧 API Documentation:     http://localhost:{Config.API_PORT}/docs")
    print(f"🔧 API Health Check:      http://localhost:{Config.API_PORT}/health")
    
    if enable_proxy:
        print(f"\n🔗 Proxy (for ngrok):     http://localhost:{Config.PROXY_PORT}")
        print("   Use: ngrok http 9000")
    
    print("\n📁 Serving Structure:")
    print(f"   Static Dir: {paths['static_dir']}")
    print(f"   → /ui/html/ → {paths['ui_dir'] / 'html'}")
    print(f"   → /ui/css/  → {paths['ui_dir'] / 'css'}")
    print(f"   → /ui/js/   → {paths['ui_dir'] / 'js'}")
    
    print("\n🛑 Press Ctrl+C to stop all servers")
    print("=" * 60)
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down ACTIVnet...")
        print("👋 All servers stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()