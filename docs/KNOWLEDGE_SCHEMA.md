# Knowledge Database Schema

**Purpose:** Define the database structure for storing and sharing user-generated skills/knowledge packages.

**Last Updated:** October 22, 2025

---

## Overview

The Knowledge Sharing system allows users to:
1. Upload packaged skills (`.zip` files) to a central repository
2. Browse and search available knowledge packages
3. Download skills created by other users
4. Rate and categorize shared knowledge

This schema supports a simple, flat database structure suitable for SQLite or PostgreSQL.

---

## Schema Design

### Table: `knowledge`

Primary table for storing knowledge/skill packages.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | INTEGER | Yes | Auto-increment primary key |
| `name` | VARCHAR(100) | Yes | Skill name (e.g., "godot", "react") |
| `title` | VARCHAR(200) | Yes | Display title (e.g., "Godot Game Engine") |
| `description` | TEXT | Yes | Brief description of what the skill covers |
| `category` | VARCHAR(50) | Yes | Primary category (see categories below) |
| `framework` | VARCHAR(100) | No | Associated framework/library/tool |
| `version` | VARCHAR(20) | No | Documentation version (e.g., "4.0", "stable") |
| `file_path` | VARCHAR(500) | Yes | Path to stored .zip file (relative to storage root) |
| `file_size` | INTEGER | Yes | File size in bytes |
| `file_hash` | VARCHAR(64) | Yes | SHA-256 hash of .zip file (for integrity) |
| `page_count` | INTEGER | No | Number of documentation pages scraped |
| `upload_date` | TIMESTAMP | Yes | When skill was uploaded |
| `uploader_name` | VARCHAR(100) | No | Username/name of uploader (optional) |
| `uploader_email` | VARCHAR(200) | No | Contact email (optional, not displayed) |
| `source_url` | VARCHAR(500) | No | Original documentation URL |
| `config_json` | TEXT | No | JSON config used to create this skill |
| `downloads` | INTEGER | Yes | Download counter (default 0) |
| `rating_sum` | INTEGER | Yes | Sum of all ratings (default 0) |
| `rating_count` | INTEGER | Yes | Number of ratings (default 0) |
| `rating_avg` | DECIMAL(3,2) | No | Average rating (calculated: rating_sum/rating_count) |
| `status` | VARCHAR(20) | Yes | Status: "pending", "approved", "rejected" |
| `tags` | VARCHAR(500) | No | Comma-separated tags for search |
| `created_at` | TIMESTAMP | Yes | Record creation timestamp |
| `updated_at` | TIMESTAMP | Yes | Record last update timestamp |

**Indexes:**
- Primary key on `id`
- Index on `category` (for filtering)
- Index on `status` (for admin queue)
- Index on `name` (for lookups)
- Full-text index on `title`, `description`, `tags` (for search)

**Constraints:**
- `name` must be unique (prevent duplicates)
- `file_hash` must be unique (prevent duplicate uploads)
- `downloads` >= 0
- `rating_sum` >= 0
- `rating_count` >= 0
- `status` IN ('pending', 'approved', 'rejected')

---

## Categories

**Predefined categories** for organization:

| Category | Description | Examples |
|----------|-------------|----------|
| `web-framework` | Web development frameworks | React, Vue, Django, Laravel, FastAPI |
| `game-engine` | Game development engines | Godot, Unity, Unreal |
| `css-framework` | CSS/styling frameworks | Tailwind, Bootstrap, Material UI |
| `cloud-platform` | Cloud and DevOps tools | Kubernetes, Docker, AWS, Azure |
| `programming-language` | Programming language docs | Python, JavaScript, Rust, Go |
| `database` | Database systems | PostgreSQL, MongoDB, Redis |
| `library` | Utility libraries | NumPy, Pandas, Lodash |
| `api` | API documentation | REST APIs, GraphQL, Steam API |
| `other` | Miscellaneous | Anything not fitting above |

**Note:** Categories can be expanded based on community needs.

---

## Storage Structure

**File storage layout:**

```
storage/
├── knowledge/
│   ├── web-framework/
│   │   ├── react_20251022_abc123.zip
│   │   ├── vue_20251022_def456.zip
│   │   └── django_20251022_ghi789.zip
│   ├── game-engine/
│   │   └── godot_20251022_jkl012.zip
│   ├── css-framework/
│   │   └── tailwind_20251022_mno345.zip
│   └── other/
│       └── steam-economy_20251022_pqr678.zip
```

**File naming convention:**
```
{name}_{upload_date}_{short_hash}.zip
```

Where:
- `name` = skill name from database
- `upload_date` = YYYYMMDD format
- `short_hash` = first 6 chars of SHA-256 hash

---

## Example Record

```json
{
  "id": 1,
  "name": "godot",
  "title": "Godot Game Engine Documentation",
  "description": "Complete skill for Godot 4.0 game engine, including GDScript API, tutorials, and examples",
  "category": "game-engine",
  "framework": "Godot",
  "version": "4.0",
  "file_path": "knowledge/game-engine/godot_20251022_a3f8c2.zip",
  "file_size": 2458624,
  "file_hash": "a3f8c2d91e7b4f6a0c8e5d3f1a9b2c4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
  "page_count": 342,
  "upload_date": "2025-10-22 14:30:00",
  "uploader_name": "John Doe",
  "uploader_email": "john@example.com",
  "source_url": "https://docs.godotengine.org/en/stable/",
  "config_json": "{\"name\": \"godot\", \"base_url\": \"https://docs.godotengine.org/en/stable/\", ...}",
  "downloads": 127,
  "rating_sum": 45,
  "rating_count": 10,
  "rating_avg": 4.50,
  "status": "approved",
  "tags": "game-engine, godot, gdscript, 3d, 2d",
  "created_at": "2025-10-22 14:30:00",
  "updated_at": "2025-10-22 14:30:00"
}
```

---

## API Considerations

**For A2.2 (Upload endpoint):**
- Accept multipart/form-data with .zip file + metadata
- Validate .zip structure (check for SKILL.md, references/)
- Generate SHA-256 hash
- Store file and create database record
- Set status to "pending" for review

**For A2.3 (Download/fetch):**
- Query by `id`, `name`, or category
- Return JSON metadata + download URL
- Increment `downloads` counter
- Filter by `status = "approved"` only

**For A2.4 (Preview):**
- Extract SKILL.md from .zip (without full download)
- Return first 500 chars as preview
- Cache previews for performance

**For A2.5 (Categorization):**
- Query by `category`
- Filter by `framework`
- Support multiple categories via tags

**For A2.6 (Search):**
- Full-text search on `title`, `description`, `tags`
- Filter by category, framework, rating
- Sort by: upload_date, downloads, rating_avg

---

## Future Enhancements

**Not included in v1 but could be added:**

1. **User accounts** - Track uploaders with proper authentication
2. **Comments/reviews** - Allow users to leave feedback
3. **Versions** - Support multiple versions of same skill
4. **Dependencies** - Link related skills
5. **Analytics** - Track which skills are most popular
6. **Automatic quality scoring** - Rate skills based on size, examples, etc.

---

## SQL Schema (SQLite)

```sql
CREATE TABLE knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    framework VARCHAR(100),
    version VARCHAR(20),
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    page_count INTEGER,
    upload_date TIMESTAMP NOT NULL,
    uploader_name VARCHAR(100),
    uploader_email VARCHAR(200),
    source_url VARCHAR(500),
    config_json TEXT,
    downloads INTEGER NOT NULL DEFAULT 0,
    rating_sum INTEGER NOT NULL DEFAULT 0,
    rating_count INTEGER NOT NULL DEFAULT 0,
    rating_avg DECIMAL(3,2),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    tags VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (downloads >= 0),
    CHECK (rating_sum >= 0),
    CHECK (rating_count >= 0),
    CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX idx_category ON knowledge(category);
CREATE INDEX idx_status ON knowledge(status);
CREATE INDEX idx_name ON knowledge(name);
```

---

**Status:** Design complete, ready for implementation (A2.2)
