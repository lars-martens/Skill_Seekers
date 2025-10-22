#!/usr/bin/env python3
"""
Knowledge Sharing API Server

Simple Flask API for uploading and downloading Skill Seeker knowledge packages.
Implements the schema defined in docs/KNOWLEDGE_SCHEMA.md
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, is_zipfile
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Configuration
DATABASE_PATH = os.getenv('KNOWLEDGE_DB_PATH', 'data/knowledge.db')
STORAGE_PATH = os.getenv('KNOWLEDGE_STORAGE_PATH', 'storage/knowledge')
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit
ALLOWED_EXTENSIONS = {'zip'}

app = Flask(__name__)

# ============================================================================
# Database Setup
# ============================================================================

def init_db():
    """Initialize SQLite database with schema from KNOWLEDGE_SCHEMA.md"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
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
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON knowledge(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON knowledge(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON knowledge(name)")

    conn.commit()
    conn.close()
    print(f"Database initialized at {DATABASE_PATH}")

# ============================================================================
# Helper Functions
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_hash(file_path):
    """Calculate SHA-256 hash of file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def validate_skill_zip(zip_path):
    """Validate that zip file contains required skill structure"""
    if not is_zipfile(zip_path):
        return False, "File is not a valid zip archive"

    try:
        with ZipFile(zip_path, 'r') as zf:
            files = zf.namelist()

            # Check for SKILL.md at root
            if 'SKILL.md' not in files:
                return False, "Missing required SKILL.md file at root"

            # Check for references directory
            has_references = any(f.startswith('references/') for f in files)
            if not has_references:
                return False, "Missing required references/ directory"

            return True, "Valid skill package"
    except Exception as e:
        return False, f"Error reading zip: {str(e)}"

def get_category_path(category):
    """Get storage subdirectory for category"""
    valid_categories = [
        'web-framework', 'game-engine', 'css-framework', 'cloud-platform',
        'programming-language', 'database', 'library', 'api', 'other'
    ]

    if category not in valid_categories:
        category = 'other'

    return category

# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': os.path.exists(DATABASE_PATH),
        'storage': os.path.exists(STORAGE_PATH),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/knowledge/upload', methods=['POST'])
def upload_knowledge():
    """
    Upload a new knowledge package (.zip file)

    Form data:
    - file: .zip file (required)
    - name: skill name (required)
    - title: display title (required)
    - description: skill description (required)
    - category: category (required)
    - framework: framework name (optional)
    - version: version string (optional)
    - source_url: original docs URL (optional)
    - uploader_name: uploader name (optional)
    - uploader_email: uploader email (optional)
    - tags: comma-separated tags (optional)
    - config_json: JSON config used (optional)
    """

    # Validate file upload
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only .zip files are allowed'}), 400

    # Validate required fields
    required_fields = ['name', 'title', 'description', 'category']
    missing_fields = [f for f in required_fields if not request.form.get(f)]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

    # Get form data
    name = secure_filename(request.form.get('name'))
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    framework = request.form.get('framework', '')
    version = request.form.get('version', '')
    source_url = request.form.get('source_url', '')
    uploader_name = request.form.get('uploader_name', '')
    uploader_email = request.form.get('uploader_email', '')
    tags = request.form.get('tags', '')
    config_json = request.form.get('config_json', '')

    # Save file temporarily
    temp_dir = Path('temp')
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / secure_filename(file.filename)
    file.save(str(temp_path))

    try:
        # Check file size
        file_size = temp_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large (max {MAX_FILE_SIZE / 1024 / 1024}MB)'}), 400

        # Validate zip structure
        is_valid, message = validate_skill_zip(str(temp_path))
        if not is_valid:
            return jsonify({'error': f'Invalid skill package: {message}'}), 400

        # Calculate hash
        file_hash = calculate_hash(str(temp_path))
        short_hash = file_hash[:6]

        # Check if hash already exists
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM knowledge WHERE file_hash = ?", (file_hash,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return jsonify({'error': f'File already exists (duplicate of {existing[0]})'}), 409

        # Create storage path
        category_path = get_category_path(category)
        storage_dir = Path(STORAGE_PATH) / category_path
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Generate final filename
        upload_date = datetime.now().strftime('%Y%m%d')
        final_filename = f"{name}_{upload_date}_{short_hash}.zip"
        final_path = storage_dir / final_filename

        # Move file to storage
        temp_path.rename(final_path)

        # Relative path for database
        relative_path = f"knowledge/{category_path}/{final_filename}"

        # Insert into database
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO knowledge (
                name, title, description, category, framework, version,
                file_path, file_size, file_hash,
                upload_date, uploader_name, uploader_email,
                source_url, config_json, tags,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, title, description, category, framework, version,
            relative_path, file_size, file_hash,
            now, uploader_name, uploader_email,
            source_url, config_json, tags,
            'pending', now, now
        ))

        knowledge_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'id': knowledge_id,
            'name': name,
            'file_hash': file_hash,
            'file_size': file_size,
            'status': 'pending',
            'message': 'Knowledge package uploaded successfully. Pending approval.'
        }), 201

    except sqlite3.IntegrityError as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({'error': f'Database error: {str(e)}'}), 409
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/knowledge/list', methods=['GET'])
def list_knowledge():
    """
    List all approved knowledge packages

    Query params:
    - category: filter by category
    - framework: filter by framework
    - status: filter by status (default: approved)
    - limit: max results (default: 50)
    - offset: pagination offset (default: 0)
    """

    category = request.args.get('category')
    framework = request.args.get('framework')
    status = request.args.get('status', 'approved')
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query
    query = "SELECT * FROM knowledge WHERE status = ?"
    params = [status]

    if category:
        query += " AND category = ?"
        params.append(category)

    if framework:
        query += " AND framework = ?"
        params.append(framework)

    query += " ORDER BY upload_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'name': row['name'],
            'title': row['title'],
            'description': row['description'],
            'category': row['category'],
            'framework': row['framework'],
            'version': row['version'],
            'file_size': row['file_size'],
            'page_count': row['page_count'],
            'upload_date': row['upload_date'],
            'downloads': row['downloads'],
            'rating_avg': row['rating_avg'],
            'tags': row['tags'],
            'source_url': row['source_url']
        })

    conn.close()

    return jsonify({
        'results': results,
        'count': len(results),
        'limit': limit,
        'offset': offset
    })

@app.route('/api/knowledge/<int:knowledge_id>', methods=['GET'])
def get_knowledge(knowledge_id):
    """Get detailed information about a specific knowledge package"""

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM knowledge WHERE id = ?", (knowledge_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Knowledge package not found'}), 404

    return jsonify({
        'id': row['id'],
        'name': row['name'],
        'title': row['title'],
        'description': row['description'],
        'category': row['category'],
        'framework': row['framework'],
        'version': row['version'],
        'file_size': row['file_size'],
        'file_hash': row['file_hash'],
        'page_count': row['page_count'],
        'upload_date': row['upload_date'],
        'uploader_name': row['uploader_name'],
        'source_url': row['source_url'],
        'downloads': row['downloads'],
        'rating_avg': row['rating_avg'],
        'rating_count': row['rating_count'],
        'status': row['status'],
        'tags': row['tags'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at']
    })

@app.route('/api/knowledge/<int:knowledge_id>/download', methods=['GET'])
def download_knowledge(knowledge_id):
    """Download a knowledge package (increments download counter)"""

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM knowledge WHERE id = ? AND status = 'approved'", (knowledge_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({'error': 'Knowledge package not found or not approved'}), 404

    file_path = Path(STORAGE_PATH).parent / row['file_path']

    if not file_path.exists():
        conn.close()
        return jsonify({'error': 'File not found on server'}), 404

    # Increment download counter
    cursor.execute("UPDATE knowledge SET downloads = downloads + 1 WHERE id = ?", (knowledge_id,))
    conn.commit()
    conn.close()

    return send_file(
        str(file_path),
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{row['name']}.zip"
    )

@app.route('/api/knowledge/<int:knowledge_id>/preview', methods=['GET'])
def preview_knowledge(knowledge_id):
    """
    Get a preview of the SKILL.md file from a knowledge package

    Query params:
    - lines: Number of lines to preview (default: 50, max: 200)
    - full: If 'true', return full SKILL.md content (default: false)
    """

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM knowledge WHERE id = ? AND status = 'approved'", (knowledge_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Knowledge package not found or not approved'}), 404

    file_path = Path(STORAGE_PATH).parent / row['file_path']

    if not file_path.exists():
        return jsonify({'error': 'File not found on server'}), 404

    # Extract SKILL.md from zip
    try:
        with ZipFile(file_path, 'r') as zf:
            if 'SKILL.md' not in zf.namelist():
                return jsonify({'error': 'SKILL.md not found in package'}), 404

            # Read SKILL.md content
            with zf.open('SKILL.md') as f:
                content = f.read().decode('utf-8')

            # Get query params
            full = request.args.get('full', 'false').lower() == 'true'
            max_lines = min(int(request.args.get('lines', 50)), 200)

            if full:
                # Return full content
                preview = content
                is_truncated = False
            else:
                # Return limited preview
                lines = content.split('\n')
                preview = '\n'.join(lines[:max_lines])
                is_truncated = len(lines) > max_lines

            # Get file listing
            file_list = zf.namelist()
            reference_files = [f for f in file_list if f.startswith('references/')]

            return jsonify({
                'id': row['id'],
                'name': row['name'],
                'title': row['title'],
                'preview': preview,
                'is_truncated': is_truncated,
                'total_lines': len(content.split('\n')),
                'preview_lines': len(preview.split('\n')),
                'file_count': len(file_list),
                'reference_count': len(reference_files),
                'reference_files': reference_files[:20]  # Limit to first 20
            })

    except Exception as e:
        return jsonify({'error': f'Failed to read package: {str(e)}'}), 500

@app.route('/api/categories', methods=['GET'])
def list_categories():
    """List all available categories with counts"""

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM knowledge
        WHERE status = 'approved'
        GROUP BY category
        ORDER BY count DESC
    """)

    results = []
    for row in cursor.fetchall():
        results.append({
            'category': row[0],
            'count': row[1]
        })

    conn.close()

    return jsonify({'categories': results})

@app.route('/api/knowledge/<int:knowledge_id>/related', methods=['GET'])
def get_related_knowledge(knowledge_id):
    """
    Get related knowledge packages based on category, framework, and tags

    Query params:
    - limit: Maximum results (default: 5)
    """

    limit = min(int(request.args.get('limit', 5)), 20)

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get the source package
    cursor.execute("SELECT * FROM knowledge WHERE id = ? AND status = 'approved'", (knowledge_id,))
    source = cursor.fetchone()

    if not source:
        conn.close()
        return jsonify({'error': 'Knowledge package not found or not approved'}), 404

    # Find related packages using scoring algorithm
    # Score: +3 for same category, +2 for same framework, +1 for shared tags
    query = """
        SELECT
            k.*,
            (CASE WHEN k.category = ? THEN 3 ELSE 0 END +
             CASE WHEN k.framework = ? AND k.framework != '' THEN 2 ELSE 0 END) as score
        FROM knowledge k
        WHERE k.id != ? AND k.status = 'approved'
        ORDER BY score DESC, k.downloads DESC
        LIMIT ?
    """

    cursor.execute(query, (source['category'], source['framework'], knowledge_id, limit))
    rows = cursor.fetchall()

    results = []
    for row in rows:
        if row['score'] > 0:  # Only include if there's some relation
            results.append({
                'id': row['id'],
                'name': row['name'],
                'title': row['title'],
                'description': row['description'],
                'category': row['category'],
                'framework': row['framework'],
                'downloads': row['downloads'],
                'rating_avg': row['rating_avg'],
                'relevance_score': row['score']
            })

    conn.close()

    return jsonify({
        'source_id': knowledge_id,
        'source_title': source['title'],
        'related': results,
        'count': len(results)
    })

@app.route('/api/knowledge/<int:knowledge_id>/suggest-tags', methods=['GET'])
def suggest_tags(knowledge_id):
    """
    Suggest additional tags for a knowledge package based on content analysis

    This analyzes the SKILL.md content and suggests relevant tags
    """

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM knowledge WHERE id = ?", (knowledge_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Knowledge package not found'}), 404

    file_path = Path(STORAGE_PATH).parent / row['file_path']

    if not file_path.exists():
        return jsonify({'error': 'File not found on server'}), 404

    try:
        with ZipFile(file_path, 'r') as zf:
            if 'SKILL.md' not in zf.namelist():
                return jsonify({'error': 'SKILL.md not found in package'}), 404

            # Read SKILL.md
            with zf.open('SKILL.md') as f:
                content = f.read().decode('utf-8').lower()

            # Common technology keywords to look for
            tag_keywords = {
                'web': ['web', 'html', 'css', 'http', 'browser'],
                'api': ['api', 'rest', 'graphql', 'endpoint'],
                'database': ['database', 'sql', 'query', 'table'],
                'frontend': ['frontend', 'ui', 'component', 'jsx', 'tsx'],
                'backend': ['backend', 'server', 'middleware'],
                '3d': ['3d', 'mesh', 'shader', 'render'],
                '2d': ['2d', 'sprite', 'canvas'],
                'game': ['game', 'player', 'scene', 'physics'],
                'mobile': ['mobile', 'android', 'ios', 'app'],
                'cloud': ['cloud', 'aws', 'azure', 'deployment'],
                'testing': ['test', 'testing', 'unit test', 'integration'],
                'async': ['async', 'promise', 'await', 'concurrent'],
                'realtime': ['realtime', 'websocket', 'streaming'],
                'authentication': ['auth', 'login', 'oauth', 'jwt'],
                'documentation': ['docs', 'documentation', 'guide'],
            }

            # Find matching tags
            suggested_tags = []
            existing_tags = set(row['tags'].lower().split(',')) if row['tags'] else set()

            for tag, keywords in tag_keywords.items():
                if tag not in existing_tags:
                    if any(keyword in content for keyword in keywords):
                        suggested_tags.append(tag)

            return jsonify({
                'id': knowledge_id,
                'name': row['name'],
                'current_tags': row['tags'].split(',') if row['tags'] else [],
                'suggested_tags': suggested_tags,
                'suggestion_count': len(suggested_tags)
            })

    except Exception as e:
        return jsonify({'error': f'Failed to analyze package: {str(e)}'}), 500

@app.route('/api/frameworks', methods=['GET'])
def list_frameworks():
    """List all frameworks with counts"""

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT framework, COUNT(*) as count
        FROM knowledge
        WHERE status = 'approved' AND framework IS NOT NULL AND framework != ''
        GROUP BY framework
        ORDER BY count DESC
    """)

    results = []
    for row in cursor.fetchall():
        results.append({
            'framework': row[0],
            'count': row[1]
        })

    conn.close()

    return jsonify({'frameworks': results})

@app.route('/api/search', methods=['GET'])
def search_knowledge():
    """
    Full-text search across knowledge packages

    Query params:
    - q: Search query (required)
    - category: Filter by category (optional)
    - framework: Filter by framework (optional)
    - sort: Sort by 'relevance', 'downloads', 'rating', 'date' (default: relevance)
    - limit: Maximum results (default: 20, max: 100)
    - offset: Pagination offset (default: 0)
    """

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query (q) is required'}), 400

    category = request.args.get('category')
    framework = request.args.get('framework')
    sort_by = request.args.get('sort', 'relevance')
    limit = min(int(request.args.get('limit', 20)), 100)
    offset = int(request.args.get('offset', 0))

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build search query
    # SQLite doesn't have great full-text search without FTS5, so we use LIKE
    # In production, you'd want to use FTS5 or external search engine

    search_pattern = f"%{query}%"

    sql = """
        SELECT
            *,
            (
                CASE WHEN title LIKE ? THEN 10 ELSE 0 END +
                CASE WHEN name LIKE ? THEN 8 ELSE 0 END +
                CASE WHEN description LIKE ? THEN 5 ELSE 0 END +
                CASE WHEN tags LIKE ? THEN 3 ELSE 0 END +
                CASE WHEN framework LIKE ? THEN 2 ELSE 0 END
            ) as relevance
        FROM knowledge
        WHERE status = 'approved'
        AND (
            title LIKE ? OR
            name LIKE ? OR
            description LIKE ? OR
            tags LIKE ? OR
            framework LIKE ?
        )
    """

    params = [search_pattern] * 10  # 5 for scoring + 5 for WHERE

    # Add filters
    if category:
        sql += " AND category = ?"
        params.append(category)

    if framework:
        sql += " AND framework = ?"
        params.append(framework)

    # Add sorting
    if sort_by == 'downloads':
        sql += " ORDER BY downloads DESC"
    elif sort_by == 'rating':
        sql += " ORDER BY rating_avg DESC, rating_count DESC"
    elif sort_by == 'date':
        sql += " ORDER BY upload_date DESC"
    else:  # relevance
        sql += " ORDER BY relevance DESC, downloads DESC"

    # Add pagination
    sql += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'name': row['name'],
            'title': row['title'],
            'description': row['description'],
            'category': row['category'],
            'framework': row['framework'],
            'version': row['version'],
            'file_size': row['file_size'],
            'page_count': row['page_count'],
            'upload_date': row['upload_date'],
            'downloads': row['downloads'],
            'rating_avg': row['rating_avg'],
            'tags': row['tags'],
            'source_url': row['source_url'],
            'relevance_score': row['relevance']
        })

    # Get total count for pagination
    count_sql = """
        SELECT COUNT(*) as total
        FROM knowledge
        WHERE status = 'approved'
        AND (
            title LIKE ? OR
            name LIKE ? OR
            description LIKE ? OR
            tags LIKE ? OR
            framework LIKE ?
        )
    """
    count_params = [search_pattern] * 5

    if category:
        count_sql += " AND category = ?"
        count_params.append(category)

    if framework:
        count_sql += " AND framework = ?"
        count_params.append(framework)

    cursor.execute(count_sql, count_params)
    total = cursor.fetchone()['total']

    conn.close()

    return jsonify({
        'query': query,
        'results': results,
        'count': len(results),
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': (offset + len(results)) < total,
        'filters': {
            'category': category,
            'framework': framework,
            'sort': sort_by
        }
    })

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("Initializing Knowledge Sharing API...")
    init_db()

    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('API_DEBUG', 'false').lower() == 'true'

    print(f"Starting server at http://{host}:{port}")
    print(f"Database: {DATABASE_PATH}")
    print(f"Storage: {STORAGE_PATH}")

    app.run(host=host, port=port, debug=debug)
