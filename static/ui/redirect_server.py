# redirect_server.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Forward the request to ngrok
            response = requests.get(f"https://ethical-lately-racer.ngrok-free.app{self.path}")
            
            self.send_response(response.status_code)
            for header, value in response.headers.items():
                if header.lower() not in ['content-encoding', 'transfer-encoding']:
                    self.send_header(header, value)
            self.end_headers()
            
            self.wfile.write(response.content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode())

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 80), ProxyHandler)
    print("Proxy server running on http://127.0.0.1:80")
    print("activnet.prutech will now proxy to ngrok tunnel")
    server.serve_forever()