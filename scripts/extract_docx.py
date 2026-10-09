"""Extract text from a DOCX file for KB summarization.

Usage:
  uv run --python 3.12 --with python-docx extract_docx.py <path>
  uv run --python 3.12 --with python-docx extract_docx.py <path> --headings-only
  uv run --python 3.12 --with python-docx extract_docx.py <path> --tables-only
  uv run --python 3.12 --with python-docx extract_docx.py <path> --max-rows 5

Workflow:
  1. Run with --headings-only first to see document structure (like reading a PDF TOC).
  2. Run without flags to get full content (all paragraphs, all table rows, unclipped cells).
  3. Use --max-rows / --max-cell only for previews; the COVERAGE line reports what was cut.
"""

import sys
import io
import argparse
import docx

# Force stdout to UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _clip(text, max_cell):
    if max_cell and len(text) > max_cell:
        return text[:max_cell], True
    return text, False


def extract_docx(path, tables_only=False, headings_only=False, max_rows=0, max_cell=0):
    doc = docx.Document(path)
    paras_shown = 0

    if not tables_only:
        print("=== PARAGRAPHS ===")
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            style = p.style.name
            if headings_only and "heading" not in style.lower():
                continue
            print(f"[{style}] {text}")
            paras_shown += 1

    rows_shown = rows_total = cells_clipped = tables_cut = 0
    if not headings_only:
        print(f"\n=== TABLES ({len(doc.tables)} total) ===")
        for i, table in enumerate(doc.tables):
            print(f"\n--- Table {i + 1} ---")
            shown = total = 0
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if not any(cells):
                    continue
                total += 1
                if max_rows and shown >= max_rows:
                    continue
                clipped = [_clip(c, max_cell) for c in cells]
                cells_clipped += sum(1 for _, cut in clipped if cut)
                print(" | ".join(c for c, _ in clipped))
                shown += 1
            if shown < total:
                print(f"  ... ({total - shown} more rows not shown)")
                tables_cut += 1
            rows_shown += shown
            rows_total += total

    parts = []
    if not tables_only:
        parts.append(f"paragraphs {paras_shown}" + (" (headings only)" if headings_only else ""))
    if not headings_only:
        parts.append(f"tables {len(doc.tables) - tables_cut}/{len(doc.tables)} complete")
        parts.append(f"rows {rows_shown}/{rows_total}")
        parts.append(f"cells clipped {cells_clipped}")
    partial = headings_only or tables_only or tables_cut or cells_clipped
    print(f"\n[COVERAGE: {', '.join(parts)}{', PARTIAL' if partial else ', FULL'}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract text from a DOCX file for KB summarization."
    )
    parser.add_argument("path", help="Path to the DOCX file")
    parser.add_argument(
        "--headings-only",
        action="store_true",
        help="Output only headings (document structure overview)",
    )
    parser.add_argument(
        "--tables-only",
        action="store_true",
        help="Output only table content",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=0,
        help="Maximum rows to show per table; 0 = all (default: 0)",
    )
    parser.add_argument(
        "--max-cell",
        type=int,
        default=0,
        help="Clip each table cell to this many characters; 0 = no clip (default: 0)",
    )
    args = parser.parse_args()

    extract_docx(
        args.path,
        tables_only=args.tables_only,
        headings_only=args.headings_only,
        max_rows=args.max_rows,
        max_cell=args.max_cell,
    )
