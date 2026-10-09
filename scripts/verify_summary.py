"""Check that every identifier and number in a KB summary appears in its source extract.

Usage:
  python verify_summary.py <summary.md> <extract.txt> [<extract2.txt> ...] [--ignore TOKEN ...]

What it checks:
  - Control-style identifiers such as AC-11, AC-11(1), SC-7(4), NTC-0013
  - Numbers of two or more digits, decimals, and percentages (20%, 157, 1.7, 2024)
Each token found in the summary body (front-matter is skipped) must appear in at least
one extract file. Tokens that do not are listed with their summary line numbers.

It reports only; it never edits. A hit is not always an error (a number derived by
counting, one taken from a second cited source, or a DOCX heading number that Word
generates and python-docx does not extract), so each hit needs a human or model
decision: fix the summary, or confirm the token and pass it with --ignore. It cannot
catch wording drift ("will not consider" vs "consult the PMO"); that needs a read
against the source.

Exit code: 0 = no unsupported tokens, 1 = unsupported tokens found, 2 = usage error.
Stdlib only.
"""

import sys
import io
import re
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ID_RE = re.compile(r"\b[A-Z]{2,5}-\d+(?:\s?\(\d+\))*")
NUM_RE = re.compile(r"(?<![\w.-])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(%?)(?![\w])")


def _norm_id(token):
    return re.sub(r"\s+\(", "(", token)


def _body_lines(text):
    """Return (line_number, line) pairs after any YAML front-matter block."""
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    return [(n + 1, lines[n]) for n in range(start, len(lines))]


def _tokens(line):
    found = []
    id_spans = []
    for m in ID_RE.finditer(line):
        found.append(("id", _norm_id(m.group(0))))
        id_spans.append(m.span())
    for m in NUM_RE.finditer(line):
        if any(a <= m.start() < b for a, b in id_spans):
            continue
        digits = m.group(1).replace(",", "")
        if len(digits.replace(".", "")) < 2 and not m.group(2):
            continue  # single digits are too common to check usefully
        found.append(("num", digits))
    return found


def _present(kind, token, source):
    if kind == "id":
        # AC-11 must not match AC-110; AC-11 does match inside AC-11(1)
        pattern = re.escape(token) + r"(?!\d)"
        return re.search(pattern, source) is not None
    pattern = r"(?<![\d.])" + re.escape(token) + r"(?![\d])"
    return re.search(pattern, source) is not None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("summary")
    parser.add_argument("extracts", nargs="+")
    parser.add_argument("--ignore", nargs="*", default=[],
                        help="Tokens confirmed as supported (e.g. derived counts)")
    args = parser.parse_args()

    try:
        with open(args.summary, encoding="utf-8") as f:
            summary = f.read()
        source = ""
        for path in args.extracts:
            with open(path, encoding="utf-8", errors="replace") as f:
                source += f.read() + "\n"
    except OSError as e:
        print(f"verify_summary.py: {e}", file=sys.stderr)
        sys.exit(2)

    # Normalize the extract the same way as the summary tokens
    source = re.sub(r"(?<=\d)\s+\(", "(", source)
    source = re.sub(r"(?<=\d),(?=\d{3}\b)", "", source)
    ignore = {_norm_id(t).replace(",", "") for t in args.ignore}

    missing = {}
    checked = set()
    for n, line in _body_lines(summary):
        for kind, token in _tokens(line):
            checked.add(token)
            if token in ignore or _present(kind, token, source):
                continue
            lines = missing.setdefault((kind, token), [])
            if n not in lines:
                lines.append(n)

    print(f"[verify_summary: {len(checked)} distinct tokens checked against "
          f"{len(args.extracts)} extract file(s)]")
    if not missing:
        print("No unsupported identifiers or numbers.")
        sys.exit(0)
    print(f"{len(missing)} token(s) not found in the extract:")
    for (kind, token), lines in sorted(missing.items(), key=lambda kv: kv[1][0]):
        label = "ID " if kind == "id" else "NUM"
        print(f"  {label} {token:<16} summary line(s) {', '.join(map(str, lines))}")
    sys.exit(1)


if __name__ == "__main__":
    main()
