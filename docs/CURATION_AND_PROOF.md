# Curation queue and proof bundles

## Why these exist

Bulk ingestion increases throughput but also creates review debt. The review queue makes that debt explicit. Proof bundles make the opposite direction auditable: every admitted answer can be exported with the exact verified evidence and provenance that justified it.

## Curator review queue

Generate:

```bash
python scripts/build_review_queue.py --output dist/review_queue.json
```

The queue is generated from authoritative project state and currently recognizes:

- verification mismatch / missing independent witness
- `needs_review`
- script-normalization uncertainty
- transliteration uncertainty
- variants that still need an attesting source
- semantic cross-source relations requiring curator review
- unresolved or conditional source rights

Priority meaning:

- **P0** blocks authority or safe publication.
- **P1** blocks enrichment, semantic promotion, or a release profile.
- **P2** curator-quality cleanup.
- **P3** optional polish.

Update one item without deleting its audit trail:

```bash
python scripts/review_queue.py dist/review_queue.json REVIEW_ID \
  --status resolved --reviewed-by curator-id \
  --notes "Checked source terms" --resolution "research-nc only"
```

`resolved` and `rejected` require a reviewer identity.

## Proof bundle

Export directly from evidence IDs:

```bash
python scripts/export_proof_bundle.py \
  --evidence-id bhagavatam.7.8.29 \
  --context '{"operation":"verify","claim":"..."}' \
  --output dist/proof.json
python scripts/check_proof_bundle.py dist/proof.json
```

A proof bundle contains:

- exact verified corpus records
- any accepted cross-source relations fully supported by those records
- the relevant evidence-graph subgraph
- source and rights metadata
- per-record SHA-256 hashes
- a SHA-256 hash of the evidence payload

Unverified evidence is rejected at export time.

## Product service

The local service also exposes a `proof` operation. It accepts `evidence_ids`, or can recursively collect evidence IDs from an already-generated product artifact.

## Moat rule

The review queue prevents uncertainty from being silently promoted. The proof bundle makes admitted authority portable and independently inspectable. Neither lets model output become source evidence.
