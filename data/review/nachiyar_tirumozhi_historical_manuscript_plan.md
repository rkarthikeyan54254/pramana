# Nachiyar Tirumozhi — Historical Manuscript Adjudication Plan

**Authority:** UNVERIFIED RESEARCH WORKFLOW  
**Current corpus authority:** UNVERIFIED  
**Purpose:** Replace digital-copy majority voting with evidence from substantially older manuscript witnesses.

## Breakthrough

The British Library Endangered Archives Programme / Tamil University palm-leaf collection contains a **17th-century manuscript specifically catalogued as `நாச்சியார் திருமொழி வியாக்கியானம்`**, shelfmark **EAP1217/1/1299**.

The catalogue describes it as Andal's 143 Nachiyar Tirumozhi songs, corresponding to Divya Prabandham 504–646, with **202 digitized images**.

This is now the first-choice historical witness for the five high-value unresolved loci:

1. 604 / unit 101
2. 505 / unit 2
3. 526 / unit 23
4. 630 / unit 127
5. 549 / unit 46

A second 17th-century witness, **EAP1217/1/1298 `முதலாயிரம் அரும்பதம்`**, contains the First Thousand with detailed commentary and 282 digitized images.

Multiple 18th-century `முதலாயிரம்` manuscripts are also digitized: EAP1217/1/1254, /1333, /1348 and /1747.

## Why this changes the plan

The blocked 1923 Tamil Digital Library print and the 1909 DLI print remain useful, but they are no longer the oldest accessible research leads. The EAP material predates them by roughly two centuries and is directly relevant to textual-history investigation.

Age alone still does **not** establish the canonical reading. The manuscripts are evidence, not authority by fiat.

## Acquisition

EAP documents that IIIF manifests are available for archive-file records by appending `/manifest` to the archive-file URL.

Primary target:

```text
catalogue:
https://eap.bl.uk/archive-file/EAP1217-1-1299

IIIF:
https://eap.bl.uk/archive-file/EAP1217-1-1299/manifest
```

Use:

```bash
python3 scripts/fetch_eap_iiif.py \
  --source-key eap1217-1-1299-nachiyar-vyakhyanam \
  --manifest-url https://eap.bl.uk/archive-file/EAP1217-1-1299/manifest \
  --output-dir sources/raw/verification/eap1217_1_1299 \
  --expected-canvas-count 202 \
  --manifest-only
```

Then list canvases:

```bash
python3 scripts/fetch_eap_iiif.py \
  --source-key eap1217-1-1299-nachiyar-vyakhyanam \
  --manifest-url https://eap.bl.uk/archive-file/EAP1217-1-1299/manifest \
  --output-dir sources/raw/verification/eap1217_1_1299 \
  --expected-canvas-count 202 \
  --list
```

Once page/canvas ranges have been located, download **only the relevant canvas ranges first**:

```bash
python3 scripts/fetch_eap_iiif.py \
  --source-key eap1217-1-1299-nachiyar-vyakhyanam \
  --manifest-url https://eap.bl.uk/archive-file/EAP1217-1-1299/manifest \
  --output-dir sources/raw/verification/eap1217_1_1299 \
  --expected-canvas-count 202 \
  --canvases <comma-separated-or-ranges>
```

After the first successful manifest fetch, record its SHA-256 in the source contract so subsequent fetches fail closed.

## Review protocol

For each target locus:

1. Identify the exact verse from surrounding words, not presumed page number.
2. Record manuscript shelfmark + canvas index.
3. Preserve the manuscript's exact visible spelling.
4. Do **not** silently modernize pulli, sandhi, spacing, Grantha/Tamil glyph conventions, or scribal conventions.
5. Record an image SHA-256 linking the reading to the preserved local snapshot.
6. If a glyph is genuinely ambiguous, record `uncertain_graphic_reading` rather than guessing.
7. Cross-check against EAP1217/1/1298 and at least one 18th-century `முதலாயிரம்` manuscript when practical.
8. Never count manuscripts as independent merely because catalogue records are separate; scribal/editorial genealogy remains unknown.

## Decision vocabulary

Use only:

- `orthographic_sandhi_equivalent`
- `source_transcription_error_candidate`
- `omission_candidate`
- `historically_attested_variant`
- `unresolved_textual_variant`
- `uncertain_graphic_reading`

A historical witness can establish **historical attestation**. It does not automatically establish which reading Pramāṇa should call canonical.

## Rights discipline

EAP states that IIIF manifests are available for archive images and provides tools to download JPEGs for research. Its tools page says downloaded images are for personal use and further sharing/publishing requires custodian permission. Individual catalogue records may additionally specify licences (for example, EAP1217/1/1747 is catalogued CC BY-NC).

Therefore:

- keep raw manuscript images in `sources/raw/verification/` (gitignored);
- commit hashes, canvas IDs, locus readings and review metadata;
- do not put manuscript images into the public dataset/repo without confirmed permission.

## Tiruppavai after Nachiyar

Do not broaden scope yet, but retain these high-value leads for the four Tiruppavai hard cases after Nachiyar closes:

- EAP1217/1/1293 — `திருப்பாவை வியாக்கியானம்`, 17th century, 134 digitized images
- EAP1217/1/1296 — `திருப்பாவை பிரமாணத்திரட்டு`, 17th century, 72 digitized images

These may make the later Tiruppavai adjudication substantially stronger than another modern digital-text comparison.

## Stop condition for this workstream

The Nachiyar historical-manuscript pass is complete when:

- all five priority loci have an EAP1217/1/1299 reading or a documented reason the manuscript is unreadable/missing there;
- 604 is cross-checked against at least one additional historical manuscript;
- each reading is tied to shelfmark, canvas and local image SHA;
- no manuscript image itself is committed;
- authority remains explicitly UNVERIFIED unless the project's verification policy is separately satisfied.
