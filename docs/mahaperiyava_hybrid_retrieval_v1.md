# Mahaperiyava Hybrid Retrieval Foundation v1

This phase improves retrieval quality without changing the evidence model.

## Scope

- Corpus: 3,368 Deivathin Kural V1-V7 public-safe teaching records.
- Authority frontier at bootstrap: 3,329 `dk_attested`, 39 `earlier_witness_supported`, 0 `primary_source_verified`.
- Semantic embedding input is restricted to curator-authored `claim_summary`, `topics`, Tamil chapter title, and record identifier.
- Raw/restricted source text, private scans, provenance hashes, and earlier-witness text are not embedded.
- Retrieval scores cannot alter authority.

## Benchmark

`data/review/mahaperiyava_retrieval_benchmark_v2.json` contains 124 cases:

- 80 natural supported queries across English, Tamil and Roman-Tamil/mixed usage.
- 14 exact Tamil chapter-title lookups.
- 30 hard modern negatives that must abstain.
- Concept-level dev/test separation prevents language variants of the same concept from leaking across splits.

## Hybrid model

The first reproducible semantic component is
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, pinned to a specific model revision in code. It is used only to rank public-safe metadata. Lexical and semantic rankings are fused with reciprocal-rank fusion (RRF).

The existing lexical retriever remains untouched in this tranche. Product integration is allowed only after the held-out benchmark shows no trust regression.

## Commands

Structural/offline gate:

```bash
make mahaperiyava-hybrid-retrieval-structure-gate
```

Real multilingual benchmark (requires `requirements-hybrid.txt` and model acquisition):

```bash
make mahaperiyava-hybrid-retrieval-benchmark
```

The evaluator selects fusion parameters on `dev` only and reports untouched `test` metrics for lexical vs hybrid Top-1, Top-5, MRR and abstention.
