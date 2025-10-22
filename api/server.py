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
        elif self.path == "/" or self.path == "/api":
            self.serve_api_info()
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
                "/api/configs/{id}": "Get specific config by ID"
            },
            "examples": {
                "list_all": "curl http://localhost:8000/api/configs",
                "get_react": "curl http://localhost:8000/api/configs/react"
            }
        }
        self.send_json_response(response)

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
    print(f"\nPress Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
