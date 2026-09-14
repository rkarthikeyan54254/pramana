# Mahaperiyava Corpus v0.1 — Deivathin Kural Volume 1

## Goal

Build the first complete evidence-bounded source layer for an eventual
**Ask Mahaperiyava** experience.

The app must answer from Mahaperiyava-source material and expose the evidence
behind every answer. It must be able to say **not established from the corpus**
instead of filling gaps with generic devotional or Vedantic prose.

## Current bootstrap

Official index:

`https://www.kamakoti.org/tamil/part1index.htm`

Discovered and pinned chapter pages: **175**

Tracked/public files contain metadata, provenance and review state only.
The fetched Deivathin Kural HTML is retained under ignored `sources/raw/`.

## Architecture

```text
official DK Volume 1 index
        |
        v
complete chapter catalog
        |
        v
human-curated teaching units
        |
        +--> DK attestation / print check
        |
        +--> earlier historical witness matching
        |
        +--> primary-source matching where available
        |
        v
public evidence metadata + private retrieval corpus
```

## What is a teaching unit?

A teaching unit is an answerable proposition or closely related cluster of
propositions from a source passage. It is **not** an arbitrary token chunk.

Examples of the shape we want:

- Why perform bhakti?
- Who gives the fruits of karma?
- What is the purpose of temple worship?
- Why should a temple be kept clean?
- What relationship does Advaita have to bhakti?

The exact DK wording remains private/restricted unless rights are explicitly
cleared.

## Authority ladder

```text
unreviewed
dk_attested
dk_print_checked
earlier_witness_supported
primary_source_verified
unattested
```

Collection-level provenance never silently propagates authority to individual
teaching units.

## Next review loop

For each queue entry in
`data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl`:

1. read the private source snapshot;
2. identify natural teaching units;
3. create curator-authored claim summaries;
4. attach source loci and topics/entities;
5. validate against `schema/teaching_record.schema.json`;
6. keep exact source wording private;
7. search historical witnesses only after the DK unit is well-defined;
8. upgrade authority only when evidence supports that specific unit.

## Hugging Face target

The eventual public artifact should be an evidence dataset, not a dump of
Deivathin Kural text. Candidate tables/configurations:

- `sources`
- `teachings`
- `witness_links`
- `chronology`

A later `mahaperiyava-qa-benchmark` can test whether an Ask Mahaperiyava system
answers from this corpus, cites correctly and refuses unsupported claims.
