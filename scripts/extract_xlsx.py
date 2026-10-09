"""Extract data from an XLSX file for KB summarization.

Usage:
  uv run --python 3.12 --with openpyxl extract_xlsx.py <path>
  uv run --python 3.12 --with openpyxl extract_xlsx.py <path> --sheet Sheet1
  uv run --python 3.12 --with openpyxl extract_xlsx.py <path> --headers-only
  uv run --python 3.12 --with openpyxl extract_xlsx.py <path> --max-rows 0 --max-cell 0

Workflow:
  1. Run without flags to see all sheet names and a 50-row preview of each.
  2. Use --sheet to focus on a specific sheet.
  3. Use --headers-only to inspect column structure before extracting full content.
  4. For a full extract use --max-rows 0 --max-cell 0 (all rows, unclipped cells).
     The COVERAGE line at the end reports whether anything was cut.
"""

import sys
import io
import argparse
import openpyxl

# Force stdout to UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def extract_xlsx(path, sheet_name=None, headers_only=False, max_rows=50, max_cell=200):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet_names = wb.sheetnames
    print(f"Sheets ({len(sheet_names)}): {', '.join(sheet_names)}\n")

    target_sheets = [sheet_name] if sheet_name else sheet_names
    coverage = []
    cells_clipped = 0
    partial = headers_only

    for name in target_sheets:
        if name not in sheet_names:
            print(f"Sheet '{name}' not found. Available: {', '.join(sheet_names)}", file=sys.stderr)
            continue

        ws = wb[name]
        print(f"=== {name} ===")

        headers = None
        shown = total = 0
        for row in ws.iter_rows(values_only=True):
            cells = [str(c).strip() if c is not None else "" for c in row]
            if not any(cells):
                continue
            if headers is None:
                headers = cells
                print("Headers: " + " | ".join(headers))
                if headers_only:
                    break
                continue
            total += 1
            if max_rows and shown >= max_rows:
                continue
            for c in cells:
                if max_cell and len(c) > max_cell:
                    cells_clipped += 1
            print(" | ".join(c[:max_cell] if max_cell else c for c in cells))
            shown += 1

        if shown < total:
            print(f"  ... ({total - shown} more rows not shown; use --max-rows 0 for all)")
            partial = True
        if not headers_only:
            coverage.append(f"{name} {shown}/{total}")
        print()

    wb.close()
    if cells_clipped:
        partial = True
    rows = "; ".join(coverage) if coverage else "headers only"
    print(f"[COVERAGE: sheets {len(target_sheets)}/{len(sheet_names)}, rows {rows}, "
          f"cells clipped {cells_clipped}, {'PARTIAL' if partial else 'FULL'}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract data from an XLSX file for KB summarization."
    )
    parser.add_argument("path", help="Path to the XLSX file")
    parser.add_argument("--sheet", help="Extract only this sheet (default: all sheets)")
    parser.add_argument(
        "--headers-only",
        action="store_true",
        help="Show only column headers per sheet",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=50,
        help="Maximum rows to show per sheet; 0 = all (default: 50)",
    )
    parser.add_argument(
        "--max-cell",
        type=int,
        default=200,
        help="Clip each cell to this many characters; 0 = no clip (default: 200)",
    )
    args = parser.parse_args()

    extract_xlsx(
        args.path,
        sheet_name=args.sheet,
        headers_only=args.headers_only,
        max_rows=args.max_rows,
        max_cell=args.max_cell,
    )
