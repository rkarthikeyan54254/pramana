# Session Checkpoint — publication, acquisition handoff, and moat proof

Date: 2026-09-09

## What this session completed

### 1. Publication/rights lane
- File-level license/reuse matrix for all 51 currently catalogued sources.
- Default-deny release policy with `open`, `research-nc`, and `internal` profiles.
- Verified-only release builder with SHA-256 artifact manifest.
- Release checker that audits row authority, license eligibility, duplicate IDs, graph closure, and artifact checksums.
- Current reproducible `research-nc` release: **24 verified records, 29 nodes, 41 evidence edges**.
- Current `open` release: **0 records**, intentionally, because all materialized verified source rows currently carry CC BY-NC-SA 4.0.

### 2. Network/source acquisition handoff
- Source fetcher now expands templated chapter sources (e.g. all 13 Ved Path Devī chapters).
- Every fetched snapshot receives SHA-256 and provenance metadata sidecars.
- Priority groups separate core materialization, Mahābhārata parent, and Sundara verification lanes.
- `network_materialize.py` orchestrates acquisition → checksums → staging → explicit certification where supported.
- GitHub workflow can acquire raw snapshots as private workflow artifacts rather than committing them.

### 3. Moat benchmark consolidation
- Main repo restored to benchmark v2 rather than the older 5-case branch.
- Native contract result: **25/25 cases, 82/82 checks**.
- Competitor scorecard templates remain unscored until the exact prompts are behaviorally tested.

### 4. Claim verifier productionization
- Exact original-script text can authenticate only from verified rows.
- Exact canonical transliteration can also authenticate from verified rows.
- Lossy ASCII/diacritic and fuzzy similarity are candidate retrieval only, never authentication.
- Exact text found only in an unverified row is explicitly reported and ignored for authority.
- JSON and human-readable “not found” reporting are available.

## Gates passed
- `publication-gate`: GREEN
- `claim-verifier-test`: GREEN
- `moat-benchmark-v2`: GREEN — 25/25 cases, 82/82 checks

## Remaining primary blocker
The ChatGPT shell runtime cannot resolve external hosts, so raw P0 source files are not physically materialized here. No scripture text was reconstructed to bypass this.

On a normal network-enabled machine:

```bash
python scripts/network_materialize.py --group core-materialization --fetch --materialize
```

This is designed to fetch/checksum and then attempt:
- 4,000 Divya Prabandham staging rows
- 8,240 Tevaram staging rows
- full 13-chapter Devī Māhātmya alignment/certification
- full 12-skandha Bhagavata staging parent

Mahābhārata parent is separate:

```bash
python scripts/network_materialize.py --group mahabharata-parent --fetch --materialize
```

## Moat check
This session strengthens the moat because it makes three boundaries executable rather than aspirational:
1. **Authority boundary:** only verified rows authenticate claims.
2. **Rights/provenance boundary:** a row is not publishable merely because it is technically in `data/public/`.
3. **Reproducibility boundary:** source acquisition and releases are checksummed and auditable.

The next value jump is still **materialized verified depth**, not more architecture.
