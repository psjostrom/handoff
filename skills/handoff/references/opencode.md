# opencode invocation

Active harness: **opencode**.

## Invocation

- Command: `/handoff`
- Optional `$ARGUMENTS`: `standard`, `frontier`

Resolve `SHARED_ROOT` from the install symlink as instructed by the thin command shell, then read `$SHARED_ROOT/SKILL.md`. Shared skill owns the workflow. Do not use Claude plugin prefixes or Codex `$skill` syntax in opencode prompts.
