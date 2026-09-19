# Mahaperiyava candidate generation + constrained reranking v3

Phase 14 changes retrieval architecture rather than continuing global embedding-fusion tuning.

## Motivation

Phase 13 preserved 100% abstention and improved held-out Top-5 to 0.80, but held-out
Top-1 fell to 0.425. Tamil and Roman-Tamil were the main ranking weaknesses.

The Phase-14 hypothesis is:

1. understand the query first;
2. generate a broad evidence candidate set from multiple independent views;
3. rerank only those candidates;
4. choose language-specific reranking profiles on DEV only;
5. preserve all evidence/authority boundaries.

## Public-safe inputs only

The implementation uses curator metadata already permitted for retrieval:
`claim_summary`, `topics`, Tamil chapter title, and record identity. It does not embed
restricted Deivathin Kural text, private scans, witness text, provenance hashes, or
source snapshots.

## Candidate generation

- original lexical query
- augmented lexical query
- concept-only lexical query
- semantic claim candidates
- semantic title candidates

Tamil and Roman-Tamil aliases are converted into a compact concept-only English/Sanskrit
view so Tamil surface forms do not dilute the lexical coverage calculation.

## Reranking

A small explicit set of deterministic profiles combines reciprocal ranks, concept
coverage, and Tamil-title character overlap. The best profile is chosen independently
for `en`, `ta`, and `roman_ta` using DEV cases only.

The test split is evaluated exactly once after profile selection.

## Product boundary

Even if the Phase-14 quality threshold is met, this checkpoint authorizes only a later
shadow-integration phase. It does not switch the product retriever.
