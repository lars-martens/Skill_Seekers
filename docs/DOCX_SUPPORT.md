# Microsoft Word (.docx) Support

**Status:** In Development (B2 Tasks)
**Progress:** B2.1-B2.6 Complete (MCP Integration Pending)

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

**B2.3: Heading Extraction** - Completed October 22, 2025
- Created `cli/extract_docx_headings.py`
- Extracts H1-H6 headings with hierarchy
- Auto-categorizes based on heading structure
- Outputs as JSON, markdown outline, or categories

**B2.4: Code Block Detection** - Completed October 22, 2025
- Created `cli/extract_docx_code.py`
- Detects code via monospace fonts
- Language detection for 15+ languages
- Context extraction and grouping

**B2.5: Table Conversion** - Completed October 22, 2025
- Created `cli/extract_docx_tables.py`
- Extracts tables and converts to markdown
- Table type detection (API, config, data, etc.)
- Context paragraph extraction

**B2.6: Complete CLI Tool** - Completed October 22, 2025
- Created `cli/docx_scraper.py` - full-featured tool
- Processes single or multiple .docx files
- Generates SKILL.md and reference files
- Compatible with Skill Seeker's build pipeline
- Interactive mode, config file support

### 🚧 In Progress

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

### Complete Workflow (B2.6) - Recommended

**Interactive mode:**
```bash
python3 cli/docx_scraper.py --interactive
# Follow prompts to configure skill
```

**Single document:**
```bash
python3 cli/docx_scraper.py document.docx --name myskill --description "My documentation"
```

**Multiple documents:**
```bash
python3 cli/docx_scraper.py doc1.docx doc2.docx doc3.docx --name myskill
```

**Rebuild from cached data:**
```bash
python3 cli/docx_scraper.py --name myskill --skip-extract
```

### Individual Component Tools

**Text Extraction (B2.2):**
```bash
python3 cli/extract_docx_text.py document.docx --stats
```

**Heading Extraction (B2.3):**
```bash
python3 cli/extract_docx_headings.py document.docx --categories
python3 cli/extract_docx_headings.py document.docx --json --output headings.json
```

**Code Block Detection (B2.4):**
```bash
python3 cli/extract_docx_code.py document.docx --context
python3 cli/extract_docx_code.py document.docx --by-language --markdown
```

**Table Extraction (B2.5):**
```bash
python3 cli/extract_docx_tables.py document.docx --context
python3 cli/extract_docx_tables.py document.docx --detect-type --output tables.md
```

### Complete Features

- ✅ Extracts text, headings, code blocks, and tables
- ✅ Auto-categorization based on heading structure
- ✅ Language detection for code (15+ languages)
- ✅ Table type detection (API, config, data, etc.)
- ✅ Generates SKILL.md and reference files
- ✅ Compatible with existing enhancement pipeline
- ✅ Interactive configuration wizard
- ✅ Multi-document support
- ✅ Cached data reuse (--skip-extract)

---

## Next: MCP Integration (B2.7)

### B2.7: MCP Tool Integration
- Add `mcp__skill-seeker__scrape_docx` tool to MCP server
- Enable .docx scraping directly from Claude Code
- Compatible with existing 9 MCP tools
- Same API as `scrape_docs` but for Word files

**Expected completion:** October 22, 2025

Once B2.7 is complete, users will be able to:
```python
# From Claude Code MCP
mcp__skill-seeker__scrape_docx(
    files=["doc1.docx", "doc2.docx"],
    skill_name="myskill",
    description="My documentation skill"
)
```

---

## Roadmap

| Task | Status | Description | File |
|------|--------|-------------|------|
| B2.1 | ✅ Done | Research .docx parsing libraries | `docs/research/B2.1_DOCX_PARSING_RESEARCH.md` |
| B2.2 | ✅ Done | Create simple text extractor | `cli/extract_docx_text.py` |
| B2.3 | ✅ Done | Extract headings and categorize | `cli/extract_docx_headings.py` |
| B2.4 | ✅ Done | Extract code blocks | `cli/extract_docx_code.py` |
| B2.5 | ✅ Done | Convert tables to markdown | `cli/extract_docx_tables.py` |
| B2.6 | ✅ Done | Create full CLI tool | `cli/docx_scraper.py` |
| B2.7 | 🚧 Next | Add MCP tool integration | `mcp_server/skill_seeker_server.py` |

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
