# activnet_redirect_8000.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

class ActivnetRedirectHandler(BaseHTTPRequestHandler):
    def handle_request(self, method):
        try:
            # Forward ALL requests to your ngrok tunnel
            target_url = f"https://ethical-lately-racer.ngrok-free.app{self.path}"
            
            print(f"🔗 {method} activnet.prutech:8000{self.path} → {target_url}")
            
            if method == 'GET':
                response = requests.get(target_url, allow_redirects=True)
            elif method == 'POST':
                content_length = int(self.headers.get('content-length', 0))
                post_data = self.rfile.read(content_length) if content_length > 0 else b''
                response = requests.post(target_url, data=post_data, 
                                       headers={k: v for k, v in self.headers.items()})
            elif method == 'PUT':
                content_length = int(self.headers.get('content-length', 0))
                put_data = self.rfile.read(content_length) if content_length > 0 else b''
                response = requests.put(target_url, data=put_data,
                                      headers={k: v for k, v in self.headers.items()})
            elif method == 'DELETE':
                response = requests.delete(target_url)
            else:
                self.send_response(405)
                self.end_headers()
                return
            
            # Send response back
            self.send_response(response.status_code)
            for header, value in response.headers.items():
                if header.lower() not in ['content-encoding', 'transfer-encoding', 'connection']:
                    self.send_header(header, value)
            self.end_headers()
            
            self.wfile.write(response.content)
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to ngrok tunnel")
            self.send_response(502)
            self.end_headers()
            self.wfile.write(b"Cannot connect to ngrok tunnel - is it running?")
        except Exception as e:
            print(f"❌ Error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Redirect Error: {e}".encode())

    def do_GET(self):
        self.handle_request('GET')
    
    def do_POST(self):
        self.handle_request('POST')
        
    def do_PUT(self):
        self.handle_request('PUT')
        
    def do_DELETE(self):
        self.handle_request('DELETE')

if __name__ == '__main__':
    # Run on port 8000 to intercept activnet.prutech:8000 requests
    server = HTTPServer(('127.0.0.1', 8000), ActivnetRedirectHandler)
    print("🔗 ACTIVnet redirect server running on port 8000")
    print("🌐 activnet.prutech:8000 → https://ethical-lately-racer.ngrok-free.app")
    print("")
    print("Enterprise users can now access:")
    print("  📁 Frontend: http://activnet.prutech:8000/html/index.html")
    print("  🔌 API: http://activnet.prutech:8000/api/*")
    print("  📖 Docs: http://activnet.prutech:8000/docs")
    print("")
    print("Make sure ngrok tunnel is running!")
    server.serve_forever()