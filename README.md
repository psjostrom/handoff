# Handoff

`handoff` writes one self-contained dossier so a fresh agent can continue a
task without polluted or unnecessarily expensive context. It is create-only:
there is no takeover command. The receiving agent reads the dossier and
continues only after its tier gate passes.

The shared workflow is
[`skills/handoff/SKILL.md`](skills/handoff/SKILL.md). Platform adapters and
the dossier contract live in
[`skills/handoff/references/`](skills/handoff/references/).

## When to use it

Use Handoff when:

- context is polluted or too large;
- the next step should move to a cheaper standard agent;
- unresolved architecture, debugging, or risk needs a stronger frontier agent;
- the current agent is ending and another session must continue safely.

Handoff may offer a handoff, but it must not create one automatically. It runs
only after the user invokes it or explicitly accepts an offer.

## Invoke it

| Harness | Invocation | Optional tier |
| --- | --- | --- |
| Codex | `$handoff:handoff` | `standard` or `frontier` |
| Claude Code | `/handoff:handoff` | `standard` or `frontier` |
| Cursor | `/handoff` | `standard` or `frontier` |
| opencode | `/handoff` | `standard` or `frontier` |

Examples:

```text
Use $handoff:handoff to prepare the task for a fresh agent.
Use $handoff:handoff standard.
Use $handoff:handoff frontier.
```

```text
/handoff:handoff standard
/handoff:handoff frontier
```

Cursor and opencode use the bare `/handoff` form. Do not use Claude's
`/handoff:handoff` or Codex's `$handoff:handoff` syntax in those harnesses.

## Offer versus execution

The skill distinguishes an offer from an execution:

1. The agent may explain why a handoff would help.
2. The user accepts the offer or invokes Handoff directly.
3. Handoff gathers facts, selects a tier, writes one dossier, reports its path,
   and stops.

It does not continue the original implementation after writing the dossier
unless the user starts a new task and asks for that work.

## Tier selection

An explicit `standard` or `frontier` argument wins and does not require a
confirmation question. Without an argument, Handoff recommends a tier and asks
exactly:

```text
I recommend a <tier> agent for this one — do you agree?
```

It stops if the recommendation is rejected without a recognized tier choice.

| Tier | Use when | Example agent families |
| --- | --- | --- |
| `standard` | Bounded continuation with clear interfaces, settled design, or a cost step-down | Claude Sonnet, GPT 5.6 Terra, Composer 2.5 |
| `frontier` | Architecture is open, ambiguity remains, or cross-system/high-risk judgment is needed | Claude Opus, Grok 4.5, GPT 5.6 Sol |

When unsure, it recommends `standard`.

The tier is a contract, not a preference. A frontier dossier must stop an
under-tier, Auto, unknown, or unlabeled receiver before that receiver explores
the repository. A standard dossier may be received by any recognized agent,
including a frontier agent.

## Facts gathered

Handoff prefers cheap tool verification over chat memory. It records:

- repository root and worktree path;
- branch, `HEAD`, and linked-worktree status when relevant;
- `git status --short` and dirty/untracked summary;
- mission and definition of done;
- completed, in-progress, and not-started work;
- decisions and hidden facts;
- risks, open questions, and exact next actions;
- useful commands and verification already run.

If the git root cannot be identified, Handoff stops and asks. If there is no
code yet, it still writes a dossier based on mission, decisions, and next
actions.

It does not modify existing repository files or the dirty working tree. It does
not stash, commit, clean, or otherwise mutate Git work state. It creates
exactly one new dossier file under `.handoff/`, and may add the required
`.handoff/` entry to the repository-local Git exclude file.

## Dossier path and safety

Every run writes exactly one new file under the target repository root:

```text
<repo-root>/.handoff/<slug>-YYYYMMDD-HHMM.md
```

Before writing, it:

1. resolves `<repo-root>` with `git rev-parse --show-toplevel`;
2. uses that root for every `.handoff/` path;
3. ensures `.handoff/` is in the repository-local Git exclude file;
4. verifies the exact future path is ignored;
5. creates the directory and verifies the candidate remains strictly beneath it.

It never edits a global gitignore. If exclusion or containment cannot be
established, it stops before writing.

### Filename normalization

The slug comes from the mission:

- lowercase;
- split on whitespace and separators (`_`, `/`, `\`, `.`, and punctuation other
  than `-`);
- keep only `a-z`, `0-9`, and `-`;
- collapse repeated hyphens and trim them;
- require two to six non-empty kebab-case words;
- reject empty, absolute, traversal, or unsafe values and fall back to
  `handoff`.

If the filename exists, Handoff adds `-2`, `-3`, and so on while re-checking
containment.

## Dossier contents

Every tier uses the same sections, in this order:

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

### Receiver startup

The receiver must follow this order:

1. Read the required tier from Handoff metadata.
2. Classify the active model using the receiver rules in
   [`skills/handoff/references/tier-selection.md`](skills/handoff/references/tier-selection.md).
3. For a frontier dossier, stop immediately if the receiver is under-tier,
   Auto, unknown, or unlabeled. Ask the user to switch models or explicitly
   reply `proceed anyway`.
4. Do not inspect the workspace, search files, edit, or execute next actions
   before that gate passes.
5. After the gate passes, read the full dossier, verify workspace fields against
   reality, restate the next action in one sentence, then begin work.

The mismatch response is intentionally short: required tier, current
under-tier, Auto, unknown, or unlabeled status, and the switch-or-override
instruction.

### Mission

States the goal, definition of done, and explicit non-goals.

### Workspace

Records absolute repository/worktree path, branch, `HEAD` SHA, linked-worktree
status, relevant remotes, and dirty/untracked summary.

### State of work

Separates done, in progress, and not started work. Names touched paths and
commands/tests already run, with results. It must say when no code exists.

### Decisions and risks

Captures choices not obvious from the tree, rejected options, constraints,
tribal knowledge, remaining questions, and concrete failure modes.

### Next actions

Lists ordered, actionable continuation steps. Standard dossiers favor exact
file paths and commands; frontier dossiers spend more space on intent,
architecture, and risk than mechanical sequencing.

### Metadata

Includes `created_at`, `tier`, optional `recommended_tier`, source harness when
known, and optional outgoing model note. It never invents secrets.

### Resume prompt

Contains one fenced prompt with the absolute dossier path, worktree path,
branch, and required tier. A repo-relative path alone is insufficient because a
new chat may open another worktree.

Example shape:

```text
Continue from the handoff dossier at <absolute-path>.
Worktree: <absolute-worktree> | Branch: <branch> | Required tier: <tier>
Open this chat on a <tier>-class model. Read Receiver startup first.
```

## Platform behavior

### Codex

Invoke `$handoff:handoff [standard|frontier]`. The Codex adapter owns only the
entrypoint syntax; the shared skill owns facts, tier selection, and dossier
format.

### Claude Code

Invoke `/handoff:handoff [standard|frontier]`. The command reads the shared
skill and Claude adapter through `${CLAUDE_PLUGIN_ROOT}`.

### Cursor

Invoke `/handoff [standard|frontier]`. Bare `/handoff` is the Cursor syntax.

### opencode

Invoke `/handoff [standard|frontier]`. The thin command resolves `SHARED_ROOT`
from the trusted global install symlink and rejects an unresolved install. Do
not use Claude plugin prefixes or Codex `$skill` syntax in opencode prompts.

## Troubleshooting

| Symptom | Meaning | Action |
| --- | --- | --- |
| Handoff runs without confirmation | It was not explicitly invoked or accepted | Stop; the workflow must be user-authorized |
| Git root cannot be found | Workspace is not inside a repository | Re-run from the target repository |
| Tier rejected | No recognized `standard`/`frontier` choice | Supply one of those exact arguments |
| `.handoff/` is not ignored | Safe output containment is not established | Fix repository-local exclusion and retry |
| Frontier receiver stops | Receiver is under-tier, Auto, unknown, or unlabeled | Switch to a frontier-class model or reply `proceed anyway` |
| opencode cannot resolve shared root | Handoff is not installed through its trusted symlink | Run the opencode handoff installer |

## Source map

- [`skills/handoff/SKILL.md`](skills/handoff/SKILL.md) — complete shared
  workflow and stop conditions.
- [`skills/handoff/references/tier-selection.md`](skills/handoff/references/tier-selection.md)
  — tier recommendation and receiver gate.
- [`skills/handoff/references/dossier.md`](skills/handoff/references/dossier.md)
  — exact path, slug, sections, resume prompt, and tier emphasis.
- [`skills/handoff/references/codex.md`](skills/handoff/references/codex.md),
  [`skills/handoff/references/claude-code.md`](skills/handoff/references/claude-code.md),
  [`skills/handoff/references/cursor.md`](skills/handoff/references/cursor.md),
  and [`skills/handoff/references/opencode.md`](skills/handoff/references/opencode.md)
  — platform invocation adapters.
- `commands/` and `opencode/commands/` — thin discovery shells.

## Validation

After changing Handoff platform files, run:

```sh
python3 plugins/handoff/scripts/validate_handoff.py
```

After changing validator logic, also run:

```sh
python3 -m unittest plugins/handoff/scripts/test_validate_handoff.py
```
