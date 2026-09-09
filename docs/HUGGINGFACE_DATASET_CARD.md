---
pretty_name: Pramana Bhakthi Corpus
language:
- sa
- ta
license: other
task_categories:
- question-answering
- text-retrieval
---

# Pramāṇa Bhakthi Corpus — Dataset Card Draft

> **Status:** pre-release. This card is generated as publication documentation; do not publish until a rights-aware release artifact passes `publication-gate` and the selected profile's terms are reflected in the hosting configuration.

## What this dataset is
A provenance-first, independently verified corpus of Indic scriptural text. The project is optimized for evidence retrieval and claim verification, not for model-generated devotional prose.

Every released row must include a stable ID, original-script text, canonical transliteration, primary source provenance and license, verification status, and an independent verification source.

## Trust contract
- No model-reconstructed scripture text.
- No `verified:true` without a second witness.
- Textual differences are preserved for review rather than silently reconciled.
- Generated answers/commentary never feed back into authoritative corpus rows.
- Evidence-graph edges are released only when all supporting evidence IDs are themselves released.

## Configurations
The repository supports multiple release profiles rather than pretending all source files share one license.

### `open`
Only rows whose exact source-file terms permit open redistribution under the configured allowlist.

### `research-nc`
Includes qualifying CC BY-NC-SA 4.0 source rows. This configuration is non-commercial/share-alike and must be hosted accordingly.

## Current pre-release seed
The current repository contains a small set of independently verified Purāṇic seed rows and a filtered evidence graph. Corpus architecture is much broader than materialized verified depth; the project explicitly does not equate scaffolding with dataset coverage.

## Sources and licensing
See `sources/LICENSE_MATRIX.json`, `SOURCES.md`, and `docs/PUBLICATION_POLICY.md`. Rights are tracked per exact electronic source file. Verification-only witnesses do not contribute protected translation/commentary text to public releases.

## Intended uses
- exact quote/claim verification
- evidence-backed cross-text comparison
- textual-variant and recension analysis
- deity/episode/genealogy/ritual/sacred-geography evidence graphs
- grounded retrieval systems that refuse unsupported claims

## Out-of-scope / discouraged uses
- treating generated explanations as source text
- silently harmonizing recensions or traditions
- using verification-only copyrighted material as training data
- representing graph inferences as scripture without evidence IDs

## Reproducibility
A release artifact contains `records.jsonl`, `evidence_graph.json`, and `release_manifest.json` with SHA-256 hashes and counts. Raw-source snapshots are separately checksummed by the acquisition pipeline and are not automatically redistributed.

## Citation
Citation metadata will be finalized with the first public release. Users should cite both this compiled dataset and the underlying source edition(s) exposed in each row's provenance.
