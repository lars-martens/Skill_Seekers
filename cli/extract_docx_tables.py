#!/usr/bin/env python3
"""
.docx Table Extractor and Markdown Converter

Task: B2.5 - Extract tables and convert to markdown
Purpose: Extract tables from Word documents and convert to markdown format
Usage: python3 cli/extract_docx_tables.py <input.docx> [options]

Features:
- Extract all tables from .docx files
- Convert to markdown table format
- Handle merged cells
- Include context (surrounding paragraphs)
- Export as markdown or JSON
- Compatible with Skill Seeker's documentation format

Requirements:
    pip install python-docx
"""

import sys
import argparse
import json
from pathlib import Path


def extract_tables(filepath, include_context=False):
    """
    Extract all tables from a .docx file.

    Args:
        filepath: Path to the .docx file
        include_context: Include paragraph before table for context

    Returns:
        list: List of table dicts with data and metadata
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
    tables_data = []

    # If context requested, we need to track document order
    if include_context:
        # Get all block-level elements in order
        from docx.oxml.text.paragraph import CT_P
        from docx.oxml.table import CT_Tbl
        from docx.table import Table
        from docx.text.paragraph import Paragraph

        last_paragraph = None
        table_index = 0

        for child in doc._element.body:
            if isinstance(child, CT_P):
                # Store paragraph for potential context
                para = Paragraph(child, doc)
                if para.text.strip():
                    last_paragraph = para.text.strip()

            elif isinstance(child, CT_Tbl):
                # Found a table
                table = Table(child, doc)

                # Extract table data
                rows = []
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    rows.append(cells)

                if rows:  # Only include non-empty tables
                    table_data = {
                        'index': table_index,
                        'rows': rows,
                        'row_count': len(rows),
                        'column_count': len(rows[0]) if rows else 0,
                    }

                    if include_context and last_paragraph:
                        table_data['context'] = last_paragraph

                    tables_data.append(table_data)
                    table_index += 1

    else:
        # Simple extraction without context
        for idx, table in enumerate(doc.tables):
            rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                rows.append(cells)

            if rows:  # Only include non-empty tables
                tables_data.append({
                    'index': idx,
                    'rows': rows,
                    'row_count': len(rows),
                    'column_count': len(rows[0]) if rows else 0,
                })

    return tables_data


def table_to_markdown(table_data, header_row=True):
    """
    Convert table data to markdown format.

    Args:
        table_data: Table dict with 'rows' key
        header_row: Treat first row as header

    Returns:
        str: Markdown-formatted table
    """
    rows = table_data['rows']
    if not rows:
        return ""

    lines = []

    # First row
    first_row = rows[0]
    col_count = len(first_row)

    if header_row:
        # Treat first row as header
        lines.append("| " + " | ".join(first_row) + " |")
        lines.append("| " + " | ".join(["---"] * col_count) + " |")

        # Data rows
        for row in rows[1:]:
            # Pad row if needed
            padded_row = row + [""] * (col_count - len(row))
            lines.append("| " + " | ".join(padded_row[:col_count]) + " |")

    else:
        # All rows are data
        for row in rows:
            # Pad row if needed
            padded_row = row + [""] * (col_count - len(row))
            lines.append("| " + " | ".join(padded_row[:col_count]) + " |")

    return "\n".join(lines)


def format_tables_as_markdown(tables_data, include_context=True, header_row=True):
    """
    Format all tables as markdown document.

    Args:
        tables_data: List of table dicts
        include_context: Include context paragraphs
        header_row: Treat first row as header

    Returns:
        str: Markdown document with all tables
    """
    lines = []

    for idx, table in enumerate(tables_data, 1):
        lines.append(f"\n## Table {idx}")

        # Add context if available
        if include_context and table.get('context'):
            lines.append(f"\n{table['context']}\n")

        # Add table info
        lines.append(f"*{table['row_count']} rows × {table['column_count']} columns*\n")

        # Add markdown table
        md_table = table_to_markdown(table, header_row=header_row)
        lines.append(md_table)
        lines.append("")  # Blank line

    return "\n".join(lines)


def detect_table_type(table_data):
    """
    Attempt to detect what kind of table this is.

    Args:
        table_data: Table dict

    Returns:
        str: Table type (api, config, data, list, etc.)
    """
    if not table_data['rows'] or len(table_data['rows']) < 2:
        return 'unknown'

    header_row = [cell.lower() for cell in table_data['rows'][0]]

    # API reference table
    if any(keyword in ' '.join(header_row) for keyword in ['method', 'endpoint', 'parameter', 'return', 'argument']):
        return 'api'

    # Configuration table
    if any(keyword in ' '.join(header_row) for keyword in ['setting', 'config', 'option', 'value', 'default']):
        return 'config'

    # Property/attribute table
    if any(keyword in ' '.join(header_row) for keyword in ['property', 'attribute', 'type', 'description']):
        return 'properties'

    # Data table (numeric)
    if len(header_row) > 2:
        # Check if data cells are mostly numeric
        numeric_count = 0
        total_cells = 0
        for row in table_data['rows'][1:]:
            for cell in row:
                total_cells += 1
                if cell.replace('.', '').replace('-', '').isdigit():
                    numeric_count += 1

        if total_cells > 0 and numeric_count / total_cells > 0.5:
            return 'data'

    # List table (2 columns)
    if len(header_row) == 2:
        return 'list'

    return 'general'


def main():
    parser = argparse.ArgumentParser(
        description='Extract tables from .docx documents and convert to markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Extract tables as markdown
  python3 cli/extract_docx_tables.py document.docx

  # Export as JSON
  python3 cli/extract_docx_tables.py document.docx --json

  # Include context paragraphs
  python3 cli/extract_docx_tables.py document.docx --context

  # No header row
  python3 cli/extract_docx_tables.py document.docx --no-header

  # Save to file
  python3 cli/extract_docx_tables.py document.docx --output tables.md
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
        '-c', '--context',
        action='store_true',
        help='Include context paragraphs before tables'
    )

    parser.add_argument(
        '--no-header',
        action='store_true',
        help='Do not treat first row as header'
    )

    parser.add_argument(
        '-t', '--detect-type',
        action='store_true',
        help='Detect and show table types'
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
        # Extract tables
        if args.verbose:
            print(f"Extracting tables from: {args.input}", file=sys.stderr)

        tables_data = extract_tables(args.input, include_context=args.context)

        if not tables_data:
            print("No tables found in document.", file=sys.stderr)
            sys.exit(0)

        if args.verbose:
            print(f"Found {len(tables_data)} tables", file=sys.stderr)

        # Detect types if requested
        if args.detect_type:
            for table in tables_data:
                table['type'] = detect_table_type(table)

        # Generate output based on format
        if args.json:
            # JSON output
            output = {
                'file': str(input_path),
                'table_count': len(tables_data),
                'tables': tables_data
            }
            output_text = json.dumps(output, indent=2, ensure_ascii=False)

        else:
            # Markdown format
            header_row = not args.no_header

            lines = [f"# Tables from: {input_path.name}\n"]
            lines.append(f"Total tables: {len(tables_data)}\n")
            lines.append("---")

            for idx, table in enumerate(tables_data, 1):
                lines.append(f"\n## Table {idx}")

                # Show table type if detected
                if args.detect_type and table.get('type'):
                    lines.append(f"**Type:** {table['type']}")

                # Add context if available
                if args.context and table.get('context'):
                    lines.append(f"\n**Context:** {table['context']}\n")

                # Add table info
                lines.append(f"*{table['row_count']} rows × {table['column_count']} columns*\n")

                # Add markdown table
                md_table = table_to_markdown(table, header_row=header_row)
                lines.append(md_table)
                lines.append("")  # Blank line

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
        print(f"Error: Failed to extract tables", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        import traceback
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
