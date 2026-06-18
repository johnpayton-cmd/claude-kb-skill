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


# Hosts that must never be fetched — loopback, link-local, and cloud metadata.
# Lightweight SSRF guard appropriate for a human-driven local tool, not a full proxy.
_BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "169.254.169.254",          # AWS/GCP/Azure instance metadata
    "metadata.google.internal",
}


def _check_url_host(url):
    """Reject obviously-internal hosts before any network request is made."""
    from urllib.parse import urlparse
    host = (urlparse(url).hostname or "").lower()
    if host in _BLOCKED_HOSTS or host.startswith("127.") or host.startswith("169.254."):
        raise ValueError(
            f"Refusing to fetch internal/link-local host: {host!r}. "
            "extract_html.py only fetches public web pages."
        )


def _get_html(source):
    """Return raw HTML from a URL or local file path."""
    if source.startswith("http://") or source.startswith("https://"):
        import requests
        _check_url_host(source)
        resp = requests.get(source, timeout=30, headers={"User-Agent": "Mozilla/5.0 (KB-extractor)"})
        resp.raise_for_status()
        return resp.text, source
    elif re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", source):
        # Has a URL scheme that isn't http/https (file:, ftp:, gopher:, …) — reject
        # explicitly rather than silently treating it as a local path. Windows paths
        # like C:\ or C:/ have no '://' and correctly fall through to the file branch.
        raise ValueError(
            f"Unsupported URL scheme in {source!r}. Use http(s):// or a local file path."
        )
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

    try:
        extract_html(
            args.source,
            selector=args.selector,
            headings_only=args.headings_only,
            max_chars=args.max_chars,
        )
    except (ValueError, OSError) as e:
        print(f"extract_html.py: {e}", file=sys.stderr)
        sys.exit(2)
