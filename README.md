# Handoff

`handoff` writes one self-contained dossier so a fresh agent can continue a
task without polluted or unnecessarily expensive context. It is create-only:
there is no takeover command. The receiving agent reads the dossier and
continues only after its tier gate passes.

## Install

### Claude Code

Handoff installs through the Agent Plugins catalog:

```sh
claude plugin marketplace add psjostrom/agent-plugins
claude plugin install handoff@agent-plugins
```

### Codex

Handoff installs through the Agent Plugins catalog:

```sh
codex plugin marketplace add psjostrom/agent-plugins
codex plugin add handoff@agent-plugins
```

### Cursor

The public marketplace listing is not available. Load this repository as a
local Cursor plugin.

### OpenCode

OpenCode discovery requires the trusted global install. From this repository:

```sh
./install-opencode.sh install
```

This creates `~/.config/opencode/commands/handoff.md`. `--project` creates an
additional `.opencode/` discovery link for local iteration, but it does not
replace the global trusted shared-root install.

```sh
./install-opencode.sh install --project
./install-opencode.sh list
./install-opencode.sh uninstall
```

### Antigravity

Install directly from GitHub or local directory:

```sh
agy plugin install https://github.com/psjostrom/handoff
# Or from a local clone:
agy plugin install .
```

## Invoke

| Harness | Invocation | Optional tier |
| --- | --- | --- |
| Claude Code | `/handoff:handoff` | `standard` or `frontier` |
| Codex | `$handoff:handoff` | `standard` or `frontier` |
| Cursor | `/handoff` | `standard` or `frontier` |
| OpenCode | `/handoff` | `standard` or `frontier` |
| Antigravity | `/handoff` | `standard` or `frontier` |

An explicit `standard` or `frontier` argument wins. Without one, Handoff
recommends a tier and asks before writing. It creates exactly one dossier under
`.handoff/` and adds `.handoff/` to `.git/info/exclude`; tracked files and the
index remain unchanged.

## Behavior

Handoff may offer a handoff but never auto-runs without user confirmation. It
records workspace state, decisions, risks, verification, and next actions in a
dossier a fresh agent can use. A frontier dossier stops an under-tier, Auto,
unknown, or unlabeled receiver before repository work begins.

The dossier path is:

```text
<repo-root>/.handoff/<slug>-YYYYMMDD-HHMM.md
```

The shared skill and references define the detailed workflow, tier gate, slug
normalization, safety checks, and dossier contract:

- [`skills/handoff/SKILL.md`](skills/handoff/SKILL.md)
- [`skills/handoff/references/tier-selection.md`](skills/handoff/references/tier-selection.md)
- [`skills/handoff/references/dossier.md`](skills/handoff/references/dossier.md)
- [`skills/handoff/references/codex.md`](skills/handoff/references/codex.md)
- [`skills/handoff/references/claude-code.md`](skills/handoff/references/claude-code.md)
- [`skills/handoff/references/cursor.md`](skills/handoff/references/cursor.md)
- [`skills/handoff/references/opencode.md`](skills/handoff/references/opencode.md)
- [`skills/handoff/references/antigravity.md`](skills/handoff/references/antigravity.md)

## Develop

Handoff is a standalone repository at
<https://github.com/psjostrom/handoff>. Claude Code and Codex install through
the Agent Plugins catalog; Cursor and OpenCode use this repository directly.

Run after platform changes:

```sh
python3 scripts/validate_handoff.py
python3 -m unittest scripts/test_validate_handoff.py
agy plugin validate .
```

Licensed under [MIT](LICENSE).
