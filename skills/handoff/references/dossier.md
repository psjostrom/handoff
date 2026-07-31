# Dossier format

## Path

Write exactly one new file:

`<repo-root>/.handoff/<slug>-YYYYMMDD-HHMM.md`

- Resolve `<repo-root>` with `git rev-parse --show-toplevel`; never write `.handoff/` relative to an arbitrary current working directory.
- Report the resulting path as repo-relative `.handoff/<slug>-YYYYMMDD-HHMM.md`.
- **Slug normalization** (from the mission; fallback `handoff` if invalid):
  - Lowercase; split on whitespace and separators (`_`, `/`, `\`, `.`, and punctuation other than `-`).
  - Keep only `[a-z0-9-]` characters; collapse repeated `-`; trim leading/trailing `-`.
  - Require **2–6** non-empty kebab words (segments separated by single `-`).
  - Reject empty results, absolute paths, `..`, or any other traversal/unsafe form → use `handoff`.
- Timestamp: local time at write (`YYYYMMDD-HHMM`).
- Join as `"$repo_root/.handoff/<slug>-YYYYMMDD-HHMM.md"`, then **resolve** the candidate path and verify it remains strictly beneath `"$repo_root/.handoff"` before writing. If not, stop and use slug `handoff` (re-check containment).
- If the path exists, append `-2`, `-3`, … before `.md` (still under `.handoff/`, re-check containment after each suffix).

## Shared spine (every tier)

Use these sections in order, with these headings:

1. `# Handoff: <short title>`
2. `## Receiver startup`
3. `## Mission`
4. `## Workspace`
5. `## State of work`
6. `## Decisions & hidden facts`
7. `## Risks & open questions`
8. `## Next actions`
9. `## Handoff metadata`
10. `## Resume prompt`

### Section contents

**Receiver startup** — Instruct the receiving agent to follow these steps **in order**. Do not explore the repo, edit files, or execute next actions until the tier gate passes (or the user overrides).

1. **Tier gate (first).** Read `tier` from Handoff metadata. Classify the model running this chat using [tier-selection.md](tier-selection.md) receiver classification. A stronger model may take a `standard` dossier. For a `frontier` dossier, under-tier, Auto, unknown, and unlabeled receivers must **stop** — unless the user explicitly replies `proceed anyway`.
2. **On under-tier / Auto / unknown / unlabeled mismatch:** Stop immediately. Reply with a short mismatch warning only: required tier, that the current model is under-tier / Auto / unknown / unlabeled, and that the user should switch models and re-open — or explicitly reply `proceed anyway` to override. Do not verify workspace, search the tree, or start work until then.
3. **After the gate passes** (matching tier, over-tier, or explicit `proceed anyway`): read this file fully; verify workspace fields match reality; restate the next action in one sentence; then begin work. Do not edit before that restatement.

**Mission** — Goal, definition of done, explicit non-goals.

**Workspace** — Absolute worktree/repo path, branch, HEAD SHA, whether this is a linked git worktree, remotes if relevant, dirty/untracked summary (`git status --short`).

**State of work** — Done / in progress / not started. Key paths touched. Commands/tests run and results. If no code exists yet, say so and lean on mission + decisions.

**Decisions & hidden facts** — Anything important that is not obvious from the tree (rejected options, constraints, tribal knowledge, “we agreed X”).

**Risks & open questions** — Remaining unknowns and failure modes.

**Next actions** — Ordered list; depth follows tier emphasis below.

**Handoff metadata** — `created_at`, `tier` (`standard`|`frontier`), `recommended_tier` (if different from override), source harness if known, optional outgoing model note. Never invent secrets.

**Resume prompt** — A single fenced block the user can paste into a new chat. Always use the **absolute** dossier path plus worktree path, branch, and required tier so a receiver on the wrong checkout or wrong model class can still open the file and learn where to go. Example:

```text
Continue from the handoff dossier at <absolute-path-to-dossier>.
Worktree: <absolute-worktree-root> | Branch: <branch-name> | Required tier: <tier>
Open this chat on a <tier>-class model. Read Receiver startup first — for a frontier dossier, under-tier / Auto / unknown / unlabeled receivers must stop and ask to switch (or await `proceed anyway`); do not begin work.
```

Do **not** use only a repo-relative `.handoff/...` path in the resume prompt — different worktrees and repos cannot open it, and the receiver then cannot discover the correct branch from the dossier.

## Emphasis by tier

Both tiers use the full spine. Change depth, not inventory.

| Area | **standard** | **frontier** |
| --- | --- | --- |
| Next actions | Step-by-step, file-level, exact commands, verify steps | Outcome-oriented; leave sequencing to the receiver when safe |
| Hidden facts | Implementation gotchas and local conventions | Architectural constraints and design rationale |
| Plan quality | Do not assume a good plan will be invented | Trust derivation; invest tokens in intent, tradeoffs, risks |
| Length | Longer when the path is mechanical but non-obvious | Shorter on how-to; denser on why / boundaries |
