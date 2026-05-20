# Domain-Specific Script Examples

This directory contains example scripts that extend the KB skill for a specific domain. They are not part of the core skill — they illustrate how to build extraction or visualization tools tailored to a particular dataset.

## Included Examples

### `extract_fedramp_baselines.py`
Parses the **FedRAMP Security Controls Baseline XLSX** (available from fedramp.gov). The spreadsheet has a fixed structure with sheets named `High Baseline`, `Moderate Baseline`, and `Low Baseline`, each with specific column positions for control IDs, family names, parameters, and ConMon periodicity.

**Why domain-specific:** The column parsing logic (`SORT ID` header detection, column positions 0–9, sheet names) is tightly coupled to this particular FedRAMP spreadsheet layout. It will not work on an arbitrary XLSX without modification.

**Usage:**
```
python extract_fedramp_baselines.py --xlsx "<path-to-FedRAMP-Baselines.xlsx>"
```

**Output:** Control counts by family across Low/Moderate/High baselines, key control parameters, High/Moderate deltas, and ConMon periodicity samples.

---

### `generate_fedramp_diagram.py`
Generates an interactive **FedRAMP Interdependency Diagram** as both a Graphviz `.dot` file and a standalone `vis.js` HTML file. All node and edge data is embedded directly in the script — it covers the full FedRAMP authorization lifecycle: upstream policy, NIST standards, actors, baselines, phases 1–3, ConMon escalation, penetration testing attack vectors, and container security.

**Why domain-specific:** The NODES and EDGES data is hardcoded FedRAMP content derived from the CSP/Agency Playbooks, ConMon Playbook, Pen Test Guidance, and Security Controls Baseline. It is not a general-purpose diagram generator.

**Usage:**
```
python generate_fedramp_diagram.py --output-dir "<output-directory>"
```

**Output:** `fedramp_diagram.dot` and `fedramp_diagram.html` in the specified directory. Open the HTML in any browser. Render PDF with `dot -Tpdf fedramp_diagram.dot -o fedramp_diagram.pdf` (requires Graphviz).

---

## Building Your Own Domain Script

To create a domain-specific script for your sub-KB:

1. Identify what the generic extractors (`extract_xlsx.py`, `extract_pdf.py`, `extract_docx.py`) cannot handle — usually a fixed schema or highly structured output format.
2. Write a script that accepts a file path argument and outputs structured text the KB summarization pipeline can consume.
3. Place it in your sub-KB's `scripts/` directory (e.g., `knowledgebase/mysubkb/scripts/`).
4. Reference it in your sub-KB's `INDEX.md` under a "Tools" or "Scripts" section.
