# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Contact: [contact@invictrix.com](mailto:contact@invictrix.com)

Include in your report:
- A description of the vulnerability and its potential impact
- Steps to reproduce or proof-of-concept
- Any suggested remediation if known

## Response

This is a solo-maintained open source project. I will review reports and respond on a best-effort basis. There is no guaranteed response SLA. I appreciate your patience and your responsible disclosure.

## Usage caveat — `/kb add <url>`

The `add` pipeline and `extract_html.py` fetch whatever URL they are given. Fetching is
restricted to `http`/`https` and blocks loopback/link-local/cloud-metadata hosts as a
lightweight SSRF guard, but it is **not** a hardened proxy. Run `/kb add <url>` only against
**trusted, public source documents** — treat an untrusted URL the same as any untrusted
input.

## Scope

This policy applies to the `claude-kb-skill` repository. Vulnerabilities in upstream dependencies (pymupdf, python-docx, openpyxl) should be reported to their respective maintainers.
