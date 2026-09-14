# Mahaperiyava Historical Witness Acquisition v0.02

Baseline: `911bbe1` (`Map Mahaperiyava historical source lineage`)

## Acquisition decision

The next witness family to acquire is the 1957-58 Tamil
`Acharya Swamigalin Upanyasangal` publication family.

Why this family moved up:
- an extant modern scan-locator exposes direct PDF links for Part 1 and Part 2;
- the official Kanchi historical account places these books inside the
  1957-59 Madras discourse publication family;
- later first-person provenance testimony attributed to "Ananthan" describes
  shorthand capture of the talks followed by conversion into continuous prose;
- institutional TDL metadata independently confirms that G. S. Ananthanarayanan
  authored a Tamil shorthand manual in 1965.

## Critical classification

The established collection-level transmission model is:

Mahaperiyava oral discourse
    -> shorthand capture (claimed)
    -> prose / continuous-text rendering (claimed)
    -> Kalaimagal printed volume
    -> later hosted scan

This is NOT the same as:

Mahaperiyava oral discourse
    -> verbatim printed transcript

The printed book's own front matter has now been inspected. Part 1's 1958
preface states that `Sri Ananthan` took the Mylapore discourses in shorthand,
typed copies were produced, and the material was arranged into published
volumes. The shorthand-derived relation is therefore `established` at
collection level. The editorial transformation remains explicit, so printed
wording is still not treated as verbatim by default.

## Acquired/located objects

### Part 1
Direct historical-scan URL located. Store only under ignored `sources/raw/`.
Do not publish full text or scan.

### Part 2
Direct historical-scan URL located. Store only under ignored `sources/raw/`.
Do not publish full text or scan.

### Part 3
Official Kanchi material says the discourse publication ran to three parts, and
secondary citations support Part 3's existence. No trustworthy direct scan URL
has yet been located.

Rule: do not guess Part 3's URL from the Part 1/2 filename pattern.

### Jagadguruvin Upadesangal
TDL item number `35317` has been located for a 1957 edition. The direct scan
object and edition front matter still need to be resolved and inspected.

### The Call of the Jagadguru (Kanchi, 1958)
Bibliographic identity is already pinned. A contemporary 1958 review provides
useful content leads, but the full Kanchi book has not yet been acquired.

## What can change after this acquisition?

Nothing moves to `primary_source_verified`.

Part 1's 1958 front matter confirms the recording/editorial mechanism at
collection level: `Sri Ananthan` took shorthand, typed copies were produced,
and the material was arranged for publication. The relation therefore moves
from `plausible` to `established` at collection level. The preface itself does
not supply the full name G. S. Ananthanarayanan, so that identity remains
separately corroborated rather than established by this page alone.

Only page-level comparison to a Deivathin Kural teaching can move that teaching
to `earlier_witness_supported`.

## Moat test

This work strengthens the Pramana moat because it records:
- who captured the discourse;
- by what recording mechanism;
- what editorial transformation intervened;
- which physical/scan witness survives;
- what remains missing;
- and exactly which authority upgrade is still forbidden.


<!-- PRAMANA_MAHAPERIYAVA_FRONT_MATTER_V003 -->

## Front-matter verification — v0.03

### Part 1

The 1958 preface, printed pp. vii–viii / PDF pp. 12–13, signed by
Ki. Va. Jagannathan and dated 22-7-1958, directly confirms the production path:

```text
Mahaperiyava oral discourse
    -> shorthand by "Sri Ananthan"
    -> typed copies
    -> editorial arrangement
    -> Kalaimagal printed volume
```

This establishes the `shorthand_rendering_of` relation at **collection level**.

It does not establish:

```text
verbatim printed wording
G. S. Ananthanarayanan's full-name identity from this page alone
item-level Mahaperiyava review/correction
primary_source_verified
```

### Part 2 / publication-family correction

The inspected 1974 Part 2 publisher preface says:

- the talks derive from the 1957–59 Chennai stay;
- the books were issued with Mahaperiyava's blessing;
- Parts 1 and 3 had already been published;
- the inspected Part 2 is a third edition;
- Part 4 was expected shortly.

Therefore:

```text
Part 3 = publisher-confirmed published; scan not yet located
Part 4 = publisher-announced; actual publication still unconfirmed
```

`Blessing` is not silently converted into evidence of proofreading or textual
approval; `acharya_review` remains `unknown`.

### Item-level review

See:

```text
data/review/mahaperiyava_dk_v1_historical_witness_review.json
data/research/mahaperiyava_dk_v1_historical_witness_review.md
```

for the ten DK Volume 1 pilot comparisons.
