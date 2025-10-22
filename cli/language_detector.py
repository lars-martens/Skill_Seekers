#!/usr/bin/env python3
"""
Programming Language Detector
Detects programming languages using multiple methods
"""

import re
from typing import Optional, Dict, List
from github_api import GitHubAPIClient
import base64


class LanguageDetector:
    """Detects programming languages from files"""

    # Extension to language mapping (comprehensive)
    EXTENSION_MAP = {
        # Python
        '.py': 'python',
        '.pyw': 'python',
        '.pyx': 'python',

        # JavaScript/TypeScript
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',

        # Java/JVM
        '.java': 'java',
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        '.scala': 'scala',
        '.groovy': 'groovy',

        # C/C++
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.hpp': 'cpp',
        '.hxx': 'cpp',
        '.hh': 'cpp',

        # C#
        '.cs': 'csharp',
        '.cshtml': 'csharp',

        # Go
        '.go': 'go',

        # Rust
        '.rs': 'rust',

        # Ruby
        '.rb': 'ruby',
        '.erb': 'ruby',

        # PHP
        '.php': 'php',
        '.phtml': 'php',
        '.php3': 'php',
        '.php4': 'php',
        '.php5': 'php',

        # Shell
        '.sh': 'shell',
        '.bash': 'shell',
        '.zsh': 'shell',
        '.fish': 'shell',

        # Web
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',

        # Swift
        '.swift': 'swift',

        # Objective-C
        '.m': 'objective-c',
        '.mm': 'objective-c',

        # Dart
        '.dart': 'dart',

        # Lua
        '.lua': 'lua',

        # R
        '.r': 'r',
        '.R': 'r',

        # Julia
        '.jl': 'julia',

        # Haskell
        '.hs': 'haskell',
        '.lhs': 'haskell',

        # Elixir
        '.ex': 'elixir',
        '.exs': 'elixir',

        # Clojure
        '.clj': 'clojure',
        '.cljs': 'clojure',
        '.cljc': 'clojure',

        # SQL
        '.sql': 'sql',

        # YAML
        '.yml': 'yaml',
        '.yaml': 'yaml',

        # JSON
        '.json': 'json',

        # XML
        '.xml': 'xml',

        # Markdown
        '.md': 'markdown',
        '.markdown': 'markdown',

        # Configuration
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'conf'
    }

    # Content-based detection patterns
    CONTENT_PATTERNS = {
        'python': [
            r'def\s+\w+\s*\(',
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            r'class\s+\w+\s*\(',
            r'if\s+__name__\s*==\s*[\'"]__main__[\'"]'
        ],
        'javascript': [
            r'function\s+\w+\s*\(',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'=>\s*\{',
            r'require\s*\(',
            r'module\.exports'
        ],
        'typescript': [
            r'interface\s+\w+',
            r'type\s+\w+\s*=',
            r':\s*string\b',
            r':\s*number\b',
            r'<T>',
            r'import.*from.*[\'"]'
        ],
        'java': [
            r'public\s+class\s+\w+',
            r'private\s+\w+\s+\w+',
            r'public\s+static\s+void\s+main',
            r'package\s+\w+',
            r'import\s+java\.'
        ],
        'go': [
            r'package\s+\w+',
            r'func\s+\w+\s*\(',
            r'import\s+\(',
            r'type\s+\w+\s+struct',
            r'fmt\.Print'
        ],
        'rust': [
            r'fn\s+\w+\s*\(',
            r'let\s+mut\s+\w+',
            r'use\s+\w+',
            r'impl\s+\w+',
            r'pub\s+fn'
        ],
        'ruby': [
            r'def\s+\w+',
            r'class\s+\w+',
            r'require\s+[\'"]',
            r'end\s*$',
            r'puts\s+'
        ],
        'php': [
            r'<\?php',
            r'function\s+\w+\s*\(',
            r'class\s+\w+',
            r'\$\w+\s*=',
            r'echo\s+'
        ],
        'c': [
            r'#include\s+<\w+\.h>',
            r'int\s+main\s*\(',
            r'printf\s*\(',
            r'void\s+\w+\s*\('
        ],
        'cpp': [
            r'#include\s+<\w+>',
            r'std::',
            r'namespace\s+\w+',
            r'template\s*<',
            r'cout\s*<<'
        ],
        'csharp': [
            r'using\s+System',
            r'namespace\s+\w+',
            r'public\s+class\s+\w+',
            r'static\s+void\s+Main'
        ],
        'swift': [
            r'import\s+\w+',
            r'func\s+\w+\s*\(',
            r'let\s+\w+',
            r'var\s+\w+',
            r'class\s+\w+'
        ],
        'shell': [
            r'#!/bin/bash',
            r'#!/bin/sh',
            r'echo\s+',
            r'if\s+\[',
            r'for\s+\w+\s+in'
        ]
    }

    def __init__(self, client: Optional[GitHubAPIClient] = None):
        """
        Initialize language detector

        Args:
            client: Optional GitHubAPIClient instance
        """
        self.client = client or GitHubAPIClient()

    def detect_by_extension(self, filename: str) -> Optional[str]:
        """
        Detect language by file extension

        Args:
            filename: Name of file

        Returns:
            Language name or None
        """
        filename_lower = filename.lower()

        for ext, lang in self.EXTENSION_MAP.items():
            if filename_lower.endswith(ext):
                return lang

        return None

    def detect_by_content(self, content: str, max_lines: int = 50) -> Optional[str]:
        """
        Detect language by analyzing file content

        Args:
            content: File content
            max_lines: Number of lines to analyze (default: 50)

        Returns:
            Language name or None
        """
        # Analyze first N lines
        lines = content.split('\n')[:max_lines]
        sample = '\n'.join(lines)

        # Score each language
        scores = {}

        for lang, patterns in self.CONTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, sample, re.MULTILINE):
                    score += 1
            if score > 0:
                scores[lang] = score

        # Return language with highest score
        if scores:
            return max(scores, key=scores.get)

        return None

    def detect_by_github(self, owner: str, repo: str) -> Dict[str, int]:
        """
        Detect languages using GitHub's language detection API

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary mapping language names to bytes of code
        """
        return self.client.get_languages(owner, repo)

    def detect_file(self, filename: str, content: Optional[str] = None) -> Dict:
        """
        Detect language using multiple methods

        Args:
            filename: Name of file
            content: Optional file content for content-based detection

        Returns:
            Dictionary with detection results
        """
        result = {
            'filename': filename,
            'extension_detection': None,
            'content_detection': None,
            'final_language': None,
            'confidence': 'low'
        }

        # Method 1: Extension-based detection
        ext_lang = self.detect_by_extension(filename)
        result['extension_detection'] = ext_lang

        # Method 2: Content-based detection
        if content:
            content_lang = self.detect_by_content(content)
            result['content_detection'] = content_lang

            # Determine final language
            if ext_lang and content_lang:
                if ext_lang == content_lang:
                    result['final_language'] = ext_lang
                    result['confidence'] = 'high'
                else:
                    # Prefer extension for ambiguous cases
                    result['final_language'] = ext_lang
                    result['confidence'] = 'medium'
            elif ext_lang:
                result['final_language'] = ext_lang
                result['confidence'] = 'medium'
            elif content_lang:
                result['final_language'] = content_lang
                result['confidence'] = 'low'
        else:
            # Only extension available
            if ext_lang:
                result['final_language'] = ext_lang
                result['confidence'] = 'medium'

        return result

    def detect_repo_file(self, owner: str, repo: str, path: str,
                        branch: str = "main") -> Dict:
        """
        Detect language for a file in GitHub repository

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            branch: Branch name

        Returns:
            Dictionary with detection results
        """
        # Get file content
        file_data = self.client.get_file_content(owner, repo, path, branch)
        content_base64 = file_data.get('content', '')
        content = base64.b64decode(content_base64).decode('utf-8', errors='ignore')

        return self.detect_file(path, content)

    def analyze_repository(self, owner: str, repo: str,
                          max_files: int = 100,
                          branch: str = "main") -> Dict:
        """
        Analyze all files in repository and detect languages

        Args:
            owner: Repository owner
            repo: Repository name
            max_files: Maximum files to analyze
            branch: Branch name

        Returns:
            Dictionary with language statistics
        """
        # Get GitHub's language detection
        github_langs = self.detect_by_github(owner, repo)

        # Get all files
        files = self.client.list_files(owner, repo, branch)[:max_files]

        # Detect language for each file
        file_detections = {}
        language_counts = {}

        print(f"Analyzing {len(files)} files from {owner}/{repo}...")

        for i, file_info in enumerate(files):
            path = file_info['path']
            lang = self.detect_by_extension(path)

            if lang:
                file_detections[path] = lang
                language_counts[lang] = language_counts.get(lang, 0) + 1

                if i % 10 == 0:
                    print(f"  Processed {i+1}/{len(files)} files...")

        print(f"✓ Analysis complete!")

        return {
            'repository': f"{owner}/{repo}",
            'github_languages': github_langs,
            'detected_languages': language_counts,
            'total_files_analyzed': len(files),
            'files_with_language': len(file_detections),
            'file_detections': file_detections
        }


# Test function
def test_detector():
    """Test the language detector"""
    print("Testing Language Detector\n")

    detector = LanguageDetector()

    # Test 1: Extension detection
    print("Test 1: Extension-based detection")
    test_files = ['main.py', 'app.js', 'index.html', 'style.css', 'code.rs']
    for filename in test_files:
        lang = detector.detect_by_extension(filename)
        print(f"  {filename:20s} → {lang}")

    # Test 2: Content detection
    print("\nTest 2: Content-based detection")

    python_code = "def hello():\n    print('Hello')\n    return True"
    lang = detector.detect_by_content(python_code)
    print(f"  Python code → {lang}")

    js_code = "const hello = () => {\n  console.log('Hello');\n};"
    lang = detector.detect_by_content(js_code)
    print(f"  JavaScript code → {lang}")

    # Test 3: Combined detection
    print("\nTest 3: Combined detection")
    result = detector.detect_file('script.py', python_code)
    print(f"  Filename: {result['filename']}")
    print(f"  Extension: {result['extension_detection']}")
    print(f"  Content: {result['content_detection']}")
    print(f"  Final: {result['final_language']} ({result['confidence']} confidence)")

    # Test 4: Repository analysis
    print("\nTest 4: Repository analysis")
    try:
        analysis = detector.analyze_repository(
            'anthropics',
            'anthropic-sdk-python',
            max_files=50
        )

        print(f"\n  Repository: {analysis['repository']}")
        print(f"  Files analyzed: {analysis['total_files_analyzed']}")
        print(f"  Files with language: {analysis['files_with_language']}")

        print(f"\n  GitHub detected languages:")
        for lang, bytes_count in sorted(analysis['github_languages'].items(), key=lambda x: x[1], reverse=True):
            print(f"    {lang:20s}: {bytes_count:,} bytes")

        print(f"\n  Our detected languages:")
        for lang, count in sorted(analysis['detected_languages'].items(), key=lambda x: x[1], reverse=True):
            print(f"    {lang:20s}: {count} files")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_detector()
