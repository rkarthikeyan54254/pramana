---
pretty_name: Pramana Mahaperiyava Deivathin Kural V1-V7 Metadata
language:
- ta
- en
license: other
task_categories:
- text-retrieval
- question-answering
tags:
- rag
- provenance
- tamil
- indic
---

# Pramāṇa — Mahaperiyava / Deivathin Kural V1–V7 metadata-only release candidate

**Status: release candidate. Publication approval is still false.**

This bundle contains 3,368 curator-authored teaching metadata records covering Deivathin Kural Volumes 1–7. It is designed for evidence-grounded retrieval and answer attribution.

## Critical rights boundary

This is a **metadata-only** dataset. Deivathin Kural source text is not redistributed. The underlying official digital witnesses are used for private/reference verification under their governing terms. Curator summaries are not verbatim quotations and must never be presented as Mahaperiyava's exact words.

The Hugging Face `license` field is intentionally `other` until the project owner chooses and records explicit terms for the Pramāṇa-authored metadata. This card does not grant rights in the underlying Deivathin Kural source.

## Evidence status

At this release-candidate snapshot:

- 3,335 records are `dk_attested`
- 33 records are `earlier_witness_supported`
- 0 records are `dk_print_checked`
- 0 records are `primary_source_verified`

`dk_attested` means the teaching is attested in Deivathin Kural as a teaching of Mahaperiyava. It does not mean verbatim oral wording, print-edition verification, or primary-source verification.

## Fields

Each row exposes only public-safe metadata: stable ID, curator claim summary, topics, context flags, volume/chapter/title/URL, attribution status, evidence status, a restricted provenance subset, rights classification, a generated citation, and a SHA-256 of the exported metadata record.

Private review anchors, source paragraphs, curator notes containing private review references, provenance loci, and exact source text are excluded.

## Intended use

- evidence-grounded RAG over Mahaperiyava teaching metadata
- Tamil/English retrieval experiments
- claim-to-source navigation
- provenance-aware answer generation
- refusal/abstention evaluation

## Not intended for

- reconstructing Deivathin Kural source text
- quoting Mahaperiyava verbatim from curator summaries
- training a model to imitate Mahaperiyava
- treating every teaching as print-checked or independently historical
- bypassing the rights of the underlying source edition

## Retrieval benchmark

The release builder can include a deterministic regression benchmark containing the manually curated Phase-8 cases, stratified proposition-anchored tests across all seven volumes, Tamil chapter-title lookups, and modern false-attribution negatives.

The benchmark measures retrieval and refusal behavior. It does not establish source-text authenticity beyond the evidence status of each record, and it does not qualify a particular embedding model unless that model is separately benchmarked.

## Publication approval

Publication approval remains separate from corpus hardening. Before public Hugging Face upload, the owner must choose metadata license/terms, namespace/repository name, and release version, then rerun the release gate and inspect the manifest.
