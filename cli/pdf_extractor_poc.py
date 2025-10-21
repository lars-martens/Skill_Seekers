#!/usr/bin/env python3
"""
PDF Text Extractor - Enhanced with Syntax Detection (Tasks B1.2 + B1.3 + B1.4)

Extracts text and code blocks from PDF documentation files.
Uses PyMuPDF (fitz) for fast, high-quality text extraction.

Features:
    - Text and markdown extraction
    - Code block detection (font, indent, pattern)
    - Language detection with confidence scoring (19+ languages) (ENHANCED in B1.4)
    - Syntax validation and quality scoring (NEW in B1.4)
    - Quality statistics and filtering (NEW in B1.4)
    - Page chunking and chapter detection (B1.3)
    - Code block merging across pages (B1.3)

Usage:
    python3 pdf_extractor_poc.py input.pdf
    python3 pdf_extractor_poc.py input.pdf --output output.json
    python3 pdf_extractor_poc.py input.pdf --verbose
    python3 pdf_extractor_poc.py input.pdf --chunk-size 20
    python3 pdf_extractor_poc.py input.pdf --min-quality 5.0

Example:
    python3 pdf_extractor_poc.py docs/python_guide.pdf -o output.json -v --chunk-size 15 --min-quality 6.0
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

    def __init__(self, pdf_path, verbose=False, chunk_size=10, min_quality=0.0):
        self.pdf_path = pdf_path
        self.verbose = verbose
        self.chunk_size = chunk_size  # Pages per chunk (0 = no chunking)
        self.min_quality = min_quality  # Minimum quality score (0-10)
        self.doc = None
        self.pages = []
        self.chapters = []  # Detected chapters/sections

    def log(self, message):
        """Print message if verbose mode enabled"""
        if self.verbose:
            print(message)

    def detect_language_from_code(self, code):
        """
        Detect programming language from code content using patterns.
        Enhanced in B1.4 with confidence scoring.

        Returns (language, confidence) tuple
        """
        code_lower = code.lower()

        # Language detection patterns with weights
        patterns = {
            'python': [
                (r'\bdef\s+\w+\s*\(', 3),
                (r'\bimport\s+\w+', 2),
                (r'\bclass\s+\w+:', 3),
                (r'\bfrom\s+\w+\s+import', 2),
                (r':\s*$', 1),  # Lines ending with :
                (r'^\s{4}|\t', 1),  # Indentation
            ],
            'javascript': [
                (r'\bfunction\s+\w+\s*\(', 3),
                (r'\bconst\s+\w+\s*=', 2),
                (r'\blet\s+\w+\s*=', 2),
                (r'=>', 2),
                (r'\bconsole\.log', 2),
                (r'\bvar\s+\w+\s*=', 1),
            ],
            'java': [
                (r'\bpublic\s+class\s+\w+', 4),
                (r'\bprivate\s+\w+\s+\w+', 2),
                (r'\bSystem\.out\.println', 3),
                (r'\bpublic\s+static\s+void', 3),
            ],
            'cpp': [
                (r'#include\s*<', 3),
                (r'\bstd::', 3),
                (r'\bnamespace\s+\w+', 2),
                (r'cout\s*<<', 3),
                (r'\bvoid\s+\w+\s*\(', 1),
            ],
            'c': [
                (r'#include\s+<\w+\.h>', 4),
                (r'\bprintf\s*\(', 3),
                (r'\bmain\s*\(', 2),
                (r'\bstruct\s+\w+', 2),
            ],
            'csharp': [
                (r'\bnamespace\s+\w+', 3),
                (r'\bpublic\s+class\s+\w+', 3),
                (r'\busing\s+System', 3),
            ],
            'go': [
                (r'\bfunc\s+\w+\s*\(', 3),
                (r'\bpackage\s+\w+', 4),
                (r':=', 2),
                (r'\bfmt\.Print', 2),
            ],
            'rust': [
                (r'\bfn\s+\w+\s*\(', 4),
                (r'\blet\s+mut\s+\w+', 3),
                (r'\bprintln!', 3),
                (r'\bimpl\s+\w+', 2),
            ],
            'php': [
                (r'<\?php', 5),
                (r'\$\w+\s*=', 2),
                (r'\bfunction\s+\w+\s*\(', 1),
            ],
            'ruby': [
                (r'\bdef\s+\w+', 3),
                (r'\bend\b', 2),
                (r'\brequire\s+[\'"]', 2),
            ],
            'swift': [
                (r'\bfunc\s+\w+\s*\(', 3),
                (r'\bvar\s+\w+:', 2),
                (r'\blet\s+\w+:', 2),
            ],
            'kotlin': [
                (r'\bfun\s+\w+\s*\(', 4),
                (r'\bval\s+\w+\s*=', 2),
                (r'\bvar\s+\w+\s*=', 2),
            ],
            'shell': [
                (r'#!/bin/bash', 5),
                (r'#!/bin/sh', 5),
                (r'\becho\s+', 1),
                (r'\$\{?\w+\}?', 1),
            ],
            'sql': [
                (r'\bSELECT\s+', 4),
                (r'\bFROM\s+', 3),
                (r'\bWHERE\s+', 2),
                (r'\bINSERT\s+INTO', 4),
                (r'\bCREATE\s+TABLE', 4),
            ],
            'html': [
                (r'<html', 4),
                (r'<div', 2),
                (r'<span', 2),
                (r'<script', 2),
            ],
            'css': [
                (r'\{\s*[\w-]+\s*:', 3),
                (r'@media', 3),
                (r'\.[\w-]+\s*\{', 2),
            ],
            'json': [
                (r'^\s*\{', 2),
                (r'^\s*\[', 2),
                (r'"\w+"\s*:', 3),
            ],
            'yaml': [
                (r'^\w+:', 2),
                (r'^\s+-\s+\w+', 2),
            ],
            'xml': [
                (r'<\?xml', 5),
                (r'<\w+>', 1),
            ],
        }

        # Calculate confidence scores for each language
        scores = {}
        for lang, lang_patterns in patterns.items():
            score = 0
            for pattern, weight in lang_patterns:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    score += weight
            if score > 0:
                scores[lang] = score

        if not scores:
            return 'unknown', 0

        # Get language with highest score
        best_lang = max(scores, key=scores.get)
        confidence = min(scores[best_lang] / 10.0, 1.0)  # Normalize to 0-1

        return best_lang, confidence

    def validate_code_syntax(self, code, language):
        """
        Validate code syntax (basic checks).
        Enhanced in B1.4 with syntax validation.

        Returns (is_valid, issues) tuple
        """
        issues = []

        # Common syntax checks
        if not code.strip():
            return False, ['Empty code block']

        # Language-specific validation
        if language == 'python':
            # Check indentation consistency
            lines = code.split('\n')
            indent_chars = set()
            for line in lines:
                if line.startswith(' '):
                    indent_chars.add('space')
                elif line.startswith('\t'):
                    indent_chars.add('tab')

            if len(indent_chars) > 1:
                issues.append('Mixed tabs and spaces')

            # Check for unclosed brackets/parens
            open_count = code.count('(') + code.count('[') + code.count('{')
            close_count = code.count(')') + code.count(']') + code.count('}')
            if abs(open_count - close_count) > 2:  # Allow small mismatch
                issues.append('Unbalanced brackets')

        elif language in ['javascript', 'java', 'cpp', 'c', 'csharp', 'go']:
            # Check for balanced braces
            open_braces = code.count('{')
            close_braces = code.count('}')
            if abs(open_braces - close_braces) > 1:
                issues.append('Unbalanced braces')

        elif language == 'json':
            # Try to parse JSON
            try:
                json.loads(code)
            except:
                issues.append('Invalid JSON syntax')

        # General checks
        # Check if code looks like natural language (too many common words)
        common_words = ['the', 'and', 'for', 'with', 'this', 'that', 'have', 'from']
        word_count = sum(1 for word in common_words if word in code.lower())
        if word_count > 5 and len(code.split()) < 50:
            issues.append('May be natural language, not code')

        # Check code/comment ratio
        comment_lines = sum(1 for line in code.split('\n') if line.strip().startswith(('#', '//', '/*', '*', '--')))
        total_lines = len([l for l in code.split('\n') if l.strip()])
        if total_lines > 0 and comment_lines / total_lines > 0.7:
            issues.append('Mostly comments')

        return len(issues) == 0, issues

    def score_code_quality(self, code, language, confidence):
        """
        Score the quality/usefulness of detected code block.
        New in B1.4.

        Returns quality score (0-10)
        """
        score = 5.0  # Start with neutral score

        # Factor 1: Language detection confidence
        score += confidence * 2.0

        # Factor 2: Code length (not too short, not too long)
        code_length = len(code.strip())
        if 20 <= code_length <= 500:
            score += 1.0
        elif 500 < code_length <= 2000:
            score += 0.5
        elif code_length < 10:
            score -= 2.0

        # Factor 3: Number of lines
        lines = [l for l in code.split('\n') if l.strip()]
        if 2 <= len(lines) <= 50:
            score += 1.0
        elif len(lines) > 100:
            score -= 1.0

        # Factor 4: Has function/class definitions
        if re.search(r'\b(def|function|class|func|fn|public class)\b', code):
            score += 1.5

        # Factor 5: Has meaningful variable names (not just x, y, i)
        meaningful_vars = re.findall(r'\b[a-z_][a-z0-9_]{3,}\b', code.lower())
        if len(meaningful_vars) >= 2:
            score += 1.0

        # Factor 6: Syntax validation
        is_valid, issues = self.validate_code_syntax(code, language)
        if is_valid:
            score += 1.0
        else:
            score -= len(issues) * 0.5

        # Clamp score to 0-10 range
        return max(0, min(10, score))

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
                                lang, confidence = self.detect_language_from_code(code_text)
                                quality = self.score_code_quality(code_text, lang, confidence)
                                is_valid, issues = self.validate_code_syntax(code_text, lang)

                                code_blocks.append({
                                    'code': code_text,
                                    'language': lang,
                                    'confidence': confidence,
                                    'quality_score': quality,
                                    'is_valid': is_valid,
                                    'validation_issues': issues if not is_valid else [],
                                    'font': current_font,
                                    'detection_method': 'font'
                                })
                            current_code = []
                            current_font = None

        # Handle final code block
        if current_code:
            code_text = ''.join(current_code).strip()
            if len(code_text) > 10:
                lang, confidence = self.detect_language_from_code(code_text)
                quality = self.score_code_quality(code_text, lang, confidence)
                is_valid, issues = self.validate_code_syntax(code_text, lang)

                code_blocks.append({
                    'code': code_text,
                    'language': lang,
                    'confidence': confidence,
                    'quality_score': quality,
                    'is_valid': is_valid,
                    'validation_issues': issues if not is_valid else [],
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
                        lang, confidence = self.detect_language_from_code(code_text)
                        quality = self.score_code_quality(code_text, lang, confidence)
                        is_valid, issues = self.validate_code_syntax(code_text, lang)

                        code_blocks.append({
                            'code': code_text,
                            'language': lang,
                            'confidence': confidence,
                            'quality_score': quality,
                            'is_valid': is_valid,
                            'validation_issues': issues if not is_valid else [],
                            'detection_method': 'indent'
                        })
                current_block = []
                indent_pattern = None

        # Handle final block
        if current_block and len(current_block) >= 2:
            code_text = '\n'.join(current_block).strip()
            if len(code_text) > 20:
                lang, confidence = self.detect_language_from_code(code_text)
                quality = self.score_code_quality(code_text, lang, confidence)
                is_valid, issues = self.validate_code_syntax(code_text, lang)

                code_blocks.append({
                    'code': code_text,
                    'language': lang,
                    'confidence': confidence,
                    'quality_score': quality,
                    'is_valid': is_valid,
                    'validation_issues': issues if not is_valid else [],
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
                    lang, confidence = self.detect_language_from_code(code_text)
                    quality = self.score_code_quality(code_text, lang, confidence)
                    is_valid, issues = self.validate_code_syntax(code_text, lang)

                    code_blocks.append({
                        'code': code_text,
                        'language': lang,
                        'confidence': confidence,
                        'quality_score': quality,
                        'is_valid': is_valid,
                        'validation_issues': issues if not is_valid else [],
                        'detection_method': 'pattern',
                        'pattern_type': block_type
                    })

        return code_blocks

    def detect_chapter_start(self, page_data):
        """
        Detect if a page starts a new chapter/section.

        Returns (is_chapter_start, chapter_title) tuple.
        """
        headings = page_data.get('headings', [])

        # Check for h1 or h2 at start of page
        if headings:
            first_heading = headings[0]
            # H1 headings are strong indicators of chapters
            if first_heading['level'] in ['h1', 'h2']:
                return True, first_heading['text']

        # Check for specific chapter markers in text
        text = page_data.get('text', '')
        first_line = text.split('\n')[0] if text else ''

        chapter_patterns = [
            r'^Chapter\s+\d+',
            r'^Part\s+\d+',
            r'^Section\s+\d+',
            r'^\d+\.\s+[A-Z]',  # "1. Introduction"
        ]

        for pattern in chapter_patterns:
            if re.match(pattern, first_line, re.IGNORECASE):
                return True, first_line.strip()

        return False, None

    def merge_continued_code_blocks(self, pages):
        """
        Merge code blocks that are split across pages.

        Detects when a code block at the end of one page continues
        on the next page.
        """
        for i in range(len(pages) - 1):
            current_page = pages[i]
            next_page = pages[i + 1]

            # Check if current page has code blocks
            if not current_page['code_samples']:
                continue

            # Get last code block of current page
            last_code = current_page['code_samples'][-1]

            # Check if next page starts with code
            if not next_page['code_samples']:
                continue

            first_next_code = next_page['code_samples'][0]

            # Same language and detection method = likely continuation
            if (last_code['language'] == first_next_code['language'] and
                last_code['detection_method'] == first_next_code['detection_method']):

                # Check if last code block looks incomplete (doesn't end with closing brace/etc)
                last_code_text = last_code['code'].rstrip()
                continuation_indicators = [
                    not last_code_text.endswith('}'),
                    not last_code_text.endswith(';'),
                    last_code_text.endswith(','),
                    last_code_text.endswith('\\'),
                ]

                if any(continuation_indicators):
                    # Merge the code blocks
                    merged_code = last_code['code'] + '\n' + first_next_code['code']
                    last_code['code'] = merged_code
                    last_code['merged_from_next_page'] = True

                    # Remove the first code block from next page
                    next_page['code_samples'].pop(0)
                    next_page['code_blocks_count'] -= 1

                    self.log(f"  Merged code block from page {i+1} to {i+2}")

        return pages

    def create_chunks(self, pages):
        """
        Create chunks of pages for better organization.

        Returns array of chunks, each containing:
        - chunk_number
        - start_page, end_page
        - pages (array)
        - chapter_title (if detected)
        """
        if self.chunk_size == 0:
            # No chunking - return all pages as one chunk
            return [{
                'chunk_number': 1,
                'start_page': 1,
                'end_page': len(pages),
                'pages': pages,
                'chapter_title': None
            }]

        chunks = []
        current_chunk = []
        chunk_start = 0
        current_chapter = None

        for i, page in enumerate(pages):
            # Check if this page starts a new chapter
            is_chapter, chapter_title = self.detect_chapter_start(page)

            if is_chapter and current_chunk:
                # Save current chunk before starting new one
                chunks.append({
                    'chunk_number': len(chunks) + 1,
                    'start_page': chunk_start + 1,
                    'end_page': i,
                    'pages': current_chunk,
                    'chapter_title': current_chapter
                })
                current_chunk = []
                chunk_start = i
                current_chapter = chapter_title

            if not current_chapter and is_chapter:
                current_chapter = chapter_title

            current_chunk.append(page)

            # Check if chunk size reached (but don't break chapters)
            if not is_chapter and len(current_chunk) >= self.chunk_size:
                chunks.append({
                    'chunk_number': len(chunks) + 1,
                    'start_page': chunk_start + 1,
                    'end_page': i + 1,
                    'pages': current_chunk,
                    'chapter_title': current_chapter
                })
                current_chunk = []
                chunk_start = i + 1
                current_chapter = None

        # Add remaining pages as final chunk
        if current_chunk:
            chunks.append({
                'chunk_number': len(chunks) + 1,
                'start_page': chunk_start + 1,
                'end_page': len(pages),
                'pages': current_chunk,
                'chapter_title': current_chapter
            })

        return chunks

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
            else:
                # Keep the one with higher quality score
                if block['quality_score'] > unique_code[code_hash]['quality_score']:
                    unique_code[code_hash] = block

        code_samples = list(unique_code.values())

        # Filter by minimum quality (NEW in B1.4)
        if self.min_quality > 0:
            code_samples_before = len(code_samples)
            code_samples = [c for c in code_samples if c['quality_score'] >= self.min_quality]
            filtered_count = code_samples_before - len(code_samples)
            if filtered_count > 0:
                self.log(f"  Filtered out {filtered_count} low-quality code blocks (min_quality={self.min_quality})")

        # Sort by quality score (highest first)
        code_samples.sort(key=lambda x: x['quality_score'], reverse=True)

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

        # Merge code blocks that span across pages
        self.log("\n🔗 Merging code blocks across pages...")
        self.pages = self.merge_continued_code_blocks(self.pages)

        # Create chunks
        self.log(f"\n📦 Creating chunks (chunk_size={self.chunk_size})...")
        chunks = self.create_chunks(self.pages)

        # Build summary
        total_chars = sum(p['char_count'] for p in self.pages)
        total_code_blocks = sum(p['code_blocks_count'] for p in self.pages)
        total_headings = sum(len(p['headings']) for p in self.pages)
        total_images = sum(p['images_count'] for p in self.pages)

        # Detect languages used
        languages = {}
        all_code_blocks_list = []
        for page in self.pages:
            for code in page['code_samples']:
                lang = code['language']
                languages[lang] = languages.get(lang, 0) + 1
                all_code_blocks_list.append(code)

        # Calculate quality statistics (NEW in B1.4)
        quality_stats = {}
        if all_code_blocks_list:
            quality_scores = [c['quality_score'] for c in all_code_blocks_list]
            confidences = [c['confidence'] for c in all_code_blocks_list]
            valid_count = sum(1 for c in all_code_blocks_list if c['is_valid'])

            quality_stats = {
                'average_quality': sum(quality_scores) / len(quality_scores),
                'average_confidence': sum(confidences) / len(confidences),
                'valid_code_blocks': valid_count,
                'invalid_code_blocks': total_code_blocks - valid_count,
                'validation_rate': valid_count / total_code_blocks if total_code_blocks > 0 else 0,
                'high_quality_blocks': sum(1 for s in quality_scores if s >= 7.0),
                'medium_quality_blocks': sum(1 for s in quality_scores if 4.0 <= s < 7.0),
                'low_quality_blocks': sum(1 for s in quality_scores if s < 4.0),
            }

        # Extract chapter information
        chapters = []
        for chunk in chunks:
            if chunk['chapter_title']:
                chapters.append({
                    'title': chunk['chapter_title'],
                    'start_page': chunk['start_page'],
                    'end_page': chunk['end_page']
                })

        result = {
            'source_file': self.pdf_path,
            'metadata': self.doc.metadata,
            'total_pages': len(self.doc),
            'total_chars': total_chars,
            'total_code_blocks': total_code_blocks,
            'total_headings': total_headings,
            'total_images': total_images,
            'total_chunks': len(chunks),
            'chapters': chapters,
            'languages_detected': languages,
            'quality_statistics': quality_stats,  # NEW in B1.4
            'chunks': chunks,
            'pages': self.pages  # Still include all pages for compatibility
        }

        # Close document
        self.doc.close()

        print(f"\n✅ Extraction complete:")
        print(f"   Total characters: {total_chars:,}")
        print(f"   Code blocks found: {total_code_blocks}")
        print(f"   Headings found: {total_headings}")
        print(f"   Images found: {total_images}")
        print(f"   Chunks created: {len(chunks)}")
        print(f"   Chapters detected: {len(chapters)}")
        print(f"   Languages detected: {', '.join(languages.keys())}")

        # Print quality statistics (NEW in B1.4)
        if quality_stats:
            print(f"\n📊 Code Quality Statistics:")
            print(f"   Average quality: {quality_stats['average_quality']:.1f}/10")
            print(f"   Average confidence: {quality_stats['average_confidence']:.1%}")
            print(f"   Valid code blocks: {quality_stats['valid_code_blocks']}/{total_code_blocks} ({quality_stats['validation_rate']:.1%})")
            print(f"   High quality (7+): {quality_stats['high_quality_blocks']}")
            print(f"   Medium quality (4-7): {quality_stats['medium_quality_blocks']}")
            print(f"   Low quality (<4): {quality_stats['low_quality_blocks']}")

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
    parser.add_argument('--chunk-size', type=int, default=10,
                        help='Pages per chunk (0 = no chunking, default: 10)')
    parser.add_argument('--no-merge', action='store_true',
                        help='Disable merging code blocks across pages')
    parser.add_argument('--min-quality', type=float, default=0.0,
                        help='Minimum code quality score (0-10, default: 0 = no filtering)')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.pdf_file):
        print(f"❌ Error: File not found: {args.pdf_file}")
        sys.exit(1)

    if not args.pdf_file.lower().endswith('.pdf'):
        print(f"⚠️  Warning: File does not have .pdf extension")

    # Extract
    extractor = PDFExtractor(args.pdf_file, verbose=args.verbose,
                           chunk_size=args.chunk_size, min_quality=args.min_quality)
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
