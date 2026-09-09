# Bhakthi Corpus

A provenance-first, source-auditable corpus for Tamil Bhakthi and Sanskrit scripture.

**Asset thesis:** the corpus is the durable asset; models are replaceable. The dataset must preserve exact text, stable IDs, source provenance, textual variants, tradition/recension distinctions, and verification state.

## Current mapped scope
- Nalayira Divya Prabandham: **24 works / 4,000 pasurams**
- Andal: **173 pasurams** (Tiruppavai 30 + Nachiyar Tirumozhi 143)
- Tevaram: **7 Tirumurai / 8,240 numbered verses** mapped to source blocks
- Sanskrit discovery lane: Bhagavad Gita + Isha Upanishad started

## Safety invariant
`ingested` does not mean `verified`. Nothing becomes publishable merely because a parser produced a row.

## Useful commands
```bash
make audit             # catalog + schema smoke tests
make fetch             # raw source snapshots; network-enabled host required
make ingest-tiruppavai
make ingest-nachiyar
python scripts/ingest_work.py perumal_tirumozhi
python scripts/quality_report.py data
python scripts/audit_numbering.py --input <raw.html> --start 1 --end 100
```

See `MASTER_PLAN.md`, `EXECUTION_PLAN.md`, `STATUS.md`, and `SOURCES.md`.

## Ithihasa & Purana expansion
The project now uses a two-level strategy for very large Sanskrit works: ingest the **full canonical parent corpus**, while certifying high-demand slices early so the grounded assistant becomes useful before 100k+ verses are curated. See `schema/ithihasa_purana_catalog.json`.

Tier-1 anchors are Valmiki Ramayana, Mahabharata Critical Edition, Harivamsha, Bhagavata Purana, Vishnu Purana and Devi Mahatmya. Derived products such as episode graphs and genealogy graphs are always evidence-backed views over verified verse IDs, never replacement source material.

### Mahābhārata CE pipeline
The repo now includes a strict parent ingester for the finalized Bombay-Indology/BORI Critical Edition Unicode-Roman files plus curated materializers for Nala-Damayanti, Savitri, Yaksha Prashna (broad frame + exact question core), Vidura Niti, Narayaniya, and Vishnu Sahasranama. Run `make completion-gate` for the full regression suite; once `MBh01.txt`–`MBh18.txt` are acquired, run `make mahabharata-parent` followed by `make mahabharata-materialize`.

## Verified-only retrieval
The first realization layer lives under `rag/`. It deliberately starts with deterministic lexical retrieval so the trust boundary is easy to audit. Only records with `verified:true` and a non-empty `verification_source` are eligible. If nothing verified matches, the tool refuses rather than falling back to model memory. See `MOAT_CHECK.md` and `rag/ANSWER_POLICY.md`.

Run:
```bash
make realization-gate
python rag/query.py "Narayana" tests/rag/verified_mix.jsonl
```

## Verified semantic retrieval

The RAG layer supports hybrid lexical + semantic retrieval while preserving a hard authority boundary:

```bash
python rag/hybrid_query.py "your query" data/public/**/*.jsonl --model BAAI/bge-m3
```

Only rows with `verified:true` and a non-empty `verification_source` are eligible **before** semantic ranking. For offline/regression use, precomputed vectors are supported. `rag/assemble_answer.py` produces an auditable answer packet with claim-level support IDs rather than free-form unsupported output.

### Evidence-backed cross-text comparison
`rag/cross_text_compare.py` + `schema/comparison.schema.json` provide a moat-gated comparison layer. Every comparison statement must cite verified row IDs from the declared source/work; missing evidence becomes an explicit gap, and the engine never silently harmonizes traditions or recensions. See `CROSS_TEXT_COMPARISON.md`.

## Moat proof experiences

The repository now contains three executable evidence experiences:

```bash
python3 product/verify_claim.py 'नरसिंहः स्तम्भमध्याद् निर्गत्य'
python3 product/compare_sources.py
python3 product/trace_evidence.py person:prahlada --depth 2
python3 product/demo_suite.py
```

Run the measurable self-consistency benchmark with:

```bash
make moat-proof-gate
```

The benchmark measures evidence behavior, not prose quality. See `benchmark/RUBRIC.md`.


## Publication and network handoff

Build and audit rights-aware release candidates:

```bash
make publication-gate
```

Current profiles:
- `open` — excludes non-commercial/restricted/unresolved source licenses.
- `research-nc` — admits qualifying CC BY-NC-SA 4.0 verified source rows.

On a network-enabled machine, acquire and materialize the primary P0 corpus tranche with:

```bash
python scripts/network_materialize.py --group core-materialization --fetch --materialize
```

See `docs/PUBLICATION_POLICY.md`, `docs/NETWORK_HANDOFF.md`, `sources/LICENSE_MATRIX.json`, and `docs/HUGGINGFACE_DATASET_CARD.md`.
