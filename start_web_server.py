#!/usr/bin/env python3
# ACTIVnet Web Server Startup

import sys
import os
import http.server
import socketserver
from pathlib import Path

# Ensure we're in the right directory
project_root = Path(__file__).parent
os.chdir(project_root)

PORT = 8000

print("🌐 Starting ACTIVnet Web Server")
print(f"📁 Serving from: {project_root}")
print(f"🔗 URL: http://localhost:{PORT}")
print(f"📊 Data files:")
print(f"   • JSON: /templates/activnet_data.json")
print(f"   • Excel: /static/ui/data/synthetic_flows_apps_archetype_mapped.xlsx")
print(f"   • JavaScript: /static/ui/js/app_data.js")
print()
print("Press Ctrl+C to stop")

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers if needed
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

try:
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"✅ Server started at http://localhost:{PORT}")
        httpd.serve_forever()
        
except KeyboardInterrupt:
    print("\n🛑 Server stopped")
    sys.exit(0)
except Exception as e:
    print(f"❌ Server error: {e}")
    sys.exit(1)
