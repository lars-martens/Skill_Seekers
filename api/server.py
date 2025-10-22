#!/usr/bin/env python3
"""
Simple HTTP server for Skill Seeker Config API.

Usage:
    python3 api/server.py [port]

Default port: 8000

Endpoints:
    GET /api/configs - List all configs
    GET /api/configs/{id} - Get specific config by ID
"""

import json
import sys
import cgi
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from list_configs import list_configs, load_config_metadata


class ConfigAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Config API."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/api/configs":
            self.serve_configs_list()
        elif self.path.startswith("/api/configs/"):
            config_id = self.path.split("/")[-1]
            self.serve_config_detail(config_id)
        elif self.path == "/upload":
            self.serve_upload_form()
        elif self.path == "/" or self.path == "/api":
            self.serve_api_info()
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        """Handle POST requests."""
        if self.path == "/api/upload":
            self.handle_config_upload()
        else:
            self.send_error(404, "Endpoint not found")

    def serve_configs_list(self):
        """Serve the full list of configs."""
        try:
            configs = list_configs()
            response = {
                "version": "1.0.0",
                "total_configs": len(configs),
                "configs": configs
            }
            self.send_json_response(response)
        except Exception as e:
            self.send_error(500, f"Error loading configs: {str(e)}")

    def serve_config_detail(self, config_id: str):
        """Serve details for a specific config."""
        try:
            repo_root = Path(__file__).parent.parent
            config_path = repo_root / "configs" / f"{config_id}.json"

            if not config_path.exists():
                self.send_error(404, f"Config '{config_id}' not found")
                return

            # Load full config file
            with open(config_path, 'r') as f:
                config = json.load(f)

            response = {
                "id": config_id,
                "config": config
            }
            self.send_json_response(response)
        except Exception as e:
            self.send_error(500, f"Error loading config: {str(e)}")

    def serve_api_info(self):
        """Serve API information."""
        response = {
            "name": "Skill Seeker Config API",
            "version": "1.0.0",
            "endpoints": {
                "/api/configs": "List all available configs",
                "/api/configs/{id}": "Get specific config by ID",
                "/api/upload": "Upload a new config (POST)",
                "/upload": "Upload form (web UI)"
            },
            "examples": {
                "list_all": "curl http://localhost:8000/api/configs",
                "get_react": "curl http://localhost:8000/api/configs/react",
                "upload_form": "Open http://localhost:8000/upload in browser"
            }
        }
        self.send_json_response(response)

    def serve_upload_form(self):
        """Serve the HTML upload form."""
        try:
            form_path = Path(__file__).parent / "upload_form.html"
            with open(form_path, 'r') as f:
                html_content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode())
        except Exception as e:
            self.send_error(500, f"Error loading upload form: {str(e)}")

    def handle_config_upload(self):
        """Handle config file upload."""
        try:
            # Parse multipart form data
            content_type = self.headers.get('Content-Type')
            if not content_type:
                self.send_json_response({"error": "Missing Content-Type header"}, 400)
                return

            # Parse form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                }
            )

            config_data = None
            config_name = None

            # Check if file upload
            if 'file' in form:
                file_item = form['file']
                if file_item.filename:
                    # Read file content
                    config_json = file_item.file.read().decode('utf-8')
                    config_data = json.loads(config_json)
                    config_name = config_data.get('name', Path(file_item.filename).stem)
            # Check if JSON paste
            elif 'name' in form and 'config_json' in form:
                config_name = form.getvalue('name')
                config_json = form.getvalue('config_json')
                config_data = json.loads(config_json)
            else:
                self.send_json_response({"error": "No file or config data provided"}, 400)
                return

            # Validate config
            if not config_data:
                self.send_json_response({"error": "Invalid config data"}, 400)
                return

            if not config_name:
                self.send_json_response({"error": "Config name is required"}, 400)
                return

            # Sanitize filename
            safe_name = "".join(c for c in config_name if c.isalnum() or c in '-_').lower()

            # Create community directory
            repo_root = Path(__file__).parent.parent
            community_dir = repo_root / "configs" / "community"
            community_dir.mkdir(parents=True, exist_ok=True)

            # Save config
            config_path = community_dir / f"{safe_name}.json"

            # Check if already exists
            if config_path.exists():
                self.send_json_response({
                    "error": f"Config '{safe_name}' already exists in community directory",
                    "path": str(config_path.relative_to(repo_root))
                }, 409)
                return

            # Save the config
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Success response
            self.send_json_response({
                "success": True,
                "message": f"Config '{safe_name}' uploaded successfully!",
                "path": str(config_path.relative_to(repo_root)),
                "status": "pending_review",
                "note": "Config uploaded to community directory and pending review"
            }, 201)

        except json.JSONDecodeError as e:
            self.send_json_response({"error": f"Invalid JSON: {str(e)}"}, 400)
        except Exception as e:
            self.send_json_response({"error": f"Upload failed: {str(e)}"}, 500)

    def send_json_response(self, data: dict, status_code: int = 200):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def log_message(self, format, *args):
        """Custom log message format."""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port: int = 8000):
    """Run the HTTP server."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, ConfigAPIHandler)

    print(f"Skill Seeker Config API Server")
    print(f"Listening on http://localhost:{port}")
    print(f"\nEndpoints:")
    print(f"  http://localhost:{port}/api/configs - List all configs")
    print(f"  http://localhost:{port}/api/configs/{{id}} - Get specific config")
    print(f"  http://localhost:{port}/upload - Upload form (web UI)")
    print(f"  http://localhost:{port}/api/upload - Upload endpoint (POST)")
    print(f"\nPress Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
