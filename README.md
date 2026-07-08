# claude-kb-skill

A [Claude Code](https://claude.ai/code) skill for building and maintaining a local knowledgebase of curated reference summaries. Works with any domain — security, legal, finance, coding standards, or anything you summarize from PDFs, Word documents, spreadsheets, or Markdown files.

## What it does

- **Organizes** reference documents into sub-KBs (topic folders), each with an index and source files
- **Extracts** text from PDFs, DOCX, XLSX, HTML pages, CSV files, and Markdown using bundled scripts
- **Summarizes** source documents into structured, searchable summary files
- **Indexes** everything so you can search by topic across all sub-KBs
- **Tracks** batch status so you know what's been added and when
- **Reviews** sub-KBs for staleness and produces tiered update plans
- **Consults proactively** — an optional hook makes Claude check the KB before answering from training data, without you typing `/kb` (see [Proactive consultation](#proactive-consultation))

## Installation

1. Copy this directory to `~/.claude/skills/kb/`
2. Run `/kb init` — this sets up (or points to) your knowledgebase location **and offers to install the proactive-consultation hook** (confirmation-gated). Running any action command (e.g. `/kb list`) also walks you through creation if no knowledgebase exists yet. `/kb` alone always shows usage regardless of KB state.
3. *(Optional)* Add a one-line pointer to the skill in your `CLAUDE.md` if you like — it is **not** required for the skill to work or to consult the KB; proactive consultation is driven by the hook, not by `CLAUDE.md`.

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

> **Note on HTML export:** `/kb export --format html` produces a deliberately minimal,
> self-contained HTML file. A richer, branded multi-page HTML "hub" generator
> is intentionally kept private (an Invictrix-specific feature) and is **not** part of
> this repository. The public skill is complete without it.
>
> `/kb export all` skips any sub-KB listed in the `export_exclude` array of `config.json`,
> so internal sub-KBs stay out of bulk exports (they remain exportable when named explicitly).

## Proactive consultation

A skill's description makes it *available* and routes explicit `/kb` calls, but it does **not**
reliably make Claude consult the KB *proactively* on an ordinary question. That behavior is
delivered by a `UserPromptSubmit` hook (`hooks/kb-consult-hook.py`) whose output is injected into
context each turn — the same mechanism as a standing `CLAUDE.md` instruction, which is what makes
it reliable.

Already have an install from before the hook existed? See [UPGRADING.md](UPGRADING.md) for the
update + hook-install steps.

`/kb init` offers to install the hook for you (and any `/kb` command will offer it if it sees a
knowledgebase but no hook). The hook is **conditional**: it emits the "consult the KB first"
mandate only when a knowledgebase is resolvable, and stays silent otherwise, so it adds nothing
to sessions with no KB. To install it manually, add this to `~/.claude/settings.json` (adjust the
path; use `python3` on macOS/Linux):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "python \"~/.claude/skills/kb/hooks/kb-consult-hook.py\"" } ] }
    ]
  }
}
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

> **Note:** `/kb add <url>` and `extract_html.py` fetch the URL you provide. Fetching is
> limited to `http`/`https` and blocks loopback/link-local/metadata hosts, but it is not a
> hardened proxy — use it only with trusted, public source documents.

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
