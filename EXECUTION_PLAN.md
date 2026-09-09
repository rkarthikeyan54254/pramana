# Execution Plan — optimize time to realization

## Principle
Scale acquisition and structuring in parallel; serialize only the **promotion to verified/publishable**.

## Lane A — Divya Prabandham
1. Fetch/preserve four Project Madurai raw snapshots.
2. Run source-numbering audits before extraction.
3. Ingest all 24 catalogued works to `data/staging/` with `verified:false`.
4. Certify Tiruppavai first; then verify Andal in batches; continue through all works.
5. Never auto-repair source number anomalies. Record them as source issues/variants.

## Lane B — Tevaram
1. Fetch 14 mapped Project Madurai source blocks covering Tirumurai 1–7.
2. Build patikam-aware parser: `tirumurai`, `patikam`, local verse, global-in-tirumurai verse.
3. Validate counts: 1469, 1331, 1347, 1070, 1016, 981, 1026.
4. Cross-check against an independent Saiva reference before publication.

## Lane C — Sanskrit core
1. Use Gita Supersite for chapter/sloka-addressable text discovery; pin terms before public-source designation.
2. Keep SanskritDocuments as verification/reference only unless permission/terms allow redistribution.
3. Start Isha Upanishad with GRETIL Kāṇva recension; explicitly track recension in `section`/notes.
4. Map all Gita chapter counts and 10–13 principal Upanishads before large ingestion.

## Lane D — Platform
- `make audit` must stay green.
- Raw files get checksums.
- Every structured row must have provenance.
- `verified:true` requires a second source.
- RAG indexes **verified-only** rows by default.

## Fast realization milestones
**R0 — machinery:** catalog + source manifests + validators. ✅

**R1 — trusted pilot:** Tiruppavai 30 publishable.

**R2 — useful Tamil asset:** Andal 173 + complete DP staging + Tevaram source map.

**R3 — product proof:** verified-only citation RAG with refusal on missing corpus evidence.

**R4 — breadth:** Tevaram verified batches + Gita/Isha Sanskrit lane operational.

## Lane E — Ithihasas + Puranas (accelerated realization)

### Parent corpora — Tier 1
1. **Valmiki Ramayana critical-edition lane** — full 7-kanda parent corpus; certify Sundara Kanda early.
2. **Mahabharata BORI Critical Edition** — full 18-parva parent corpus; certify high-value slices early rather than waiting for the whole epic.
3. **Harivamsha** — separate supplement corpus, especially valuable for Krishna/Yadava genealogy.
4. **Bhagavata Purana** — 12-skandha parent corpus; prioritize Skandha 10 plus Prahlada/Narasimha, Gajendra Moksha, Dhruva, Kapila and Uddhava Gita.
5. **Vishnu Purana** — high priority because it combines avatara material with dynastic/genealogical structure.
6. **Devi Mahatmya** — ingest as both standalone devotional corpus and Markandeya Purana 81–93 linked slice.

### Tier 2
Linga, Kurma, Garuda, Brahma, Brahmanda, Markandeya, Skanda and Shiva Puranas. Skanda/Shiva are explicitly partial-source lanes until a full publication-compatible Sanskrit source is pinned.

### Epic high-value slices
- Ramayana: Sundara Kanda first; then Ayodhya selected episodes.
- Mahabharata: Yaksha Prashna, Nala-Damayanti, Savitri, Vidura Niti, Narayaniya, Vishnu Sahasranama; Bhagavad Gita remains its existing separately addressable corpus with cross-links.

### Product-realization datasets generated from verified text
- episode/event graph
- genealogy/dynasty graph
- sacred geography / tirtha graph
- festival & vrata evidence index
- deity/avatara/epithet index
- quote/story claim verifier

The derivative datasets never become independent truth sources: every edge/claim must link back to one or more verified corpus IDs.

## Active realization sequence — 2026-09-09

Approved order: **Devī Māhātmya → Sundara Kāṇḍa → Bhāgavata high-value episodes → Mahābhārata devotional/dharma slices → full parent corpora in parallel.**

### Current source contracts
- Devī Māhātmya: GRETIL Mārkaṇḍeya Purāṇa 81–93; stable `MarkP_` loci pinned.
- Sundara Kāṇḍa: GRETIL Vālmīki Rāmāyaṇa kanda 5; this e-text has 66 sargas; stable `5.sarga.verse` markers pinned.
- Episode catalog intentionally marks Bhāgavata/Mahābhārata ranges `needs_locus_verification` until exact edition loci are checked.

### Parallel parent-corpus rule
Every certified slice is a view over a parent corpus contract. IDs must preserve parent locus so later full-work ingestion deduplicates rather than re-ingests the same text under incompatible IDs.

## Mahābhārata devotional/dharma realization lane

Pinned Critical Edition slices:

| Offering | CE locus | Default product view |
|---|---|---|
| Nala–Damayantī | 3.50–3.78 | Complete Nalopākhyāna |
| Sāvitrī | 3.277–3.283 | Complete Sāvitryupākhyāna |
| Yakṣa Praśna | 3.296–3.299 | Crisis + questions + restoration; derive 3.297 question-only view |
| Vidura Nīti | 5.33–5.40 | Complete counsel sequence |
| Nārāyaṇīya | 12.321–12.339 | Complete 19-chapter devotional/philosophical unit |
| Viṣṇu Sahasranāma | 13.135 | Hymn chapter; exact verse subrange to be pinned from parent extraction |

Execution principle: ingest the finalized CE parent once, then materialize these as evidence-preserving views. Do not create separate independently edited scripture copies for each offering.

## Mahābhārata completion path
The Mahābhārata lane is now implementation-complete up to source acquisition:
1. `make fetch` (or otherwise place `MBh01.txt` ... `MBh18.txt` under `sources/raw/mahabharata/`).
2. `make mahabharata-parent` to build and validate the normalized parent JSONL.
3. `make mahabharata-materialize` to emit the seven curated devotional/dharma views.
4. Add independent second-source verification before promoting any parent/slice row to `verified:true` / public publishable status.

Exact high-value views now include the full Vishnu Sahasranama chapter (`13.135.001-142`) and a narrower Yaksha question-answer core (`3.297.026-061`) in addition to the broader narrative frame (`3.296-299`).
