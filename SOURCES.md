# Sources Registry

Every source used by the corpus must be recorded here before data from it is accepted.

| Key | Work | Repository | URL | Accessed | Source terms / redistribution note | Corpus usage | Status |
|---|---|---|---|---|---|---|---|
| `pm-divya-0005-02` | Tiruppavai + neighboring Divya Prabandham works | Project Madurai | https://projectmadurai.org/pm_etexts/utf8/pmuni0005_02.html | 2026-09-09 | Page states © Project Madurai 1998–2021 and permits free redistribution provided its header is kept intact. Ancient underlying text is public domain; preserve Project Madurai provenance/terms for the e-text. | Primary Tiruppavai Tamil text | verified-live |

## License handling note

Do not reduce a source's website/e-text terms to `PD` merely because the ancient underlying work is public domain. Track both the ancient work status and the actual electronic-source provenance/terms. Public release policy must respect both.
| `pm-dp-1-947` | Nalayira Divya Prabandham 1–947 | Project Madurai | https://www.projectmadurai.org/pm_etexts/utf8/pmuni0621_tam.html | 2026-09-09 | © Project Madurai 1998–2018; page documents permission/publication provenance. Preserve header and source terms. | Primary Tamil block | verified-live |
| `pm-dp-948-2081` | Nalayira Divya Prabandham 948–2081 | Project Madurai | https://www.projectmadurai.org/pm_etexts/utf8/pmuni0622_tam.html | 2026-09-09 | © Project Madurai 1998–2018; preserve source provenance/terms. | Primary Tamil block | verified-live |
| `pm-dp-2082-2970` | Nalayira Divya Prabandham 2082–2970 | Project Madurai | https://www.projectmadurai.org/pm_etexts/utf8/pmuni0623_tam.html | 2026-09-09 | © Project Madurai 1998–2018; preserve source provenance/terms. | Primary Tamil block | verified-live |
| `pm-dp-2971-4000` | Nalayira Divya Prabandham 2971–4000 | Project Madurai | https://www.projectmadurai.org/pm_etexts/utf8/pmuni0624_tam.html | 2026-09-09 | © Project Madurai 1998–2018; preserve source provenance/terms. | Primary Tamil block | verified-live |
| `pm-tevaram-t1-p1` | Sambandar Tevaram, Tirumurai 1 part 1, verses 1–721 | Project Madurai | https://www.projectmadurai.org/pm_etexts/utf8/pmuni0150.html | 2026-09-09 | Project Madurai e-text; free redistribution stated if header retained. | Saiva adapter discovery | verified-live |
| `pm-tevaram-t1-p2` | Sambandar Tevaram, Tirumurai 1 part 2, verses 722–1469 | Project Madurai | https://www.projectmadurai.org/pm_etexts/utf8/pmuni0151.html | 2026-09-09 | Project Madurai e-text; free redistribution stated if header retained. | Saiva adapter discovery | verified-live |
| `pm-tevaram-t5-p1` | Appar Tevaram, Tirumurai 5 part 1, verses 1–509 | Project Madurai | https://www.projectmadurai.org/pm_etexts/utf8/pmuni0186.html | 2026-09-09 | Project Madurai e-text; free redistribution stated if header retained. | Saiva adapter discovery | verified-live |

## Expanded source map — 2026-09-09

### Divya Prabandham
The four Project Madurai Unicode editions are now pinned in `schema/work_catalog.json`, with all **24 work boundaries** mapped continuously from global pasuram 1 through 4000. The catalog intentionally records the Part 4/Thiruvaymozhi overlap behavior rather than assuming the HTML header equals its actual content range.

### Tevaram
All seven Tevaram Tirumurai are now mapped to Project Madurai source blocks in `sources/manifest.json`:

- Tirumurai 1: 1–721, 722–1469
- Tirumurai 2: 1–654, 655–1331
- Tirumurai 3: 1–713, 714–1347
- Tirumurai 4: 1–487, 488–1070
- Tirumurai 5: 1–519, 520–1016
- Tirumurai 6: 1–508, 509–981
- Tirumurai 7: 1–517, 518–1026

Total mapped numbered Tevaram units: **8,240**. These are acquisition counts, not verification claims.

### Sanskrit core
- **Gita Supersite (IIT Kanpur):** confirmed live with chapter/sloka-addressable Sanskrit मूल श्लोक text. Candidate primary/verification source; redistribution terms still need a separate explicit check.
- **SanskritDocuments:** confirmed live with Devanagari/IAST/ITRANS formats, but its current page states personal-study/research use and restricts copying/reposting for promotional/commercial use without permission. Therefore it is **verification/reference only** for now, not a public-dataset source.
- **GRETIL Isha Upanishad:** confirmed live, Kāṇva recension, with stable verse markers such as `IsUp_1`. Candidate scholarly primary for the Upanishad lane; source-level terms still must be recorded before public redistribution.

## Ithihasa / Purana discovery — 2026-09-09

These are **source candidates**, not yet automatically approved for public redistribution. Ancient-work public-domain status and e-text distribution rights are tracked separately.

- **BORI — Mahabharata project**: official institutional description of the Critical Edition: 18 parvas, 89,000+ verses in the constituted text; also records a Critical Edition of the Harivamsha in 4 parvans. Source: https://bori.ac.in/department/mahabharata/
- **Bombay Indology / John Smith — Mahabharata electronic critical text**: https://bombay.indology.info/mahabharata/welcome.html . Site states the text was checked with BORI involvement/agreement; current page (2026-06-14) considers the electronic text final. Publication/reuse terms still need explicit pinning.
- **Bombay Indology / John Smith — Ramayana electronic critical text**: https://bombay.indology.info/ramayana/welcome.html . Critical-edition electronic text in Devanagari, Unicode Roman and ASCII. Publication/reuse terms still need explicit pinning.
- **GRETIL — Epics**: machine-readable Mahabharata and Ramayana, including a distinct Southern-recension Ramayana lane. GRETIL source-specific licenses/legacy restrictions must be preserved; do not assume all files share identical terms.
- **GRETIL — Puranas**: machine-readable holdings include Bhagavata (12 skandhas), Vishnu, Brahma, Brahmanda, Garuda, Kurma, Linga, Markandeya 1–93, Matsya 1–176, Narada, Narasimha, Vamana; partial Shiva (Books 1 and 7) and partial/recension-specific Skanda material. Source: https://gretil.sub.uni-goettingen.de/gretil.html
- **GRETIL / BORI — Harivamsha**: treat Harivamsha as a distinct source/ID namespace even when linked to Mahabharata.

### Licensing caution
The legacy GRETIL UTF index explicitly states scholarly-reference/non-commercial restrictions, while some newer TEI records carry file-specific Creative Commons terms. Therefore **license must be pinned per exact file**, not at the site level.

### GRETIL — Bhāgavatapurāṇa (Skandhas 1–12)
- URL: https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_bhAgavatapurANa.htm
- Structure: stable `BhP_SS.CC.VVV` markers.
- File-specific license: CC BY-NC-SA 4.0.
- Use: primary parent-corpus candidate; episode boundaries still require independent locus verification.

## Mahābhārata Critical Edition — finalized electronic parent lane
- **Source:** Bombay Indology electronic text of the Mahābhārata Critical Edition
- **URL:** https://bombay.indology.info/mahabharata/welcome.html
- **State checked:** 2026-09-09
- **Edition note:** source states on 2026-06-14 that the electronic text is considered final; Devanagari, ISO-15919 Roman and Harvard/Kyoto ASCII formats are exposed for all 18 books.
- **Use:** primary parent corpus for CE-addressed devotional/dharma slices.
- **Redistribution:** do not assume unrestricted reuse; pin exact terms before publishing raw electronic text.
- **Recension rule:** never translate Gita Press/vulgate chapter numbers into CE addresses silently.

## Nārāyaṇīya — dedicated verification witness
- **Source:** GRETIL, Nārāyaṇīya (Mahābhārata 12.321–339), input by Peter Schreiner based on *Narayaniya-Studien* (1997).
- **URL:** https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_nArAyaNIya.htm
- **License:** CC BY-NC-SA 4.0 for this exact GRETIL e-text.
- **Use:** independent structured witness for the 19-chapter Nārāyaṇīya boundary and future text-level cross-checking.

## Tevaram second-source verification — IFP/EFEO Digital Tēvāram
- **Witness:** Digital Tēvāram / Kaṇiṉit Tēvāram, IFP/EFEO, Collection Indologie 103 (2007).
- **Text lineage:** Tamil text is the PIFI edition prepared by T.V. Gopal Iyer, published as *Mūvar Tēvāram* vol. 1 (1984) and vol. 2 (1985).
- **Coverage:** 798 patikams = 385 Campantar + 312 Appar + 101 Cuntarar; Tirumurai 1–7.
- **Structural key:** `[tirumurai:patikam]` with verse numbers inside each patikam; Tamil-script pages are directly accessible.
- **Use in this corpus:** **verification-only witness** until exact electronic reuse terms are pinned. English rendering, concordance, maps, audio and other enrichment are not ingested.
- **Verification rule:** same `tirumurai.patikam.verse` + conservative normalized Tamil exact match => eligible for `verified:true`; mismatch => explicit review/variant lane, never fuzzy auto-certification.

## Viṣṇu Purāṇa — real Prahlāda/Narasiṃha graph seed
- **Primary electronic text:** GRETIL `sa_viSNupurANa.htm`, based on Bombay Venkatesvara Steam Press (1910).
- **Primary file terms:** CC BY-NC-SA 4.0 on the current GRETIL transformed file.
- **Primary caveat:** GRETIL explicitly states the mass-converted text still needs further proofreading; exact second-witness comparison is therefore mandatory before promotion.
- **Second witness used for this seed:** Vedapath Viṣṇu Purāṇa chapter pages, Sanskrit text only, for 1.17.12 and 1.20.32/35/39.
- **Verification-only rule:** Vedapath translations, word-by-word explanations, philosophical themes, FAQs, generated/enrichment copy, and audio are NOT ingested into the authoritative corpus.
- **Deliberately held back:** ViP 1.17.10 is not promoted in this seed because GRETIL's converted reading has a word-boundary defect (`gurugehaṅgator'bhakaḥ`) relative to the cleaner second witness (`gurugehaṃ gato 'rbhakaḥ`). It belongs in the transcription-variant review lane first.

### GRETIL — Vāmanapurāṇa 1–69
- Exact file: https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/sa_vAmanapurANa1-69.htm
- Based on A.S. Gupta, All India Kashiraj Trust, 1967; data entry by Sansknet Project.
- File-specific license: CC BY-NC-SA 4.0.
- GRETIL warns that the mass-converted file has irregular word boundaries and needs further proofreading; every promoted row therefore requires a second Sanskrit witness.
- Current certified seed uses chapter 68 temple/ritual loci with Vedapath as the second Sanskrit witness; modern translations/commentary are not ingested.
