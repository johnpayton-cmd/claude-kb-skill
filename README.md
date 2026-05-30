# claude-kb-skill

A [Claude Code](https://claude.ai/code) skill for building and maintaining a local knowledgebase of curated reference summaries. Works with any domain — security, legal, finance, coding standards, or anything you summarize from PDFs, Word documents, spreadsheets, or Markdown files.

## What it does

- **Organizes** reference documents into sub-KBs (topic folders), each with an index and source files
- **Extracts** text from PDFs, DOCX, XLSX, HTML pages, CSV files, and Markdown using bundled scripts
- **Summarizes** source documents into structured, searchable summary files
- **Indexes** everything so you can search by topic across all sub-KBs
- **Tracks** batch status so you know what's been added and when
- **Reviews** sub-KBs for staleness and produces tiered update plans

## Installation

1. Copy this directory to `~/.claude/skills/kb/`
2. In your `CLAUDE.md`, add:
   ```
   ### kb (~/.claude/skills/kb/)
   Knowledgebase navigation and maintenance skill. Invoke with /kb.
   ```
3. Run any action command (e.g. `/kb list`) — if no knowledgebase exists yet, you'll be walked through creating one. Run `/kb init` to set it up explicitly. `/kb` alone always shows usage regardless of KB state.

## Commands

```
/kb                                               Show this command reference
/kb list                                          List all sub-KBs with document counts
/kb list <sub-kb>                                 List all summaries in a sub-KB
/kb search <topic> [--tag <tag>]                  Find relevant documents across all sub-KBs
/kb add <sub-kb> <file>                           Add a new source document (full pipeline)
/kb update <sub-kb> [doc]                         Refresh an existing summary
/kb review <sub-kb>                               Audit for staleness; produce a staged update plan
/kb validate [sub-kb]                             Check structural integrity (read-only)
/kb export [sub-kb] [--format md|html] [--tag T]  Render to a merged output file
/kb status                                        Show batch status across all sub-KBs
/kb new <name>                                    Scaffold a new sub-KB
/kb init                                          Set or change the knowledgebase location
/kb help                                          Show this command reference
```

## Knowledgebase structure

```
knowledgebase/
├── BATCH_STATUS.md          # Tracks all batches across sub-KBs
├── security/                # Example sub-KB
│   ├── INDEX.md             # Document index and quick-lookup table
│   ├── _source/             # Original source files (PDFs, DOCX, XLSX)
│   └── summary_*.md         # One summary per source document
└── coding/                  # Another sub-KB
    ├── INDEX.md
    ├── _source/
    └── summary_*.md
```

Sub-KBs are discovered dynamically — any subdirectory containing an `INDEX.md` is recognized as a sub-KB. You can have as many as you need.

## Discovery

The skill finds your knowledgebase in this order:

1. `knowledgebase/` in the current working directory
2. `knowledgebase/` one level up (for running inside a project subfolder)
3. Path in `.kb-config.json` in the current working directory (per-project override)
4. Path stored in `~/.claude/skills/kb/config.json` (global fallback)
5. If none found: prompts to create one

## Scripts

| Script | Purpose | Usage |
|---|---|---|
| `extract_pdf.py` | Extract text from a PDF by page range | `uv run --python 3.12 --with pymupdf extract_pdf.py <path> [start] [end]` |
| `extract_docx.py` | Extract text and tables from a DOCX file | `uv run --python 3.12 --with python-docx extract_docx.py <path> [--headings-only] [--max-rows N]` |
| `extract_xlsx.py` | Extract data from any XLSX spreadsheet | `uv run --python 3.12 --with openpyxl extract_xlsx.py <path> [--sheet Name] [--headers-only] [--max-rows N]` |
| `extract_html.py` | Extract readable text from a URL or local HTML file | `uv run --python 3.12 --with requests --with beautifulsoup4 extract_html.py <url-or-path> [--selector CSS] [--headings-only] [--max-chars N]` |
| `extract_csv.py` | Extract data from a CSV file (no extra deps) | `python extract_csv.py <path> [--columns A,B] [--headers-only] [--max-rows N] [--delimiter C]` |

### Domain-specific scripts

The `examples/domain-specific/` directory contains scripts for specific document formats that require custom parsing logic. See `examples/domain-specific/README.md` for details.

## Dependencies

Scripts use [`uv`](https://github.com/astral-sh/uv) for isolated dependency management. Key libraries:

- `pymupdf` (fitz) — PDF extraction
- `python-docx` — DOCX extraction
- `openpyxl` — XLSX extraction
- `requests` + `beautifulsoup4` — HTML extraction
- CSV extraction uses the Python standard library only — no install needed

Install `uv` once: `pip install uv`

## License

MIT
