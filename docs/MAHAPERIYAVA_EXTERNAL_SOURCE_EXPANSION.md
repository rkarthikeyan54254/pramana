# Mahaperiyava external-source expansion

## Status

`MAHAPERIYAVA_EXTERNAL_SOURCE_FAMILY_PILOT_V1`

This lane expands Pramāṇa beyond *Deivathin Kural* without weakening the evidence model.

The pilot intentionally tracks **metadata and curator-authored proposition summaries only**.
It does not redistribute source text and it performs no authority promotion.

## Evidence rules

1. An official web page is not automatically an original historical artifact.
2. A translated transcription does not prove Mahaperiyava's exact original wording.
3. An interview described by its host as a “gist” is not treated as a verbatim transcript.
4. Multiple editions or web pages descended from one discourse/reporting chain do not count as independent votes.
5. `primary_source_verified` requires an item-level original primary artifact with pinned provenance.
6. A source-family relationship never propagates authority to every teaching in that family.
7. Rights review and evidence review remain separate.

## Pilot source families

### 15 August 1947 Independence Day message

The Kanchi-hosted page explicitly dates the message to 15 August 1947.
The current digital page is retained as a metadata/citation target only.
The original 1947 document has not yet been pinned.

### 1962 Ilayathangudi Vyasa Bharata Agama Shilpa Sadas

Two Kanchi-hosted English pages represent Part 1 and Part 2 of one event.
The pages acknowledge V. Srinivasan as translator from Tamil for web publication.
The two pages therefore belong to one source family and do not count as independent witnesses.

### J. W. Elder interview

The Kanchi-hosted page describes itself as a detailed gist of the discussion.
It is useful direct-interview evidence at proposition level, but the surviving page is not modeled as a verbatim transcript.

### Acharya's Call editorial chain

The 1995 preface states that the 1957-58 Madras discourses were reported in *The Hindu*,
were later issued in book form in 1964 and 1968, and were then regrouped by subject with minor editing for the later reprint.

This is lineage evidence, not an independent teaching witness.

## Next acquisition targets

Priority-A work now moves toward item-level original or contemporaneous artifacts:

- original *The Hindu* 1957-60 reports;
- original *The Hindu* 1932 reports;
- *Swadesamitran* reports;
- the original *Bhavan's Journal* issue carrying “What Life Has Taught Me”;
- the 11 August 1963 *Illustrated Weekly of India* interview.

The next engineering step is deterministic candidate cross-linking from the pilot external claims
to the 3,368 Deivathin Kural teaching records. Candidate generation must not grant authority.
Only item-level review can do so.

## External → Deivathin Kural cross-linking

The pilot external claims are now passed through the same deterministic
Mahaperiyava retriever used by the product.

This stage creates only candidate pairs. It deliberately does **not**
decide that two propositions are equivalent.

Every candidate remains:

`human_decision: unreviewed`

Allowed later human decisions are:

- `same_teaching`
- `related_teaching`
- `possible_tension`
- `contradiction`
- `not_same_teaching`
- `insufficient_to_decide`

Only `same_teaching`, combined with separately valid item-level source
provenance, can become an input to evidence-authority review.

Retrieval score, topic overlap, model similarity, or the number of
matching source families can never grant authority.

## Semantic adjudication and provenance eligibility

External-to-DK candidate retrieval is followed by a separate semantic
adjudication layer.

`same_teaching` means proposition-level semantic correspondence between
curator summaries. It does **not** mean textual identity.

Compound external summaries are atomized before they may enter a
same-teaching promotion path.

A second gate then asks whether the external source is actually capable
of functioning as an earlier or primary witness.

At the current pilot checkpoint:

- the 1947 Kanchi page is a later official web reproduction; the
  original 1947 artifact has not been pinned;
- the 1962 Ilayathangudi English pages explicitly represent translations
  from Tamil; the underlying Tamil/original proceedings witness has not
  yet been pinned;
- the J. W. Elder page is explicitly a gist rather than a verbatim
  transcript.

Therefore semantic corroboration may be recorded, but authority remains
unchanged until stronger item-level provenance is acquired.

## Archival acquisition checkpoint V2

The next evidence-depth bottleneck is no longer semantic retrieval. It is
historical artifact acquisition.

Four priority lanes are now explicit:

1. **Illustrated Weekly of India, 1963** — a surviving scan locator has
   been found for A. S. Raman's interview. A later Kanchi source gives
   11 August 1963 for the interview while the scan locator identifies the
   magazine issue as 18 August 1963. These dates must remain separate
   until the original issue is inspected.

2. **Bhavan's Journal, 1961** — Bharatiya Vidya Bhavan confirms that its
   institutional digital archive contains the complete 1961 run. The
   exact issue/pages for *What Life Has Taught Me* remain to be pinned.

3. **Ilayathangudi, 1962** — Kanchi's English web edition explicitly says
   it was translated from Tamil and indicates an underlying Tamil
   version. That Tamil object is not yet pinned.

4. **Independence Day, 1947** — the later Kanchi reproduction is clearly
   dated 15 August 1947, but an original or near-contemporaneous witness
   remains unlocated.

None of these discovery states changes teaching authority.

## 1963 A. S. Raman / Illustrated Weekly artifact

A private research snapshot of the surviving historical-periodical
scan has been hash-pinned.

- SHA-256: `7f5ea38fca50b67553338af3525c64ccae11d83f2d8a0c5eaac2de813f285ee8`
- bytes: `3492363`
- source text redistribution: **no**
- independent of Deivathin Kural event: **yes**
- verbatim transcript: **no**
- potential item-level authority ceiling:
  `earlier_witness_supported`

The publication is treated as an editorialized near-contemporaneous
interview witness. It is not treated as Mahaperiyava's exact wording.

The ignored private scan is never required by CI. CI validates the
metadata/hash pin and, when a private local snapshot is present,
the local test additionally validates its bytes and SHA-256.
