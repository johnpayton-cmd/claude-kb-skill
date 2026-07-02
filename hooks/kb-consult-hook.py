#!/usr/bin/env python3
"""kb skill — UserPromptSubmit hook: proactive-consult mandate.

Why this exists: a skill's `description` frontmatter reliably makes the skill *available*
and routes *explicit* `/kb` calls, but it does NOT reliably drive *proactive* consultation
of the knowledgebase on an ordinary question (measured ~0-1/10 in testing). A UserPromptSubmit
hook, whose stdout is injected into per-turn context, does (measured ~10/10). So the "always
consult the KB before answering from training data" behavior lives here, not in the frontmatter.

Behavior: emit the mandate ONLY when a local knowledgebase is resolvable (CWD -> parent ->
~/.claude/skills/kb/config.json). Silent otherwise, so it adds zero noise/cost in sessions with
no KB. Mandate-only: which sub-KB to use is decided by the kb skill reading each sub-KB's INDEX
(and its `Covers:` line) once consultation is triggered.

Install: /kb init offers to add this to the user's settings.json under hooks.UserPromptSubmit.
"""
import os
import sys
import json


def resolve_kb():
    """Mirror the skill's discovery order for the two file-based cases."""
    cwd = os.getcwd()
    for base in (cwd, os.path.dirname(cwd)):
        p = os.path.join(base, "knowledgebase")
        if os.path.isdir(p):
            return p
    cfg = os.path.expanduser(os.path.join("~", ".claude", "skills", "kb", "config.json"))
    try:
        with open(cfg, encoding="utf-8") as f:
            p = json.load(f).get("knowledgebase_path")
        if p and os.path.isdir(p):
            return p
    except Exception:
        pass
    return None


def main():
    kb = resolve_kb()
    if not kb:
        return  # no KB in scope -> inject nothing
    sys.stdout.write(
        "IMPORTANT - A local knowledgebase is available at `%s` (a folder of sub-KBs, each "
        "with an INDEX.md). It may hold authoritative, curated information that is more current "
        "and accurate than your training data. BEFORE answering the user's question from your "
        "training data, first check whether a local sub-KB covers the topic: enumerate the "
        "sub-KBs under that folder, and if any covers the subject area, use the kb skill (run "
        "/kb search, or read that sub-KB's INDEX.md and the relevant summary_*.md) and ground "
        "your answer in the knowledgebase. Do this proactively, without being asked and without "
        "the user typing /kb. Do not assume a topic is absent from the KB without checking.\n"
        % kb
    )


if __name__ == "__main__":
    main()
