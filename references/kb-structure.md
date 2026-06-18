# KB Structure Guide

## Folder Layout

```
knowledgebase/
├── BATCH_STATUS.md              # Top-level tracking for all sub-KBs
├── <sub-kb-name>/               # One folder per topic domain
│   ├── INDEX.md                 # Required — marks this as a sub-KB; master navigator
│   ├── _source/                 # Original source files (PDFs, XLSX, Markdown)
│   ├── summary_*.md             # One summary per source document
│   └── <optional-subfolders>/   # e.g., 800-53a-procedures/ for verbatim procedure extracts
└── <another-sub-kb>/
    ├── INDEX.md
    ├── _source/
    └── summary_*.md
```

## Summary File Naming

`summary_<name>.md` — all kebab-case, lowercase. The `<name>` is the document's short
identifier. Include a version suffix **only when needed to disambiguate editions of the
same document** (e.g. two RAR template versions kept side by side); most summaries are
versionless because the version lives inside the front-matter.

Examples:
- `summary_nist-sp-800-53r5.md`         (revision is part of the document's name)
- `summary_fedramp-csp-playbook.md`     (versionless — normal case)
- `summary_cis-controls-v8.md`
- `summary_fedramp-rar-high-template-v1.7.md`  (suffix disambiguates from v1.4)

## Summary File Front-Matter

Every summary **must** begin with a YAML front-matter block. This is the canonical schema:

> **Migration note:** Summaries created before front-matter became standard use a legacy
> bold-header (`**Version/Date:** … | **File:** …`) instead. These are valid for lookup but
> are being backfilled to the schema below. `/kb validate` reports an un-migrated summary as
> a **warning** ("needs front-matter backfill"), not a failure.

```yaml
---
source_file: _source/<filename-with-extension>
version: "<version-string>"        # e.g. "r5", "v4.2", "2024-01", "n/a"
date_added: YYYY-MM-DD
last_updated: YYYY-MM-DD           # same as date_added on first add
tags: [tag1, tag2, tag3]           # lowercase, hyphenated; see tag guidance below
checksum_sha256: <64-char hex>     # SHA-256 of the source file at add-time
---
```

**Tag guidance:** Use concise, reusable labels. Examples: `nist`, `fedramp`, `owasp`, `cloud`, `zero-trust`, `ai-security`, `incident-response`, `controls`, `federal`, `access-control`. Tags drive `/kb search --tag` filtering and `/kb export --tag` scoping.

**Checksum:** Compute with `python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <path>`. Used by `/kb review` to detect source file changes deterministically.

## Summary File Structure

Every summary should follow this order (after the front-matter block):

```markdown
---
[front-matter as above]
---

# [Full Document Title]
**One-line hook:** What this document does and why it matters.

## Purpose
What problem this document solves; who it is written for.

## Scope
What it covers and what it explicitly excludes.

## Key Sections
Brief description of the document's major parts (match the actual TOC).

## Critical Controls / Requirements
The most actionable items — specific controls, thresholds, timelines,
or requirements a practitioner needs to know.

## Workspace Relevance
How this document applies to the work done in this specific workspace
(job search, security research, client deliverables, coding projects, etc.).
```

## INDEX.md Structure

Each sub-KB's INDEX.md should contain:

1. **Quick use-case lookup table** — maps job/question to specific KB file(s)
2. **Document sections** — grouped by topic/domain, one entry per summary
3. **Cross-references** — pointers to related docs in other sub-KBs
4. **Naming table** (if applicable) — e.g., control family → procedure file mapping

### INDEX.md Template

```markdown
# [Sub-KB Name] Knowledge Base Index

## Quick Use-Case Lookup

| I need to... | Start here |
|---|---|
| [Task description] | [filename.md] → [related.md] |

## [Section 1 Name]

### [document-title] (`summary_filename.md`)
One-sentence description of this document's purpose and coverage.

## [Section 2 Name]
...

## Cross-References to [Other Sub-KB]
- **[Topic]:** See `../other-sub-kb/summary_relevant.md`
```

## BATCH_STATUS.md Structure

The top-level `knowledgebase/BATCH_STATUS.md` tracks what has been processed.

```markdown
# Knowledgebase — Batch Status

## [Sub-KB Name] KB

| Batch | Date | Status | Summary Files Created |
|---|---|---|---|
| **S1** | YYYY-MM-DD | COMPLETE | summary_file1.md, summary_file2.md |

**INDEX.md** — last updated YYYY-MM-DD, N documents

## [Another Sub-KB] KB
...
```

## What Makes a Valid Sub-KB

A directory under `knowledgebase/` is recognized as a sub-KB if it contains:
- An `INDEX.md` file (required)
- At least one `summary_*.md` file (expected, but not required for new/empty KBs)

A `_source/` directory is strongly recommended for traceability.
