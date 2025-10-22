# Knowledge Sharing API

Simple REST API for uploading and downloading Skill Seeker knowledge packages.

## Quick Start

### 1. Install Dependencies

```bash
pip3 install -r api/requirements.txt
```

### 2. Run the Server

```bash
python3 api/knowledge_api.py
```

Server will start at `http://localhost:5000`

### 3. Test the API

```bash
# Health check
curl http://localhost:5000/api/health

# List all knowledge packages
curl http://localhost:5000/api/knowledge/list
```

---

## Configuration

Use environment variables to configure:

```bash
# Database path (default: data/knowledge.db)
export KNOWLEDGE_DB_PATH=data/knowledge.db

# Storage path (default: storage/knowledge)
export KNOWLEDGE_STORAGE_PATH=storage/knowledge

# Server host (default: 0.0.0.0)
export API_HOST=0.0.0.0

# Server port (default: 5000)
export API_PORT=5000

# Debug mode (default: false)
export API_DEBUG=true
```

---

## API Endpoints

### Health Check

```bash
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "database": true,
  "storage": true,
  "timestamp": "2025-10-22T14:30:00"
}
```

### Upload Knowledge Package

```bash
POST /api/knowledge/upload
Content-Type: multipart/form-data

Required fields:
- file: .zip file
- name: skill name (e.g., "godot")
- title: display title (e.g., "Godot Game Engine")
- description: what the skill covers
- category: one of the predefined categories

Optional fields:
- framework: framework name
- version: version string
- source_url: original documentation URL
- uploader_name: your name
- uploader_email: your email
- tags: comma-separated tags
- config_json: JSON config used to create skill
```

Example using curl:

```bash
curl -X POST http://localhost:5000/api/knowledge/upload \
  -F "file=@output/godot.zip" \
  -F "name=godot" \
  -F "title=Godot Game Engine Documentation" \
  -F "description=Complete skill for Godot 4.0 game engine" \
  -F "category=game-engine" \
  -F "framework=Godot" \
  -F "version=4.0" \
  -F "source_url=https://docs.godotengine.org/en/stable/" \
  -F "tags=game-engine,godot,gdscript,3d,2d"
```

Response:
```json
{
  "success": true,
  "id": 1,
  "name": "godot",
  "file_hash": "a3f8c2d91e7b4f6a...",
  "file_size": 2458624,
  "status": "pending",
  "message": "Knowledge package uploaded successfully. Pending approval."
}
```

### List Knowledge Packages

```bash
GET /api/knowledge/list?category=game-engine&limit=10&offset=0
```

Query parameters:
- `category`: filter by category
- `framework`: filter by framework
- `status`: filter by status (default: approved)
- `limit`: max results (default: 50, max: 100)
- `offset`: pagination offset (default: 0)

Response:
```json
{
  "results": [
    {
      "id": 1,
      "name": "godot",
      "title": "Godot Game Engine Documentation",
      "description": "Complete skill for Godot 4.0 game engine",
      "category": "game-engine",
      "framework": "Godot",
      "version": "4.0",
      "file_size": 2458624,
      "page_count": 342,
      "upload_date": "2025-10-22T14:30:00",
      "downloads": 127,
      "rating_avg": 4.5,
      "tags": "game-engine,godot,gdscript,3d,2d",
      "source_url": "https://docs.godotengine.org/en/stable/"
    }
  ],
  "count": 1,
  "limit": 50,
  "offset": 0
}
```

### Get Knowledge Details

```bash
GET /api/knowledge/<id>
```

Example:
```bash
curl http://localhost:5000/api/knowledge/1
```

Response:
```json
{
  "id": 1,
  "name": "godot",
  "title": "Godot Game Engine Documentation",
  "description": "Complete skill for Godot 4.0 game engine",
  "category": "game-engine",
  "framework": "Godot",
  "version": "4.0",
  "file_size": 2458624,
  "file_hash": "a3f8c2d91e7b4f6a...",
  "page_count": 342,
  "upload_date": "2025-10-22T14:30:00",
  "uploader_name": "John Doe",
  "source_url": "https://docs.godotengine.org/en/stable/",
  "downloads": 127,
  "rating_avg": 4.5,
  "rating_count": 10,
  "status": "approved",
  "tags": "game-engine,godot,gdscript,3d,2d",
  "created_at": "2025-10-22T14:30:00",
  "updated_at": "2025-10-22T14:30:00"
}
```

### Download Knowledge Package

```bash
GET /api/knowledge/<id>/download
```

Example:
```bash
curl -O http://localhost:5000/api/knowledge/1/download
```

Downloads the .zip file and increments the download counter.

### Preview Knowledge Package

```bash
GET /api/knowledge/<id>/preview?lines=50&full=false
```

Query parameters:
- `lines`: Number of lines to preview (default: 50, max: 200)
- `full`: If 'true', return full SKILL.md content (default: false)

Example:
```bash
curl http://localhost:5000/api/knowledge/1/preview
curl http://localhost:5000/api/knowledge/1/preview?lines=100
curl http://localhost:5000/api/knowledge/1/preview?full=true
```

Response:
```json
{
  "id": 1,
  "name": "godot",
  "title": "Godot Game Engine Documentation",
  "preview": "# Godot Game Engine\n\n...",
  "is_truncated": true,
  "total_lines": 342,
  "preview_lines": 50,
  "file_count": 45,
  "reference_count": 12,
  "reference_files": ["references/index.md", "references/api.md", ...]
}
```

### List Categories

```bash
GET /api/categories
```

Response:
```json
{
  "categories": [
    {
      "category": "web-framework",
      "count": 5
    },
    {
      "category": "game-engine",
      "count": 2
    }
  ]
}
```

---

## Categories

Valid categories:
- `web-framework` - React, Vue, Django, Laravel, FastAPI
- `game-engine` - Godot, Unity, Unreal
- `css-framework` - Tailwind, Bootstrap, Material UI
- `cloud-platform` - Kubernetes, Docker, AWS, Azure
- `programming-language` - Python, JavaScript, Rust, Go
- `database` - PostgreSQL, MongoDB, Redis
- `library` - NumPy, Pandas, Lodash
- `api` - REST APIs, GraphQL, Steam API
- `other` - Anything not fitting above

---

## Validation

The API validates uploaded .zip files to ensure they contain:
1. `SKILL.md` file at root
2. `references/` directory

Files are rejected if they don't match this structure.

---

## File Storage

Files are stored in:
```
storage/knowledge/<category>/<name>_<date>_<hash>.zip
```

Example:
```
storage/knowledge/game-engine/godot_20251022_a3f8c2.zip
```

---

## Database

SQLite database stored at `data/knowledge.db` (configurable).

Schema defined in `docs/KNOWLEDGE_SCHEMA.md`.

---

## Status Workflow

1. **Upload** → Status: `pending`
2. **Admin approval** → Status: `approved`
3. **Public download** → Only `approved` packages visible

Admin approval endpoint not yet implemented (A2.4+).

---

## Security Notes

- Max file size: 100MB
- Only .zip files accepted
- File structure validated before storage
- SHA-256 hash prevents duplicates
- Secure filenames using werkzeug
- Status prevents unapproved content from being downloaded

---

## Next Steps (Future Tasks)

- **A2.3** - Add MCP tool `fetch_knowledge`
- **A2.4** - Add preview/description extraction
- **A2.5** - Enhanced categorization
- **A2.6** - Full-text search

---

## Example Workflow

```bash
# 1. Start server
python3 api/knowledge_api.py

# 2. Build a skill
python3 cli/doc_scraper.py --config configs/godot.json --enhance-local
python3 cli/package_skill.py output/godot/

# 3. Upload to API
curl -X POST http://localhost:5000/api/knowledge/upload \
  -F "file=@output/godot.zip" \
  -F "name=godot" \
  -F "title=Godot Game Engine Documentation" \
  -F "description=Complete skill for Godot 4.0 game engine" \
  -F "category=game-engine" \
  -F "framework=Godot"

# 4. List uploaded skills
curl http://localhost:5000/api/knowledge/list

# 5. Download a skill
curl -O http://localhost:5000/api/knowledge/1/download
```

---

**Status:** API complete, ready for MCP integration (A2.3)
