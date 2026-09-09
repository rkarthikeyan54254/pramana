# Publication and Rights Policy

The repository's `data/public/` directory means **eligible for corpus engineering and review**, not automatically unrestricted redistribution.
Actual releases are built through a rights-aware profile.

## Release profiles

### `open`
Accepts only verified rows whose primary source license permits redistribution without a non-commercial restriction (for example PD, PD-TRANS, CC0, CC-BY, CC-BY-SA when file-level terms are pinned).

### `research-nc`
Also admits verified rows whose exact primary source is CC BY-NC-SA 4.0. The resulting release must preserve attribution, non-commercial, and share-alike terms.

### `internal`
For private testing only. It is not a publication profile and does not imply redistribution permission.

## Witness rule
A restricted or copyrighted secondary source may be recorded as **verification metadata** (source name, URL, locus, hashes/alignment result) when permitted, but its protected translation/commentary/source text is never copied into a public dataset merely because it was used to verify a row.

## Default deny
Unknown terms, reference-only sources, copyrighted critical-edition e-texts with unresolved reuse rights, and conditional sources whose packaging requirements are not yet satisfied are excluded from releases.

## Build contract
`build_release.py` requires `verified:true`, a non-empty `verification_source`, source provenance, and a profile-approved primary `source_license`. `check_release.py` re-audits the artifact and ensures graph edges reference only released evidence IDs.

## Moat connection
Licensing is part of provenance. A corpus cannot be called auditable if we can prove a verse's textual origin but cannot explain whether and how the electronic source may be redistributed.
