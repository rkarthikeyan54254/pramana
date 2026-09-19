# Mahaperiyava cross-encoder reranker v4

Phase 15 keeps Phase-14 candidate generation and changes only the final ranking stage.

## Why

Phase 14 achieved 1.000 held-out candidate recall, proving the correct record is already
present in the candidate set. The remaining problem is therefore ranking rather than
candidate discovery.

## Architecture

1. Phase-14 query understanding and candidate generation.
2. Existing fail-closed modern/OOD guard.
3. Exact-title route remains deterministic.
4. A pinned multilingual mMARCO MiniLM cross-encoder scores only public-safe candidate
   metadata.
5. Phase-14 heuristic rank and cross-encoder rank are fused using RRF.
6. Fusion weights are selected separately for English, Tamil and Roman-Tamil on DEV only.
7. Held-out TEST is evaluated after selection.

For Tamil and Roman-Tamil, the cross-encoder receives the public-safe English concept
view produced by the Phase-14 query normalizer. This avoids assuming that the external
reranker itself has authoritative Tamil coverage.

## Trust boundary

The reranker receives only curator-authored `claim_summary`, `topics`, and Tamil chapter
title. It never receives restricted Deivathin Kural source text, private scans, witness
text, hashes, or source snapshots.

Reranking cannot:
- change evidence authority;
- convert an abstention into an answer;
- create source claims;
- enter generated material into the corpus.

Even if the benchmark threshold is met, this phase authorizes only a later shadow-mode
integration. Product retrieval is not switched here.
