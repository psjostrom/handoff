---
description: "Write a handoff dossier for a fresh standard or frontier agent"
argument-hint: "[standard|frontier]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Edit", "Write", "AskUserQuestion"]
---

# Handoff

**Argument:** "$ARGUMENTS"

## Active harness

You are the **Claude Code** entrypoint for handoff.

Read completely, in order (plugin-absolute paths):

1. `${CLAUDE_PLUGIN_ROOT}/skills/handoff/SKILL.md`
2. `${CLAUDE_PLUGIN_ROOT}/skills/handoff/references/claude-code.md`

## Claude argument parsing

Before following the shared workflow, parse `$ARGUMENTS` for a tier token (`standard`, `frontier`). Pass the result into shared tier selection.

Then execute the shared workflow end-to-end. Do not redefine dossier sections or tier heuristics here.
