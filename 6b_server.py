from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ColorServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.end_headers()
        
        response = {"color": "orange"}
        self.wfile.write(json.dumps(response).encode())

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ColorServer)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
