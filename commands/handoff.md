---
description: "Creates a self-contained handoff dossier for continuing work in a fresh agent session at standard or frontier capability. Use when the user invokes /handoff, asks for a handoff, context is polluted, or work should continue on a cheaper or stronger model."
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
