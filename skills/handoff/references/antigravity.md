# Antigravity invocation

Multi-tier handoff dossier generation reference for Google Antigravity.

## Invocation

- Command: `/handoff [standard|frontier]`
- Natural language: `prepare a handoff`, `write a handoff dossier`, `handoff to standard`, `handoff to frontier`

Bare `/handoff` is the Antigravity form. Shared `SKILL.md` owns the workflow.

## Gemini Model Tiers

- **`standard`**: Gemini Flash (e.g. Gemini 2.5/3.0 Flash). Suitable for bounded continuation, clear interfaces, and routine implementation.
- **`frontier`**: Gemini 3.7 Flash with High Reasoning (`reasoningEffort: "high"`) or Gemini Pro. Required when architecture is open, high-complexity judgment is needed, or critical invariants apply.
