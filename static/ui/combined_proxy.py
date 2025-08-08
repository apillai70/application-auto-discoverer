# combined_proxy.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

class CombinedProxyHandler(BaseHTTPRequestHandler):
    def handle_request(self, method):
        # Route API calls to FastAPI (port 8001), everything else to frontend (port 8000)
        if self.path.startswith('/api') or self.path.startswith('/docs') or self.path.startswith('/redoc'):
            target = f"http://127.0.0.1:8001{self.path}"
            service = "API"
        else:
            target = f"http://127.0.0.1:8002{self.path}"
            service = "Frontend"
        
        print(f"🔗 {method} {self.path} → {service} ({target})")
        
        try:
            # Forward request to appropriate local service
            if method == 'GET':
                response = requests.get(target)
            elif method == 'POST':
                content_length = int(self.headers.get('content-length', 0))
                post_data = self.rfile.read(content_length) if content_length > 0 else b''
                response = requests.post(target, data=post_data, 
                                       headers={k: v for k, v in self.headers.items()})
            elif method == 'PUT':
                content_length = int(self.headers.get('content-length', 0))
                put_data = self.rfile.read(content_length) if content_length > 0 else b''
                response = requests.put(target, data=put_data,
                                      headers={k: v for k, v in self.headers.items()})
            elif method == 'DELETE':
                response = requests.delete(target)
            elif method == 'HEAD':
                response = requests.head(target)  # Add HEAD support
            else:
                self.send_response(405)
                self.end_headers()
                return
            
            # Send response back
            self.send_response(response.status_code)
            
            # Copy headers (excluding problematic ones)
            for header, value in response.headers.items():
                if header.lower() not in ['content-encoding', 'transfer-encoding', 'connection']:
                    self.send_header(header, value)
            
            self.end_headers()
            self.wfile.write(response.content)
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed to {service} server")
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"{service} service unavailable - is it running?".encode())
        except Exception as e:
            print(f"❌ Error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Proxy Error: {e}".encode())

    def do_GET(self):
        self.handle_request('GET')
    
    def do_POST(self):
        self.handle_request('POST')
        
    def do_PUT(self):
        self.handle_request('PUT')
        
    def do_DELETE(self):
        self.handle_request('DELETE')
        
    def do_HEAD(self):
        self.handle_request('HEAD')  # Add HEAD method handler

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 9000), CombinedProxyHandler)
    print("🚀 Combined proxy server running on http://127.0.0.1:9000")
    print("📁 Frontend: http://127.0.0.1:9000/html/index.html")
    print("🔌 API: http://127.0.0.1:9000/api/*")
    print("📖 API Docs: http://127.0.0.1:9000/docs")
    print("")
    print("Make sure both services are running:")
    print("  Frontend: python -m http.server 8002")
    print("  FastAPI: uvicorn main:app --port 8001")
    print("")
    print("Next steps:")
    print("  1. Run: ngrok http 9000")
    print("  2. Run your redirect_server.py")
    print("")
    server.serve_forever()