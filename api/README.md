# Skill Seeker Config API

Simple JSON API for listing and fetching Skill Seeker configuration files.

## Features

- List all available configs with metadata
- Get specific config by ID
- Simple HTTP server with CORS support
- No dependencies beyond Python standard library

## Quick Start

### List Configs (Command Line)

```bash
python3 api/list_configs.py
```

Output:
```json
{
  "version": "1.0.0",
  "total_configs": 13,
  "configs": [
    {
      "id": "react",
      "name": "react",
      "description": "React framework for UIs",
      "base_url": "https://react.dev/",
      "max_pages": 500,
      "categories": ["getting_started", "api", "hooks"],
      "config_file": "configs/react.json"
    }
  ]
}
```

### Start HTTP Server

```bash
python3 api/server.py
```

Or specify a custom port:
```bash
python3 api/server.py 3000
```

## API Endpoints

### GET /api/configs

List all available configs with metadata and ratings. Supports search, filtering, and sorting.

**Query Parameters:**
- `q` - Search term (searches name, description, url)
- `category` - Filter by category name
- `min_score` - Minimum rating score
- `sort` - Sort by: `name`, `score` (default), or `votes`

**Examples:**
```bash
# List all configs
curl http://localhost:8000/api/configs

# Search for "react"
curl 'http://localhost:8000/api/configs?q=react'

# Filter by category
curl 'http://localhost:8000/api/configs?category=getting_started'

# Minimum score of 5
curl 'http://localhost:8000/api/configs?min_score=5'

# Sort by name
curl 'http://localhost:8000/api/configs?sort=name'

# Combined filters
curl 'http://localhost:8000/api/configs?q=framework&min_score=3&sort=votes'
```

**Response:**
```json
{
  "version": "1.0.0",
  "total_configs": 3,
  "total_available": 13,
  "filters_applied": {
    "search": "react",
    "category": null,
    "min_score": null,
    "sort": "score"
  },
  "configs": [
    {
      "id": "react",
      "name": "react",
      "description": "React framework",
      "rating": {
        "upvotes": 15,
        "downvotes": 2,
        "score": 13,
        "total_votes": 17
      }
    }
  ]
}
```

### GET /api/configs/{id}

Get full configuration for a specific config.

**Example:**
```bash
curl http://localhost:8000/api/configs/react
```

**Response:**
```json
{
  "id": "react",
  "config": {
    "name": "react",
    "description": "React framework for UIs",
    "base_url": "https://react.dev/",
    "selectors": {...},
    "url_patterns": {...},
    "categories": {...}
  }
}
```

### GET / or GET /api

Get API information and available endpoints.

### GET /upload

Serve the web-based config upload form. Opens a user-friendly HTML form for uploading configs.

**Example:**
Open http://localhost:8000/upload in your browser.

**Features:**
- Upload .json files directly
- Paste JSON config manually
- Automatic validation
- Saves to `configs/community/` directory

### POST /api/upload

Upload a new config (backend endpoint used by the form).

**Parameters:**
- `file`: Config .json file (multipart form data), OR
- `name` + `config_json`: Config name and JSON text

**Example (file upload):**
```bash
curl -F "file=@my-config.json" http://localhost:8000/api/upload
```

**Example (JSON paste):**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "name=my-framework" \
  -F 'config_json={"name":"my-framework","base_url":"..."}'
```

**Response:**
```json
{
  "success": true,
  "message": "Config 'my-framework' uploaded successfully!",
  "path": "configs/community/my-framework.json",
  "status": "pending_review"
}
```

**Notes:**
- Uploaded configs are saved to `configs/community/` directory
- Community configs are git-ignored (not committed automatically)
- Configs are marked as "pending_review" status
- Duplicate names are rejected (409 Conflict)

### POST /api/vote/{config_id}/upvote

Upvote a config (increases rating score).

**Example:**
```bash
curl -X POST http://localhost:8000/api/vote/react/upvote
```

**Response:**
```json
{
  "success": true,
  "config_id": "react",
  "action": "upvote",
  "rating": {
    "upvotes": 16,
    "downvotes": 2,
    "score": 14,
    "total_votes": 18
  }
}
```

### POST /api/vote/{config_id}/downvote

Downvote a config (decreases rating score).

**Example:**
```bash
curl -X POST http://localhost:8000/api/vote/vue/downvote
```

**Response:**
```json
{
  "success": true,
  "config_id": "vue",
  "action": "downvote",
  "rating": {
    "upvotes": 8,
    "downvotes": 3,
    "score": 5,
    "total_votes": 11
  }
}
```

**Notes:**
- Ratings are stored in `api/ratings_data.json` (git-ignored)
- Config list is automatically sorted by rating score
- No authentication required (for simplicity)
- Votes are counted, not tracked per user

### GET /api/review/pending

List all configs pending review (submitted to `configs/community/`).

**Example:**
```bash
curl http://localhost:8000/api/review/pending
```

**Response:**
```json
{
  "total_pending": 2,
  "configs": [
    {
      "id": "my-framework",
      "name": "my-framework",
      "description": "My custom framework",
      "base_url": "https://example.com",
      "submitted_at": "2025-10-22T12:30:00",
      "file_path": "configs/community/my-framework.json"
    }
  ]
}
```

### GET /api/review/stats

Get review queue statistics.

**Example:**
```bash
curl http://localhost:8000/api/review/stats
```

**Response:**
```json
{
  "pending": 2,
  "approved": 15,
  "rejected": 3,
  "total": 20
}
```

### POST /api/review/{config_id}/approve

Approve a community config (moves it from `configs/community/` to `configs/`).

**Example:**
```bash
curl -X POST http://localhost:8000/api/review/my-framework/approve \
  -H "Content-Type: application/json" \
  -d '{"note": "Great config!"}'
```

**Response:**
```json
{
  "success": true,
  "status": "approved",
  "message": "Config 'my-framework' approved and moved to main configs",
  "new_path": "configs/my-framework.json"
}
```

### POST /api/review/{config_id}/reject

Reject a community config (keeps in community dir but marks as rejected).

**Example:**
```bash
curl -X POST http://localhost:8000/api/review/my-framework/reject \
  -H "Content-Type: application/json" \
  -d '{"note": "Needs better selectors"}'
```

**Response:**
```json
{
  "success": true,
  "status": "rejected",
  "message": "Config 'my-framework' rejected",
  "note": "Needs better selectors"
}
```

**Notes:**
- Review status stored in `api/review_data.json` (git-ignored)
- Approved configs are moved to main `configs/` directory
- Rejected configs remain in `configs/community/` but marked as rejected
- Optional `note` field for reviewer comments
- No authentication required (for simplicity)

## Response Format

### Config Metadata

Each config in the list includes:

- `id`: Unique identifier (filename without .json)
- `name`: Config name
- `description`: When to use this config
- `base_url`: Documentation base URL
- `max_pages`: Maximum pages to scrape
- `categories`: List of documentation categories
- `config_file`: Path to config file

## Integration

### Use with MCP Tool (A1.2)

Coming soon: `fetch_config` MCP tool to download configs from the API.

### Use with Website (A1.3)

Coming soon: Config gallery and upload form.

## Development

### Project Structure

```
api/
├── README.md          # This file
├── list_configs.py    # JSON generator
└── server.py          # HTTP server
```

### Testing

```bash
# Test JSON generation
python3 api/list_configs.py | jq '.total_configs'

# Test server (in another terminal)
python3 api/server.py &
curl http://localhost:8000/api/configs | jq '.total_configs'
```

## Future Enhancements

- [ ] A1.2: MCP tool `fetch_config`
- [ ] A1.3: Config upload endpoint
- [ ] A1.4: Rating/voting system
- [ ] A1.5: Search/filter API
- [ ] A1.6: Review queue API

## Notes

- All configs are read from the `configs/` directory
- Server uses Python's built-in `http.server` (no external dependencies)
- CORS is enabled for cross-origin requests
- Suitable for local development and static hosting
