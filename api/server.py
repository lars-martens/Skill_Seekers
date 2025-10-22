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
from urllib.parse import urlparse, parse_qs
from list_configs import list_configs, load_config_metadata
from ratings import RatingsManager
from review import ReviewManager


class ConfigAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Config API."""

    # Class-level managers (shared across requests)
    ratings_manager = RatingsManager()
    review_manager = ReviewManager()

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/api/configs":
            self.serve_configs_list()
        elif self.path.startswith("/api/configs/"):
            config_id = self.path.split("/")[-1]
            self.serve_config_detail(config_id)
        elif self.path == "/api/review/pending":
            self.serve_pending_reviews()
        elif self.path == "/api/review/stats":
            self.serve_review_stats()
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
        elif self.path.startswith("/api/vote/"):
            self.handle_vote()
        elif self.path.startswith("/api/review/"):
            self.handle_review_action()
        else:
            self.send_error(404, "Endpoint not found")

    def serve_configs_list(self):
        """Serve the full list of configs with optional filtering."""
        try:
            configs = list_configs()

            # Add ratings to each config
            for config in configs:
                config_id = config.get("id", "")
                if config_id:
                    config["rating"] = self.ratings_manager.get_rating(config_id)

            # Parse query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            # Apply filters
            filtered_configs = configs

            # Search filter (?q=search_term)
            if 'q' in query_params:
                search_term = query_params['q'][0].lower()
                filtered_configs = [
                    c for c in filtered_configs
                    if search_term in c.get('name', '').lower() or
                       search_term in c.get('description', '').lower() or
                       search_term in c.get('base_url', '').lower()
                ]

            # Category filter (?category=getting_started)
            if 'category' in query_params:
                category = query_params['category'][0].lower()
                filtered_configs = [
                    c for c in filtered_configs
                    if category in [cat.lower() for cat in c.get('categories', [])]
                ]

            # Minimum score filter (?min_score=5)
            if 'min_score' in query_params:
                try:
                    min_score = int(query_params['min_score'][0])
                    filtered_configs = [
                        c for c in filtered_configs
                        if c.get('rating', {}).get('score', 0) >= min_score
                    ]
                except ValueError:
                    pass  # Ignore invalid min_score values

            # Sort parameter (?sort=name|score|votes)
            sort_by = query_params.get('sort', ['score'])[0]
            if sort_by == 'name':
                filtered_configs.sort(key=lambda x: x.get('name', '').lower())
            elif sort_by == 'votes':
                filtered_configs.sort(key=lambda x: x.get('rating', {}).get('total_votes', 0), reverse=True)
            else:  # Default: sort by score
                filtered_configs.sort(key=lambda x: x.get('rating', {}).get('score', 0), reverse=True)

            response = {
                "version": "1.0.0",
                "total_configs": len(filtered_configs),
                "total_available": len(configs),
                "filters_applied": {
                    "search": query_params.get('q', [None])[0],
                    "category": query_params.get('category', [None])[0],
                    "min_score": query_params.get('min_score', [None])[0],
                    "sort": sort_by
                },
                "configs": filtered_configs
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
                "/api/configs": "List all available configs (with ratings and filters)",
                "/api/configs/{id}": "Get specific config by ID",
                "/api/upload": "Upload a new config (POST)",
                "/api/vote/{id}/upvote": "Upvote a config (POST)",
                "/api/vote/{id}/downvote": "Downvote a config (POST)",
                "/api/review/pending": "List configs pending review (GET)",
                "/api/review/stats": "Review queue statistics (GET)",
                "/api/review/{id}/approve": "Approve a config (POST)",
                "/api/review/{id}/reject": "Reject a config (POST)",
                "/upload": "Upload form (web UI)"
            },
            "query_parameters": {
                "q": "Search term (searches name, description, url)",
                "category": "Filter by category",
                "min_score": "Minimum rating score",
                "sort": "Sort by: name, score (default), votes"
            },
            "examples": {
                "list_all": "curl http://localhost:8000/api/configs",
                "search": "curl 'http://localhost:8000/api/configs?q=react'",
                "filter_category": "curl 'http://localhost:8000/api/configs?category=getting_started'",
                "min_score": "curl 'http://localhost:8000/api/configs?min_score=5'",
                "sort_by_name": "curl 'http://localhost:8000/api/configs?sort=name'",
                "combined": "curl 'http://localhost:8000/api/configs?q=framework&min_score=3&sort=votes'",
                "get_react": "curl http://localhost:8000/api/configs/react",
                "upload_form": "Open http://localhost:8000/upload in browser",
                "upvote": "curl -X POST http://localhost:8000/api/vote/react/upvote",
                "downvote": "curl -X POST http://localhost:8000/api/vote/vue/downvote",
                "review_pending": "curl http://localhost:8000/api/review/pending",
                "review_stats": "curl http://localhost:8000/api/review/stats",
                "approve": "curl -X POST http://localhost:8000/api/review/my-config/approve",
                "reject": "curl -X POST http://localhost:8000/api/review/my-config/reject -d '{\"note\":\"reason\"}'"
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

    def handle_vote(self):
        """Handle voting for configs."""
        try:
            # Parse path: /api/vote/{config_id}/{action}
            path_parts = self.path.split("/")
            if len(path_parts) < 5:
                self.send_json_response({"error": "Invalid vote endpoint. Use /api/vote/{config_id}/upvote or /api/vote/{config_id}/downvote"}, 400)
                return

            config_id = path_parts[3]
            action = path_parts[4]

            # Validate action
            if action not in ["upvote", "downvote"]:
                self.send_json_response({"error": f"Invalid action '{action}'. Use 'upvote' or 'downvote'"}, 400)
                return

            # Perform vote
            if action == "upvote":
                rating = self.ratings_manager.upvote(config_id)
            else:
                rating = self.ratings_manager.downvote(config_id)

            self.send_json_response({
                "success": True,
                "config_id": config_id,
                "action": action,
                "rating": rating
            })

        except Exception as e:
            self.send_json_response({"error": f"Vote failed: {str(e)}"}, 500)

    def serve_pending_reviews(self):
        """Serve list of configs pending review."""
        try:
            pending = self.review_manager.get_pending_configs()
            self.send_json_response({
                "total_pending": len(pending),
                "configs": pending
            })
        except Exception as e:
            self.send_error(500, f"Error loading pending reviews: {str(e)}")

    def serve_review_stats(self):
        """Serve review queue statistics."""
        try:
            stats = self.review_manager.get_review_stats()
            self.send_json_response(stats)
        except Exception as e:
            self.send_error(500, f"Error loading review stats: {str(e)}")

    def handle_review_action(self):
        """Handle review approval/rejection."""
        try:
            # Parse path: /api/review/{config_id}/approve or /api/review/{config_id}/reject
            path_parts = self.path.split("/")
            if len(path_parts) < 5:
                self.send_json_response({"error": "Invalid review endpoint. Use /api/review/{config_id}/approve or /api/review/{config_id}/reject"}, 400)
                return

            config_id = path_parts[3]
            action = path_parts[4]

            # Parse request body for optional note
            content_length = int(self.headers.get('Content-Length', 0))
            note = None
            if content_length > 0:
                try:
                    body = self.rfile.read(content_length).decode('utf-8')
                    data = json.loads(body)
                    note = data.get('note')
                except Exception:
                    pass  # Note is optional

            # Validate action
            if action not in ["approve", "reject"]:
                self.send_json_response({"error": f"Invalid action '{action}'. Use 'approve' or 'reject'"}, 400)
                return

            # Perform review action
            if action == "approve":
                result = self.review_manager.approve_config(config_id, note)
            else:
                result = self.review_manager.reject_config(config_id, note)

            self.send_json_response(result)

        except FileNotFoundError as e:
            self.send_json_response({"error": str(e)}, 404)
        except FileExistsError as e:
            self.send_json_response({"error": str(e)}, 409)
        except Exception as e:
            self.send_json_response({"error": f"Review action failed: {str(e)}"}, 500)

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
