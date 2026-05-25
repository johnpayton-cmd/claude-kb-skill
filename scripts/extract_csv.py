"""Extract data from a CSV file for KB summarization.

Usage:
  python extract_csv.py <path>
  python extract_csv.py <path> --headers-only
  python extract_csv.py <path> --columns "Name,Type,Description"
  python extract_csv.py <path> --max-rows 30
  python extract_csv.py <path> --delimiter ";"

Workflow:
  1. Run with --headers-only to see all column names before loading full content.
  2. Use --columns to filter to the subset of columns relevant for the summary.
  3. Use --max-rows to control how many rows are shown (default: 50).
  4. Use --delimiter if the file uses semicolons, tabs, or other separators.

Notes:
  - Tab-delimited files: pass --delimiter $'\\t' (bash) or --delimiter "\\t".
  - Uses stdlib csv only — no external dependencies.
  - Encoding is UTF-8 with BOM handling (common in Excel exports).
"""

import sys
import io
import csv
import argparse

# Force stdout to UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def extract_csv(path, columns=None, headers_only=False, max_rows=50, delimiter=","):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        all_headers = reader.fieldnames or []

        print(f"[CSV: {path}  |  {len(all_headers)} columns]\n")
        print("Columns: " + " | ".join(all_headers))

        if headers_only:
            return

        # Determine which columns to emit
        if columns:
            requested = [c.strip() for c in columns.split(",")]
            missing = [c for c in requested if c not in all_headers]
            if missing:
                print(f"Warning: columns not found: {missing}", file=sys.stderr)
            keep = [c for c in requested if c in all_headers]
        else:
            keep = list(all_headers)

        print()
        row_count = 0
        for row in reader:
            values = [row.get(c, "") for c in keep]
            # Truncate individual cell values to prevent runaway output
            values = [v[:200] for v in values]
            print(" | ".join(values))
            row_count += 1
            if row_count >= max_rows:
                print(f"\n  ... (more rows — use --max-rows to see more)")
                break

        print(f"\n[{row_count} rows shown]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract data from a CSV file for KB summarization."
    )
    parser.add_argument("path", help="Path to the CSV file")
    parser.add_argument(
        "--headers-only",
        action="store_true",
        help="Show only column names",
    )
    parser.add_argument(
        "--columns",
        help="Comma-separated list of column names to include (default: all)",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=50,
        help="Maximum rows to display (default: 50)",
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="Field delimiter character (default: ',')",
    )
    args = parser.parse_args()

    extract_csv(
        args.path,
        columns=args.columns,
        headers_only=args.headers_only,
        max_rows=args.max_rows,
        delimiter=args.delimiter,
    )
