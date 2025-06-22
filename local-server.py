#!/usr/bin/env python3
"""
Simple HTTP server for local development of Robot Puzzle Game
Serves static files and handles CORS for local testing
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse, parse_qs

class LocalDevHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        # Redirect root to local development version
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index-local.html'
        elif self.path == '/wall-editor.html':
            self.path = '/wall-editor-local.html'
        
        super().do_GET()

def main():
    port = 8000
    
    # Change to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"🚀 Starting Robot Puzzle Game Local Development Server")
    print(f"📁 Serving files from: {script_dir}")
    print(f"🌐 Server running at: http://localhost:{port}")
    print(f"🎮 Game URL: http://localhost:{port}/")
    print(f"🎨 Board Editor URL: http://localhost:{port}/wall-editor.html")
    print(f"")
    print(f"🔧 Local Development Features:")
    print(f"   • No authentication required")
    print(f"   • Mock data stored in localStorage")
    print(f"   • Same behavior as AWS deployment")
    print(f"   • Real-time leaderboard testing")
    print(f"")
    print(f"📝 Press Ctrl+C to stop the server")
    print(f"=" * 60)
    
    try:
        with socketserver.TCPServer(("", port), LocalDevHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"\n❌ Port {port} is already in use!")
            print(f"💡 Try stopping any other servers or use a different port")
            print(f"   You can also try: lsof -ti:{port} | xargs kill")
        else:
            print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()