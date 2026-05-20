# KB Workflows

Step-by-step procedures for common knowledgebase operations.

---

## Workflow 0: First-Run Initialization

**Trigger:** No `knowledgebase/` folder found via local discovery (CWD / parent) and no valid config at `~/.claude/skills/kb/config.json`. Also triggered by `/kb init`.

1. Tell the user no knowledgebase was found.
2. Show the default parent directory — the current working directory with its full absolute path — and explain that `knowledgebase/` will be created inside it.
3. Ask: "Create `knowledgebase/` here, or enter a different parent directory?" Do not proceed until the user responds.
4. **Validate the path before proceeding.** If the user entered something other than the default:
   - Must be an absolute path — Windows: starts with a drive letter (`C:\`) or UNC (`\\`); macOS/Linux: starts with `/`
   - If relative (e.g., `../somewhere`, `kb`): reject and re-prompt — "That looks like a relative path. Please enter an absolute path."
   - Re-prompt until an absolute path is given or the user cancels (types "cancel" or "quit")
5. With the confirmed, validated parent directory:
   - Create `<parent>/knowledgebase/`
   - Create `<parent>/knowledgebase/BATCH_STATUS.md` with a minimal header:
     ```markdown
     # Knowledgebase — Batch Status
     (No batches yet. Add sub-KBs with /kb new <name>.)
     ```
6. Write `~/.claude/skills/kb/config.json`:
   ```json
   {"knowledgebase_path": "<parent>/knowledgebase"}
   ```
7. Confirm the location and prompt: "Run `/kb new <name>` to add your first sub-KB."

**For `/kb init` when config already exists:**
- Read the config, show the current path, ask: "Keep `<current-path>` or enter a new parent directory?"
- If changing: validate the new parent exists (offer to create it if not), update the config.
- Never move or delete existing content — only the pointer changes.

---

## Workflow 1: Add a New PDF Document

**Trigger:** `/kb add <sub-kb> <pdf-path>`

1. **Check the sub-KB exists.** If `knowledgebase/<sub-kb>/` is missing, ask the user whether to create it. If yes, run `/kb new <sub-kb>` first.

2. **Read the TOC.** Extract pages 1–5 of the PDF to identify structure:
   ```
   uv run --python 3.12 --with pymupdf extract_pdf.py "<pdf-path>" 1 5
   ```

3. **Extract key sections.** Based on the TOC, extract the sections most relevant for a summary (typically introduction + each major chapter opener). Respect the 80,000 char limit — extract in passes if needed.

4. **Draft the summary.** Follow the template in `kb-structure.md`. Name the file `summary_<source>-<version>.md`.

5. **Place files:**
   - Summary → `knowledgebase/<sub-kb>/summary_<name>.md`
   - Source file → `knowledgebase/<sub-kb>/_source/<Descriptive-Name>.pdf` (copy if not already there)

6. **Update INDEX.md.** Read the current INDEX.md first. Determine the correct section. Add an entry. Update the quick-lookup table if this document enables a new use case.

7. **Update BATCH_STATUS.md.** Add a completed batch row with today's date.

---

## Workflow 2: Add a New Excel/XLSX Document

**Trigger:** `/kb add <sub-kb> <xlsx-path>` where the file is an XLSX

1. Run `extract_xlsx.py` with `--headers-only` to map sheet names and column structure:
   ```
   uv run --python 3.12 --with openpyxl extract_xlsx.py "<xlsx-path>" --headers-only
   ```

2. Run without flags (or with `--sheet <name>`) to extract full content:
   ```
   uv run --python 3.12 --with openpyxl extract_xlsx.py "<xlsx-path>"
   uv run --python 3.12 --with openpyxl extract_xlsx.py "<xlsx-path>" --sheet "Sheet1" --max-rows 100
   ```

3. Use the output to draft the summary.
4. Follow steps 5–7 from Workflow 1.

**Note:** If the XLSX has a fixed, domain-specific schema that requires custom parsing, consider a domain-specific script in your sub-KB's `scripts/` directory. See `examples/domain-specific/` for examples.

---

## Workflow 3: Add a New DOCX Document

**Trigger:** `/kb add <sub-kb> <docx-path>` where the file is `.docx`

1. Run `extract_docx.py` with `--headings-only` to map the document structure:
   ```
   uv run --python 3.12 --with python-docx extract_docx.py "<docx-path>" --headings-only
   ```

2. Run `extract_docx.py` without flags to extract full content (paragraphs + tables):
   ```
   uv run --python 3.12 --with python-docx extract_docx.py "<docx-path>"
   ```
   If tables are large, add `--max-rows N` to limit output per table.

3. Draft the summary following the template.
4. Follow steps 5–7 from Workflow 1.

---

## Workflow 4: Add a New Markdown or Text Document

**Trigger:** `/kb add <sub-kb> <md-path>` where the file is `.md` or `.txt`

1. Read the file directly with the Read tool.
2. Draft the summary following the template.
3. Follow steps 5–7 from Workflow 1.

---

## Workflow 5: Update an Existing Summary

**Trigger:** `/kb update <sub-kb> <document-name>` (document-name is the summary filename or source title)

1. Find the existing summary file in `knowledgebase/<sub-kb>/summary_*.md`.
2. Locate the source file in `_source/` — if a newer version exists, use that. If not, re-read the existing source.
3. Extract fresh text from the source (same as Workflow 1 steps 2–3).
4. Rewrite the summary. Preserve the filename.
5. Update the BATCH_STATUS.md entry with today's date and "UPDATED".

---

## Workflow 6: Create a New Sub-KB

**Trigger:** `/kb new <name>`

1. Create directory: `knowledgebase/<name>/`
2. Create source directory: `knowledgebase/<name>/_source/`
3. Create INDEX.md from the template in `kb-structure.md`
4. Add an entry in `knowledgebase/BATCH_STATUS.md`:
   ```
   ## <Name> KB
   | Batch | Date | Status | Summary Files Created |
   |---|---|---|---|
   | **Init** | YYYY-MM-DD | INITIALIZED | (no summaries yet) |
   ```
5. Inform the user: "Sub-KB '<name>' is ready. Add documents with `/kb add <name> <file>`."

---

## Workflow 7: Review a Sub-KB for Staleness

**Trigger:** `/kb review <sub-kb>`

This workflow is read-only until the user approves a batch. All analysis happens
before anything is written.

1. **Inventory pass (parallel reads):**
   - List files in `_source/` and `summary_*.md`
   - Read INDEX.md and BATCH_STATUS.md
   - Skim the first 10–15 lines of each existing summary (version/date line + any supersession notice)

2. **Classify each item:**
   - P1: Source file in `_source/` with no corresponding summary
   - P1: Source filename version is newer than summary filename version
   - P2: Summary's first lines indicate it covers a superseded version
   - P2: Source file in `_source/` is newer (by filename date) than the existing summary
   - P3: BATCH_STATUS.md shows last touch was 12+ months ago AND the standard revises regularly
   - P3: Summary file exists but is missing from INDEX.md

3. **Group into batches of 3–5 by domain.** Common domain groupings:
   - FedRAMP documents together
   - NIST SP 800-series together
   - OWASP documents together
   - Compliance frameworks (CIS, PCI, ISO) together

4. **Present the tiered plan** (see SKILL.md format) and stop. Do not execute.

5. **On user go-ahead for a batch:**
   - For P1 (no summary): run the full `/kb add` pipeline
   - For P2/P3 (existing summary): run the `/kb update` pipeline
   - Confirm each item completed before starting the next
   - After all items in the batch: update BATCH_STATUS.md, print remaining batches

**Key constraint:** Never skip the wait-for-approval step between presenting the plan
and executing. The user controls the pace.

---

## Common Patterns

**Extracting a large PDF in chunks:**
```
# Extract pages 1–50
uv run --python 3.12 --with pymupdf extract_pdf.py "doc.pdf" 1 50

# Extract pages 51–120
uv run --python 3.12 --with pymupdf extract_pdf.py "doc.pdf" 51 120
```

**Extracting a DOCX document:**
```
# Step 1: scan structure
uv run --python 3.12 --with python-docx extract_docx.py "doc.docx" --headings-only

# Step 2: full content (limit table rows if the doc is table-heavy)
uv run --python 3.12 --with python-docx extract_docx.py "doc.docx" --max-rows 8
```

**Extracting an XLSX spreadsheet:**
```
# Step 1: inspect sheet names and column headers
uv run --python 3.12 --with openpyxl extract_xlsx.py "data.xlsx" --headers-only

# Step 2: extract content (limit rows if the sheet is large)
uv run --python 3.12 --with openpyxl extract_xlsx.py "data.xlsx" --sheet "Sheet1" --max-rows 100
```

**Finding what's already in the KB before adding:**
```
/kb list <sub-kb>
```
Check existing summaries before adding to avoid duplicates.

**Checking source file inventory:**
List `knowledgebase/<sub-kb>/_source/` to see what source documents are available.
