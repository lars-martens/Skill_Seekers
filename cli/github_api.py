#!/usr/bin/env python3
"""
GitHub API Client for Skill Seeker
Fetches repository structure and content from GitHub
"""

import requests
import time
from typing import Dict, List, Optional, Any


class GitHubAPIClient:
    """Client for interacting with GitHub API v3"""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API client

        Args:
            token: Optional GitHub personal access token for higher rate limits
        """
        self.base_url = "https://api.github.com"
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Skill-Seeker/1.0"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"

        self.rate_limit_remaining = None
        self.rate_limit_reset = None

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the GitHub API

        Args:
            endpoint: API endpoint (e.g., "/repos/owner/repo")
            params: Optional query parameters

        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)

        # Update rate limit info
        self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))

        # Check rate limit
        if response.status_code == 403 and self.rate_limit_remaining == 0:
            reset_time = time.time() - self.rate_limit_reset
            raise Exception(f"GitHub API rate limit exceeded. Resets in {reset_time} seconds.")

        response.raise_for_status()
        return response.json()

    def get_repo_info(self, owner: str, repo: str) -> Dict:
        """
        Get repository information

        Args:
            owner: Repository owner (username or organization)
            repo: Repository name

        Returns:
            Repository metadata
        """
        return self._make_request(f"/repos/{owner}/{repo}")

    def get_repo_tree(self, owner: str, repo: str, branch: str = "main", recursive: bool = True) -> Dict:
        """
        Get repository file tree

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: "main")
            recursive: Get full tree recursively (default: True)

        Returns:
            Tree structure with all files and directories
        """
        # First get the branch to find the tree SHA
        try:
            branch_info = self._make_request(f"/repos/{owner}/{repo}/branches/{branch}")
            tree_sha = branch_info['commit']['sha']
        except requests.exceptions.HTTPError:
            # Try 'master' if 'main' fails
            if branch == "main":
                branch = "master"
                branch_info = self._make_request(f"/repos/{owner}/{repo}/branches/{branch}")
                tree_sha = branch_info['commit']['sha']
            else:
                raise

        # Get the tree
        params = {}
        if recursive:
            params['recursive'] = '1'

        return self._make_request(f"/repos/{owner}/{repo}/git/trees/{tree_sha}", params)

    def get_file_content(self, owner: str, repo: str, path: str, branch: str = "main") -> Dict:
        """
        Get content of a specific file

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            branch: Branch name (default: "main")

        Returns:
            File metadata and content (base64 encoded)
        """
        params = {"ref": branch}
        return self._make_request(f"/repos/{owner}/{repo}/contents/{path}", params)

    def get_readme(self, owner: str, repo: str) -> Dict:
        """
        Get repository README

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            README content and metadata
        """
        return self._make_request(f"/repos/{owner}/{repo}/readme")

    def parse_github_url(self, url: str) -> tuple:
        """
        Parse GitHub URL to extract owner and repo

        Args:
            url: GitHub URL (e.g., "https://github.com/owner/repo")

        Returns:
            Tuple of (owner, repo)

        Example:
            >>> client.parse_github_url("https://github.com/anthropics/claude-code")
            ('anthropics', 'claude-code')
        """
        # Remove trailing slash
        url = url.rstrip('/')

        # Handle different URL formats
        if url.startswith("https://github.com/"):
            parts = url.replace("https://github.com/", "").split('/')
        elif url.startswith("http://github.com/"):
            parts = url.replace("http://github.com/", "").split('/')
        elif url.startswith("github.com/"):
            parts = url.replace("github.com/", "").split('/')
        else:
            # Assume format is "owner/repo"
            parts = url.split('/')

        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")

        owner = parts[0]
        repo = parts[1]

        return owner, repo

    def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """
        Get programming languages used in repository

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary mapping language names to bytes of code
        """
        return self._make_request(f"/repos/{owner}/{repo}/languages")

    def list_files(self, owner: str, repo: str, branch: str = "main",
                   extensions: Optional[List[str]] = None) -> List[Dict]:
        """
        List all files in repository, optionally filtered by extension

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: "main")
            extensions: Optional list of file extensions to filter (e.g., ['.py', '.js'])

        Returns:
            List of file dictionaries with path, size, and type information
        """
        tree = self.get_repo_tree(owner, repo, branch, recursive=True)
        files = []

        for item in tree.get('tree', []):
            if item['type'] == 'blob':  # It's a file
                # Filter by extension if specified
                if extensions:
                    if any(item['path'].endswith(ext) for ext in extensions):
                        files.append(item)
                else:
                    files.append(item)

        return files

    def get_rate_limit_status(self) -> Dict:
        """
        Get current rate limit status

        Returns:
            Rate limit information
        """
        return self._make_request("/rate_limit")


# Quick test function
def test_client():
    """Test the GitHub API client"""
    client = GitHubAPIClient()

    # Test with a public repository
    test_url = "https://github.com/anthropics/anthropic-sdk-python"

    print(f"Testing GitHub API client with: {test_url}")

    try:
        # Parse URL
        owner, repo = client.parse_github_url(test_url)
        print(f"✓ Parsed URL: owner={owner}, repo={repo}")

        # Get repo info
        info = client.get_repo_info(owner, repo)
        print(f"✓ Repository: {info['full_name']}")
        print(f"  Description: {info.get('description', 'N/A')}")
        print(f"  Stars: {info['stargazers_count']}")

        # Get languages
        languages = client.get_languages(owner, repo)
        print(f"✓ Languages: {', '.join(languages.keys())}")

        # Get README
        readme = client.get_readme(owner, repo)
        print(f"✓ README: {readme['name']} ({readme['size']} bytes)")

        # List Python files
        py_files = client.list_files(owner, repo, extensions=['.py'])
        print(f"✓ Python files: {len(py_files)} found")
        if py_files:
            print(f"  Example: {py_files[0]['path']}")

        # Check rate limit
        rate_limit = client.get_rate_limit_status()
        core_limit = rate_limit['resources']['core']
        print(f"✓ Rate limit: {core_limit['remaining']}/{core_limit['limit']} remaining")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

    return True


if __name__ == "__main__":
    test_client()
