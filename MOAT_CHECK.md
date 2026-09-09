# MOAT CHECK — required for every workstream

**Moat:** The asset is verified, citation-linked, structured ground truth. Fluency is not the product moat.

Before promoting any workstream, answer all six:

1. **Ground truth:** Does this add or improve source-backed evidence rather than model-generated prose?
2. **Provenance:** Can every promoted record/edge trace to an exact source and stable corpus ID?
3. **Verification:** Is independent verification explicit, with disagreement preserved rather than silently reconciled?
4. **Structure:** Does the result become queryable/reusable data (verse, locus, variant, evidence edge), not just narrative text?
5. **Refusal boundary:** Can the product distinguish “not verified / not in corpus” from “known,” and refuse the former?
6. **Feedback-loop safety:** Are generated explanations kept out of the authoritative corpus unless independently sourced?

## Promotion rule
- **6/6 YES:** strengthens the moat; proceed.
- **Any NO:** do not promote as authoritative corpus/product evidence. Keep as staging/research or redesign.

## Current realization layer assessment
- Verified-only retrieval: YES to all 6.
- LLM freestyle answer generation without evidence IDs: FAILS #1, #2, #5; prohibited as authoritative mode.
- Embeddings/vector search: neutral infrastructure; acceptable only if filtering to verified evidence happens before answer generation.

## Semantic retrieval rule

**Embeddings may broaden recall; they must never broaden authority.**

- Filter to verified records *before* creating/querying the semantic index.
- Similarity score is a retrieval heuristic, never a verification signal.
- An unverified row MUST remain unreachable even if it is the nearest vector match.
- Every assembled answer claim must carry one or more `support_ids` pointing to verified records.

## Claim authenticity rule
- A quote/scriptural claim may be marked authenticated only by exact/normalized matching against **verified** corpus evidence.
- Text present only in staging/unverified records is treated as **not verified**.
- Fuzzy/semantic similarity may surface inspection candidates; it can never establish authenticity.

## Devī Māhātmya full-certification gate
- [x] Primary text comes from a pinned authoritative e-text, not model memory.
- [x] Second witness is edition-aware; numbering drift is preserved rather than hidden.
- [x] Secondary copyrighted meanings/commentary are excluded from corpus ingestion.
- [x] Script conversion is deterministic and fail-closed, with independent spot checks.
- [x] Claim-by-claim synthesis requires verified `support_ids` and extractive quotes.
- [x] Unsupported synthesis claims are rejected; generation cannot become ground truth.
- [ ] Full 13-chapter raw alignment has physically run on locally captured source files.

The final unchecked item is an execution/acquisition gate, not an invitation to fill data from the model.

## Tevaram second-source verification gate
- [x] Primary and secondary witnesses have independent scholarly/e-text provenance documented.
- [x] Structural identity is source-native `tirumurai.patikam.verse`, not display running number.
- [x] IFP Tamil-script PIFI text is used directly; no LLM transliteration is needed for verification.
- [x] Only conservative normalized exact text can auto-certify a row.
- [x] Mismatches are preserved for review/variant analysis; fuzzy similarity cannot establish truth.
- [x] IFP English gloss and enrichment remain outside the authoritative public corpus.
- [ ] Full 798-patikam/8,240-row real-source comparison must physically run after raw snapshots are acquired.

Moat result: architecture is 6/6 aligned; final unchecked item is an execution/acquisition gate, not a truth shortcut.

## Cross-text comparison moat rule
Cross-text breadth must never broaden authority. A comparison is admissible only when each source-specific statement is backed by verified IDs from that declared corpus/work. Missing evidence is a first-class output (`gaps[]`), not an invitation for the model to harmonize from memory. Differences and variants remain source-specific.

## Contradiction / variant rule
- A textual difference can be detected mechanically; a semantic contradiction cannot be inferred merely because wording differs.
- `contradiction`, `agreement`, `expansion`, `omission`, `scope_difference`, and other semantic relationships require explicit curator review.
- Both sides retain their verified support IDs; no preferred reading is silently selected.
- The relation layer may describe disagreement but may not promote an unsourced reconciliation.

## Evidence graph rule
- Every graph edge must resolve to one or more verified corpus `evidence_ids`.
- Semantic edges require curator review or an already accepted evidence-backed relation.
- Generated/model-inferred edges without verified evidence are rejected.
- The graph is a derived index over corpus evidence, never a replacement source of truth.

## Real graph population moat checkpoint
- [x] Nodes themselves are evidence-gated; a model cannot invent an entity and then attach valid-looking edges to it.
- [x] Genealogy edges are admitted only from explicit relational wording or curator-reviewed cross-locus evidence.
- [x] Cross-text agreement is a separately reviewed relation object; matching entity names do not automatically create semantic agreement.
- [x] `relation_ids` in graph nodes/edges are audited against accepted relation sets.
- [x] GRETIL conversion defects are not silently repaired: Viṣṇu Purāṇa 1.17.10 remains held back pending transcription-variant handling.
- [x] Secondary-site translations/enrichment are excluded; only Sanskrit witness text is used for verification.
- [x] Temple/place edges are withheld until the textual association itself is sourced.

**Moat result: 6/6 YES.** The graph is becoming more useful while remaining a derived, inspectable index over verified corpus evidence—not an LLM-populated mythology knowledge base.

## Checkpoint: temple / genealogy / ritual expansion
**Moat status: PASS.**
- Temple edges point only to a generic scriptural Hari/Keśava shrine because the cited verses do not identify a modern temple.
- Genealogy uses explicit Sanskrit birth/descent wording; ambiguous Prahlāda→Virocana direction is curator-reviewed, while Virocana→Bali is deterministic from `balir jajñe virocanāt`.
- Festival/ritual nodes preserve the source's own scope: `annual autumn mahāpūjā` is not silently renamed to a modern festival, and tithi/upavāsa claims stay at the level explicitly supported by the verse.
- No model-generated enrichment becomes graph authority.

## 2026-09-09 — Moat proof suite checkpoint

The project now has three end-to-end evidence experiences and a machine-checkable benchmark:

1. **Verify a Claim** — authenticates only exact text found in verified rows; fuzzy similarity never authenticates.
2. **Compare Sources** — keeps texts separate, requires verified support IDs, preserves gaps, and exposes only reviewed semantic relations.
3. **Trace Evidence** — traverses the evidence graph only through edges whose evidence IDs resolve to verified rows.

`benchmark/pramana_moat_benchmark_v1` currently passes 5/5 native cases (16/16 checks). This is a **self-consistency baseline**, not proof of competitive superiority. The benchmark becomes moat evidence only after the same prompts are scored against competing products/models.

New operating rule: progress should be measured by (a) verified rows, and (b) benchmark questions answered more audibly/accurately than alternatives — not by number of pipelines built.
