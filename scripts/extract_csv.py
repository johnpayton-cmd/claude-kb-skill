"""Extract data from a CSV file for KB summarization.

Usage:
  python extract_csv.py <path>
  python extract_csv.py <path> --headers-only
  python extract_csv.py <path> --columns "Name,Type,Description"
  python extract_csv.py <path> --max-rows 0 --max-cell 0
  python extract_csv.py <path> --delimiter ";"

Workflow:
  1. Run with --headers-only to see all column names before loading full content.
  2. Use --columns to filter to the subset of columns relevant for the summary.
  3. Without flags you get a 50-row preview; --max-rows 0 --max-cell 0 gives everything.
     The COVERAGE line at the end reports whether anything was cut.
  4. Use --delimiter if the file uses semicolons, tabs, or other separators.

Notes:
  - Tab-delimited files: pass --delimiter $'\\t' (bash) or --delimiter "\\t".
  - Uses stdlib csv only, no external dependencies.
  - Encoding is UTF-8 with BOM handling (common in Excel exports).
"""

import sys
import io
import csv
import argparse

# Force stdout to UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def extract_csv(path, columns=None, headers_only=False, max_rows=50, delimiter=",", max_cell=200):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        all_headers = reader.fieldnames or []

        print(f"[CSV: {path}  |  {len(all_headers)} columns]\n")
        print("Columns: " + " | ".join(all_headers))

        if headers_only:
            print("\n[COVERAGE: headers only, PARTIAL]")
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
        shown = total = cells_clipped = 0
        for row in reader:
            total += 1
            if max_rows and shown >= max_rows:
                continue
            values = [row.get(c) or "" for c in keep]
            if max_cell:
                cells_clipped += sum(1 for v in values if len(v) > max_cell)
                values = [v[:max_cell] for v in values]
            print(" | ".join(values))
            shown += 1

        if shown < total:
            print(f"\n  ... ({total - shown} more rows not shown; use --max-rows 0 for all)")
        partial = shown < total or cells_clipped or len(keep) < len(all_headers)
        print(f"\n[COVERAGE: rows {shown}/{total}, columns {len(keep)}/{len(all_headers)}, "
              f"cells clipped {cells_clipped}, {'PARTIAL' if partial else 'FULL'}]")


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
        help="Maximum rows to display; 0 = all (default: 50)",
    )
    parser.add_argument(
        "--max-cell",
        type=int,
        default=200,
        help="Clip each cell to this many characters; 0 = no clip (default: 200)",
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
        max_cell=args.max_cell,
    )
