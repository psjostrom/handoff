---
description: "Creates a self-contained handoff dossier for continuing work in a fresh agent session at standard or frontier capability. Use when the user invokes /handoff, asks for a handoff, context is polluted, or work should continue on a cheaper or stronger model."
---

# Handoff

**Argument:** "$ARGUMENTS"

## Active harness

You are the **opencode** entrypoint for handoff.

Resolve the shared skill root from the **global** install symlink only (never from the target repository):

```bash
SHARED_ROOT=""
f="${HOME}/.config/opencode/commands/handoff.md"
if [ -L "$f" ]; then
  real=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$f")
  case "$real" in
    */plugins/handoff/opencode/commands/handoff.md)
      candidate=$(cd "$(dirname "$real")/../../skills/handoff" && pwd)
      if [ -f "$candidate/SKILL.md" ]; then
        SHARED_ROOT="$candidate"
      fi
      ;;
  esac
fi
if [ -z "$SHARED_ROOT" ]; then
  echo "Could not resolve shared handoff skill root from ~/.config/opencode. Run ./install-opencode.sh install handoff first." >&2
  exit 1
fi
printf 'SHARED_ROOT=%s\n' "$SHARED_ROOT"
```

Read completely, in order, using absolute paths under `$SHARED_ROOT`:

1. `$SHARED_ROOT/SKILL.md`
2. `$SHARED_ROOT/references/opencode.md`

## opencode argument parsing

Parse `$ARGUMENTS` for `standard`, `frontier`, then execute the shared workflow. Do not duplicate dossier or tier prose here.
