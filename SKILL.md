---
name: kb
description: >
  Use this skill when the user types /kb or any subcommand (/kb list, /kb search,
  /kb add, /kb update, /kb status, /kb new, /kb review). Also invoke proactively
  when the user asks about a topic covered by a local knowledgebase sub-folder,
  references a framework or standard that may be in the KB (NIST, FedRAMP, OWASP,
  MITRE ATT&CK, CIS, ISO, PCI DSS, CMMC, FISMA, RMF, etc.), or when CLAUDE.md
  directs consulting the KB before answering. Handles: KB navigation, document
  lookup, adding new source documents (full extract → summarize → index pipeline),
  updating existing summaries, reviewing a sub-KB for staleness and planning staged
  updates, status tracking, and scaffolding new sub-KBs.
argument-hint: [list|search|add|update|review|status|new] [sub-kb] [args...]
---

# KB Skill — Knowledgebase Navigation and Maintenance

This skill manages a local knowledgebase of curated reference summaries. The
knowledgebase lives in a `knowledgebase/` folder at the workspace root. Each
subdirectory inside it that contains an `INDEX.md` is a sub-KB. Any number of
sub-KBs are supported — security, coding, legal, finance, or any domain.

## Discovery

On every command **except `/kb` bare (no args)**, resolve the knowledgebase root using this priority order:

1. **CWD check:** Look for `knowledgebase/` in the current working directory
2. **Parent check:** If not found, look one level up (covers running from inside a project subfolder)
3. **Workspace config check:** If still not found, look for `.kb-config.json` in the current working directory. If it exists and contains a `knowledgebase_path` key pointing to an existing directory, use that path. This enables per-project overrides without touching the global config — useful when the same machine has multiple independent workspaces.
4. **Global config check:** If still not found, read `~/.claude/skills/kb/config.json`. If it contains a `knowledgebase_path` key pointing to an existing directory, use that path. (The stored path always ends with `/knowledgebase`.)
5. **Initialization:** If no knowledgebase is found by any of the above, run the Initialization Flow (see below).

Local discovery (steps 1–2) always takes priority over config files. Workspace config (step 3) takes priority over global config (step 4). This lets different workspaces maintain independent knowledgebases while the global config acts as a fallback.

Once the path is resolved, use it as the **absolute base** for all file operations in the session.

List sub-KBs by enumerating subdirectories of the resolved root that contain an `INDEX.md` file. Do not hardcode sub-KB names — discover them dynamically.

---

## Initialization Flow

Triggered automatically when no `knowledgebase/` folder is found via Discovery steps 1–3. Also triggered by `/kb init`.

The user chooses the **parent directory**. The skill always creates a folder named exactly `knowledgebase/` inside it — the name is not configurable.

1. Inform the user that no knowledgebase was found.
2. Propose the **default parent directory**: the current working directory. Show the full absolute path (e.g., `C:\Users\john_\ClaudeWork`) so the user sees exactly where `knowledgebase/` will be created.
3. Ask: "Create `knowledgebase/` inside `<CWD>`, or enter a different parent directory?" Wait for the user's response before doing anything.
4. **Validate the parent directory path** before proceeding:
   - Must be an absolute path. On Windows: starts with a drive letter (`C:\`, `D:\`) or UNC (`\\`). On macOS/Linux: starts with `/`.
   - If the user entered a relative path (e.g., `../somewhere`, `.\kb`, `knowledgebase`), reject it and re-prompt: "That looks like a relative path. Please enter an absolute path (e.g., `C:\Users\alice\ClaudeWork`)."
   - Keep re-prompting until an absolute path is provided or the user cancels.
5. Using the confirmed, validated parent directory:
   a. Create `<parent>/knowledgebase/`
   b. Create a minimal `<parent>/knowledgebase/BATCH_STATUS.md` with a placeholder header.
6. Store the resolved path in `~/.claude/skills/kb/config.json`:
   ```json
   {"knowledgebase_path": "<parent>/knowledgebase"}
   ```
7. **Check dependencies** — run each check and report results:

   | Dependency | Check command | Used by |
   |---|---|---|
   | Python 3.x | `python --version` | all scripts |
   | uv | `uv --version` | recommended script runner |
   | pymupdf | `python -c "import fitz"` | `extract_pdf.py` |
   | python-docx | `python -c "import docx"` | `extract_docx.py` |
   | openpyxl | `python -c "import openpyxl"` | `extract_xlsx.py` |
   | requests | `python -c "import requests"` | `extract_html.py` |
   | beautifulsoup4 | `python -c "import bs4"` | `extract_html.py` |

   Print a report:
   ```
   Dependency check:
     ✓ Python 3.12.3
     ✓ uv 0.4.2
     ✓ pymupdf
     ✗ python-docx   → pip install python-docx
     ✓ openpyxl
     ✗ requests      → pip install requests
     ✗ beautifulsoup4 → pip install beautifulsoup4
   ```
   Missing dependencies do not block initialization — they are only needed when using the relevant extractor. If anything is missing, note: "Install missing packages before using those extractors."

8. Confirm: "Knowledgebase created at `<parent>/knowledgebase`. Create your first sub-KB with `/kb new <name>`."

**Config file:** `~/.claude/skills/kb/config.json`
```json
{"knowledgebase_path": "/absolute/path/to/knowledgebase"}
```
The path always ends with `/knowledgebase`. To change it: run `/kb init` or edit the file directly.

## Commands

### `/kb` — Show usage

Print this command reference. Do not run discovery, initialization, or any file operations. This command always works regardless of whether a knowledgebase exists.

```
Usage: /kb <command> [args]

  list                          List all sub-KBs with document counts
  list <sub-kb>                 List all summaries in a sub-KB
  search <topic> [--tag <tag>]  Find relevant documents across all sub-KBs
  add <sub-kb> <file>           Add a new source document (full pipeline)
  update <sub-kb> [doc]         Refresh an existing summary
  review <sub-kb>               Audit for staleness; produce a staged update plan
  validate [sub-kb]             Check structural integrity (read-only)
  export [sub-kb] [--format md|html] [--tag <tag>]  Render to merged output file
  status                        Show BATCH_STATUS.md
  new <name>                    Scaffold a new sub-KB
  init                          Set or change the knowledgebase location
  help                          Show this command reference
```

---

### `/kb help`

Alias for bare `/kb`. Print the command reference above. No discovery, no file operations.

---

### `/kb list [sub-kb]`

**No argument:** Read each sub-KB's INDEX.md, count summary files (files matching
`summary_*.md`), and print a table:

```
sub-kb      docs  index
----------  ----  -----
security      56  ✓
coding        18  ✓
```

The `docs` count reflects `summary_*.md` files only. Verbatim subfolder content (e.g. the
20 `800-53a-procedures/*.md` files in the security KB) is catalogued separately in INDEX.md
and is not included in this count — so `security = 56` is expected and correct.

**With sub-KB name:** Read `knowledgebase/<sub-kb>/INDEX.md` and print the document
list from it. If INDEX.md doesn't exist, list `summary_*.md` files directly.

---

### `/kb search <topic>`

1. Read `knowledgebase/BATCH_STATUS.md` (if it exists) for context on what's in the KB
2. Read the INDEX.md for every sub-KB
3. Surface the most relevant documents for the topic with their file paths
4. If the user then needs the content, read the specific summary file

---

### `/kb add <sub-kb> <source-path>`

Full pipeline for adding a new source document to a sub-KB. Steps:

1. **Verify** the sub-KB exists (`knowledgebase/<sub-kb>/`). If not, ask whether to create it first.
2. **Resolve source:** If `<source-path>` starts with `http://` or `https://`, download the file before doing anything else:
   - Detect the file type from the URL extension (`.pdf`, `.docx`, `.xlsx`, `.csv`) or the HTTP `Content-Type` response header.
   - Download to `knowledgebase/<sub-kb>/_source/<filename>` (derive filename from the URL path; add a datestamp if the name is ambiguous).
   - Use the downloaded local file as `<source-path>` for all subsequent steps.
   - If the URL has no recognizable document extension and `Content-Type` is `text/html`, treat it as an HTML page and use `extract_html.py` instead.
   - Only `http`/`https` URLs are fetched. Do not download from internal/link-local hosts (`localhost`, `127.0.0.0/8`, `169.254.169.254`, cloud metadata endpoints) — `/kb add <url>` is for public source documents from trusted origins.
   - Download command: `python -c "import urllib.request,sys; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])" <url> <dest-path>`
3. **Determine document type:**
   - PDF → use `extract_pdf.py` (in this skill's `scripts/` folder) to extract text
   - DOCX → use `extract_docx.py` (in this skill's `scripts/` folder) to extract text
   - Markdown/text → read directly
   - Excel/XLSX → use `extract_xlsx.py` (in this skill's `scripts/` folder) to extract data
   - HTML file or HTML URL → use `extract_html.py` (in this skill's `scripts/` folder) to extract text
   - CSV → use `extract_csv.py` (in this skill's `scripts/` folder) to extract data
4. **Extract text** — for PDFs, extract in sections (respect the 80,000 char limit in extract_pdf.py). Read the TOC page(s) first to identify structure, then extract relevant sections. For DOCX, run with `--headings-only` first to map structure, then run without flags for full content.
5. **Draft summary** — follow the standard summary format (see `references/kb-structure.md`). Every newly added summary must include the full YAML front-matter block (the pipeline below computes the checksum in step 8):
   - YAML front-matter block (required for new docs): `source_file`, `version`, `date_added`, `last_updated`, `tags`, `checksum_sha256`
   - Title + one-line hook
   - Purpose, Scope, Key Sections, Critical Controls/Requirements
   - Workspace Relevance
   - File should be named `summary_<name>.md` in kebab-case (version suffix only to disambiguate editions)
6. **Place the summary** in `knowledgebase/<sub-kb>/summary_<name>.md`
7. **Copy or confirm** the source file is in `knowledgebase/<sub-kb>/_source/` (URL sources are already there from step 2)
8. **Compute and record checksum** — compute the SHA-256 of the source file and write it into the summary's `checksum_sha256` front-matter field. Use: `python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <source-path>`
9. **Update INDEX.md** — add an entry for the new document in the correct section, add cross-references if relevant, update the quick-lookup table if applicable
10. **Update BATCH_STATUS.md** — add a new completed batch entry with today's date and the summary filename

Run `extract_pdf.py` as: `uv run --python 3.12 --with pymupdf <path-to-script> <pdf-path> [start_page] [end_page]`

Run `extract_docx.py` as: `uv run --python 3.12 --with python-docx <path-to-script> <docx-path> [--headings-only] [--tables-only] [--max-rows N]`

---

### `/kb update <sub-kb> [document]`

**With document name:** Re-read the source file, then regenerate the summary for that document. Follow the same summary format. Overwrite the existing `summary_*.md` file. Update the "last updated" note in BATCH_STATUS.md.

**Without document:** Read INDEX.md and BATCH_STATUS.md, then list all summaries and ask which one to refresh.

---

### `/kb review <sub-kb>`

Audit a sub-KB for source documents that need updating, produce a prioritized plan,
and stage the work into groups that the user can approve and execute one at a time.

#### Step 1 — Inventory

Read all of these in parallel:
- `knowledgebase/<sub-kb>/INDEX.md`
- `knowledgebase/BATCH_STATUS.md`
- The file listing of `knowledgebase/<sub-kb>/_source/` (use Glob or Bash `ls`)
- The file listing of `knowledgebase/<sub-kb>/summary_*.md`

#### Step 2 — Cross-reference and identify gaps

For each source file in `_source/`, check whether a corresponding summary exists.
Then for each existing summary, assess staleness using these signals:

| Signal | How to detect |
|---|---|
| **No summary** | Source file in `_source/` with no matching `summary_*.md` |
| **Checksum mismatch** | Compute SHA-256 of the current source file; compare to `checksum_sha256` in the summary's front-matter. A mismatch means the source file changed since the summary was written. (Only applicable to summaries that have the front-matter field.) |
| **Version mismatch** | Source filename contains a version/date newer than the version recorded **inside** the summary — its front-matter `version` field, or the legacy `**Version/Date:**` header line if no front-matter exists (e.g., `_source/NIST-SP-800-53r6.pdf` but the summary records r5). Do not rely on a version in the summary *filename* — most summaries are versionless. |
| **Superseded standard** | Read the first page of the source PDF and check for a "superseded by" or "withdrawn" notice; or the summary itself mentions it was superseded |
| **Aged summary** | BATCH_STATUS.md shows this summary was last touched more than 12 months ago AND the framework is known to publish on a regular revision cycle (NIST, OWASP, FedRAMP, CIS, PCI DSS) |
| **Missing from INDEX** | `summary_*.md` file exists but is not referenced in INDEX.md |

Do not read every summary file in full — skim the first 10–15 lines to extract the
document version/date and any supersession notice.

#### Step 3 — Produce a tiered update plan

Classify each identified item into one of three tiers:

| Tier | Criteria | Example |
|---|---|---|
| **P1 — Critical** | Source file present but no summary exists; or a version-mismatched source file is present | New PDF in `_source/` with no summary |
| **P2 — Recommended** | Summary exists but version mismatch or supersession notice detected in the document itself | Summary says "Rev 4" but `_source/` has Rev 5 PDF |
| **P3 — Routine** | Summary is 12+ months old for a regularly revised framework; or summary not in INDEX | Aged CIS Controls or FedRAMP baseline summary |

Within each tier, group into **batches of 3–5 documents** that can be worked in a
single session. Prefer grouping by domain (e.g., all FedRAMP items together, all
OWASP items together) so context carries across the batch.

#### Step 4 — Present the staged plan

Print a structured report:

```
KB Review: knowledgebase/<sub-kb>/
Scanned: <N> source files, <N> summaries

P1 — Critical (N items)
  Batch A  [~X min]
    • <source-file>  → no summary exists
    • <source-file>  → version mismatch (summary: v4, source: v5)

P2 — Recommended (N items)
  Batch B  [~X min]
    • <summary-file>  → superseded (detected in document)
    • <summary-file>  → version bump available in _source/

P3 — Routine (N items)
  Batch C  [~X min]
    • <summary-file>  → 14 months old (FedRAMP — revises annually)
    • <summary-file>  → missing from INDEX.md

No issues found: <N> summaries appear current.

To execute: reply "run batch A", "run batch B", etc.
To skip a batch: reply "skip batch A".
To update a single item: /kb update <sub-kb> <document>
```

Estimate time as ~15 min per new summary (PDF extraction + draft + index update)
and ~10 min per refresh (re-extract changed sections + update existing summary).

#### Step 5 — Wait for user go-ahead

Do not execute any updates automatically. After presenting the plan, stop and wait.
When the user says "run batch X", execute the `/kb add` or `/kb update` pipeline
for each item in that batch in sequence, confirming completion after each one before
moving to the next. After the batch is done, update BATCH_STATUS.md and remind the
user of remaining batches.

---

### `/kb status`

Read and display `knowledgebase/BATCH_STATUS.md`. If it doesn't exist, scan the sub-KBs and produce a summary of what's present.

---

### `/kb validate [sub-kb]`

Read-only structural integrity check. Makes no changes.

**No argument:** Validate all sub-KBs.

**With sub-KB name:** Validate only that sub-KB.

For each sub-KB being validated, check and report:

| Check | Pass | Fail |
|---|---|---|
| INDEX.md exists | ✓ | "Missing INDEX.md" |
| Every `summary_*.md` listed in INDEX.md exists on disk | ✓ | "INDEX references missing file: <filename>" |
| Every `summary_*.md` on disk is referenced in INDEX.md | ✓ | "Orphaned summary (not in INDEX): <filename>" |
| Every file linked from INDEX.md exists on disk (includes subfolder content like `800-53a-procedures/AC.md`, not just `summary_*.md`) | ✓ | "INDEX links missing file: <path>" |
| INDEX document count matches reality | ✓ | "Count drift: INDEX header says <N>, found <M> summaries" |
| Every source file referenced in summary front-matter (`source_file`) exists in `_source/` | ✓ | "Missing source: <filename> (referenced in <summary>)" — *checked only when front-matter is present* |
| Summary front-matter present and parseable | ✓ | If a block is present but malformed/incomplete → **fail**: "Malformed front-matter in <filename>: missing <field>". If no block is present (legacy bold-header) → **warning**, not a failure: "Needs front-matter backfill: <filename>" |

Print a structured report:

```
KB Validate: knowledgebase/<sub-kb>/
  ✓ INDEX.md present
  ✓ 56 summaries — all referenced in INDEX, all files exist
  ✗ Orphaned summary: summary_old-guide.md (not in INDEX.md)
  ✗ Missing source: _source/nist-ai-rmf-1.1.pdf (referenced in summary_nist-ai-rmf.md)
  ✗ Malformed front-matter in summary_cis-controls-v8.md: missing 'checksum_sha256'
  ⚠ Needs front-matter backfill: summary_fips-199.md

Failures: 3   Warnings: 1   Clean: 52
```

Failures (✗) are integrity problems that should be fixed. Warnings (⚠) — currently only
"needs front-matter backfill" — are legacy summaries that still work but predate the
front-matter schema. If no failures and no warnings: print "All checks passed — <N> summaries clean."

---

### `/kb export [sub-kb] [--format md|html] [--tag <tag>]`

Render KB summaries to a single merged output file for offline use, sharing, or review.

**Arguments:**
- `[sub-kb]` — export one sub-KB; omit to export all sub-KBs (excluding any listed in `export_exclude`, see below)
- `--format md` (default) — merged Markdown file
- `--format html` — self-contained HTML with basic styling (headings, code blocks)
- `--tag <tag>` — include only summaries whose front-matter `tags` list contains `<tag>`

**Behavior:**

1. Resolve the sub-KB(s) to export. When no sub-KB is named (export all), skip any sub-KB
   listed in the `export_exclude` array in `config.json` — this keeps internal/private
   sub-KBs out of a bulk export. A sub-KB in `export_exclude` is still exported when it is
   named explicitly (e.g. `/kb export music`); the exclusion only applies to "export all".
   If `export_exclude` is absent, nothing is excluded.
2. If `--tag` is specified, read the front-matter of each `summary_*.md` and skip files whose `tags` list doesn't include the requested tag. (Summaries with no front-matter are skipped with a warning.)
3. Sort summaries alphabetically by filename within each sub-KB.
4. Concatenate all selected summaries into a single output, prefixed by a generated table of contents:
   ```
   # KB Export: <sub-kb> [tag: <tag>]
   Generated: YYYY-MM-DD
   Documents: N

   ## Table of Contents
   1. [Document Title](#anchor)
   ...

   ---
   [summary content]
   ```
5. For `--format html`: wrap in a minimal `<html>` document with `<style>` block (monospace pre blocks, readable sans-serif body, max-width 900px).
6. Write output to `knowledgebase/<sub-kb>/export_<sub-kb>_<date>[_<tag>].<ext>` and print the path.

**Example outputs:**
- `export_security_2025-06-01.md`
- `export_security_2025-06-01_fedramp.html`
- `export_all_2025-06-01.md` (when no sub-KB specified)

---

### `/kb new <name>`

Scaffold a new sub-KB named `<name>` inside the resolved `knowledgebase/` folder:

1. If `knowledgebase/` has not been resolved yet, run the Initialization Flow first.
2. Create `knowledgebase/<name>/` inside the resolved knowledgebase folder
3. Create `knowledgebase/<name>/_source/`
4. Create `knowledgebase/<name>/INDEX.md` with the standard template (see `references/kb-structure.md`)
5. Add an entry to `knowledgebase/BATCH_STATUS.md` noting the new sub-KB was initialized

---

### `/kb init`

Re-run the Initialization Flow to set or change the **parent directory** that contains `knowledgebase/`.

- If a config already exists, show the current parent directory and ask whether to keep it or change it.
- If the user changes the parent directory: apply the same absolute-path validation as the Initialization Flow (reject relative paths, re-prompt until an absolute path is given). Validate the directory exists; offer to create it if not. Then update `~/.claude/skills/kb/config.json`.
- Does **not** move or delete any existing knowledgebase content — only updates the stored pointer.

---

## Scripts

Scripts live in this skill's `scripts/` subdirectory:

| Script | Purpose | Usage |
|---|---|---|
| `extract_pdf.py` | Extract text from a PDF by page range | `python extract_pdf.py <path> [start] [end]` |
| `extract_docx.py` | Extract text and tables from a DOCX file | `python extract_docx.py <path> [--headings-only] [--tables-only] [--max-rows N]` |
| `extract_xlsx.py` | Extract data from any XLSX spreadsheet | `python extract_xlsx.py <path> [--sheet Name] [--headers-only] [--max-rows N]` |
| `extract_html.py` | Extract readable text from a URL or local HTML file | `python extract_html.py <url-or-path> [--selector CSS] [--headings-only] [--max-chars N]` |
| `extract_csv.py` | Extract data from a CSV file (stdlib only) | `python extract_csv.py <path> [--columns A,B] [--headers-only] [--max-rows N] [--delimiter C]` |

To run scripts, use `uv run --python 3.12 --with <dep> <script> <args>` or `python <script> <args>` if dependencies are already installed. Key dependencies: `pymupdf` (fitz) for PDF extraction, `python-docx` for DOCX, `openpyxl` for Excel, `requests beautifulsoup4` for HTML. CSV uses stdlib only.

Domain-specific scripts (e.g., parsers for a fixed spreadsheet schema or diagram generators) belong in your sub-KB's own `scripts/` directory, not here. See `examples/domain-specific/` for examples.

---

## Notes

- Sub-KB names are discovered dynamically — never hardcode `security` or `coding`
- The `_source/` subdirectory holds original source files (PDFs, XLSX, DOCX, etc.) — source documents are kept out of context unless specifically required; always use `summary_*.md` files for lookups and answers
- Summary naming convention: `summary_<name>.md` (kebab-case); add a version suffix only to disambiguate editions of the same document — most summaries are versionless (version lives in front-matter)
- BATCH_STATUS.md at `knowledgebase/` root tracks all sub-KBs in one place
- When adding documents, always read the source INDEX.md before updating it to avoid duplicating sections
- Config file: `~/.claude/skills/kb/config.json` — stores the absolute path to the `knowledgebase/` folder; local discovery (CWD / parent) always takes priority over this file
