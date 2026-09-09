# Cross-Text Comparison — Milestone 1

## Goal
Compare concepts/episodes across multiple verified scripture corpora without harmonizing away differences.

## Moat contract
1. Only `verified:true` rows with a non-empty `verification_source` can support comparison claims.
2. Every claim declares a `source_key`, `dimension`, and one or more `support_ids`.
3. Support IDs must belong to the declared corpus/work; cross-source evidence cannot be silently reused.
4. Direct quotes must be extractive from supporting rows.
5. Missing evidence becomes an explicit `gap`; model memory cannot fill it.
6. Differences remain source-specific. The engine must not collapse them into one synthesized canonical account.

## Formal artifact
Schema: `schema/comparison.schema.json`

Key fields:
- `concept`, `question`
- `dimensions[]`
- `sources[]` with evidence/no-evidence status
- `claims[]` with source-specific support IDs and variant notes
- `gaps[]` for unsupported/conflicting dimensions
- fixed policy declaring verified-corpus authority and no silent reconciliation

## Engine
`rag/cross_text_compare.py`

The engine accepts a proposed comparison specification and corpus JSONL rows. It filters authority first, validates source/work ownership of evidence, validates extractive quotes, rejects unsupported claims, and emits gaps.

## Canonical first test case
Prahlāda–Narasimha is used as the first comparison fixture because it naturally spans Purāṇic and Bhakti traditions. The fixture is deliberately synthetic and tests the trust contract, not the historical content itself.

It includes:
- a verified Bhāgavata row
- a verified Viṣṇu Purāṇa row
- an unverified Āḻvār row

The unverified Āḻvār claim is rejected and represented as an evidence gap. This proves that comparison breadth cannot override verification status.

## Gate
Run:

```bash
make cross-text-gate
```

The gate includes all prior Tevaram verification gates plus comparison-engine and schema validation tests.
