# Antigravity invocation

Multi-tier handoff dossier generation reference for Google Antigravity.

## Invocation

- Command: `/handoff [standard|frontier]`
- Natural language: `prepare a handoff`, `write a handoff dossier`, `handoff to standard`, `handoff to frontier`

Bare `/handoff` is the Antigravity form. Read shared `SKILL.md` completely and follow its workflow. Shared `SKILL.md` owns the workflow.

## Gemini Model Tiers

- **`standard`**: `flash` (Gemini Flash). Suitable for bounded continuation, clear interfaces, and routine implementation.
- **`frontier`**: `flash` with `--effort high` (or `pro`). Required when architecture is open, high-complexity judgment is needed, or critical invariants apply.
