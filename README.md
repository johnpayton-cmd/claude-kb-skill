# claude-kb-skill

A [Claude Code](https://claude.ai/code) skill for building and maintaining a local knowledgebase of curated reference summaries. Works with any domain — security, legal, finance, coding standards, or anything you summarize from PDFs, Word documents, spreadsheets, or Markdown files.

## What it does

- **Organizes** reference documents into sub-KBs (topic folders), each with an index and source files
- **Extracts** text from PDFs, DOCX, XLSX, and Markdown files using bundled scripts
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
3. Run `/kb` in Claude Code — if no knowledgebase exists yet, the skill will walk you through creating one.

## Commands

```
/kb                        Show this command reference
/kb list                   List all sub-KBs with document counts
/kb list <sub-kb>          List all summaries in a sub-KB
/kb search <topic>         Find relevant documents across all sub-KBs
/kb add <sub-kb> <file>    Add a new source document (full pipeline)
/kb update <sub-kb> [doc]  Refresh an existing summary
/kb review <sub-kb>        Audit for staleness; produce a staged update plan
/kb status                 Show batch status across all sub-KBs
/kb new <name>             Scaffold a new sub-KB
/kb init                   Set or change the knowledgebase location
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
3. Path stored in `~/.claude/skills/kb/config.json`
4. If none found: prompts to create one

## Scripts

| Script | Purpose | Usage |
|---|---|---|
| `extract_pdf.py` | Extract text from a PDF by page range | `uv run --python 3.12 --with pymupdf extract_pdf.py <path> [start] [end]` |
| `extract_docx.py` | Extract text and tables from a DOCX file | `uv run --python 3.12 --with python-docx extract_docx.py <path> [--headings-only] [--max-rows N]` |
| `extract_xlsx.py` | Extract data from any XLSX spreadsheet | `uv run --python 3.12 --with openpyxl extract_xlsx.py <path> [--sheet Name] [--headers-only] [--max-rows N]` |

### Domain-specific scripts

The `examples/domain-specific/` directory contains scripts for specific document formats that require custom parsing logic. See `examples/domain-specific/README.md` for details.

## Dependencies

Scripts use [`uv`](https://github.com/astral-sh/uv) for isolated dependency management. Key libraries:

- `pymupdf` (fitz) — PDF extraction
- `python-docx` — DOCX extraction
- `openpyxl` — XLSX extraction

Install `uv` once: `pip install uv`

## License

MIT
