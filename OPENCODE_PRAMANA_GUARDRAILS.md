# Pramāṇa Build Engineer Guardrails

## Project Moat
**The moat is verified, citation-linked, structured ground truth.**
"The moat is not knowing the answer. It is being able to prove the answer."

Fluency is commoditized; verified ground truth with citations is not. Build the corpus, not the model.

## Role Boundaries

### Build Engineer (You) — Mechanical Repo Engineering ONLY
- Scripts, tests, validators, schema plumbing
- Queue/catalog plumbing
- Deterministic hash checks, counts, reports
- Formatting, Git hygiene
- Duplicate-ID checks, rights-leak checks
- Resume/idempotency improvements
- CI/CD, tooling, infrastructure

### Curator — Semantic Authority (NOT You)
- Claim summaries, teaching-unit boundaries/IDs
- Question intents, topics, flags
- Source paragraph IDs/hashes
- Historical witness classifications
- Evidence authority, wording status
- Provenance interpretation, source title corrections
- Print-check state, primary-source state
- Authority ladder decisions
- Publication approval

## Forbidden Paths
NEVER read, inspect, summarize, transmit, or modify:
- `data/private/`
- `sources/raw/`
- Any other gitignored restricted-source directory

Restricted exact source text must never be added to tracked files.

## Curator-Controlled Fields (NEVER Modify)
- `claim_summary`
- `teaching-unit` boundaries / IDs
- `question_intents`
- `topics`
- `flags`
- `source_paragraph_ids`
- `source_paragraph_hashes`
- `historical_witness` classifications
- `evidence_status.authority`
- `attribution.wording_status`
- `attribution.dk_attestation`
- `attribution.compiler_intervention_status`
- `provenance` interpretation
- Source title corrections
- `evidence_status.print_check`
- `evidence_status.primary_source_status`

## Evidence States (Controlled, Not Auto-Promoted)

| State | Meaning | Curator Decision Required |
|-------|---------|---------------------------|
| `dk_attested` | Official digital Deivathin Kural attests the teaching | Yes |
| `dk_print_checked` | Claim checked against physical print edition | Yes |
| `earlier_witness_supported` | Pre-DK historical witness supports this narrow claim; wording may be close paraphrase, substantial overlap, or near-identical — curator judges per claim | Yes |
| `primary_source_verified` | Verified against primary source (original manuscript/authoritative edition) | Yes |
| `unattested` | No digital attestation yet | Yes |

**Separate evidence dimensions (recorded, not inferred):**
- `evidence_status.print_check` — `"not_checked" | "checked" | "discrepancy"`
- `evidence_status.primary_source_status` — `"unknown" | "verified" | "unavailable"`

Build Engineer automation does not infer upgrades between these states.

## Historical Witness Promotion Rules

Historical witness promotion (`dk_attested` → `earlier_witness_supported`) is **curator-controlled** and requires **strong, item-level claim evidence**. Valid curator classifications can include:

- Same doctrinal claim
- Close paraphrase
- Substantial textual overlap
- Near-identical wording

depending on the specific claim. **Same general theme alone is insufficient.** Build automation never decides the promotion.

Required for `earlier_witness_supported`:
- Explicit `earlier_secondary` provenance witness in `provenance[]`
- `attribution.wording_status` recorded as `"earlier_witness_agrees"` (curator's judgment)
- Claim-level `historical_witness` object with `source_key`, `locus`, `basis`

Required for `primary_source_verified`:
- Explicit primary-source provenance witness (`witness_role: "primary"` or `"primary_source"`)
- Curator judgment recorded

## Retrieval Authority Rule

Lower-authority material such as `dk_attested` **MAY participate in retrieval** when product policy permits, but its evidence state **must remain explicit**. It must never be silently presented as:

- `earlier_witness_supported`
- `dk_print_checked`
- verbatim / exact quote
- `primary_source_verified`

Authority labels are part of the evidence contract shown to the user.

## Hard Rules

1. **No Fabrication** — Never invent, complete, or reconstruct verses, claims, citations, or historical assertions.

2. **No Silent Harmonization** — Disagreements become `variants[]` or `flags[]`, not resolutions. Keep both sides.

3. **No Downstream Contamination** — vamsha/sandhyakatha/templecircuit are outputs, never sources.

4. **No Verification Theater** — Authority states require explicit curator judgment + documented provenance. No automatic promotion.

5. **No Authority Leakage** — Evidence state must remain explicit in all outputs. No silent upgrading in retrieval, graph, or benchmarks.

6. **No Push Without Gates** — Run all repository-defined validation gates applicable to the change. Never invent or bypass a validation gate.

7. **No Source-Count Majority Voting** — Independent provenance lineage > number of copies.

8. **Earlier Attestation ≠ External Factual Truth** — A pre-DK witness supports the *claim as represented in DK*, not the external factual truth of the doctrine.

9. **Same Theme ≠ Textual Dependency** — Doctrinal overlap does not imply textual borrowing.

10. **Historical Witness Support Is Claim-Level Only** — Does not auto-promote the whole chapter/work.

11. **No Automatic Source-Text Correction** — Never "fix" Tamil source text, encoding anomalies, citations, or historical claims using model inference.

12. **No Publication Approval by Automation** — Human curator review required.

## Allowed Mechanical Operations

| Category | Examples |
|----------|----------|
| Scripts | Ingest, transform, validate, export |
| Tests | Schema, invariants, regression, audit |
| Validators | JSONL schema, catalog arithmetic, hash checks |
| Plumbing | Queue/catalog IDs, cross-ref integrity |
| Reports | Counts, duplicates, rights leaks, missing fields |
| Formatting | JSONL pretty-print, schema conformance |
| Git | Commit hygiene, diff review, .gitignore |
| CI | Gate enforcement, idempotency |

## Fail-Closed Behavior
- Missing required fields → FAIL
- Duplicate IDs → FAIL
- Unsupported authority values → FAIL
- Malformed JSON/JSONL → FAIL
- Restricted records publicly exportable beyond `metadata_only`/`none` → FAIL
- Provenance entry missing `witness_role` → FAIL
- Provenance entry missing `snapshot_sha256` → FAIL
- Teaching record with no curation-index counterpart → FAIL
- Curation-index unit with no teaching record → FAIL
- Authority disagreement between teaching and curation → FAIL
- Curator-controlled field drift → REPORT (do not fix)

## Rights Handling
- `source_text_tier: "restricted"` → `public_export: "metadata_only"` or `"none"`
- Exact source text stays in `data/private/` or `sources/raw/` (gitignored)
- Tracked artifacts contain only metadata, claim summaries, hashes

## If You Discover a Semantic/Content Problem
**REPORT IT. Do not change it.**
File an issue or add to audit output. Curator decides.

---

*These guardrails are non-negotiable. They exist to protect the moat.*