# Variants, contradictions, and evidence graph

## Why this layer exists
The corpus must preserve source differences without allowing a language model to harmonize them. A difference between two verified passages is evidence that the passages differ; it is **not automatically evidence that they contradict**.

## Relation model
Cross-source relations use one of:
- `agreement`
- `expansion`
- `omission`
- `textual_variant`
- `recension_difference`
- `scope_difference`
- `contradiction`
- `unresolved_difference`

Every side carries exact verified `support_ids`.

### Classification authority
- `deterministic_textual_diff`: may establish a textual difference, not a semantic contradiction.
- `edition_metadata`: may establish an edition/recension relationship documented by the source.
- `curator_reviewed`: required for semantic classifications such as contradiction, expansion, omission, agreement, or scope difference.

The system never sets a preferred side and never silently resolves a difference.

## Evidence graph
Nodes model reusable entities such as people, deities, avatars, episodes, texts, traditions, places, temples, concepts, festivals, rituals, and lineages.

An edge is admitted only when:
1. every `evidence_id` resolves to a verified corpus row; and
2. its derivation is auditable (`deterministic_metadata`, `curator_reviewed`, or an accepted cross-source relation).

Model-generated graph edges without verified evidence are rejected.

## Moat rule
**The graph is an index over evidence, not an alternate source of truth.**
If the graph and corpus ever disagree, the corpus evidence wins and the graph edge is re-reviewed.
