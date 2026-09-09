# Network-enabled handoff

The current ChatGPT runtime can build and validate the corpus but cannot resolve external hosts from Python/shell. On a normal laptop or GitHub Actions runner, the following turns the P0 source contracts into real snapshots and staging data.

## One-command core acquisition + materialization

```bash
python scripts/network_materialize.py --group core-materialization --fetch --materialize
```

This will:
1. fetch/checksum the four Divya Prabandham blocks;
2. fetch/checksum all fourteen Tevaram blocks;
3. fetch GRETIL Mārkaṇḍeya 1–93 plus all 13 Ved Path verification chapters;
4. fetch the GRETIL Bhagavata parent;
5. materialize and count-gate all 4,000 Divya Prabandham staging rows;
6. materialize and count-gate all 8,240 Tevaram staging rows;
7. run the complete Devī Māhātmya second-witness certification pipeline;
8. materialize the 12-skandha Bhagavata staging parent without incorrectly promoting it before second-source verification.

## Mahābhārata parent

```bash
python scripts/network_materialize.py --group mahabharata-parent --fetch --materialize
```

This fetches all 18 Unicode-Roman CE parent files, builds the normalized parent JSONL, validates it, and materializes the curated devotional/dharma slices. It does **not** imply public redistribution rights or `verified:true` status.

## Acquisition-only GitHub workflow
Use `.github/workflows/acquire-sources.yml`. Raw source snapshots are uploaded as private workflow artifacts rather than committed or included in dataset releases.

## Non-negotiable authority boundary
A successful download or parser run never means a row is verified. Only the explicit second-source certification workflow can promote a row. Missing network data must never be substituted with model-generated scripture text.
