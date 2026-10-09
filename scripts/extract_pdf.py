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
    last_read = start  # 1-based number of the last page fully read
    for i in range(start, end):
        text = doc[i].get_text()
        if chars + len(text) > max_chars:
            chunks.append(f"\n[Truncated before page {i+1}: {chars} chars extracted. "
                          f"Continue with start_page {i+1}]\n")
            break
        chunks.append(f"\n--- Page {i+1} ---\n{text}")
        chars += len(text)
        last_read = i + 1
    doc.close()
    read = f"{start+1}-{last_read}" if last_read > start else "none"
    print(f"[PDF: {path}  |  Pages {read} of {total}  |  {chars} chars]\n")
    print("".join(chunks))
    partial = last_read < end or start > 0 or end < total
    note = ", TRUNCATED by char limit" if last_read < end else ""
    print(f"\n[COVERAGE: pages {read} of {total} read{note}, "
          f"{'PARTIAL' if partial else 'FULL'}]")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        _die(USAGE)
    path = sys.argv[1]
    start = _int_arg(sys.argv[2], "start_page") - 1 if len(sys.argv) > 2 else 0
    end = _int_arg(sys.argv[3], "end_page") if len(sys.argv) > 3 else None
    extract(path, start, end)
