# Handoff

`handoff` writes one self-contained dossier so a fresh agent can continue a
task without polluted or unnecessarily expensive context. It is create-only:
there is no takeover command. The receiving agent reads the dossier and
continues only after its tier gate passes.

The shared workflow is
[`skills/handoff/SKILL.md`](skills/handoff/SKILL.md). Platform adapters and
the dossier contract live in
[`skills/handoff/references/`](skills/handoff/references/).

## Install

### Antigravity

Install directly from GitHub or local directory:

```sh
agy plugin install https://github.com/psjostrom/handoff
# Or from local clone:
agy plugin install .
```

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

The standalone [Handoff plugin](https://github.com/psjostrom/handoff) Cursor
marketplace listing is pending review and is not yet available to install. Once
accepted, it will provide the bare `/handoff` command.

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

## Invoke

| Harness | Invocation | Optional tier |
| --- | --- | --- |
| Antigravity | `/handoff` | `standard` or `frontier` |
| Codex | `$handoff:handoff` | `standard` or `frontier` |
| Claude Code | `/handoff:handoff` | `standard` or `frontier` |
| Cursor | `/handoff` | `standard` or `frontier` |
| OpenCode | `/handoff` | `standard` or `frontier` |

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

The detailed workflow, tier gate, slug normalization, safety checks, and
dossier contract remain in the shared skill and references:

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
<https://github.com/psjostrom/handoff>. Claude Code and Codex keep catalog
entrypoints; Cursor and OpenCode discover this repository directly.

Run after platform changes:

```sh
python3 scripts/validate_handoff.py
python3 -m unittest scripts/test_validate_handoff.py
agy plugin validate .
```

## Migration

Existing Claude Code and Codex installs continue to use the Agent Plugins
catalog. Reinstall Cursor from this repository. For a legacy OpenCode catalog
link, run this guarded replacement, then install:

```sh
if [ ! -L "$HOME/.config/opencode/commands/handoff.md" ]; then
  echo "Refusing: Handoff command is not a symlink." >&2
  exit 1
fi
case "$(readlink "$HOME/.config/opencode/commands/handoff.md")" in
  */agent-plugins/plugins/handoff/opencode/commands/handoff.md)
    rm "$HOME/.config/opencode/commands/handoff.md"
    ;;
  *)
    echo "Refusing: Handoff command does not point at the legacy catalog." >&2
    exit 1
    ;;
esac
./install-opencode.sh install
```

It leaves any other link intact.
