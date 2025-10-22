#!/usr/bin/env python3
"""
Docstring and Comment Extractor
Extracts documentation from code files in multiple languages
"""

import re
from typing import List, Dict, Optional
from github_api import GitHubAPIClient
import base64


class DocstringExtractor:
    """Extracts docstrings and comments from code files"""

    # Language patterns for docstrings and comments
    PATTERNS = {
        'python': {
            'docstring': r'"""(.+?)"""|\'\'\'(.+?)\'\'\'',
            'single_line': r'#\s*(.+)$',
            'multi_line': None
        },
        'javascript': {
            'docstring': r'/\*\*(.+?)\*/',
            'single_line': r'//\s*(.+)$',
            'multi_line': r'/\*(.+?)\*/'
        },
        'typescript': {
            'docstring': r'/\*\*(.+?)\*/',
            'single_line': r'//\s*(.+)$',
            'multi_line': r'/\*(.+?)\*/'
        },
        'java': {
            'docstring': r'/\*\*(.+?)\*/',
            'single_line': r'//\s*(.+)$',
            'multi_line': r'/\*(.+?)\*/'
        },
        'go': {
            'docstring': None,
            'single_line': r'//\s*(.+)$',
            'multi_line': r'/\*(.+?)\*/'
        },
        'rust': {
            'docstring': r'///\s*(.+)$',
            'single_line': r'//\s*(.+)$',
            'multi_line': r'/\*(.+?)\*/'
        },
        'ruby': {
            'docstring': None,
            'single_line': r'#\s*(.+)$',
            'multi_line': r'=begin(.+?)=end'
        },
        'php': {
            'docstring': r'/\*\*(.+?)\*/',
            'single_line': r'//\s*(.+)$|#\s*(.+)$',
            'multi_line': r'/\*(.+?)\*/'
        },
        'c': {
            'docstring': r'/\*\*(.+?)\*/',
            'single_line': r'//\s*(.+)$',
            'multi_line': r'/\*(.+?)\*/'
        },
        'cpp': {
            'docstring': r'/\*\*(.+?)\*/',
            'single_line': r'//\s*(.+)$',
            'multi_line': r'/\*(.+?)\*/'
        }
    }

    def __init__(self, client: Optional[GitHubAPIClient] = None):
        """
        Initialize docstring extractor

        Args:
            client: Optional GitHubAPIClient instance
        """
        self.client = client or GitHubAPIClient()

    def detect_language(self, filename: str) -> Optional[str]:
        """
        Detect programming language from filename

        Args:
            filename: Name of file

        Returns:
            Language name or None
        """
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.hpp': 'cpp',
            '.cc': 'cpp'
        }

        for ext, lang in ext_map.items():
            if filename.endswith(ext):
                return lang

        return None

    def extract_docstrings(self, content: str, language: str) -> List[Dict]:
        """
        Extract docstrings from code content

        Args:
            content: Code file content
            language: Programming language

        Returns:
            List of extracted docstrings with line numbers
        """
        docstrings = []

        if language not in self.PATTERNS:
            return docstrings

        patterns = self.PATTERNS[language]

        # Extract docstrings (if pattern exists)
        if patterns['docstring']:
            flags = re.MULTILINE | re.DOTALL
            matches = re.finditer(patterns['docstring'], content, flags)

            for match in matches:
                # Get matched group (handles different group indices)
                text = match.group(1) if match.group(1) else match.group(0)
                text = text.strip()

                # Calculate line number
                line_num = content[:match.start()].count('\n') + 1

                if text:
                    docstrings.append({
                        'type': 'docstring',
                        'line': line_num,
                        'text': text,
                        'language': language
                    })

        return docstrings

    def extract_comments(self, content: str, language: str,
                        include_single: bool = True,
                        include_multi: bool = True) -> List[Dict]:
        """
        Extract comments from code content

        Args:
            content: Code file content
            language: Programming language
            include_single: Include single-line comments
            include_multi: Include multi-line comments

        Returns:
            List of extracted comments with line numbers
        """
        comments = []

        if language not in self.PATTERNS:
            return comments

        patterns = self.PATTERNS[language]

        # Extract single-line comments
        if include_single and patterns['single_line']:
            matches = re.finditer(patterns['single_line'], content, re.MULTILINE)

            for match in matches:
                text = match.group(1).strip()
                line_num = content[:match.start()].count('\n') + 1

                if text and not text.startswith(('TODO', 'FIXME', 'HACK', 'XXX')):
                    comments.append({
                        'type': 'single_line',
                        'line': line_num,
                        'text': text,
                        'language': language
                    })

        # Extract multi-line comments (excluding docstrings)
        if include_multi and patterns['multi_line']:
            flags = re.MULTILINE | re.DOTALL
            matches = re.finditer(patterns['multi_line'], content, flags)

            for match in matches:
                # Skip if it's a docstring (starts with **)
                if patterns['docstring'] and match.group(0).startswith('/**'):
                    continue

                text = match.group(1).strip()
                line_num = content[:match.start()].count('\n') + 1

                if text:
                    comments.append({
                        'type': 'multi_line',
                        'line': line_num,
                        'text': text,
                        'language': language
                    })

        return comments

    def extract_all(self, content: str, language: str) -> Dict:
        """
        Extract both docstrings and comments

        Args:
            content: Code file content
            language: Programming language

        Returns:
            Dictionary with docstrings and comments
        """
        return {
            'docstrings': self.extract_docstrings(content, language),
            'comments': self.extract_comments(content, language),
            'language': language
        }

    def extract_from_file(self, owner: str, repo: str, path: str,
                         branch: str = "main") -> Dict:
        """
        Extract docstrings and comments from a GitHub file

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            branch: Branch name

        Returns:
            Dictionary with extracted documentation
        """
        # Get file content
        file_data = self.client.get_file_content(owner, repo, path, branch)
        content_base64 = file_data.get('content', '')
        content = base64.b64decode(content_base64).decode('utf-8', errors='ignore')

        # Detect language
        language = self.detect_language(path)

        if not language:
            return {
                'path': path,
                'language': None,
                'error': 'Language not supported'
            }

        # Extract documentation
        result = self.extract_all(content, language)
        result['path'] = path
        result['size'] = file_data.get('size', 0)

        return result

    def extract_from_repo(self, owner: str, repo: str,
                         extensions: Optional[List[str]] = None,
                         max_files: int = 50,
                         branch: str = "main") -> Dict[str, Dict]:
        """
        Extract documentation from all code files in a repository

        Args:
            owner: Repository owner
            repo: Repository name
            extensions: File extensions to process (None = all supported)
            max_files: Maximum number of files to process
            branch: Branch name

        Returns:
            Dictionary mapping file paths to extracted documentation
        """
        results = {}

        try:
            # Get all files
            files = self.client.list_files(owner, repo, branch, extensions)

            # Limit number of files
            files = files[:max_files]

            print(f"Processing {len(files)} files from {owner}/{repo}...")

            for i, file_info in enumerate(files):
                path = file_info['path']
                language = self.detect_language(path)

                if not language:
                    continue

                try:
                    result = self.extract_from_file(owner, repo, path, branch)
                    total_docs = len(result.get('docstrings', [])) + len(result.get('comments', []))

                    if total_docs > 0:
                        results[path] = result
                        print(f"  [{i+1}/{len(files)}] ✓ {path}: {total_docs} docs")
                    else:
                        print(f"  [{i+1}/{len(files)}] - {path}: no docs")

                except Exception as e:
                    print(f"  [{i+1}/{len(files)}] ✗ {path}: {e}")

        except Exception as e:
            print(f"Error scanning repository: {e}")

        return results

    def summarize_docs(self, docs: Dict[str, Dict]) -> Dict:
        """
        Create summary statistics for extracted documentation

        Args:
            docs: Dictionary of extracted documentation

        Returns:
            Summary statistics
        """
        total_files = len(docs)
        total_docstrings = sum(len(d.get('docstrings', [])) for d in docs.values())
        total_comments = sum(len(d.get('comments', [])) for d in docs.values())

        languages = {}
        for data in docs.values():
            lang = data.get('language', 'unknown')
            languages[lang] = languages.get(lang, 0) + 1

        return {
            'total_files': total_files,
            'total_docstrings': total_docstrings,
            'total_comments': total_comments,
            'total_documentation': total_docstrings + total_comments,
            'languages': languages,
            'avg_docs_per_file': (total_docstrings + total_comments) / total_files if total_files > 0 else 0
        }


# Test function
def test_extractor():
    """Test the docstring extractor"""
    print("Testing Docstring Extractor\n")

    extractor = DocstringExtractor()

    # Test with Python code
    python_code = '''
"""
Main module docstring
This describes the module
"""

def hello(name):
    """
    Say hello to someone

    Args:
        name: Person's name

    Returns:
        Greeting string
    """
    # This is a comment
    return f"Hello, {name}!"

class MyClass:
    """A sample class"""

    def method(self):
        # Another comment
        pass
'''

    print("Test 1: Python code extraction")
    result = extractor.extract_all(python_code, 'python')
    print(f"  Docstrings: {len(result['docstrings'])}")
    print(f"  Comments: {len(result['comments'])}")

    for doc in result['docstrings']:
        print(f"    Line {doc['line']}: {doc['text'][:50]}...")

    # Test with JavaScript
    js_code = '''
/**
 * Main function
 * Does something cool
 */
function main() {
    // Single line comment
    console.log("Hello");

    /* Multi-line
       comment here */
    return true;
}
'''

    print("\nTest 2: JavaScript code extraction")
    result = extractor.extract_all(js_code, 'javascript')
    print(f"  Docstrings: {len(result['docstrings'])}")
    print(f"  Comments: {len(result['comments'])}")

    # Test with GitHub repository
    print("\nTest 3: GitHub repository extraction")
    try:
        docs = extractor.extract_from_repo(
            'anthropics',
            'anthropic-sdk-python',
            extensions=['.py'],
            max_files=10
        )

        summary = extractor.summarize_docs(docs)
        print(f"\n  Summary:")
        print(f"    Files processed: {summary['total_files']}")
        print(f"    Docstrings: {summary['total_docstrings']}")
        print(f"    Comments: {summary['total_comments']}")
        print(f"    Avg per file: {summary['avg_docs_per_file']:.1f}")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_extractor()
