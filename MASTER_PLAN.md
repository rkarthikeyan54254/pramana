# Bhakthi Corpus — Master Plan & Build Spec
**A structured, model-followable guide to building a verified corpus of Ithihasas, Puranas, Upanishads, and the Bhakthi traditions (Alwars & Nayanmars), for RAG and optional fine-tuning.**

Author context: Rama Karthikeyan — personal/spare-time project. Related public sites (downstream outputs, NOT sources): vamsha.co.in, sandhyakatha.com, templecircuit.in, abhivadhaye.co.in, nalnaal.netlify.app
Document version: v1.0 — 2026-09-09
Purpose of this file: a portable, self-contained brief you can carry to a personal laptop and hand to an AI assistant to execute step by step.

---

## 0. TL;DR — the one thing to remember

**The corpus is the asset. The model is fungible.**
Do NOT train from scratch. Do NOT feed the downstream websites back in (they are frontier-model output — training on them creates a hallucination feedback loop with no ground truth). Go to **primary/authoritative sources**, build a verified + citation-linked dataset, then layer RAG, then *optionally* a small LoRA fine-tune.

Sequence: **Source → Normalize → Structure → Verify → Store → RAG → (optional) Fine-tune.**

Start with ONE small slice (Andal's Tiruppavai, 30 verses), prove the whole loop, then scale.

---

## 0.5 What's our moat? (read this whenever you doubt the project)

**The honest starting point:** frontier models (Gemini, Claude, GPT) are *excellent* at devotional prose, meaning, and significance — and getting better. If the goal is "generate a beautiful essay on the Alwars," **we have no moat. Do not build that. Use the frontier model.**

The moat is **narrow, specific, and durable**: it is **verifiable, cited, structured ground truth** — the things frontier models fail at *structurally*, because it is a **data problem**, not a capability problem. More model scale does not close these gaps:

| Dimension | Frontier freestyle | This corpus |
|---|---|---|
| Fluency / meaning / significance | Excellent — **no moat** | n/a — don't compete here |
| **Verbatim verse text** | Paraphrases; subtly wrong words | Exact source bytes |
| **Verse number + attribution** | Confidently hallucinated | Pinned & sourced |
| **Auditable citation** | None ("trust me") | `source → id`, verifiable |
| **Textual variants** | Hidden / silently picked | Tracked, sourced (`variants[]`) |
| **Sampradaya-correct reading** | Blurred across traditions | Tagged, kept distinct |
| **Structured / queryable** | Prose only | Data (verse↔temple↔deity↔author) |
| **Durability across model churn** | Re-do each generation | Permanent asset |

### The moat, in one sentence
**Fluency is commoditized; verified ground truth with citations is not.** Build the second, never the first.

### Proven, not asserted — the Tiruppavai-5 test (2026-09-09)
Asked for "the 5th Tiruppavai pasuram," Gemini:
- **Got the attribution right** — it *is* "Maayanai Mannu" (PM no. 478). Credit due.
- **But contradicted itself in the same answer:** printed the Tamil `அணி விளக்கை` (*aṇi*, "adorning lamp") while transliterating it as `mani vilakkai` (*maṇi*, "jewel lamp") — with **no source**, so a reader cannot tell which is right. It also silently dropped sandhi (`sindhikka` for சிந்திக்கப்).
- **Our record resolves it:** primary reading `அணி` pinned to Project Madurai pmuni0005_02, the `maṇi` variant captured in `variants[]` as `status: needs_source` (never adopted on LLM output alone), and provenance to the exact pasuram.

This happened on **verse 5 of the most-quoted Tiruppavai** — where a model should be *strongest*. That is the whole business case in one pasuram.

### What the moat implies for strategy
1. **Product shape:** not a content generator — a **grounded, citing assistant**: *answer only from verified verses, cite the source, surface variants, refuse when not in corpus.* This is the one shape that beats frontier freestyle decisively.
2. **Trust is the currency.** For this audience a wrong pasuram or misattribution is not a bug — it is a credibility killer. "Every claim traces to a verified source, and we show you the variant readings" is a moat freestyle can never offer.
3. **The asset is the dataset + verification discipline, not the model.** The model is a delivery pipe. The corpus stays valuable no matter which model wins next year.
4. **Falsifiable check, any time:** take any frontier output, fact-check 5 specific claims (verbatim text, verse number, attribution, invented quotes) against the primary source, and count errors. **That error rate is the moat, quantified.** If it is ~0, we honestly have no moat and should stop. It won't be.

---

## 1. Guiding principles

1. **Provenance over volume.** Every single record carries its source and license. No record without provenance.
2. **Original language first.** Capture the source script (Tamil / Devanagari) before any translation.
3. **Two-source verification.** Cross-check each verse against an independent authoritative source; flag disagreements, never silently pick.
4. **Separate text from interpretation.** Original verse (ancient, public domain) is a different tier from translation/commentary (often modern, copyrighted). Keep them in separate fields with separate licenses.
5. **Start narrow, prove the loop, then scale.** One prabandham → one Alwar → 4000 pasurams → other corpora.
6. **Versioned & diffable.** Plain text (JSONL/CSV) in git. No binary blobs, no opaque DB as source of truth.
7. **Licensing discipline from row one.** Retrofitting provenance is misery. Tag license on creation.

---

## 2. Full corpus scope — the "full-fold" catalog

Organized into **phases by priority + licensing clarity**. Phase 1 items are finite, well-digitized, high-value, and license-clean. Later phases add breadth.

### PHASE 1 — Beachhead (Tamil Bhakthi, finite & underserved)
| Corpus | Scope / size | Why first |
|---|---|---|
| **Andal — Tiruppavai** | 30 pasurams | Tiny, famous, complete — the pipeline test slice |
| **Andal — Nachiyar Tirumozhi** | 143 pasurams | Completes Andal |
| **Nalayira Divya Prabandham (all 12 Alwars)** | 4,000 pasurams | Core Alwar corpus; badly covered by frontier models |
| **Panniru Tirumurai (Nayanmars)** | Tevaram, Tiruvasagam, etc. across 12 Tirumurai | Core Saiva bhakthi corpus |
| **Periya Puranam (Sekkizhar)** | Hagiography of the 63 Nayanmars | The Nayanmar "stories" |

### PHASE 2 — Sanskrit core (Upanishads + Gita)
| Corpus | Scope | Notes |
|---|---|---|
| **Principal Upanishads** | ~10–13 (Isha, Kena, Katha, Prashna, Mundaka, Mandukya, Taittiriya, Aitareya, Chandogya, Brihadaranyaka, Svetasvatara, Kaushitaki, Maitri) | Start with the 10–13 principal; 108 total is later |
| **Bhagavad Gita** | 700 verses, 18 chapters | Well-digitized, multiple public-domain translations |

### PHASE 3 — Ithihasas (the epics)
| Corpus | Scope | Notes |
|---|---|---|
| **Ramayana (Valmiki)** | ~24,000 slokas, 7 kandas | Use **Baroda Critical Edition** as canonical text |
| **Mahabharata** | ~100,000 slokas, 18 parvas | Use **BORI Critical Edition** as canonical text. Huge — plan sub-slicing by parva |
| **Kamba Ramayanam** (Tamil) | Tamil retelling | Bhakthi/literary bridge; optional but valuable for Tamil corpus |

### PHASE 4 — Puranas (incl. Bhagavatham)
| Corpus | Scope | Notes |
|---|---|---|
| **Srimad Bhagavatham (Bhagavata Purana)** | 12 cantos (skandhas), ~18,000 verses | High priority within Puranas — central to Vaishnava bhakthi. Do this before the other Puranas |
| **Vishnu Purana** | — | Vaishnava |
| **Shiva Purana** | — | Saiva |
| **Devi Bhagavatam / Markandeya (Devi Mahatmya)** | — | Shakta |
| **Remaining Maha Puranas** | 18 total | Coverage uneven digitally; add opportunistically |
| **Sthala Puranas** | Temple-specific | Ties directly to templecircuit.in; sourcing is fragmented — treat as long-tail |

### PHASE 5 — Commentary & Acharya layer (interpretation)
> ⚠️ Licensing-sensitive. Ancient bhashyas are public domain in original; **modern translations of them are usually copyrighted.**
| Corpus | Scope | Licensing |
|---|---|---|
| **Divya Prabandham vyakhyanas** (6000 / 9000 / 24000 / 36000 padi) | Sri Vaishnava commentaries | Original Manipravalam old; modern printed editions/translations copyrighted |
| **Adi Shankara** — Upanishad/Gita/Brahmasutra bhashyas + stotras | — | Original public domain; modern translations vary |
| **Ramanuja** — Sri Bhashya, Gita Bhashya | — | Same as above |
| **Madhva, Nimbarka, Vallabha** commentaries | — | Same |
| **Deivathin Kural (Kanchi Paramacharya)** | Compiled discourses, multi-volume | ⚠️ **COPYRIGHTED** (Vanathi Pathippagam et al.). **Private RAG use only — do NOT redistribute or publish.** Track as restricted |

### PHASE 6 — Supporting / enrichment data
| Data | Use |
|---|---|
| **Stotras & Sahasranamas** (Vishnu Sahasranama, Lalitha Sahasranama, etc.) | High-demand devotional Q&A |
| **Divya Desam (108) + Paadal Petra Sthalam (Saiva) temple metadata** | Links verses ↔ temples; powers templecircuit.in |
| **Alwar / Nayanmar biographical data** | Author metadata, timelines |
| **Calendar / panchangam concepts** | Supports sandhyakatha.com type content |

**Licensing legend used throughout:** `PD` public domain · `PD-TRANS` public-domain translation (old, dated) · `CC` explicitly Creative-Commons licensed · `©` copyrighted, private use only.

---

## 3. Sourcing map — where the PRIMARY data lives

> ⚠️ **Verify every URL before relying on it.** Repositories move. These are named because they are well-known and authoritative; confirm the live link and license on the site itself.

### Tamil sources (Alwars, Nayanmars)
| Source | What it has | Notes |
|---|---|---|
| **Project Madurai** (projectmadurai.org) | Divya Prabandham, Tevaram, Periya Puranam, Tirukkural, Kamba Ramayanam — Tamil Unicode | Clean, public-domain e-texts. **Primary Tamil source.** |
| **thevaaram.org** | Panniru Tirumurai (all 12), Tevaram with audio | Dedicated Saiva reference |
| **shaivam.org** | Nayanmars, Periya Puranam, Saiva texts | Good for hagiography/stories |
| **SriPedia / ramanuja.org / dravidaveda / ibiblio "sadagopan"** | Divya Prabandham + Sri Vaishnava commentary | Commentary tier — check license |
| **Tamil Virtual Academy** | Govt digital Tamil library | Scholarly editions |

### Sanskrit sources (Upanishads, Puranas, Gita, Ithihasas)
| Source | What it has | Notes |
|---|---|---|
| **GRETIL** (Göttingen Register of Electronic Texts in Indian Languages) | Upanishads, Puranas, Mahabharata, Ramayana, bhashyas — e-texts | **Scholarly gold standard.** Primary Sanskrit source |
| **sanskritdocuments.org** | Stotras, Upanishads, Gita, many texts (Devanagari + ITRANS) | Large, community-maintained; verify |
| **Muktabodha Digital Library** | Agamas, Kashmir Shaivism, tantra, Sanskrit | Specialist depth |
| **Digital Corpus of Sanskrit (DCS)** | Morphologically **tagged/lemmatized** Sanskrit | Great for search/linguistic features later |
| **SARIT** | TEI-encoded (XML) Indic texts | Structured, citable |
| **GRETIL/archive.org — BORI Critical Edition (Mahabharata), Baroda Critical Edition (Ramayana)** | The academic canonical text of the epics | Use these as the authoritative recension |
| **Gita Supersite (IIT Kanpur)** | Gita, Ramayana, Ramcharitmanas with commentaries | Good cross-verification source |
| **sacred-texts.com** | Müller's *Sacred Books of the East*, Ganguli Mahabharata, Griffith Ramayana | `PD-TRANS` — old but license-clear translations |
| **Wikisource (Sanskrit & Tamil)** | Mixed | Variable quality — always cross-verify |

### Rule of thumb for sourcing
- **Original verse text:** GRETIL / sanskritdocuments (Sanskrit); Project Madurai / thevaaram (Tamil).
- **Canonical recension of epics:** BORI (MB) / Baroda (Ramayana).
- **Public-domain translations:** sacred-texts.com (SBE, Ganguli, Griffith).
- **Never** the downstream sites (vamsha/sandhyakatha/etc.) as source — they are outputs.

---

## 4. Licensing framework (read before publishing anything)

Three tiers determine what you may host publicly (e.g., on HuggingFace):

1. **`PD` — Original ancient text (the verses):** public domain. ✅ Safe to host.
2. **`PD-TRANS` — Old translations** (Müller ~1880s, Ganguli, Griffith): public domain. ✅ Safe.
3. **`©` — Modern translations & commentaries** (living authors, recent presses, most vyakhyana translations, **Deivathin Kural**): copyrighted. ❌ **NOT safe to redistribute**, even if a website posted them. Private RAG only.

**Operating rules:**
- Every record has a `license` field. No exceptions.
- Public dataset = only `PD`, `PD-TRANS`, or explicitly `CC` rows.
- `©` rows live in a **separate, gitignored/private store**, used for local RAG only, never pushed to HF.
- When in doubt, mark `©` and keep private until license is confirmed.
- Keep a `SOURCES.md` logging each source's URL, access date, and stated license/terms.

---

## 5. The canonical record schema

One JSON object per verse/unit. Store as **JSONL** (one JSON per line) — git-diffable, streaming-friendly, HuggingFace-native.

### 5.1 Field definitions
| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | Stable unique key. Scheme in §5.2 |
| `corpus` | string | ✅ | Controlled vocab: `divya_prabandham`, `tirumurai`, `periya_puranam`, `upanishad`, `gita`, `ramayana`, `mahabharata`, `bhagavatam`, `purana`, `stotra`, `commentary` |
| `work` | string | ✅ | Specific work, e.g. `tiruppavai`, `isha_upanishad`, `bhagavatam` |
| `tradition` | string | ✅ | `sri_vaishnava`, `saiva_siddhanta`, `advaita`, `dvaita`, `smarta`, `shakta`, `general` |
| `author` | string | ✅ | e.g. `andal`, `sambandar`, `valmiki`, `vyasa`, `unknown` |
| `language` | string | ✅ | `tamil`, `sanskrit`, `manipravalam` |
| `section` | object | ✅ | Hierarchical locus, e.g. `{"canto":10,"chapter":1}` or `{"tirumurai":1,"patikam":1}` |
| `unit_no` | int/string | ✅ | Verse number within work (pasuram/sloka no.) |
| `text_original` | string | ✅ | Verse in original script (Tamil/Devanagari), Unicode |
| `text_iast` | string | ✅ | IAST transliteration (canonical roman scheme) |
| `text_itrans` | string | ⬜ | Optional secondary transliteration (ITRANS) for search |
| `translation_en` | string | ⬜ | English translation |
| `translation_source` | string | cond. | Required if `translation_en` present. Who/what edition |
| `translation_license` | string | cond. | `PD` / `PD-TRANS` / `CC` / `©` |
| `commentary` | array | ⬜ | List of `{text, author, source, license}` objects |
| `variants` | array | ⬜ | Textual variant readings per disputed locus: `{locus, primary, primary_translit, alternatives:[{reading, translit, gloss, source, status}], note}`. `status` ∈ `attested`/`needs_source`/`rejected`. Never adopt a variant on LLM output alone — require a source. Populated by the verification/enrichment pass, not by ingest |
| `deity` | string | ⬜ | Controlled vocab, e.g. `vishnu`, `shiva`, `krishna`, `ranganatha`, `devi` |
| `sthalam` | string | ⬜ | Associated temple (Divya Desam / Paadal Petra Sthalam) |
| `meter` | string | ⬜ | Prosodic meter if known |
| `themes` | array[string] | ⬜ | Tags: `bhakti`, `surrender`, `cosmology`, `ethics`, etc. |
| `source` | string | ✅ | Where the ORIGINAL text came from (repo + URL) |
| `source_license` | string | ✅ | License of the original text (usually `PD`) |
| `verified` | bool | ✅ | Passed two-source cross-check? |
| `verification_source` | string | cond. | Second source used to verify |
| `flags` | array[string] | ⬜ | e.g. `variant_reading`, `disputed_attribution`, `needs_review` |
| `notes` | string | ⬜ | Free text for curators |

### 5.2 ID scheme
Format: `{corpus}.{work}.{section-path}.{unit_no}`
Examples:
- `divya_prabandham.tiruppavai.1` (Tiruppavai pasuram 1)
- `tirumurai.tevaram.t1.p1.v1` (Tirumurai 1, patikam 1, verse 1)
- `bhagavatam.10.1.1` (canto 10, chapter 1, verse 1)
- `upanishad.isha.1` (Isha Upanishad verse 1)

IDs must be **stable** — once assigned, never renumber. Corrections change content, not IDs.

---

## 6. Worked example — Tiruppavai (Phase 1 test slice)

> Transliteration is a common romanization; normalize to strict IAST/Tamil-romanization with Aksharamukha in the pipeline. **English gloss below is a draft literal rendering for structure only — replace with a sourced, license-verified translation before publishing.**

```jsonl
{"id":"divya_prabandham.tiruppavai.1","corpus":"divya_prabandham","work":"tiruppavai","tradition":"sri_vaishnava","author":"andal","language":"tamil","section":{"prabandham":"tiruppavai"},"unit_no":1,"text_original":"மார்கழித் திங்கள் மதிநிறைந்த நன்னாளால் நீராடப் போதுவீர் போதுமினோ நேரிழையீர் சீர் மல்கும் ஆய்ப்பாடிச் செல்வச் சிறுமீர்காள் கூர்வேல் கொடுந்தொழிலன் நந்தகோபன் குமரன் ஏரார்ந்த கண்ணி யசோதை இளஞ்சிங்கம் கார்மேனி செங்கண் கதிர்மதியம் போல் முகத்தான் நாராயணனே நமக்கே பறை தருவான் பாரோர் புகழப் படிந்தேலோர் எம்பாவாய்","text_iast":"mārkaḻit tiṅkaḷ matiniṟainta naṉṉāḷāl / nīrāṭap pōtuvīr pōtumiṉō nēriḻaiyīr / cīr malkum āyppāṭic celvac ciṟumīrkāḷ / kūrvēl koṭuntoḻilaṉ nantakōpaṉ kumaraṉ / ērārnta kaṇṇi yacōtai iḷañciṅkam / kārmēṉi ceṅkaṇ katirmatiyam pōl mukattāṉ / nārāyaṇaṉē namakkē paṟai taruvāṉ / pārōr pukaḻap paṭintēlōr empāvāy","translation_en":"In the auspicious full-moon day of Margazhi, come, O well-adorned ones, let us go to bathe. O prosperous young girls of the flourishing cowherd village — Narayana, son of Nandagopa of the sharp spear, the lion-cub of lovely-eyed Yashoda, dark-hued, red-eyed, face like the radiant moon — He alone will grant us the 'parai' (our boon). Come and join, that the world may praise us, O our maiden (vow).","translation_source":"DRAFT literal gloss — REPLACE with sourced/verified translation","translation_license":"©","deity":"krishna","sthalam":null,"meter":null,"themes":["bhakti","margazhi_vratam","surrender"],"source":"projectmadurai.org (VERIFY exact URL + access date)","source_license":"PD","verified":false,"verification_source":null,"flags":["needs_review","translation_placeholder"],"notes":"Opening pasuram. Cross-verify Tamil text against a second source (e.g., dravidaveda/SriPedia)."}
{"id":"divya_prabandham.tiruppavai.2","corpus":"divya_prabandham","work":"tiruppavai","tradition":"sri_vaishnava","author":"andal","language":"tamil","section":{"prabandham":"tiruppavai"},"unit_no":2,"text_original":"வையத்து வாழ்வீர்காள் நாமும் நம்பாவைக்குச் செய்யும் கிரிசைகள் கேளீரோ பாற்கடலுள் பையத் துயின்ற பரமன் அடி பாடி நெய்யுண்ணோம் பாலுண்ணோம் நாட்காலே நீராடி மையிட்டு எழுதோம் மலரிட்டு நாம் முடியோம் செய்யாதன செய்யோம் தீக்குறளைச் சென்றோதோம் ஐயமும் பிச்சையும் ஆந்தனையும் கைகாட்டி உய்யுமாறு எண்ணி உகந்தேலோர் எம்பாவாய்","text_iast":"vaiyattu vāḻvīrkāḷ nāmum nam pāvaikku / ceyyum kiricaikaḷ kēḷīrō pāṟkaṭaluḷ / paiyat tuyiṉṟa paramaṉ aṭi pāṭi / neyyuṇṇōm pāluṇṇōm nāṭkālē nīrāṭi / maiyiṭṭu eḻutōm malariṭṭu nām muṭiyōm / ceyyātaṉa ceyyōm tīkkuṟaḷai ceṉṟōtōm / aiyamum piccaiyum āntaṉaiyum kaikāṭṭi / uyyumāṟu eṇṇi ukantēlōr empāvāy","translation_en":"O dwellers of this world, hear the observances of our vow: singing the feet of the Supreme who reclines on the ocean of milk, we will not eat ghee or milk, we will bathe at dawn, not line our eyes, not wear flowers in our hair, do nothing forbidden, speak no ill, give alms and charity as we can, and live thinking of liberation. Join, O our maiden (vow).","translation_source":"DRAFT literal gloss — REPLACE with sourced/verified translation","translation_license":"©","deity":"vishnu","sthalam":null,"meter":null,"themes":["vratam","ethics","asceticism","bhakti"],"source":"projectmadurai.org (VERIFY exact URL + access date)","source_license":"PD","verified":false,"verification_source":null,"flags":["needs_review","translation_placeholder"],"notes":"Lists the vow's disciplines."}
```

### 6.1 Same schema, Sanskrit example (Isha Upanishad v.1)
```jsonl
{"id":"upanishad.isha.1","corpus":"upanishad","work":"isha_upanishad","tradition":"advaita","author":"unknown","language":"sanskrit","section":{"upanishad":"isha"},"unit_no":1,"text_original":"ॐ ईशा वास्यमिदं सर्वं यत्किञ्च जगत्यां जगत् । तेन त्यक्तेन भुञ्जीथा मा गृधः कस्यस्विद्धनम् ॥","text_iast":"oṃ īśā vāsyam idaṃ sarvaṃ yat kiñca jagatyāṃ jagat / tena tyaktena bhuñjīthā mā gṛdhaḥ kasya svid dhanam","translation_en":"REPLACE with sourced translation (e.g., Müller SBE — PD-TRANS).","translation_source":"TO SOURCE — prefer Müller (PD-TRANS)","translation_license":"PD-TRANS","deity":null,"sthalam":null,"meter":"anushtubh","themes":["vedanta","renunciation","non-attachment"],"source":"GRETIL / sanskritdocuments.org (VERIFY)","source_license":"PD","verified":false,"verification_source":null,"flags":["needs_review"],"notes":"Opening mantra. Verify Devanagari + choose PD translation."}
```

---

## 7. Repository / file structure (portable to laptop)

```
bhakthi-corpus/
├── README.md                     # project overview (this plan, condensed)
├── MASTER_PLAN.md                # this file
├── SOURCES.md                    # every source: URL, access date, license
├── LICENSE                       # for YOUR compiled dataset (e.g., CC-BY-SA for PD-derived)
├── schema/
│   ├── record.schema.json        # JSON Schema for validation (§5)
│   └── controlled_vocab.md       # allowed values for corpus/tradition/deity/etc.
├── data/
│   ├── public/                   # PD / PD-TRANS / CC only — publishable
│   │   ├── divya_prabandham/
│   │   │   ├── tiruppavai.jsonl
│   │   │   └── ...
│   │   ├── tirumurai/
│   │   ├── upanishads/
│   │   ├── gita/
│   │   ├── ramayana/
│   │   ├── mahabharata/
│   │   ├── bhagavatam/
│   │   └── stotras/
│   └── private/                  # © commentary (Deivathin Kural, modern transl.) — GITIGNORED
│       └── .gitignore            # ignore everything here
├── scripts/
│   ├── transliterate.py          # Aksharamukha / indic-transliteration wrapper
│   ├── validate.py               # validate JSONL against record.schema.json
│   ├── verify_crosscheck.py      # two-source diff helper
│   ├── ingest_<source>.py        # per-source scrapers/parsers
│   └── build_hf_dataset.py       # assemble publishable dataset
├── rag/
│   ├── embed.py                  # build embeddings (BGE-M3 / multilingual-e5)
│   ├── index/                    # vector store (Qdrant/LanceDB/pgvector)
│   └── query.py                  # retrieval + answer with citations
├── finetune/                     # PHASE 3+ (optional)
│   ├── build_instructions.py     # corpus → instruction pairs
│   └── train_lora.py
└── .gitignore                    # includes data/private/
```

---

## 8. The pipeline — step by step

**Step 1 — Acquire.** Download original-language text from an authoritative source (§3). Log source URL + access date + license in `SOURCES.md`.

**Step 2 — Normalize script & transliteration.** Convert to canonical scheme.
- Tools: **Aksharamukha** (web + API), **`indic-transliteration`** Python package (`sanscript`).
- Store `text_original` (source script) + `text_iast` (canonical roman). ITRANS optional for search.

**Step 3 — Structure.** Split into per-verse records matching §5 schema. This is ~60% of the effort. Assign stable IDs (§5.2).

**Step 4 — Verify.** Cross-check each verse against an independent source. Set `verified:true` + `verification_source`. On mismatch: keep both, add `flags:["variant_reading"]`, note it. Never silently choose.

**Step 5 — Validate.** Run `validate.py` against `record.schema.json`. Reject rows missing required fields or provenance.

**Step 6 — Store & version.** Commit JSONL to git. `PD`/`PD-TRANS`/`CC` → `data/public/`. `©` → `data/private/` (gitignored).

**Step 7 — RAG (Phase 2 usage).**
- Embed with **BGE-M3** or **multilingual-e5** (both handle Tamil/Sanskrit well — do NOT use English-only embedders).
- Vector store: **Qdrant / LanceDB / pgvector**.
- Retrieval prompt discipline: *answer only from retrieved verses; cite `id` + `source`; refuse if not in corpus.*

**Step 8 — (Optional) Fine-tune (Phase 3).**
- Base: an **Indic-adapted open model** (Sarvam / Airavata / OpenHathi) — better Indic tokenization than vanilla Llama.
- Build instruction pairs from corpus (Q→verse+cite, transliteration, register).
- Train **LoRA** on a rented single A100/H100 (hours, ~$50–300). Adapter is tiny → easy to host on HuggingFace.

---

## 9. AI Assistant Operating Protocol (paste this to the model on your laptop)

> Give the following as a system/instruction block to any AI assistant helping you curate. This is what makes the approach "model-followable."

```
ROLE: You are a curation assistant for a verified Bhakthi/Sanskrit-Tamil scripture corpus.

HARD RULES:
1. SOURCES: Use only primary/authoritative repositories (GRETIL, sanskritdocuments.org,
   Muktabodha, DCS, SARIT, BORI/Baroda critical editions, Project Madurai, thevaaram.org,
   shaivam.org, sacred-texts.com). NEVER use vamsha.co.in, sandhyakatha.com, templecircuit.in,
   abhivadhaye.co.in, nalnaal.netlify.app — these are downstream outputs, not sources.
2. NO FABRICATION: Never invent, complete, or "reconstruct" a verse, verse number, attribution,
   or citation. If you cannot source it, output flags:["needs_source"] and leave fields null.
   A missing verse is acceptable; a hallucinated one is a critical failure.
3. PROVENANCE: Every record MUST have source + source_license. No record without provenance.
4. LICENSING: Tag license on every text/translation/commentary. Modern translations and
   commentaries (incl. Deivathin Kural) = "©" → route to data/private/, never publishable.
   Original ancient verses = "PD". Old translations (Müller/Ganguli/Griffith) = "PD-TRANS".
5. VERIFICATION: For each verse, cross-check against a SECOND independent source. Set verified
   true/false and record verification_source. On mismatch, keep both + flag "variant_reading".
6. SCHEMA: Emit strictly valid JSONL conforming to record.schema.json (fields per MASTER_PLAN §5).
   Use the ID scheme in §5.2. IDs are immutable once assigned.
7. TRANSLITERATION: Produce text_original (source script) + text_iast (strict IAST). Do not
   guess diacritics — use a transliteration tool; if unsure, flag "translit_uncertain".
8. SCOPE DISCIPLINE: Work one WORK at a time (e.g., finish Tiruppavai before Nachiyar Tirumozhi).
   Report counts (rows done / expected total) at the end of each work.

WORKFLOW PER WORK:
  a. State the source URL(s) you will use and their license.
  b. Emit records one verse at a time in schema order.
  c. After the batch, run a self-check: missing fields? provenance present? counts match
     expected total (e.g., Tiruppavai = 30)? List any flags raised.
  d. Do NOT proceed to the next work until I confirm.

OUTPUT: JSONL only for data; plain prose only for status/checks. Never mix.
```

---

## 10. Roadmap & rough effort

| Phase | Deliverable | Rough effort | Cost |
|---|---|---|---|
| 0 | Repo + schema + `SOURCES.md` + validator | 1–2 evenings | $0 |
| 1a | **Tiruppavai (30) fully verified** — proves the loop | 1 weekend | $0 |
| 1b | Full Divya Prabandham (4,000) | Weeks (mostly mechanical) | ~$0–50 (embeddings) |
| 1c | Tirumurai + Periya Puranam | Weeks | ~$0–50 |
| 2 | Principal Upanishads + Gita | Weeks | small |
| 3 | Ramayana + Mahabharata (critical editions), sub-sliced | Months (large) | small–moderate |
| 4 | Srimad Bhagavatham, then other Puranas | Months | small |
| RAG | Embedded, cited retrieval over Phase 1 corpus | Days once corpus exists | ~$0–50/mo |
| 5 | Commentary layer (license-gated) | Ongoing | — |
| FT | LoRA on Indic base + HF adapter | 1–2 weekends after corpus | ~$50–300 one-off |

**Publish milestones on HuggingFace:** (1) the **dataset** (highest community value, do this at end of Phase 1b), (2) the **LoRA adapter** (tiny, cheap), (3) optional demo Space. Keep HF Inference Endpoints off for a spare-time budget — run inference locally/on-demand.

---

## 11. Environment setup checklist (personal laptop)

```
# Python env
python -m venv .venv && source .venv/bin/activate
pip install indic-transliteration aksharamukha jsonschema pandas
pip install sentence-transformers        # embeddings (BGE-M3 / multilingual-e5)
pip install qdrant-client                # or lancedb / pgvector
# Optional (fine-tune, later)
pip install transformers peft datasets accelerate bitsandbytes

# Tools to bookmark
- Aksharamukha (script converter): script conversion incl. IAST/ITRANS
- HuggingFace account (for dataset + adapter hosting later)
- A vector DB (Qdrant local / LanceDB file-based — easiest to start)
```

---

## 12. Immediate next actions (do these first)

1. Create the repo skeleton (§7) and paste `record.schema.json` from §5.
2. Add `SOURCES.md`; log Project Madurai's Tiruppavai page (URL + access date + license).
3. Hand the **Operating Protocol (§9)** to your AI assistant.
4. Produce **Tiruppavai, all 30 pasurams**, verified against a second source, valid JSONL.
5. Run `validate.py`; confirm 30/30 rows, all with provenance.
6. Only then scale to Nachiyar Tirumozhi → full Divya Prabandham.

**Golden rule to carry everywhere:** primary sources only, provenance on every row, verify against two sources, never fabricate a verse. The moment you feel tempted to "let the model fill it in" — stop, flag it, source it.

---
*End of Master Plan v1.0. This file is self-contained and portable. Email/copy freely.*
