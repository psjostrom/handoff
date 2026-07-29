# Tier selection

Target agent tiers for handoff dossiers:

| Tier | Meaning | Example models (illustrative) |
| --- | --- | --- |
| `standard` | Mid-capability continuation | Claude Sonnet, GPT 5.6 Terra, Composer 2.5 |
| `frontier` | High-capability continuation | Claude Opus, Grok 4.5, GPT 5.6 Sol |

## Argument overrides

Parse invoke arguments for a tier token (case-insensitive):

- `standard` → tier `standard`
- `frontier` → tier `frontier`

If an override is present, use it and **do not** ask for confirmation.

## Recommendation (no override)

Prefer **standard** when:

- Remaining work is bounded implementation with clear interfaces
- Design/judgment is largely settled and this is a cost step-down
- The outgoing agent mostly finished the ambiguous part

Prefer **frontier** when:

- Architecture or approach is still open
- Ambiguity, cross-system debugging, or high risk remains
- The handoff is mostly “figure out the right approach”

When unsure, recommend **standard**.

Ask exactly (substitute the tier):

> I recommend a \<tier\> agent for this one — do you agree?

Proceed only after yes, or after the user names `standard` / `frontier`. If they reject without choosing a recognized tier, stop and do not write a dossier.
