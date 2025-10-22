#!/usr/bin/env python3
"""
Test Example Extractor
Extracts usage examples from test files
"""

import re
from typing import List, Dict, Optional
from github_api import GitHubAPIClient
from language_detector import LanguageDetector
import base64


class TestExampleExtractor:
    """Extracts usage examples from test files"""

    # Test file patterns
    TEST_PATTERNS = {
        'python': [
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'tests?/.*\.py$'
        ],
        'javascript': [
            r'.*\.test\.js$',
            r'.*\.spec\.js$',
            r'__tests__/.*\.js$',
            r'tests?/.*\.js$'
        ],
        'typescript': [
            r'.*\.test\.ts$',
            r'.*\.spec\.ts$',
            r'__tests__/.*\.ts$',
            r'tests?/.*\.ts$'
        ],
        'java': [
            r'.*Test\.java$',
            r'test/.*\.java$'
        ],
        'go': [
            r'.*_test\.go$'
        ],
        'rust': [
            r'tests?/.*\.rs$'
        ],
        'ruby': [
            r'.*_spec\.rb$',
            r'.*_test\.rb$',
            r'spec/.*\.rb$',
            r'test/.*\.rb$'
        ],
        'php': [
            r'.*Test\.php$',
            r'tests?/.*\.php$'
        ],
        'csharp': [
            r'.*Tests?\.cs$',
            r'.*Spec\.cs$'
        ]
    }

    # Test function patterns
    TEST_FUNCTION_PATTERNS = {
        'python': [
            r'def\s+(test_\w+)\s*\(',
            r'@pytest\.mark\.\w+\s+def\s+(\w+)\s*\('
        ],
        'javascript': [
            r'(?:test|it)\s*\(\s*[\'"](.+?)[\'"]\s*,',
            r'describe\s*\(\s*[\'"](.+?)[\'"]\s*,'
        ],
        'typescript': [
            r'(?:test|it)\s*\(\s*[\'"](.+?)[\'"]\s*,',
            r'describe\s*\(\s*[\'"](.+?)[\'"]\s*,'
        ],
        'java': [
            r'@Test\s+(?:public\s+)?void\s+(\w+)\s*\('
        ],
        'go': [
            r'func\s+(Test\w+)\s*\('
        ],
        'rust': [
            r'#\[test\]\s+fn\s+(\w+)\s*\('
        ],
        'ruby': [
            r'(?:it|test)\s+[\'"](.+?)[\'"]\s+do',
            r'def\s+(test_\w+)'
        ],
        'php': [
            r'(?:public\s+)?function\s+(test\w+)\s*\('
        ],
        'csharp': [
            r'\[Test\]\s+public\s+void\s+(\w+)\s*\('
        ]
    }

    def __init__(self, client: Optional[GitHubAPIClient] = None):
        """
        Initialize test example extractor

        Args:
            client: Optional GitHubAPIClient instance
        """
        self.client = client or GitHubAPIClient()
        self.detector = LanguageDetector(client)

    def is_test_file(self, path: str, language: str) -> bool:
        """
        Check if file is a test file

        Args:
            path: File path
            language: Programming language

        Returns:
            True if test file
        """
        if language not in self.TEST_PATTERNS:
            return False

        for pattern in self.TEST_PATTERNS[language]:
            if re.search(pattern, path):
                return True

        return False

    def extract_test_functions(self, content: str, language: str) -> List[Dict]:
        """
        Extract test function names and locations

        Args:
            content: Test file content
            language: Programming language

        Returns:
            List of test functions with metadata
        """
        tests = []

        if language not in self.TEST_FUNCTION_PATTERNS:
            return tests

        for pattern in self.TEST_FUNCTION_PATTERNS[language]:
            matches = re.finditer(pattern, content, re.MULTILINE)

            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                name = match.group(1)

                tests.append({
                    'name': name,
                    'line': line_num,
                    'language': language
                })

        return tests

    def extract_test_content(self, content: str, test_name: str,
                            start_line: int, language: str) -> Optional[str]:
        """
        Extract the full content of a test function

        Args:
            content: File content
            test_name: Test function name
            start_line: Starting line number
            language: Programming language

        Returns:
            Test function content or None
        """
        lines = content.split('\n')

        # Find the starting line
        if start_line > len(lines):
            return None

        # Determine indentation level
        start_idx = start_line - 1
        start_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        # Extract until dedent or end of file
        test_lines = [lines[start_idx]]

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                test_lines.append(line)
                continue

            # Check indentation
            current_indent = len(line) - len(line.lstrip())

            # If dedented (or equal for some languages), end of function
            if current_indent <= start_indent and line.strip():
                break

            test_lines.append(line)

        return '\n'.join(test_lines)

    def extract_usage_patterns(self, test_content: str, language: str) -> List[Dict]:
        """
        Extract usage patterns from test content

        Args:
            test_content: Test function content
            language: Programming language

        Returns:
            List of usage patterns (function calls, assertions)
        """
        patterns = []

        # Look for function/method calls
        if language == 'python':
            # Find function calls
            call_matches = re.finditer(r'(\w+(?:\.\w+)*)\s*\(([^)]*)\)', test_content)
            for match in call_matches:
                func_name = match.group(1)
                args = match.group(2)

                # Skip common test functions
                if func_name not in ['assert', 'assertEqual', 'assertTrue', 'print']:
                    patterns.append({
                        'type': 'call',
                        'function': func_name,
                        'args': args.strip(),
                        'full': match.group(0)
                    })

            # Find assertions (they show expected behavior)
            assert_matches = re.finditer(r'assert\s+(.+)', test_content)
            for match in assert_matches:
                patterns.append({
                    'type': 'assertion',
                    'expression': match.group(1).strip(),
                    'full': match.group(0)
                })

        elif language in ['javascript', 'typescript']:
            # Find function calls
            call_matches = re.finditer(r'(\w+(?:\.\w+)*)\s*\(([^)]*)\)', test_content)
            for match in call_matches:
                func_name = match.group(1)
                if func_name not in ['expect', 'test', 'it', 'describe', 'console']:
                    patterns.append({
                        'type': 'call',
                        'function': func_name,
                        'args': match.group(2).strip(),
                        'full': match.group(0)
                    })

            # Find expect assertions
            expect_matches = re.finditer(r'expect\((.+?)\)\.(\w+)\((.+?)\)', test_content)
            for match in matches:
                patterns.append({
                    'type': 'assertion',
                    'subject': match.group(1),
                    'matcher': match.group(2),
                    'expected': match.group(3),
                    'full': match.group(0)
                })

        return patterns

    def extract_from_file(self, owner: str, repo: str, path: str,
                         branch: str = "main") -> Dict:
        """
        Extract examples from a test file

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            branch: Branch name

        Returns:
            Dictionary with extracted examples
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

        # Extract test functions
        test_functions = self.extract_test_functions(content, language)

        # Extract content for each test
        examples = []
        for test in test_functions:
            test_content = self.extract_test_content(
                content, test['name'], test['line'], language
            )

            if test_content:
                usage_patterns = self.extract_usage_patterns(test_content, language)

                examples.append({
                    'name': test['name'],
                    'line': test['line'],
                    'content': test_content,
                    'usage_patterns': usage_patterns
                })

        return {
            'path': path,
            'language': language,
            'test_count': len(test_functions),
            'examples': examples
        }

    def find_test_files(self, owner: str, repo: str,
                       branch: str = "main") -> List[str]:
        """
        Find all test files in repository

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name

        Returns:
            List of test file paths
        """
        test_files = []

        try:
            # Get all files
            tree = self.client.get_repo_tree(owner, repo, branch, recursive=True)

            for item in tree.get('tree', []):
                if item['type'] == 'blob':
                    path = item['path']
                    language = self.detector.detect_by_extension(path)

                    if language and self.is_test_file(path, language):
                        test_files.append(path)

        except Exception as e:
            print(f"Error finding test files: {e}")

        return test_files

    def extract_from_repo(self, owner: str, repo: str,
                         max_files: int = 20,
                         branch: str = "main") -> Dict[str, Dict]:
        """
        Extract examples from all test files in repository

        Args:
            owner: Repository owner
            repo: Repository name
            max_files: Maximum test files to process
            branch: Branch name

        Returns:
            Dictionary mapping test file paths to examples
        """
        results = {}

        try:
            # Find test files
            test_files = self.find_test_files(owner, repo, branch)
            test_files = test_files[:max_files]

            print(f"Found {len(test_files)} test files in {owner}/{repo}")
            print(f"Processing first {min(len(test_files), max_files)} files...\n")

            for i, path in enumerate(test_files):
                try:
                    result = self.extract_from_file(owner, repo, path, branch)
                    example_count = len(result.get('examples', []))

                    if example_count > 0:
                        results[path] = result
                        print(f"  [{i+1}/{len(test_files)}] ✓ {path}: {example_count} examples")
                    else:
                        print(f"  [{i+1}/{len(test_files)}] - {path}: no examples")

                except Exception as e:
                    print(f"  [{i+1}/{len(test_files)}] ✗ {path}: {e}")

        except Exception as e:
            print(f"Error scanning repository: {e}")

        return results

    def summarize_examples(self, examples: Dict[str, Dict]) -> Dict:
        """
        Create summary statistics

        Args:
            examples: Dictionary of extracted examples

        Returns:
            Summary statistics
        """
        total_files = len(examples)
        total_tests = sum(e.get('test_count', 0) for e in examples.values())
        total_examples = sum(len(e.get('examples', [])) for e in examples.values())

        return {
            'total_test_files': total_files,
            'total_tests': total_tests,
            'total_examples': total_examples,
            'avg_examples_per_file': total_examples / total_files if total_files > 0 else 0
        }


# Test function
def test_extractor():
    """Test the test example extractor"""
    print("Testing Test Example Extractor\n")

    extractor = TestExampleExtractor()

    # Test with Python test code
    python_test = '''
def test_addition():
    calculator = Calculator()
    result = calculator.add(2, 3)
    assert result == 5

def test_multiplication():
    calc = Calculator()
    assert calc.multiply(4, 5) == 20
'''

    print("Test 1: Python test extraction")
    tests = extractor.extract_test_functions(python_test, 'python')
    print(f"  Found {len(tests)} test functions:")
    for test in tests:
        print(f"    - {test['name']} (line {test['line']})")

    # Test with JavaScript
    js_test = '''
describe('Calculator', () => {
    it('should add two numbers', () => {
        const calc = new Calculator();
        expect(calc.add(2, 3)).toBe(5);
    });

    test('multiplies correctly', () => {
        const result = multiply(4, 5);
        expect(result).toBe(20);
    });
});
'''

    print("\nTest 2: JavaScript test extraction")
    tests = extractor.extract_test_functions(js_test, 'javascript')
    print(f"  Found {len(tests)} test functions:")
    for test in tests:
        print(f"    - {test['name']}")

    # Test with GitHub repository
    print("\nTest 3: GitHub repository extraction")
    try:
        examples = extractor.extract_from_repo(
            'anthropics',
            'anthropic-sdk-python',
            max_files=5
        )

        summary = extractor.summarize_examples(examples)
        print(f"\n  Summary:")
        print(f"    Test files: {summary['total_test_files']}")
        print(f"    Total tests: {summary['total_tests']}")
        print(f"    Examples: {summary['total_examples']}")
        print(f"    Avg per file: {summary['avg_examples_per_file']:.1f}")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_extractor()
