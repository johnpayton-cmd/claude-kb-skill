"""Extract text from a PDF, optionally limited to a page range."""
import sys
import io
import fitz  # PyMuPDF

# Force stdout to UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def extract(path, start=0, end=None, max_chars=80000):
    doc = fitz.open(path)
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
    path = sys.argv[1]
    start = int(sys.argv[2]) - 1 if len(sys.argv) > 2 else 0
    end = int(sys.argv[3]) if len(sys.argv) > 3 else None
    extract(path, start, end)
