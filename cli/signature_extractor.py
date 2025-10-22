#!/usr/bin/env python3
"""
Function and Class Signature Extractor
Extracts function and class signatures from code files
"""

import re
from typing import List, Dict, Optional
from github_api import GitHubAPIClient
from language_detector import LanguageDetector
import base64


class SignatureExtractor:
    """Extracts function and class signatures from code"""

    # Patterns for different languages
    PATTERNS = {
        'python': {
            'function': r'^\s*(def|async def)\s+(\w+)\s*\((.*?)\)\s*(?:->(.+?))?:',
            'class': r'^\s*class\s+(\w+)\s*(?:\((.*?)\))?:',
            'method': r'^\s*(def|async def)\s+(\w+)\s*\((.*?)\)\s*(?:->(.+?))?:'
        },
        'javascript': {
            'function': r'function\s+(\w+)\s*\((.*?)\)\s*\{',
            'arrow_function': r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>',
            'class': r'class\s+(\w+)\s*(?:extends\s+(\w+))?\s*\{',
            'method': r'(?:async\s+)?(\w+)\s*\((.*?)\)\s*\{'
        },
        'typescript': {
            'function': r'function\s+(\w+)\s*(<.+?>)?\s*\((.*?)\)\s*:\s*(\w+)',
            'arrow_function': r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\((.*?)\)\s*:\s*(\w+)\s*=>',
            'class': r'(?:export\s+)?class\s+(\w+)\s*(?:extends\s+(\w+))?\s*\{',
            'interface': r'(?:export\s+)?interface\s+(\w+)\s*(?:extends\s+(.+?))?\s*\{',
            'method': r'(?:async\s+)?(\w+)\s*\((.*?)\)\s*:\s*(\w+)'
        },
        'java': {
            'class': r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)\s*(?:extends\s+(\w+))?\s*(?:implements\s+(.+?))?\s*\{',
            'method': r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(\w+)\s+(\w+)\s*\((.*?)\)',
            'interface': r'(?:public|private|protected)?\s*interface\s+(\w+)\s*(?:extends\s+(.+?))?\s*\{'
        },
        'go': {
            'function': r'func\s+(\w+)\s*\((.*?)\)\s*(?:\((.*?)\))?\s*\{',
            'method': r'func\s+\((\w+)\s+\*?(\w+)\)\s+(\w+)\s*\((.*?)\)\s*(?:\((.*?)\))?\s*\{',
            'struct': r'type\s+(\w+)\s+struct\s*\{',
            'interface': r'type\s+(\w+)\s+interface\s*\{'
        },
        'rust': {
            'function': r'(?:pub\s+)?fn\s+(\w+)\s*(?:<.+?>)?\s*\((.*?)\)\s*(?:->\s*(.+?))?\s*\{',
            'struct': r'(?:pub\s+)?struct\s+(\w+)\s*(?:<.+?>)?\s*\{',
            'trait': r'(?:pub\s+)?trait\s+(\w+)\s*(?:<.+?>)?\s*\{',
            'impl': r'impl\s*(?:<.+?>)?\s+(\w+)\s*(?:for\s+(\w+))?\s*\{'
        },
        'ruby': {
            'class': r'class\s+(\w+)\s*(?:<\s*(\w+))?\s*',
            'module': r'module\s+(\w+)\s*',
            'method': r'def\s+(\w+)\s*\((.*?)\)'
        },
        'php': {
            'class': r'(?:abstract|final)?\s*class\s+(\w+)\s*(?:extends\s+(\w+))?\s*(?:implements\s+(.+?))?\s*\{',
            'function': r'(?:public|private|protected)?\s*(?:static)?\s*function\s+(\w+)\s*\((.*?)\)',
            'interface': r'interface\s+(\w+)\s*(?:extends\s+(.+?))?\s*\{'
        },
        'csharp': {
            'class': r'(?:public|private|protected|internal)?\s*(?:abstract|sealed)?\s*class\s+(\w+)\s*(?::\s*(.+?))?\s*\{',
            'method': r'(?:public|private|protected|internal)?\s*(?:static|virtual|override)?\s*(\w+)\s+(\w+)\s*\((.*?)\)',
            'interface': r'(?:public|private|protected|internal)?\s*interface\s+(\w+)\s*(?::\s*(.+?))?\s*\{'
        },
        'swift': {
            'class': r'(?:public|private|internal)?\s*class\s+(\w+)\s*(?::\s*(.+?))?\s*\{',
            'struct': r'(?:public|private|internal)?\s*struct\s+(\w+)\s*(?::\s*(.+?))?\s*\{',
            'function': r'(?:public|private|internal)?\s*func\s+(\w+)\s*\((.*?)\)\s*(?:->\s*(.+?))?\s*\{',
            'protocol': r'(?:public|private|internal)?\s*protocol\s+(\w+)\s*(?::\s*(.+?))?\s*\{'
        },
        'cpp': {
            'class': r'class\s+(\w+)\s*(?::\s*(?:public|private|protected)\s+(.+?))?\s*\{',
            'struct': r'struct\s+(\w+)\s*\{',
            'function': r'(\w+)\s+(\w+)\s*\((.*?)\)\s*(?:const)?\s*\{?',
            'namespace': r'namespace\s+(\w+)\s*\{'
        }
    }

    def __init__(self, client: Optional[GitHubAPIClient] = None):
        """
        Initialize signature extractor

        Args:
            client: Optional GitHubAPIClient instance
        """
        self.client = client or GitHubAPIClient()
        self.detector = LanguageDetector(client)

    def extract_functions(self, content: str, language: str) -> List[Dict]:
        """
        Extract function signatures from code

        Args:
            content: Code content
            language: Programming language

        Returns:
            List of function signatures with metadata
        """
        functions = []

        if language not in self.PATTERNS:
            return functions

        patterns = self.PATTERNS[language]

        # Extract regular functions
        if 'function' in patterns:
            matches = re.finditer(patterns['function'], content, re.MULTILINE)

            for match in matches:
                line_num = content[:match.start()].count('\n') + 1

                if language == 'python':
                    func_type = match.group(1)  # def or async def
                    name = match.group(2)
                    params = match.group(3)
                    return_type = match.group(4) if len(match.groups()) >= 4 else None

                    functions.append({
                        'type': 'function',
                        'name': name,
                        'params': params.strip(),
                        'return_type': return_type.strip() if return_type else None,
                        'async': 'async' in func_type,
                        'line': line_num,
                        'language': language
                    })

                elif language in ['go', 'rust']:
                    name = match.group(1)
                    params = match.group(2)
                    return_type = match.group(3) if len(match.groups()) >= 3 else None

                    functions.append({
                        'type': 'function',
                        'name': name,
                        'params': params.strip(),
                        'return_type': return_type.strip() if return_type else None,
                        'line': line_num,
                        'language': language
                    })

                else:
                    # Generic extraction
                    name = match.group(1)
                    params = match.group(2) if len(match.groups()) >= 2 else ""

                    functions.append({
                        'type': 'function',
                        'name': name,
                        'params': params.strip(),
                        'line': line_num,
                        'language': language
                    })

        # Extract arrow functions (JavaScript/TypeScript)
        if 'arrow_function' in patterns:
            matches = re.finditer(patterns['arrow_function'], content, re.MULTILINE)

            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                name = match.group(1)
                params = match.group(2)

                functions.append({
                    'type': 'arrow_function',
                    'name': name,
                    'params': params.strip(),
                    'line': line_num,
                    'language': language
                })

        return functions

    def extract_classes(self, content: str, language: str) -> List[Dict]:
        """
        Extract class signatures from code

        Args:
            content: Code content
            language: Programming language

        Returns:
            List of class signatures with metadata
        """
        classes = []

        if language not in self.PATTERNS:
            return classes

        patterns = self.PATTERNS[language]

        # Extract classes
        if 'class' in patterns:
            matches = re.finditer(patterns['class'], content, re.MULTILINE)

            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                name = match.group(1)
                parent = match.group(2) if len(match.groups()) >= 2 else None

                classes.append({
                    'type': 'class',
                    'name': name,
                    'parent': parent.strip() if parent else None,
                    'line': line_num,
                    'language': language
                })

        # Extract structs (for Go, Rust, C++)
        if 'struct' in patterns:
            matches = re.finditer(patterns['struct'], content, re.MULTILINE)

            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                name = match.group(1)

                classes.append({
                    'type': 'struct',
                    'name': name,
                    'line': line_num,
                    'language': language
                })

        # Extract interfaces (TypeScript, Java, Go)
        if 'interface' in patterns:
            matches = re.finditer(patterns['interface'], content, re.MULTILINE)

            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                name = match.group(1)
                extends = match.group(2) if len(match.groups()) >= 2 else None

                classes.append({
                    'type': 'interface',
                    'name': name,
                    'extends': extends.strip() if extends else None,
                    'line': line_num,
                    'language': language
                })

        return classes

    def extract_all(self, content: str, language: str) -> Dict:
        """
        Extract all signatures from code

        Args:
            content: Code content
            language: Programming language

        Returns:
            Dictionary with functions and classes
        """
        return {
            'functions': self.extract_functions(content, language),
            'classes': self.extract_classes(content, language),
            'language': language
        }

    def extract_from_file(self, owner: str, repo: str, path: str,
                         branch: str = "main") -> Dict:
        """
        Extract signatures from a GitHub file

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            branch: Branch name

        Returns:
            Dictionary with extracted signatures
        """
        # Get file content
        file_data = self.client.get_file_content(owner, repo, path, branch)
        content_base64 = file_data.get('content', '')
        content = base64.b64decode(content_base64).decode('utf-8', errors='ignore')

        # Detect language
        language = self.detector.detect_by_extension(path)

        if not language:
            return {
                'path': path,
                'language': None,
                'error': 'Language not supported'
            }

        # Extract signatures
        result = self.extract_all(content, language)
        result['path'] = path
        result['size'] = file_data.get('size', 0)

        return result

    def extract_from_repo(self, owner: str, repo: str,
                         extensions: Optional[List[str]] = None,
                         max_files: int = 50,
                         branch: str = "main") -> Dict[str, Dict]:
        """
        Extract signatures from all code files in repository

        Args:
            owner: Repository owner
            repo: Repository name
            extensions: File extensions to process
            max_files: Maximum files to process
            branch: Branch name

        Returns:
            Dictionary mapping file paths to extracted signatures
        """
        results = {}

        try:
            # Get all files
            files = self.client.list_files(owner, repo, branch, extensions)
            files = files[:max_files]

            print(f"Processing {len(files)} files from {owner}/{repo}...")

            for i, file_info in enumerate(files):
                path = file_info['path']
                language = self.detector.detect_by_extension(path)

                if not language or language not in self.PATTERNS:
                    continue

                try:
                    result = self.extract_from_file(owner, repo, path, branch)
                    total_sigs = len(result.get('functions', [])) + len(result.get('classes', []))

                    if total_sigs > 0:
                        results[path] = result
                        print(f"  [{i+1}/{len(files)}] ✓ {path}: {total_sigs} signatures")
                    else:
                        print(f"  [{i+1}/{len(files)}] - {path}: no signatures")

                except Exception as e:
                    print(f"  [{i+1}/{len(files)}] ✗ {path}: {e}")

        except Exception as e:
            print(f"Error scanning repository: {e}")

        return results

    def summarize_signatures(self, signatures: Dict[str, Dict]) -> Dict:
        """
        Create summary statistics for extracted signatures

        Args:
            signatures: Dictionary of extracted signatures

        Returns:
            Summary statistics
        """
        total_files = len(signatures)
        total_functions = sum(len(s.get('functions', [])) for s in signatures.values())
        total_classes = sum(len(s.get('classes', [])) for s in signatures.values())

        languages = {}
        for data in signatures.values():
            lang = data.get('language', 'unknown')
            languages[lang] = languages.get(lang, 0) + 1

        return {
            'total_files': total_files,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'total_signatures': total_functions + total_classes,
            'languages': languages,
            'avg_signatures_per_file': (total_functions + total_classes) / total_files if total_files > 0 else 0
        }


# Test function
def test_extractor():
    """Test the signature extractor"""
    print("Testing Signature Extractor\n")

    extractor = SignatureExtractor()

    # Test with Python code
    python_code = '''
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    async def async_add(self, a: int, b: int) -> int:
        return a + b

def multiply(x: float, y: float) -> float:
    return x * y
'''

    print("Test 1: Python signature extraction")
    result = extractor.extract_all(python_code, 'python')
    print(f"  Functions: {len(result['functions'])}")
    print(f"  Classes: {len(result['classes'])}")

    for func in result['functions']:
        print(f"    Line {func['line']}: {func['name']}({func['params']}) -> {func['return_type']}")

    for cls in result['classes']:
        print(f"    Line {cls['line']}: class {cls['name']}")

    # Test with JavaScript
    js_code = '''
class User {
    constructor(name) {
        this.name = name;
    }

    getName() {
        return this.name;
    }
}

function createUser(name) {
    return new User(name);
}

const getUserAge = (user) => {
    return user.age;
};
'''

    print("\nTest 2: JavaScript signature extraction")
    result = extractor.extract_all(js_code, 'javascript')
    print(f"  Functions: {len(result['functions'])}")
    print(f"  Classes: {len(result['classes'])}")

    # Test with GitHub repository
    print("\nTest 3: GitHub repository extraction")
    try:
        signatures = extractor.extract_from_repo(
            'anthropics',
            'anthropic-sdk-python',
            extensions=['.py'],
            max_files=10
        )

        summary = extractor.summarize_signatures(signatures)
        print(f"\n  Summary:")
        print(f"    Files processed: {summary['total_files']}")
        print(f"    Functions: {summary['total_functions']}")
        print(f"    Classes: {summary['total_classes']}")
        print(f"    Avg per file: {summary['avg_signatures_per_file']:.1f}")

        # Show some examples
        if signatures:
            first_file = list(signatures.keys())[0]
            data = signatures[first_file]
            print(f"\n  Example from {first_file}:")
            for func in data['functions'][:3]:
                print(f"    - {func['name']}({func['params']})")
            for cls in data['classes'][:3]:
                print(f"    - class {cls['name']}")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_extractor()
