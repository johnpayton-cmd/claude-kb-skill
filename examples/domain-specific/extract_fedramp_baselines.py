"""
Extract FedRAMP Security Controls Baseline data from XLSX.
Outputs structured data for summary_fedramp-baselines.md

Usage:
  python extract_fedramp_baselines.py [--xlsx <path>]

If --xlsx is omitted, the script searches for *FedRAMP*Baseline*.xlsx
in a _source/ subdirectory of the current working directory.
"""
import argparse
import glob
import os
import sys
import openpyxl
from collections import defaultdict

KEY_CONTROLS = {
    "AC-1": "Policy and Procedures",
    "AC-2": "Account Management",
    "AC-17": "Remote Access",
    "AU-2": "Event Logging",
    "CM-6": "Configuration Settings",
    "IA-2": "Identification and Authentication",
    "IR-6": "Incident Reporting",
    "RA-5": "Vulnerability Monitoring and Scanning",
    "SC-7": "Boundary Protection",
    "SI-2": "Flaw Remediation",
}


def find_xlsx():
    """Auto-discover FedRAMP baseline XLSX in _source/ under CWD."""
    patterns = [
        os.path.join("_source", "*FedRAMP*Baseline*.xlsx"),
        os.path.join("_source", "*fedramp*baseline*.xlsx"),
        "*FedRAMP*Baseline*.xlsx",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=False)
        if matches:
            return matches[0]
    return None


def extract_sheet(wb, sheet_name):
    """Extract control data from a baseline sheet."""
    ws = wb[sheet_name]
    controls = []
    header_found = False
    for row in ws.iter_rows(values_only=True):
        if row[0] == 'SORT ID':
            header_found = True
            continue
        if not header_found:
            continue
        sort_id = row[0]
        if sort_id is None or str(sort_id).strip() == '':
            continue
        family = str(row[1]).strip() if row[1] else ''
        ctrl_id = str(row[2]).strip() if row[2] else ''
        name = str(row[3]).strip() if row[3] else ''
        params = str(row[6]).strip() if row[6] else ''
        conmon = str(row[9]).strip() if row[9] else ''
        controls.append((sort_id, family, ctrl_id, name, params, conmon))
    return controls


def family_abbrev(ctrl_id):
    """Extract family prefix from control ID like AC-2 -> AC, AC-2(1) -> AC"""
    base = ctrl_id.split('(')[0].strip()
    parts = base.split('-')
    return parts[0] if parts else ctrl_id


def get_family_counts(controls):
    counts = defaultdict(int)
    for (sort_id, family, ctrl_id, name, params, conmon) in controls:
        fam = family_abbrev(ctrl_id)
        counts[fam] += 1
    return counts


def get_key_control(controls, target_id):
    for (sort_id, family, ctrl_id, name, params, conmon) in controls:
        if ctrl_id.strip() == target_id:
            return params, conmon
    return '', ''


def main():
    parser = argparse.ArgumentParser(description="Extract FedRAMP Security Controls Baseline data from XLSX.")
    parser.add_argument("--xlsx", help="Path to FedRAMP Security Controls Baseline XLSX file")
    args = parser.parse_args()

    xlsx_path = args.xlsx
    if not xlsx_path:
        xlsx_path = find_xlsx()
    if not xlsx_path:
        print("Error: No XLSX file specified and none found in _source/.", file=sys.stderr)
        print("Usage: python extract_fedramp_baselines.py --xlsx <path>", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(xlsx_path):
        print(f"Error: File not found: {xlsx_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading: {xlsx_path}")
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)

    high = extract_sheet(wb, 'High Baseline')
    mod = extract_sheet(wb, 'Moderate Baseline')
    low = extract_sheet(wb, 'Low Baseline')

    print(f"Control counts: High={len(high)}, Moderate={len(mod)}, Low={len(low)}")

    high_counts = get_family_counts(high)
    mod_counts = get_family_counts(mod)
    low_counts = get_family_counts(low)

    all_families = sorted(set(list(high_counts.keys()) + list(mod_counts.keys()) + list(low_counts.keys())))

    print("\n=== CONTROL COUNTS BY FAMILY ===")
    print(f"{'Family':<8} {'Low':>5} {'Mod':>5} {'High':>5}")
    print("-" * 30)
    for fam in all_families:
        l = low_counts.get(fam, 0)
        m = mod_counts.get(fam, 0)
        h = high_counts.get(fam, 0)
        print(f"{fam:<8} {l:>5} {m:>5} {h:>5}")

    print("\n=== KEY CONTROL PARAMETERS ===")
    for ctrl_id, ctrl_name in KEY_CONTROLS.items():
        lp, lc = get_key_control(low, ctrl_id)
        mp, mc = get_key_control(mod, ctrl_id)
        hp, hc = get_key_control(high, ctrl_id)
        print(f"\n--- {ctrl_id}: {ctrl_name} ---")
        print(f"  LOW params:    {lp[:200] if lp else '(none)'}")
        print(f"  MOD params:    {mp[:200] if mp else '(none)'}")
        print(f"  HIGH params:   {hp[:200] if hp else '(none)'}")
        if lc or mc or hc:
            print(f"  LOW conmon:    {lc[:150] if lc else '(none)'}")
            print(f"  MOD conmon:    {mc[:150] if mc else '(none)'}")
            print(f"  HIGH conmon:   {hc[:150] if hc else '(none)'}")

    high_ids = set(c[2] for c in high)
    mod_ids = set(c[2] for c in mod)
    low_ids = set(c[2] for c in low)

    high_only = high_ids - mod_ids
    print(f"\n=== HIGH DELTA (in High but not Moderate): {len(high_only)} controls ===")
    delta_by_family = defaultdict(list)
    for c in high:
        if c[2] in high_only:
            fam = family_abbrev(c[2])
            delta_by_family[fam].append((c[2], c[3]))

    for fam in sorted(delta_by_family.keys()):
        ctrls = delta_by_family[fam]
        print(f"\n  {fam} ({len(ctrls)}):")
        for ctrl_id, ctrl_name in ctrls:
            print(f"    {ctrl_id}: {ctrl_name}")

    mod_only = mod_ids - low_ids
    print(f"\n=== MODERATE DELTA (in Moderate but not Low): {len(mod_only)} controls ===")
    delta_mod_by_family = defaultdict(list)
    for c in mod:
        if c[2] in mod_only:
            fam = family_abbrev(c[2])
            delta_mod_by_family[fam].append((c[2], c[3]))

    for fam in sorted(delta_mod_by_family.keys()):
        ctrls = delta_mod_by_family[fam]
        print(f"\n  {fam} ({len(ctrls)}):")
        for ctrl_id, ctrl_name in ctrls:
            print(f"    {ctrl_id}: {ctrl_name}")

    print("\n=== CONMON PERIODICITY SAMPLE (controls with periodicity data) ===")
    printed = 0
    for c in mod:
        if c[5] and c[5].strip() not in ('', 'None', 'none'):
            lp, lc = get_key_control(low, c[2])
            mp, mc = get_key_control(mod, c[2])
            hp, hc = get_key_control(high, c[2])
            print(f"  {c[2]}: L={lc[:80] if lc else 'N/A'} | M={mc[:80] if mc else 'N/A'} | H={hc[:80] if hc else 'N/A'}")
            printed += 1
            if printed >= 30:
                break

    wb.close()


if __name__ == "__main__":
    main()
