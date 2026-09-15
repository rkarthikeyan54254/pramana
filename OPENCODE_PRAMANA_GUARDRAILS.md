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

## Authority Ladder (NEVER Upgrade)
```
dk_attested
    ↓
earlier_witness_supported  (requires explicit earlier-secondary provenance witness + wording_status == "earlier_witness_agrees")
    ↓
primary_source_verified    (requires explicit primary-source provenance)
```

NEVER upgrade: `dk_attested → earlier_witness_supported → primary_source_verified`

## Hard Rules

1. **No Fabrication** — Never invent, complete, or reconstruct verses, claims, citations, or historical assertions.

2. **No Silent Harmonization** — Disagreements become `variants[]` or `flags[]`, not resolutions. Keep both sides.

3. **No Downstream Contamination** — vamsha/sandhyakatha/templecircuit are outputs, never sources.

4. **No Verification Theater** — `verified:true` / `authority: earlier_witness_supported` / `authority: primary_source_verified` requires independent witness + exact normalized match.

5. **No Authority Leakage** — Unverified rows never enter retrieval, graph, or benchmark authority.

6. **No Push Without Gates** — All moat checks must pass; `make moat-proof-gate` green is minimum.

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