# Claude Code invocation

Active harness: **Claude Code**.

## Invocation

- Command: `/handoff:handoff`
- Optional `$ARGUMENTS`: `standard`, `frontier`

Claude Code command discovery and skill discovery both use the `handoff` name. `/handoff:handoff` and the discovered skill run the same shared workflow; prefer either entrypoint, with no divergent behavior.

Parse `$ARGUMENTS` for a tier token before shared tier selection. Shared `SKILL.md` owns the workflow.
