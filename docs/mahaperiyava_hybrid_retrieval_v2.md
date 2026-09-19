# Mahaperiyava Hybrid Retrieval Tuning v2

Phase 13 is a retrieval-quality tranche.  It does not modify teaching authority and does not switch the product answer backend.

## Why this phase exists

Phase 12 improved the original held-out benchmark from Top-1 0.6071 to 0.6429 and MRR 0.6399 to 0.6815 while preserving 1.0 abstention.  The failure distribution showed that Tamil-script natural queries remained the dominant weakness.

## Changes

- Expands the benchmark from 124 to 154 cases.
- Adds 24 natural supported questions across English, Tamil, and Roman-Tamil.
- Adds multilingual hard negatives so fail-closed behavior is not tested only in English.
- Separates semantic fields into claim/topic and Tamil-title/topic representations.
- Expands query-side Tamil and Roman-Tamil concept normalization.
- Compares two pinned multilingual embedding profiles on dev only:
  - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
  - intfloat/multilingual-e5-small
- Tunes lexical, claim-semantic, title-semantic, and title-overlap fusion on dev only.
- Evaluates test only after the profile/config is selected.

## Trust boundary

Semantic retrieval operates only over curator-authored public-safe metadata.  Restricted source text, private scans, provenance hashes, and earlier-witness text are excluded.  Retrieval scores never change authority.

## Product integration rule

No production switch occurs in Phase 13.  A feature-flag integration is permitted only if the checkpoint reaches its held-out quality target and a separate answer-layer regression gate remains green.
