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

## Receiver classification

Every dossier’s **Receiver startup** must gate on the metadata `tier` before work. Writers copy the rule into the dossier; receivers apply it to the live chat model.

| Required `tier` | May proceed without override | Must stop (ask to switch, or await `proceed anyway`) |
| --- | --- | --- |
| `frontier` | Opus / Grok 4.5 / Sol-class (and peers) | Sonnet / Terra / Composer / Auto / unknown / unlabeled |
| `standard` | Any recognized agent, including frontier | (none — over-tier is OK) |

This is a soft contract gate (prompt-enforced). Harnesses do not hard-block model selection; the dossier must still instruct under-tier receivers to stop before exploring or editing.
