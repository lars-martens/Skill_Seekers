#!/usr/bin/env python3
"""
GitHub Repository Scraper
Scrapes GitHub repositories and creates Claude skills
"""

import json
import os
import argparse
from typing import Dict, Optional
from github_api import GitHubAPIClient
from readme_extractor import READMEExtractor
from docstring_extractor import DocstringExtractor
from language_detector import LanguageDetector
from signature_extractor import SignatureExtractor
from test_example_extractor import TestExampleExtractor


class GitHubScraper:
    """Main scraper for GitHub repositories"""

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub scraper

        Args:
            github_token: Optional GitHub personal access token
        """
        self.client = GitHubAPIClient(github_token)
        self.readme_extractor = READMEExtractor(self.client)
        self.docstring_extractor = DocstringExtractor(self.client)
        self.language_detector = LanguageDetector(self.client)
        self.signature_extractor = SignatureExtractor(self.client)
        self.test_extractor = TestExampleExtractor(self.client)

    def scrape_repository(self, url: str, output_dir: str = "output",
                         max_files: int = 100,
                         include_tests: bool = True) -> Dict:
        """
        Scrape entire repository and extract documentation

        Args:
            url: GitHub repository URL
            output_dir: Output directory for skill
            max_files: Maximum files to process
            include_tests: Include test examples

        Returns:
            Dictionary with scraping results
        """
        print(f"\n{'='*70}")
        print(f"GitHub Repository Scraper")
        print(f"{'='*70}\n")

        # Parse URL
        owner, repo = self.client.parse_github_url(url)
        print(f"Repository: {owner}/{repo}")

        # Create output directory
        repo_output_dir = os.path.join(output_dir, f"{repo}_github")
        os.makedirs(repo_output_dir, exist_ok=True)

        results = {
            'repository': f"{owner}/{repo}",
            'url': url,
            'output_dir': repo_output_dir
        }

        # Step 1: Get repository info
        print(f"\n[1/7] Fetching repository information...")
        try:
            repo_info = self.client.get_repo_info(owner, repo)
            results['info'] = {
                'name': repo_info['name'],
                'description': repo_info.get('description', ''),
                'stars': repo_info['stargazers_count'],
                'language': repo_info.get('language', 'Unknown'),
                'topics': repo_info.get('topics', [])
            }
            print(f"  ✓ {repo_info['name']}")
            print(f"  ✓ Stars: {repo_info['stargazers_count']}")
            print(f"  ✓ Language: {repo_info.get('language', 'Unknown')}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results['info'] = {}

        # Step 2: Extract README
        print(f"\n[2/7] Extracting README...")
        try:
            readme = self.readme_extractor.extract_readme(owner, repo)
            results['readme'] = readme
            print(f"  ✓ {readme['name']} ({readme['size']} bytes)")

            # Save README
            readme_path = os.path.join(repo_output_dir, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme['content'])
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results['readme'] = None

        # Step 3: Detect languages
        print(f"\n[3/7] Analyzing languages...")
        try:
            languages = self.language_detector.detect_by_github(owner, repo)
            results['languages'] = languages
            print(f"  ✓ Found {len(languages)} languages:")
            for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    - {lang}: {bytes_count:,} bytes")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results['languages'] = {}

        # Step 4: Extract docstrings and comments
        print(f"\n[4/7] Extracting documentation...")
        try:
            docs = self.docstring_extractor.extract_from_repo(
                owner, repo,
                max_files=max_files
            )
            results['documentation'] = docs

            # Save documentation
            docs_path = os.path.join(repo_output_dir, 'documentation.json')
            with open(docs_path, 'w', encoding='utf-8') as f:
                json.dump(docs, f, indent=2)

            summary = self.docstring_extractor.summarize_docs(docs)
            print(f"  ✓ Files: {summary['total_files']}")
            print(f"  ✓ Docstrings: {summary['total_docstrings']}")
            print(f"  ✓ Comments: {summary['total_comments']}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results['documentation'] = {}

        # Step 5: Extract signatures
        print(f"\n[5/7] Extracting function/class signatures...")
        try:
            signatures = self.signature_extractor.extract_from_repo(
                owner, repo,
                max_files=max_files
            )
            results['signatures'] = signatures

            # Save signatures
            sigs_path = os.path.join(repo_output_dir, 'signatures.json')
            with open(sigs_path, 'w', encoding='utf-8') as f:
                json.dump(signatures, f, indent=2)

            summary = self.signature_extractor.summarize_signatures(signatures)
            print(f"  ✓ Files: {summary['total_files']}")
            print(f"  ✓ Functions: {summary['total_functions']}")
            print(f"  ✓ Classes: {summary['total_classes']}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results['signatures'] = {}

        # Step 6: Extract test examples
        if include_tests:
            print(f"\n[6/7] Extracting usage examples from tests...")
            try:
                examples = self.test_extractor.extract_from_repo(
                    owner, repo,
                    max_files=20
                )
                results['examples'] = examples

                # Save examples
                examples_path = os.path.join(repo_output_dir, 'examples.json')
                with open(examples_path, 'w', encoding='utf-8') as f:
                    json.dump(examples, f, indent=2)

                summary = self.test_extractor.summarize_examples(examples)
                print(f"  ✓ Test files: {summary['total_test_files']}")
                print(f"  ✓ Examples: {summary['total_examples']}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                results['examples'] = {}
        else:
            print(f"\n[6/7] Skipping test examples (disabled)")
            results['examples'] = {}

        # Step 7: Generate skill
        print(f"\n[7/7] Generating Claude skill...")
        try:
            self.generate_skill(results, repo_output_dir)
            print(f"  ✓ Skill generated successfully")
        except Exception as e:
            print(f"  ✗ Error: {e}")

        # Summary
        print(f"\n{'='*70}")
        print(f"Scraping Complete!")
        print(f"{'='*70}")
        print(f"Output directory: {repo_output_dir}")
        print(f"\nGenerated files:")
        print(f"  - README.md")
        print(f"  - SKILL.md")
        print(f"  - documentation.json")
        print(f"  - signatures.json")
        if include_tests:
            print(f"  - examples.json")
        print(f"\nNext steps:")
        print(f"  1. Review SKILL.md in {repo_output_dir}")
        print(f"  2. Package: python3 cli/package_skill.py {repo_output_dir}")
        print(f"{'='*70}\n")

        return results

    def generate_skill(self, data: Dict, output_dir: str) -> None:
        """
        Generate SKILL.md from scraped data

        Args:
            data: Scraped repository data
            output_dir: Output directory
        """
        repo_info = data.get('info', {})
        readme = data.get('readme', {})
        languages = data.get('languages', {})
        docs = data.get('documentation', {})
        signatures = data.get('signatures', {})
        examples = data.get('examples', {})

        # Build SKILL.md content
        lines = []

        # Header
        lines.append(f"# {repo_info.get('name', 'Repository')} Skill")
        lines.append("")
        lines.append(f"**Repository:** {data.get('repository', 'Unknown')}")
        lines.append(f"**Description:** {repo_info.get('description', 'No description')}")
        lines.append("")

        # When to use
        lines.append("## When to Use This Skill")
        lines.append("")
        lines.append(f"Use this skill when working with {repo_info.get('name', 'this repository')}.")
        if repo_info.get('description'):
            lines.append(f"This repository is for: {repo_info.get('description')}")
        lines.append("")

        # Languages
        if languages:
            lines.append("## Programming Languages")
            lines.append("")
            for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
                percentage = (bytes_count / sum(languages.values())) * 100
                lines.append(f"- **{lang}**: {percentage:.1f}%")
            lines.append("")

        # Key Components
        if signatures:
            lines.append("## Key Components")
            lines.append("")

            # Group by file
            files_with_sigs = sorted(signatures.items(), key=lambda x: len(x[1].get('functions', [])) + len(x[1].get('classes', [])), reverse=True)[:10]

            for path, sig_data in files_with_sigs:
                lines.append(f"### {path}")
                lines.append("")

                # Classes
                classes = sig_data.get('classes', [])
                if classes:
                    lines.append("**Classes:**")
                    for cls in classes[:5]:
                        lines.append(f"- `{cls['name']}` (line {cls['line']})")
                    lines.append("")

                # Functions
                functions = sig_data.get('functions', [])
                if functions:
                    lines.append("**Functions:**")
                    for func in functions[:10]:
                        params = func.get('params', '')
                        return_type = func.get('return_type', '')
                        if return_type:
                            lines.append(f"- `{func['name']}({params}) → {return_type}` (line {func['line']})")
                        else:
                            lines.append(f"- `{func['name']}({params})` (line {func['line']})")
                    lines.append("")

        # Usage Examples
        if examples:
            lines.append("## Usage Examples")
            lines.append("")
            lines.append("Examples extracted from test files:")
            lines.append("")

            for path, example_data in list(examples.items())[:5]:
                lines.append(f"### From {path}")
                lines.append("")

                for example in example_data.get('examples', [])[:3]:
                    lines.append(f"**{example['name']}:**")
                    lines.append("")
                    lines.append("```" + example_data.get('language', ''))
                    lines.append(example['content'][:500])  # Limit length
                    if len(example['content']) > 500:
                        lines.append("...")
                    lines.append("```")
                    lines.append("")

        # Documentation
        if docs:
            lines.append("## Code Documentation")
            lines.append("")

            doc_summary = self.docstring_extractor.summarize_docs(docs)
            lines.append(f"Total documentation: {doc_summary['total_documentation']} items")
            lines.append(f"- Docstrings: {doc_summary['total_docstrings']}")
            lines.append(f"- Comments: {doc_summary['total_comments']}")
            lines.append("")
            lines.append("See `documentation.json` for full details.")
            lines.append("")

        # Footer
        lines.append("## Additional Resources")
        lines.append("")
        if readme:
            lines.append(f"- [README]({readme.get('html_url', '#')})")
        lines.append(f"- [Repository]({data.get('url', '#')})")
        lines.append("")

        # Write SKILL.md
        skill_path = os.path.join(output_dir, 'SKILL.md')
        with open(skill_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Scrape GitHub repositories and create Claude skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape a repository
  python3 github_scraper.py https://github.com/anthropics/anthropic-sdk-python

  # Specify output directory
  python3 github_scraper.py https://github.com/owner/repo --output my_skills

  # Process more files
  python3 github_scraper.py https://github.com/owner/repo --max-files 200

  # Use GitHub token for higher rate limits
  export GITHUB_TOKEN=ghp_your_token_here
  python3 github_scraper.py https://github.com/owner/repo --token $GITHUB_TOKEN
        """
    )

    parser.add_argument('url', help='GitHub repository URL')
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--max-files', '-m', type=int, default=100,
                       help='Maximum files to process (default: 100)')
    parser.add_argument('--no-tests', action='store_true',
                       help='Skip extracting test examples')
    parser.add_argument('--token', '-t',
                       help='GitHub personal access token (or set GITHUB_TOKEN env var)')

    args = parser.parse_args()

    # Get token from args or environment
    token = args.token or os.environ.get('GITHUB_TOKEN')

    # Create scraper
    scraper = GitHubScraper(token)

    # Scrape repository
    try:
        scraper.scrape_repository(
            args.url,
            output_dir=args.output,
            max_files=args.max_files,
            include_tests=not args.no_tests
        )
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
