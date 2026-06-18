"""Extract text from a PDF, optionally limited to a page range.

Usage:
  uv run --python 3.12 --with pymupdf extract_pdf.py <path> [start_page] [end_page]
"""
import sys
import io
import fitz  # PyMuPDF

# Force stdout to UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

USAGE = "Usage: extract_pdf.py <path> [start_page] [end_page]"


def _die(msg, code=2):
    print(f"extract_pdf.py: {msg}", file=sys.stderr)
    sys.exit(code)


def _int_arg(value, name):
    try:
        return int(value)
    except ValueError:
        _die(f"{name} must be an integer (got {value!r})")

def extract(path, start=0, end=None, max_chars=80000):
    try:
        doc = fitz.open(path)
    except Exception as e:
        _die(f"could not open PDF {path!r}: {e}", code=1)
    total = len(doc)
    if end is None:
        end = total
    end = min(end, total)
    chunks = []
    chars = 0
    for i in range(start, end):
        text = doc[i].get_text()
        if chars + len(text) > max_chars:
            chunks.append(f"\n[Truncated at page {i+1} of {total} — {chars} chars extracted]\n")
            break
        chunks.append(f"\n--- Page {i+1} ---\n{text}")
        chars += len(text)
    doc.close()
    print(f"[PDF: {path}  |  Pages {start+1}–{end} of {total}  |  {chars} chars]\n")
    print("".join(chunks))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        _die(USAGE)
    path = sys.argv[1]
    start = _int_arg(sys.argv[2], "start_page") - 1 if len(sys.argv) > 2 else 0
    end = _int_arg(sys.argv[3], "end_page") if len(sys.argv) > 3 else None
    extract(path, start, end)
