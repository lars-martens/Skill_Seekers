# Microsoft Word (.docx) Support

**Status:** In Development (B2 Tasks)
**Progress:** B2.1-B2.2 Complete

---

## Overview

Skill Seeker is adding support for extracting documentation from Microsoft Word (.docx) files. This enables skills to be created from Word-based documentation, technical specifications, and guides.

---

## Current Status (B2.2)

### ✅ Completed Features

**B2.1: Research** - Completed October 22, 2025
- Evaluated python-docx library (v1.2.0)
- Documented extraction capabilities
- Planned implementation strategy
- See: `docs/research/B2.1_DOCX_PARSING_RESEARCH.md`

**B2.2: Basic Text Extraction** - Completed October 22, 2025
- Created `cli/extract_docx_text.py` proof of concept
- Extracts all paragraph text from .docx files
- Includes document statistics
- Command-line interface with output options

### 🚧 In Progress

**B2.3:** Extract headings and create categories
**B2.4:** Extract code blocks from Word docs
**B2.5:** Extract tables and convert to markdown
**B2.6:** Create `docx_scraper.py` CLI tool
**B2.7:** Add MCP tool `scrape_docx`

---

## Installation

### Requirements

```bash
# Python 3.9 or higher required
pip install python-docx>=1.2.0
```

---

## Usage

### Basic Text Extraction (B2.2)

**Extract and print to console:**
```bash
python3 cli/extract_docx_text.py document.docx
```

**Extract and save to file:**
```bash
python3 cli/extract_docx_text.py document.docx --output extracted.txt
```

**Show document statistics:**
```bash
python3 cli/extract_docx_text.py document.docx --stats
```

**Verbose output:**
```bash
python3 cli/extract_docx_text.py document.docx --verbose
```

### Features

- ✅ Extracts all paragraph text
- ✅ Preserves paragraph structure (double newline separation)
- ✅ Skips empty paragraphs
- ✅ Shows document statistics (paragraphs, words, characters, tables)
- ✅ Error handling for missing files and library
- ✅ Optional file output
- ✅ UTF-8 encoding support

---

## Coming Soon

### B2.3: Heading Extraction
- Detect Heading 1-6 styles
- Create category structure from headings
- Automatic categorization

### B2.4: Code Block Detection
- Detect monospace fonts (Courier, Consolas, etc.)
- Extract code samples
- Syntax detection via heuristics

### B2.5: Table Conversion
- Extract tables from Word documents
- Convert to markdown format
- Preserve table structure

### B2.6: Full CLI Tool
- Complete `docx_scraper.py` similar to `doc_scraper.py`
- Config-based scraping
- Integration with existing Skill Seeker workflow
- Generate SKILL.md from Word documents

### B2.7: MCP Integration
- Add `mcp__skill-seeker__scrape_docx` tool
- Enable .docx scraping from Claude Code
- Compatible with existing MCP tools

---

## Roadmap

| Task | Status | Description |
|------|--------|-------------|
| B2.1 | ✅ Done | Research .docx parsing libraries |
| B2.2 | ✅ Done | Create simple text extractor |
| B2.3 | 🚧 Next | Extract headings and categorize |
| B2.4 | ⏳ Planned | Extract code blocks |
| B2.5 | ⏳ Planned | Convert tables to markdown |
| B2.6 | ⏳ Planned | Create full CLI tool |
| B2.7 | ⏳ Planned | Add MCP tool integration |

---

## Documentation

- **Research:** `docs/research/B2.1_DOCX_PARSING_RESEARCH.md`
- **Roadmap:** `FLEXIBLE_ROADMAP.md` (Category B: New Input Formats)

---

## Technical Details

### Library: python-docx

- **Version:** 1.2.0
- **Python:** >= 3.9
- **Dependencies:** lxml
- **Status:** Production/Stable
- **Docs:** https://python-docx.readthedocs.io/

### Architecture

```
.docx file
    ↓
python-docx parsing
    ↓
Text/Heading/Table/Code extraction
    ↓
Category assignment
    ↓
JSON format (same as HTML scraper)
    ↓
Skill building (existing pipeline)
```

### Output Format

The .docx scraper will produce the same JSON structure as the HTML scraper:

```json
{
    "url": "file:///path/to/document.docx",
    "title": "Document Title",
    "content": "Full text content...",
    "code_samples": [
        {
            "language": "python",
            "code": "def example():\n    pass"
        }
    ],
    "patterns": [],
    "category": "getting_started"
}
```

---

## Contributing

Help accelerate .docx support development:

1. **Test the text extractor** with your Word documents
2. **Report issues** with extraction quality
3. **Suggest improvements** for categorization
4. **Contribute example documents** for testing

---

**Last Updated:** October 22, 2025
**Version:** B2.2 (Text Extraction POC)
