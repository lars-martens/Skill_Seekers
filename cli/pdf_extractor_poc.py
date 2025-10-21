#!/usr/bin/env python3
"""
PDF Text Extractor - Proof of Concept (Task B1.2)

Extracts text and code blocks from PDF documentation files.
Uses PyMuPDF (fitz) for fast, high-quality text extraction.

Usage:
    python3 pdf_extractor_poc.py input.pdf
    python3 pdf_extractor_poc.py input.pdf --output output.json
    python3 pdf_extractor_poc.py input.pdf --verbose

Example:
    python3 pdf_extractor_poc.py docs/python_guide.pdf --output python_extracted.json
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

# Check if PyMuPDF is installed
try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed")
    print("Install with: pip install PyMuPDF")
    sys.exit(1)


class PDFExtractor:
    """Extract text and code from PDF documentation"""

    def __init__(self, pdf_path, verbose=False):
        self.pdf_path = pdf_path
        self.verbose = verbose
        self.doc = None
        self.pages = []

    def log(self, message):
        """Print message if verbose mode enabled"""
        if self.verbose:
            print(message)

    def detect_language_from_code(self, code):
        """
        Detect programming language from code content using patterns.

        Returns language string or 'unknown'
        """
        code_lower = code.lower()

        # Language detection patterns
        patterns = {
            'python': [r'\bdef\s+\w+\s*\(', r'\bimport\s+\w+', r'\bclass\s+\w+:', r'\bfrom\s+\w+\s+import'],
            'javascript': [r'\bfunction\s+\w+\s*\(', r'\bconst\s+\w+\s*=', r'\blet\s+\w+\s*=', r'=>', r'\bconsole\.log'],
            'java': [r'\bpublic\s+class\s+\w+', r'\bprivate\s+\w+\s+\w+', r'\bSystem\.out\.println'],
            'cpp': [r'#include\s*<', r'\bstd::', r'\bnamespace\s+\w+', r'cout\s*<<'],
            'c': [r'#include\s+<\w+\.h>', r'\bprintf\s*\(', r'\bmain\s*\('],
            'csharp': [r'\bnamespace\s+\w+', r'\bpublic\s+class\s+\w+', r'\busing\s+System'],
            'go': [r'\bfunc\s+\w+\s*\(', r'\bpackage\s+\w+', r':=', r'\bfmt\.Print'],
            'rust': [r'\bfn\s+\w+\s*\(', r'\blet\s+mut\s+\w+', r'\bprintln!'],
            'php': [r'<\?php', r'\$\w+\s*=', r'\bfunction\s+\w+\s*\('],
            'ruby': [r'\bdef\s+\w+', r'\bend\b', r'\brequire\s+[\'"]'],
            'swift': [r'\bfunc\s+\w+\s*\(', r'\bvar\s+\w+:', r'\blet\s+\w+:'],
            'kotlin': [r'\bfun\s+\w+\s*\(', r'\bval\s+\w+\s*=', r'\bvar\s+\w+\s*='],
            'shell': [r'#!/bin/bash', r'#!/bin/sh', r'\becho\s+', r'\$\{?\w+\}?'],
            'sql': [r'\bSELECT\s+', r'\bFROM\s+', r'\bWHERE\s+', r'\bINSERT\s+INTO'],
            'html': [r'<html', r'<div', r'<span', r'<script'],
            'css': [r'\{\s*[\w-]+\s*:', r'@media', r'\.[\w-]+\s*\{'],
            'json': [r'^\s*\{', r'^\s*\[', r'"\w+"\s*:'],
            'yaml': [r'^\w+:', r'^\s+-\s+\w+'],
            'xml': [r'<\?xml', r'<\w+>'],
        }

        # Check each pattern
        for lang, lang_patterns in patterns.items():
            for pattern in lang_patterns:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    return lang

        return 'unknown'

    def detect_code_blocks_by_font(self, page):
        """
        Detect code blocks by analyzing font properties.
        Monospace fonts typically indicate code.

        Returns list of detected code blocks with metadata.
        """
        code_blocks = []
        blocks = page.get_text("dict")["blocks"]

        monospace_fonts = ['courier', 'mono', 'consolas', 'menlo', 'monaco', 'dejavu']

        current_code = []
        current_font = None

        for block in blocks:
            if 'lines' not in block:
                continue

            for line in block['lines']:
                for span in line['spans']:
                    font = span['font'].lower()
                    text = span['text']

                    # Check if font is monospace
                    is_monospace = any(mf in font for mf in monospace_fonts)

                    if is_monospace:
                        # Accumulate code text
                        current_code.append(text)
                        current_font = span['font']
                    else:
                        # End of code block
                        if current_code:
                            code_text = ''.join(current_code).strip()
                            if len(code_text) > 10:  # Minimum code length
                                lang = self.detect_language_from_code(code_text)
                                code_blocks.append({
                                    'code': code_text,
                                    'language': lang,
                                    'font': current_font,
                                    'detection_method': 'font'
                                })
                            current_code = []
                            current_font = None

        # Handle final code block
        if current_code:
            code_text = ''.join(current_code).strip()
            if len(code_text) > 10:
                lang = self.detect_language_from_code(code_text)
                code_blocks.append({
                    'code': code_text,
                    'language': lang,
                    'font': current_font,
                    'detection_method': 'font'
                })

        return code_blocks

    def detect_code_blocks_by_indent(self, text):
        """
        Detect code blocks by indentation patterns.
        Code often has consistent indentation.

        Returns list of detected code blocks.
        """
        code_blocks = []
        lines = text.split('\n')
        current_block = []
        indent_pattern = None

        for line in lines:
            # Check for indentation (4 spaces or tab)
            if line.startswith('    ') or line.startswith('\t'):
                # Start or continue code block
                if not indent_pattern:
                    indent_pattern = line[:4] if line.startswith('    ') else '\t'
                current_block.append(line)
            else:
                # End of code block
                if current_block and len(current_block) >= 2:  # At least 2 lines
                    code_text = '\n'.join(current_block).strip()
                    if len(code_text) > 20:  # Minimum code length
                        lang = self.detect_language_from_code(code_text)
                        code_blocks.append({
                            'code': code_text,
                            'language': lang,
                            'detection_method': 'indent'
                        })
                current_block = []
                indent_pattern = None

        # Handle final block
        if current_block and len(current_block) >= 2:
            code_text = '\n'.join(current_block).strip()
            if len(code_text) > 20:
                lang = self.detect_language_from_code(code_text)
                code_blocks.append({
                    'code': code_text,
                    'language': lang,
                    'detection_method': 'indent'
                })

        return code_blocks

    def detect_code_blocks_by_pattern(self, text):
        """
        Detect code blocks by common code patterns (keywords, syntax).

        Returns list of detected code snippets.
        """
        code_blocks = []

        # Common code patterns that span multiple lines
        patterns = [
            # Function definitions
            (r'((?:def|function|func|fn|public|private)\s+\w+\s*\([^)]*\)\s*[{:]?[^}]*[}]?)', 'function'),
            # Class definitions
            (r'(class\s+\w+[^{]*\{[^}]*\})', 'class'),
            # Import statements block
            (r'((?:import|require|use|include)[^\n]+(?:\n(?:import|require|use|include)[^\n]+)*)', 'imports'),
        ]

        for pattern, block_type in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                code_text = match.group(1).strip()
                if len(code_text) > 15:
                    lang = self.detect_language_from_code(code_text)
                    code_blocks.append({
                        'code': code_text,
                        'language': lang,
                        'detection_method': 'pattern',
                        'pattern_type': block_type
                    })

        return code_blocks

    def extract_page(self, page_num):
        """
        Extract content from a single PDF page.

        Returns dict with page content, code blocks, and metadata.
        """
        page = self.doc.load_page(page_num)

        # Extract plain text
        text = page.get_text("text")

        # Extract markdown (better structure preservation)
        markdown = page.get_text("markdown")

        # Get page images (for diagrams)
        images = page.get_images()

        # Detect code blocks using multiple methods
        font_code_blocks = self.detect_code_blocks_by_font(page)
        indent_code_blocks = self.detect_code_blocks_by_indent(text)
        pattern_code_blocks = self.detect_code_blocks_by_pattern(text)

        # Merge and deduplicate code blocks
        all_code_blocks = font_code_blocks + indent_code_blocks + pattern_code_blocks

        # Simple deduplication by code content
        unique_code = {}
        for block in all_code_blocks:
            code_hash = hash(block['code'])
            if code_hash not in unique_code:
                unique_code[code_hash] = block

        code_samples = list(unique_code.values())

        # Extract headings from markdown
        headings = []
        for line in markdown.split('\n'):
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line.lstrip('#').strip()
                if text:
                    headings.append({
                        'level': f'h{level}',
                        'text': text
                    })

        page_data = {
            'page_number': page_num + 1,  # 1-indexed for humans
            'text': text.strip(),
            'markdown': markdown.strip(),
            'headings': headings,
            'code_samples': code_samples,
            'images_count': len(images),
            'char_count': len(text),
            'code_blocks_count': len(code_samples)
        }

        self.log(f"  Page {page_num + 1}: {len(text)} chars, {len(code_samples)} code blocks, {len(headings)} headings")

        return page_data

    def extract_all(self):
        """
        Extract content from all pages of the PDF.

        Returns dict with metadata and pages array.
        """
        print(f"\n📄 Extracting from: {self.pdf_path}")

        # Open PDF
        try:
            self.doc = fitz.open(self.pdf_path)
        except Exception as e:
            print(f"❌ Error opening PDF: {e}")
            return None

        print(f"   Pages: {len(self.doc)}")
        print(f"   Metadata: {self.doc.metadata}")
        print("")

        # Extract each page
        for page_num in range(len(self.doc)):
            page_data = self.extract_page(page_num)
            self.pages.append(page_data)

        # Build summary
        total_chars = sum(p['char_count'] for p in self.pages)
        total_code_blocks = sum(p['code_blocks_count'] for p in self.pages)
        total_headings = sum(len(p['headings']) for p in self.pages)
        total_images = sum(p['images_count'] for p in self.pages)

        # Detect languages used
        languages = {}
        for page in self.pages:
            for code in page['code_samples']:
                lang = code['language']
                languages[lang] = languages.get(lang, 0) + 1

        result = {
            'source_file': self.pdf_path,
            'metadata': self.doc.metadata,
            'total_pages': len(self.doc),
            'total_chars': total_chars,
            'total_code_blocks': total_code_blocks,
            'total_headings': total_headings,
            'total_images': total_images,
            'languages_detected': languages,
            'pages': self.pages
        }

        # Close document
        self.doc.close()

        print(f"\n✅ Extraction complete:")
        print(f"   Total characters: {total_chars:,}")
        print(f"   Code blocks found: {total_code_blocks}")
        print(f"   Headings found: {total_headings}")
        print(f"   Images found: {total_images}")
        print(f"   Languages detected: {', '.join(languages.keys())}")

        return result


def main():
    parser = argparse.ArgumentParser(
        description='Extract text and code blocks from PDF documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from PDF
  python3 pdf_extractor_poc.py input.pdf

  # Save to JSON file
  python3 pdf_extractor_poc.py input.pdf --output result.json

  # Verbose mode
  python3 pdf_extractor_poc.py input.pdf --verbose

  # Extract and save
  python3 pdf_extractor_poc.py docs/python.pdf -o python_extracted.json -v
        """
    )

    parser.add_argument('pdf_file', help='Path to PDF file to extract')
    parser.add_argument('-o', '--output', help='Output JSON file path (default: print to stdout)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.pdf_file):
        print(f"❌ Error: File not found: {args.pdf_file}")
        sys.exit(1)

    if not args.pdf_file.lower().endswith('.pdf'):
        print(f"⚠️  Warning: File does not have .pdf extension")

    # Extract
    extractor = PDFExtractor(args.pdf_file, verbose=args.verbose)
    result = extractor.extract_all()

    if result is None:
        sys.exit(1)

    # Output
    if args.output:
        # Save to file
        with open(args.output, 'w', encoding='utf-8') as f:
            if args.pretty:
                json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                json.dump(result, f, ensure_ascii=False)
        print(f"\n💾 Saved to: {args.output}")
    else:
        # Print to stdout
        if args.pretty:
            print("\n" + json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
