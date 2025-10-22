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

List all available configs with metadata.

**Example:**
```bash
curl http://localhost:8000/api/configs
```

**Response:**
```json
{
  "version": "1.0.0",
  "total_configs": 13,
  "configs": [...]
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
