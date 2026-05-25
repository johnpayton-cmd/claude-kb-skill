"""Extract readable text from an HTML page or local HTML file for KB summarization.

Usage:
  uv run --python 3.12 --with requests --with beautifulsoup4 extract_html.py <url-or-path>
  uv run --python 3.12 --with requests --with beautifulsoup4 extract_html.py <url> --selector "article.main"
  uv run --python 3.12 --with requests --with beautifulsoup4 extract_html.py <url> --headings-only
  uv run --python 3.12 --with requests --with beautifulsoup4 extract_html.py <url> --max-chars 40000

Workflow:
  1. Run with --headings-only first to see document structure (h1–h3 tags).
  2. Run without flags to extract all visible text from the page body.
  3. Use --selector to target a specific element (e.g., main content div) and cut noise.
  4. Use --max-chars to control output size for large pages.

Notes:
  - Accepts either a URL (http/https) or a local file path.
  - Script/style/nav/header/footer content is stripped automatically.
  - For pages requiring JavaScript rendering, save the rendered HTML locally first.
"""

import sys
import io
import argparse
import re

# Force stdout to UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _get_html(source):
    """Return raw HTML from a URL or local file path."""
    if source.startswith("http://") or source.startswith("https://"):
        import requests
        resp = requests.get(source, timeout=30, headers={"User-Agent": "Mozilla/5.0 (KB-extractor)"})
        resp.raise_for_status()
        return resp.text, source
    else:
        with open(source, encoding="utf-8", errors="replace") as f:
            return f.read(), source


def extract_html(source, selector=None, headings_only=False, max_chars=80000):
    from bs4 import BeautifulSoup

    html, label = _get_html(source)
    soup = BeautifulSoup(html, "html.parser")

    # Remove clutter elements before any extraction
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "iframe"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else "(no title)"
    print(f"[HTML: {label}  |  Title: {title}]\n")

    # Narrow scope if selector given
    root = soup.select_one(selector) if selector else soup.body or soup
    if selector and root is None:
        print(f"Selector '{selector}' matched nothing — falling back to full body.", file=sys.stderr)
        root = soup.body or soup

    if headings_only:
        headings = root.find_all(re.compile(r"^h[1-3]$"))
        for h in headings:
            level = int(h.name[1])
            print("  " * (level - 1) + h.get_text(strip=True))
        return

    # Full text extraction: walk block elements, emit line-separated text
    chunks = []
    chars = 0
    for el in root.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6",
                              "td", "th", "pre", "blockquote", "dt", "dd"]):
        text = el.get_text(separator=" ", strip=True)
        if not text:
            continue
        line = f"{text}\n"
        if chars + len(line) > max_chars:
            chunks.append(f"\n[Truncated at {chars} chars — use --max-chars to extend]\n")
            break
        chunks.append(line)
        chars += len(line)

    print("".join(chunks))
    print(f"\n[{chars} chars extracted]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract readable text from an HTML page or local HTML file."
    )
    parser.add_argument("source", help="URL (http/https) or local file path to HTML")
    parser.add_argument(
        "--selector",
        help="CSS selector to scope extraction (e.g. 'article', 'div.content')",
    )
    parser.add_argument(
        "--headings-only",
        action="store_true",
        help="Output only h1–h3 headings (document structure overview)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=80000,
        help="Maximum characters to extract (default: 80000)",
    )
    args = parser.parse_args()

    extract_html(
        args.source,
        selector=args.selector,
        headings_only=args.headings_only,
        max_chars=args.max_chars,
    )
