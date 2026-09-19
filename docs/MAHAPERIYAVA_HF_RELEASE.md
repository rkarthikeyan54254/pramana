# Mahaperiyava Hugging Face release hardening

This lane turns the completed V1–V7 teaching metadata and Phase 8–10 product stack into a **reproducible Hugging Face-safe release candidate** without redistributing Deivathin Kural source text.

## What the gate does

`make mahaperiyava-hf-release-gate` performs four jobs:

1. Runs an expanded release retrieval benchmark.
2. Builds a strict metadata-only Hugging Face bundle under `dist/huggingface/mahaperiyava-deivathin-kural-v1-v7/`.
3. Re-audits every exported field, record, manifest hash, volume count, authority count, and leakage marker.
4. Produces a prioritized, non-promoting triage of the existing 30-record evidence-depth queue.

The bundle is included in the normal GitHub Actions `dist/` artifact.

## Bundle contents

- `records.jsonl` — 3,368 public-safe teaching metadata rows
- `dataset_info.json` — volume/authority/flag counts and rights status
- `README.md` — Hugging Face dataset card
- `release_policy.json` — exact allowlist/denylist contract
- `retrieval_eval_cases.json` — manually curated Phase-8 semantic cases
- `retrieval_benchmark.json` — expanded release regression benchmark when supplied
- `release_manifest.json` — SHA-256 and byte count for every bundled file

## Explicit exclusions

The builder does not export exact source text, private review paragraph references, private curation anchors, curator notes, provenance loci, or source packet hashes.

The release is therefore not a Deivathin Kural text dump. It is a provenance-aware RAG metadata corpus.

## Evidence-depth triage

The existing 30-record queue is scored only for review order. Sensitive scientific/medical, harmful historical advice, gender/caste, political/historical, and high-retrieval-use records rise to the top. Triage never changes authority.

## Remaining human publication decision

Passing this gate means the **technical release candidate** is green. It does not flip `publication_approval` to true. Before uploading publicly to Hugging Face, choose explicit terms for the Pramāṇa-authored curator metadata and record the Hugging Face namespace/repository/version.

If the public product is marketed specifically as using semantic embeddings, benchmark the chosen embedding model separately. The current release benchmark qualifies the deterministic evidence-retrieval contract, not an untested vector model.
