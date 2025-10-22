# GitHub Repository Config Format

This document describes the JSON configuration format for GitHub repository scraping.

## Overview

GitHub configs enable automated extraction of documentation from code repositories. Unlike web documentation configs, GitHub configs extract:

- README files
- Code comments and docstrings
- Function and class signatures
- Usage examples from tests
- Repository metadata

## Config Structure

### Basic Config

```json
{
  "type": "github",
  "name": "repository-name",
  "description": "When to use this skill",
  "repository": {
    "url": "https://github.com/owner/repo",
    "owner": "owner",
    "repo": "repository",
    "branch": "main"
  },
  "extraction": {
    "max_files": 200,
    "include_tests": true,
    "file_extensions": [".py", ".js"],
    "exclude_patterns": ["node_modules/", ".git/"]
  },
  "components": {
    "extract_readme": true,
    "extract_docstrings": true,
    "extract_comments": true,
    "extract_signatures": true,
    "extract_test_examples": true
  }
}
```

## Field Reference

### Top Level

- **type** (string, required): Must be `"github"` for repository configs
- **name** (string, required): Skill identifier (lowercase, alphanumeric, hyphens, underscores)
- **description** (string, required): When Claude should use this skill

### repository

Repository information:

- **url** (string, required): Full GitHub repository URL
- **owner** (string, required): Repository owner (username or organization)
- **repo** (string, required): Repository name
- **branch** (string, optional): Branch to scrape (default: "main")

### extraction

Extraction parameters:

- **max_files** (integer, optional): Maximum files to process (default: 100)
- **include_tests** (boolean, optional): Extract usage examples from tests (default: true)
- **file_extensions** (array, optional): File extensions to process (default: all supported)
- **exclude_patterns** (array, optional): Patterns to exclude (glob format)

**Common exclude patterns:**
```json
[
  "node_modules/",
  ".git/",
  "__pycache__/",
  "*.pyc",
  "build/",
  "dist/",
  "coverage/",
  "*.min.js"
]
```

### components

Enable/disable extraction components:

- **extract_readme** (boolean, optional): Extract README.md (default: true)
- **extract_docstrings** (boolean, optional): Extract docstrings (default: true)
- **extract_comments** (boolean, optional): Extract comments (default: true)
- **extract_signatures** (boolean, optional): Extract function/class signatures (default: true)
- **extract_test_examples** (boolean, optional): Extract test examples (default: true)

### focus_areas (optional)

Target specific directories or files:

```json
{
  "focus_areas": {
    "core": ["src/core/", "src/main/"],
    "api": ["src/api.js", "src/client.js"],
    "utils": ["src/utils/"]
  }
}
```

### metadata (optional)

Additional metadata:

- **programming_languages** (array): Languages used in repository
- **topics** (array): Repository topics/tags

## Supported Languages

The scraper automatically detects and extracts from:

**Documentation:**
- Python (docstrings, comments)
- JavaScript/TypeScript (JSDoc, comments)
- Java (Javadoc, comments)
- Go (comments)
- Rust (doc comments)
- Ruby (RDoc, comments)
- PHP (PHPDoc, comments)
- C/C++ (Doxygen, comments)
- C# (XML docs, comments)
- Swift (comments)

**Test Frameworks:**
- Python: pytest, unittest
- JavaScript: Jest, Mocha, Jasmine
- TypeScript: Jest, Mocha
- Java: JUnit
- Go: testing package
- Rust: built-in tests
- Ruby: RSpec, Minitest
- PHP: PHPUnit
- C#: NUnit, xUnit

## Usage

### Using CLI Tool

```bash
# With config file
python3 cli/github_scraper.py https://github.com/owner/repo --config configs/github-example.json

# Without config (uses defaults)
python3 cli/github_scraper.py https://github.com/owner/repo --max-files 200

# With GitHub token (higher rate limits)
export GITHUB_TOKEN=ghp_your_token_here
python3 cli/github_scraper.py https://github.com/owner/repo --token $GITHUB_TOKEN
```

### Using MCP Tool

```json
{
  "name": "scrape_github",
  "arguments": {
    "url": "https://github.com/owner/repo",
    "max_files": 200,
    "include_tests": true,
    "output_dir": "output"
  }
}
```

## Example Configs

### Python SDK

```json
{
  "type": "github",
  "name": "anthropic-sdk-python",
  "description": "Anthropic Python SDK for Claude API",
  "repository": {
    "url": "https://github.com/anthropics/anthropic-sdk-python",
    "owner": "anthropics",
    "repo": "anthropic-sdk-python",
    "branch": "main"
  },
  "extraction": {
    "max_files": 200,
    "include_tests": true,
    "file_extensions": [".py", ".md"],
    "exclude_patterns": ["__pycache__/", "*.pyc", "build/", "dist/"]
  }
}
```

### JavaScript Library

```json
{
  "type": "github",
  "name": "react",
  "description": "React library for building UIs",
  "repository": {
    "url": "https://github.com/facebook/react",
    "owner": "facebook",
    "repo": "react",
    "branch": "main"
  },
  "extraction": {
    "max_files": 300,
    "include_tests": true,
    "file_extensions": [".js", ".jsx", ".ts", ".tsx"],
    "exclude_patterns": ["node_modules/", "build/", "dist/", "*.min.js"]
  },
  "focus_areas": {
    "core": ["packages/react/", "packages/react-dom/"]
  }
}
```

### Go Package

```json
{
  "type": "github",
  "name": "cobra",
  "description": "Cobra CLI framework for Go",
  "repository": {
    "url": "https://github.com/spf13/cobra",
    "owner": "spf13",
    "repo": "cobra",
    "branch": "main"
  },
  "extraction": {
    "max_files": 100,
    "include_tests": true,
    "file_extensions": [".go", ".md"],
    "exclude_patterns": [".git/", "vendor/"]
  }
}
```

## Best Practices

### 1. Start Small

Begin with a low `max_files` value to test:

```json
{
  "extraction": {
    "max_files": 20
  }
}
```

### 2. Use Focused Extraction

For large repositories, target specific areas:

```json
{
  "focus_areas": {
    "core": ["src/core/"],
    "api": ["src/api/"]
  }
}
```

### 3. Exclude Build Artifacts

Always exclude generated files:

```json
{
  "exclude_patterns": [
    "node_modules/",
    "build/",
    "dist/",
    "*.min.js",
    "*.pyc",
    "__pycache__/"
  ]
}
```

### 4. Include Tests for Examples

Tests provide valuable usage examples:

```json
{
  "extraction": {
    "include_tests": true
  }
}
```

### 5. Use GitHub Tokens

For better rate limits and private repos:

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

## Rate Limiting

GitHub API has rate limits:

- **Without token**: 60 requests/hour
- **With token**: 5,000 requests/hour

The scraper automatically handles rate limiting and will pause when limits are reached.

## Output Structure

Generated output includes:

```
output/
└── repository-name_github/
    ├── SKILL.md              # Main skill file
    ├── README.md             # Repository README
    ├── documentation.json    # Extracted docstrings/comments
    ├── signatures.json       # Function/class signatures
    └── examples.json         # Test examples
```

## Troubleshooting

### Rate Limit Exceeded

**Problem:** Getting rate limit errors

**Solution:** Use a GitHub personal access token:
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### Too Many Files

**Problem:** Processing takes too long

**Solution:** Reduce `max_files` or use `focus_areas`:
```json
{
  "extraction": {
    "max_files": 50
  },
  "focus_areas": {
    "core": ["src/"]
  }
}
```

### Missing Documentation

**Problem:** No docstrings extracted

**Solution:** Check file extensions match repository language:
```json
{
  "extraction": {
    "file_extensions": [".py", ".js", ".go"]
  }
}
```

## See Also

- [GitHub API Documentation](https://docs.github.com/en/rest)
- [CLAUDE.md](../CLAUDE.md) - Main project documentation
- [Web Config Format](../README.md#configuration-file-structure) - For documentation websites
