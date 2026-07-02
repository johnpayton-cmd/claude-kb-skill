# Upgrading an existing install — enabling proactive consultation

If you already use this skill against an existing knowledgebase, this guide brings the install
up to date and turns on **proactive consultation** (Claude checks the KB before answering from
training data, without you typing `/kb`).

## What changed

Proactive consultation is no longer expected from the skill's `description` or from a `CLAUDE.md`
instruction — a skill description reliably makes the skill *available* and routes explicit `/kb`
calls, but does not reliably trigger *unprompted* lookups. That behavior is now delivered by a
`UserPromptSubmit` hook (`hooks/kb-consult-hook.py`) whose output is injected into per-turn
context. The hook is off until it is registered in your `settings.json`.

Also new: each sub-KB's `INDEX.md` carries a `**Covers:**` routing line so Claude can pick the
right sub-KB once consultation is triggered. Existing INDEXes that predate it still work and can
be backfilled.

## Step 1 — Update the skill files

Pull the latest and copy it over your existing install. **Do not delete the folder first** —
`config.json` lives there (it holds your KB path) and is not in the repo, so a copy-over preserves
it; a wipe-and-replace would lose it.

**Windows (PowerShell):**
```powershell
git clone https://github.com/johnpayton-cmd/claude-kb-skill.git $env:TEMP\kb-src
robocopy "$env:TEMP\kb-src" "$HOME\.claude\skills\kb" /E /XD .git
Remove-Item "$env:TEMP\kb-src" -Recurse -Force
```

**macOS/Linux:**
```bash
git clone https://github.com/johnpayton-cmd/claude-kb-skill.git /tmp/kb-src
rsync -a --exclude='.git' /tmp/kb-src/ ~/.claude/skills/kb/
rm -rf /tmp/kb-src
```

Confirm `~/.claude/skills/kb/hooks/kb-consult-hook.py` now exists.

## Step 2 — Install the hook

In a Claude Code session, run:

```
/kb init
```

Keep the existing KB location when asked, and **accept the offer to install the proactive-consult
hook.** It writes the `UserPromptSubmit` entry into your `settings.json` (confirmation-gated,
idempotent, and silent in sessions that have no KB).

To install it by hand instead, add this under `hooks` in `~/.claude/settings.json` (use `python3`
on macOS/Linux, and your real home path), merging into any existing `UserPromptSubmit` array:

```json
"UserPromptSubmit": [
  { "hooks": [ { "type": "command", "command": "python",
    "args": ["<abs path>/.claude/skills/kb/hooks/kb-consult-hook.py"] } ] }
]
```

## Step 3 — Backfill the `Covers:` routing line

Older INDEXes have no `Covers:` line. Run:

```
/kb review <sub-kb>
```

It flags the missing line and stages a backfill derived from that INDEX's own contents — approve
it. (`/kb validate` reports the same as a warning.)

## Step 4 — Verify

```
/kb validate
```

Expect no failures. Then restart the session (so the new hook loads) and ask a question your KB
covers **without** typing `/kb`. If the hook is working, Claude consults the KB before answering.

## Optional — clean up CLAUDE.md

If your `CLAUDE.md` contains "always consult the KB" or `/kb` how-to-use instructions, you can
remove them — the hook now delivers that behavior.
