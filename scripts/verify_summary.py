"""Check that every identifier and number in a KB summary appears in its source extract.

Usage:
  python verify_summary.py <summary.md> <extract.txt> [<extract2.txt> ...] [--ignore TOKEN ...]

What it checks:
  - Control-style identifiers such as AC-11, AC-11(1), SC-7(4), NTC-0013. Zero padding
    is ignored on both sides, so AC-5 matches a source's AC-05 and AC-2(2) matches AC-02 (02)
  - ISO dates (2027-01-01) as whole dates; the source may write them ISO, "January 1, 2027"
    or "1/1/2027"
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
DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
NUM_RE = re.compile(r"(?<![\w.-])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(%?)(?![\w])")
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def _norm_id(token):
    token = re.sub(r"\s+\(", "(", token)
    token = re.sub(r"-0+(?=\d)", "-", token)
    return re.sub(r"\(0+(?=\d)", "(", token)


def _date_forms(iso):
    y, m, d = iso.split("-")
    mi, di = int(m), int(d)
    if not 1 <= mi <= 12:
        return [iso]
    return [iso, f"{MONTHS[mi - 1]} {di}, {y}", f"{mi}/{di}/{y}", f"{m}/{d}/{y}"]


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
    spans = []
    for m in ID_RE.finditer(line):
        found.append(("id", _norm_id(m.group(0))))
        spans.append(m.span())
    for m in DATE_RE.finditer(line):
        found.append(("date", m.group(0)))
        spans.append(m.span())
    for m in NUM_RE.finditer(line):
        if any(a <= m.start() < b for a, b in spans):
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
    if kind == "date":
        return any(re.search(r"(?<!\d)" + re.escape(f) + r"(?!\d)", source)
                   for f in _date_forms(token))
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
    source = re.sub(r"\b([A-Z]{2,5})-0+(?=\d)", r"\1-", source)  # AC-05 -> AC-5
    source = re.sub(r"(?<=[\d)])\(0+(?=\d)", "(", source)        # AC-2(02) -> AC-2(2)
    source = re.sub(r"(?<=\d),(?=\d{3}\b)", "", source)
    ignore = {_norm_id(t) if ID_RE.fullmatch(t) else t.replace(",", "")
              for t in args.ignore}

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
        label = {"id": "ID  ", "date": "DATE", "num": "NUM "}[kind]
        print(f"  {label} {token:<16} summary line(s) {', '.join(map(str, lines))}")
    sys.exit(1)


if __name__ == "__main__":
    main()
