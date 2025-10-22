#!/usr/bin/env python3
"""
.docx Heading Extractor and Categorizer

Task: B2.3 - Extract headings and create categories
Purpose: Extract heading structure from Word documents and create categories
Usage: python3 cli/extract_docx_headings.py <input.docx> [options]

Features:
- Extract all headings (H1-H6) with levels
- Build hierarchical document structure
- Auto-categorize content based on headings
- Export as JSON or markdown outline
- Compatible with Skill Seeker category system

Requirements:
    pip install python-docx
"""

import sys
import argparse
import json
from pathlib import Path
from collections import defaultdict


def extract_headings(filepath):
    """
    Extract all headings from a .docx file with their levels.

    Args:
        filepath: Path to the .docx file

    Returns:
        list: List of dicts with heading info (level, text, style)
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "python-docx library not found. Install with: pip install python-docx"
        )

    if not Path(filepath).exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    doc = Document(filepath)
    headings = []

    for idx, para in enumerate(doc.paragraphs):
        style_name = para.style.name

        # Check if paragraph is a heading
        if style_name.startswith('Heading'):
            try:
                # Extract heading level (e.g., "Heading 1" -> 1)
                level = int(style_name.split()[-1])
            except (ValueError, IndexError):
                # Handle edge cases like "Heading" without number
                level = 1

            text = para.text.strip()
            if text:  # Only include non-empty headings
                headings.append({
                    'level': level,
                    'text': text,
                    'style': style_name,
                    'index': idx
                })

    return headings


def build_hierarchy(headings):
    """
    Build a hierarchical structure from flat heading list.

    Args:
        headings: List of heading dicts

    Returns:
        list: Nested hierarchy of headings
    """
    if not headings:
        return []

    hierarchy = []
    stack = []  # Stack to track parent headings

    for heading in headings:
        level = heading['level']

        # Pop stack until we find appropriate parent
        while stack and stack[-1]['level'] >= level:
            stack.pop()

        # Create node
        node = {
            'level': level,
            'text': heading['text'],
            'children': []
        }

        # Add to parent's children or root
        if stack:
            stack[-1]['children'].append(node)
        else:
            hierarchy.append(node)

        # Add to stack
        stack.append(node)

    return hierarchy


def create_categories(headings):
    """
    Create categories based on heading structure.

    Uses H1 and H2 headings to define categories, similar to
    HTML scraper's URL-based categorization.

    Args:
        headings: List of heading dicts

    Returns:
        dict: Category mapping and structure
    """
    categories = defaultdict(list)
    current_h1 = None
    current_h2 = None

    for heading in headings:
        level = heading['level']
        text = heading['text']

        if level == 1:
            # H1 defines main category
            current_h1 = text.lower().replace(' ', '_')
            current_h2 = None
            categories[current_h1] = []

        elif level == 2 and current_h1:
            # H2 defines subcategory
            current_h2 = text.lower().replace(' ', '_')
            categories[current_h1].append({
                'name': current_h2,
                'title': text
            })

    # Infer categories from content if none found
    if not categories:
        # Use first H1 or create default
        first_h1 = next((h for h in headings if h['level'] == 1), None)
        if first_h1:
            cat_name = first_h1['text'].lower().replace(' ', '_')
            categories[cat_name] = []
        else:
            categories['general'] = []

    return dict(categories)


def format_as_markdown_outline(hierarchy, indent_level=0):
    """
    Format heading hierarchy as markdown outline.

    Args:
        hierarchy: Nested hierarchy structure
        indent_level: Current indentation level

    Returns:
        str: Markdown-formatted outline
    """
    lines = []
    indent = '  ' * indent_level

    for node in hierarchy:
        # Create markdown heading or list item
        level_marker = '#' * node['level']
        lines.append(f"{indent}{level_marker} {node['text']}")

        # Recursively process children
        if node['children']:
            child_lines = format_as_markdown_outline(
                node['children'],
                indent_level + 1
            )
            lines.append(child_lines)

    return '\n'.join(lines)


def format_as_outline(hierarchy, indent_level=0):
    """
    Format heading hierarchy as indented outline.

    Args:
        hierarchy: Nested hierarchy structure
        indent_level: Current indentation level

    Returns:
        str: Plain text outline
    """
    lines = []
    indent = '  ' * indent_level

    for node in hierarchy:
        level_indicator = f"[H{node['level']}]"
        lines.append(f"{indent}{level_indicator} {node['text']}")

        # Recursively process children
        if node['children']:
            child_lines = format_as_outline(
                node['children'],
                indent_level + 1
            )
            lines.append(child_lines)

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Extract headings and categories from .docx documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Extract headings as outline
  python3 cli/extract_docx_headings.py document.docx

  # Export as JSON
  python3 cli/extract_docx_headings.py document.docx --json --output headings.json

  # Show categories
  python3 cli/extract_docx_headings.py document.docx --categories

  # Markdown outline
  python3 cli/extract_docx_headings.py document.docx --markdown
        '''
    )

    parser.add_argument(
        'input',
        help='Input .docx file path'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file path (optional)'
    )

    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help='Output as JSON format'
    )

    parser.add_argument(
        '-m', '--markdown',
        action='store_true',
        help='Output as markdown outline'
    )

    parser.add_argument(
        '-c', '--categories',
        action='store_true',
        help='Show category structure'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        # Extract headings
        if args.verbose:
            print(f"Extracting headings from: {args.input}", file=sys.stderr)

        headings = extract_headings(args.input)

        if not headings:
            print("No headings found in document.", file=sys.stderr)
            sys.exit(0)

        if args.verbose:
            print(f"Found {len(headings)} headings", file=sys.stderr)

        # Build hierarchy
        hierarchy = build_hierarchy(headings)

        # Create categories
        categories = create_categories(headings)

        # Generate output based on format
        if args.json:
            # JSON output
            output = {
                'file': str(input_path),
                'heading_count': len(headings),
                'headings': headings,
                'hierarchy': hierarchy,
                'categories': categories
            }
            output_text = json.dumps(output, indent=2, ensure_ascii=False)

        elif args.categories:
            # Category structure
            lines = [f"Categories from: {input_path}\n"]
            lines.append("=" * 60)

            for cat_name, subcats in categories.items():
                lines.append(f"\n{cat_name.replace('_', ' ').title()}")
                if subcats:
                    for subcat in subcats:
                        lines.append(f"  - {subcat['title']}")
                else:
                    lines.append("  (no subcategories)")

            output_text = '\n'.join(lines)

        elif args.markdown:
            # Markdown outline
            output_text = format_as_markdown_outline(hierarchy)

        else:
            # Default: plain outline
            lines = [f"Document Structure: {input_path}\n"]
            lines.append("=" * 60)
            lines.append(f"Total headings: {len(headings)}\n")
            lines.append(format_as_outline(hierarchy))
            output_text = '\n'.join(lines)

        # Output to file or console
        if args.output:
            Path(args.output).write_text(output_text, encoding='utf-8')
            if args.verbose:
                print(f"\nOutput saved to: {args.output}", file=sys.stderr)
        else:
            print(output_text)

    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nInstall required library:", file=sys.stderr)
        print("  pip install python-docx", file=sys.stderr)
        sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Error: Failed to extract headings", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
