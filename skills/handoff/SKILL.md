---
name: handoff
description: "Creates a self-contained handoff dossier for continuing work in a fresh agent session at standard or frontier capability. Use when the user invokes /handoff, asks for a handoff, context is polluted, or work should continue on a cheaper or stronger model."
---

# Handoff

Create a self-contained handoff dossier so a fresh agent can continue a task without polluted or overly expensive prior context. Create-only: there is no takeover skill; the dossier is the contract.

Invoke as `$handoff:handoff` in Codex, `/handoff:handoff` in Claude Code, or `/handoff` in Cursor (opencode: `/handoff`). Optional tier args: `standard` or `frontier`.

## 1. Offer vs execute

You may **offer** a handoff when context is polluted or a cost step-down / step-up fits. Never auto-run without user confirmation. Only execute this workflow when the user invoked handoff or explicitly accepted an offer.

## 2. Select the platform reference

Identify the active harness, then read exactly one complete reference:

- Codex: [references/codex.md](references/codex.md)
- Claude Code: [references/claude-code.md](references/claude-code.md)
- Cursor: [references/cursor.md](references/cursor.md)
- opencode: [references/opencode.md](references/opencode.md)

Stop if the harness cannot be identified.

Also read:

- [references/tier-selection.md](references/tier-selection.md)
- [references/dossier.md](references/dossier.md)

## 3. Gather facts

Prefer cheap tool verification over chat memory for workspace facts:

- Repo root and worktree path (`pwd -P`, `git rev-parse --show-toplevel`, `git worktree list` if needed)
- Branch and HEAD
- `git status --short`
- Mission, done vs not, decisions/hidden facts, risks, useful commands

If git root cannot be identified, stop and ask. If there is no code yet, still write a dossier — lean on mission, decisions, and next actions.

Do not stash, commit, clean, or otherwise mutate the dirty tree as part of handoff.

## 4. Resolve tier

Follow [references/tier-selection.md](references/tier-selection.md).

- Explicit `standard` / `frontier` override → use it; do not ask.
- Else recommend, then ask: `I recommend a <tier> agent for this one — do you agree?`
- Stop if rejected without a tier choice.

## 5. Exclude `.handoff/` then write

Before writing any `.handoff/` path:

1. `repo_root="$(git rev-parse --show-toplevel)"`; use `dossier_dir="$repo_root/.handoff"` for every dossier write. Never write `.handoff/` relative to an arbitrary current working directory.
2. `exclude_file="$(git rev-parse --git-path info/exclude)"`
3. Ensure a `.handoff/` line exists in that file (append if missing). Never edit a global gitignore.
4. `git check-ignore -q .handoff/` (or a concrete future path under it). If exclusion fails, stop and ask before using an alternate location.
5. `mkdir -p -- "$dossier_dir"` before selecting the output filename or writing the dossier.

Then write `$dossier_dir/<slug>-YYYYMMDD-HHMM.md` per [references/dossier.md](references/dossier.md) with the chosen tier’s emphasis.

## 6. Close out

Report:

- Absolute dossier path (and repo-relative form if useful)
- Chosen tier
- The resume prompt block (absolute path + worktree + branch — see [references/dossier.md](references/dossier.md))

Stop. Do not continue the original implementation task unless the user asks.
