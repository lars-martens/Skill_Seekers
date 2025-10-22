#!/usr/bin/env python3
"""
README Extractor for GitHub Repositories
Extracts and decodes README files from GitHub repos
"""

import base64
from typing import Optional, Dict
from github_api import GitHubAPIClient


class READMEExtractor:
    """Extracts README files from GitHub repositories"""

    def __init__(self, client: Optional[GitHubAPIClient] = None):
        """
        Initialize README extractor

        Args:
            client: Optional GitHubAPIClient instance (creates new if not provided)
        """
        self.client = client or GitHubAPIClient()

    def extract_readme(self, owner: str, repo: str) -> Dict[str, str]:
        """
        Extract README from repository

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with README metadata and decoded content
        """
        try:
            readme_data = self.client.get_readme(owner, repo)

            # Decode base64 content
            content_base64 = readme_data.get('content', '')
            content = base64.b64decode(content_base64).decode('utf-8')

            return {
                'name': readme_data.get('name', 'README.md'),
                'path': readme_data.get('path', ''),
                'size': readme_data.get('size', 0),
                'encoding': readme_data.get('encoding', 'base64'),
                'content': content,
                'html_url': readme_data.get('html_url', ''),
                'download_url': readme_data.get('download_url', '')
            }

        except Exception as e:
            raise Exception(f"Failed to extract README: {e}")

    def extract_from_url(self, url: str) -> Dict[str, str]:
        """
        Extract README from GitHub URL

        Args:
            url: GitHub repository URL

        Returns:
            Dictionary with README metadata and content
        """
        owner, repo = self.client.parse_github_url(url)
        return self.extract_readme(owner, repo)

    def save_readme(self, owner: str, repo: str, output_path: str) -> None:
        """
        Extract and save README to file

        Args:
            owner: Repository owner
            repo: Repository name
            output_path: Path to save README file
        """
        readme = self.extract_readme(owner, repo)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(readme['content'])

        print(f"✓ Saved README to: {output_path}")
        print(f"  Size: {readme['size']} bytes")

    def extract_all_readmes(self, owner: str, repo: str, branch: str = "main") -> Dict[str, Dict]:
        """
        Extract all README files in repository (including subdirectories)

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: "main")

        Returns:
            Dictionary mapping paths to README content
        """
        readmes = {}

        try:
            # Get all files
            tree = self.client.get_repo_tree(owner, repo, branch, recursive=True)

            # Find all README files
            readme_files = []
            for item in tree.get('tree', []):
                if item['type'] == 'blob':
                    path = item['path'].lower()
                    filename = path.split('/')[-1]
                    # Match various README formats
                    if filename in ['readme.md', 'readme.txt', 'readme.rst', 'readme']:
                        readme_files.append(item['path'])

            # Extract each README
            for readme_path in readme_files:
                try:
                    file_data = self.client.get_file_content(owner, repo, readme_path, branch)
                    content_base64 = file_data.get('content', '')
                    content = base64.b64decode(content_base64).decode('utf-8')

                    readmes[readme_path] = {
                        'name': file_data.get('name', ''),
                        'path': readme_path,
                        'size': file_data.get('size', 0),
                        'content': content,
                        'html_url': file_data.get('html_url', '')
                    }
                    print(f"✓ Extracted: {readme_path}")

                except Exception as e:
                    print(f"✗ Failed to extract {readme_path}: {e}")

        except Exception as e:
            print(f"Error scanning repository: {e}")

        return readmes

    def get_readme_sections(self, content: str) -> Dict[str, str]:
        """
        Parse README into sections based on markdown headers

        Args:
            content: README markdown content

        Returns:
            Dictionary mapping section titles to content
        """
        sections = {}
        current_section = "Introduction"
        current_content = []

        lines = content.split('\n')

        for line in lines:
            # Check for markdown headers
            if line.startswith('# '):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                # Start new section
                current_section = line[2:].strip()
                current_content = []
            elif line.startswith('## '):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                # Start new section
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def summarize_readme(self, owner: str, repo: str) -> Dict[str, any]:
        """
        Extract and summarize README

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with README summary
        """
        readme = self.extract_readme(owner, repo)
        sections = self.get_readme_sections(readme['content'])

        # Count elements
        lines = readme['content'].split('\n')
        code_blocks = readme['content'].count('```')
        links = readme['content'].count('[')

        return {
            'name': readme['name'],
            'size': readme['size'],
            'lines': len(lines),
            'code_blocks': code_blocks // 2,  # Each block has ``` twice
            'links': links,
            'sections': list(sections.keys()),
            'section_count': len(sections)
        }


# Test function
def test_extractor():
    """Test the README extractor"""
    print("Testing README Extractor\n")

    extractor = READMEExtractor()

    # Test with anthropic SDK
    test_url = "https://github.com/anthropics/anthropic-sdk-python"

    try:
        print(f"Testing with: {test_url}\n")

        # Extract README
        readme = extractor.extract_from_url(test_url)
        print(f"✓ Extracted README: {readme['name']}")
        print(f"  Size: {readme['size']} bytes")
        print(f"  Lines: {len(readme['content'].split(chr(10)))}")

        # Get sections
        sections = extractor.get_readme_sections(readme['content'])
        print(f"\n✓ Parsed {len(sections)} sections:")
        for section in list(sections.keys())[:5]:  # Show first 5
            print(f"  - {section}")
        if len(sections) > 5:
            print(f"  ... and {len(sections) - 5} more")

        # Summarize
        owner, repo = extractor.client.parse_github_url(test_url)
        summary = extractor.summarize_readme(owner, repo)
        print(f"\n✓ README Summary:")
        print(f"  Lines: {summary['lines']}")
        print(f"  Code blocks: {summary['code_blocks']}")
        print(f"  Links: {summary['links']}")
        print(f"  Sections: {summary['section_count']}")

        # Show first 500 chars
        print(f"\n✓ Content preview:")
        print("-" * 60)
        print(readme['content'][:500])
        print("...")
        print("-" * 60)

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_extractor()
