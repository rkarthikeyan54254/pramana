# Build Status — 2026-09-09

## Current strategy
Parallel expansion with hard lifecycle boundaries: **ingested ≠ normalized ≠ verified ≠ publishable**.

## Foundation ✅
- Repository, schema, controlled vocabulary, public/private split
- Source registry + raw snapshot manifest
- JSONL validator + corpus quality report
- Catalog arithmetic validator
- Source-numbering anomaly auditor
- Fail-closed Project Madurai ingester
- Catalog-driven work ingestion wrapper

## Divya Prabandham lane 🟢
- [x] Four Project Madurai Tamil source editions pinned
- [x] **24 works mapped continuously from pasuram 1–4000**
- [x] Catalog invariant check: 24 work ranges sum to exactly 4000
- [x] Andal slice pinned: Tiruppavai 30 + Nachiyar Tirumozhi 143 = **173**
- [x] Tiruvaymozhi flagged for source-numbering audit; source HTML shows numbering anomalies and file-range overlap behavior
- [ ] Raw snapshots acquired in runtime (blocked by sandbox network; fetcher ready)
- [ ] 4,000 staging rows generated from preserved snapshots
- [ ] Independent verification source pinned for Divya Prabandham

## Tevaram lane 🟢 source-mapped
- [x] Tirumurai 1–7 source blocks mapped
- [x] Total mapped numbered units: **8,240**
- [x] Author mapping: Sambandar 1–3, Appar 4–6, Sundarar 7
- [ ] Generic Tevaram patikam-aware ingester
- [ ] Independent verification source (prefer thevaaram.org or equivalent) pinned with terms

## Sanskrit core lane 🟡
- [x] Gita Supersite confirmed live with chapter/sloka Sanskrit text
- [x] SanskritDocuments confirmed live; **restricted for public redistribution** under current stated terms, so verification/reference only
- [x] GRETIL Isha Upanishad confirmed live with Kāṇva recension and stable verse markers
- [ ] Pin Gita primary + second source with explicit publication-compatible terms
- [ ] Map 18 Gita chapters and principal Upanishad unit counts/recensions

## Trust / QA findings
1. Project Madurai Thiruvaymozhi demonstrates why raw source numbering must be audited: the displayed sequence contains duplicate/out-of-order numbering near the beginning.
2. Source file headers cannot always be treated as exact content boundaries; Part 4 is labeled 2971–4000 but reproduces Thiruvaymozhi from 2791 for continuity.
3. Licensing remains source-specific. Ancient/public-domain work status does **not** imply unrestricted redistribution of every modern e-text transcription.

## Runtime constraint
Shell/Python network access in this sandbox cannot fetch the external HTML snapshots. The web layer can verify live sources, so manifests/catalogs are being prepared here; `make fetch` is ready for a network-enabled laptop/CI environment. No model-reconstructed verse text is substituted.

## Realization v1 gate
1. Tiruppavai 30/30 publishable.
2. Andal 173 ingested and measurable.
3. Full DP 4,000 ingestion path executable.
4. Tevaram 1–7 source map executable.
5. Verified-only grounded query demo.

## Ithihasa / Purana lane 🟢 portfolio-mapped
- [x] Tier-1 anchors selected: Valmiki Ramayana, Mahabharata CE, Harivamsha, Bhagavata Purana, Vishnu Purana, Devi Mahatmya
- [x] Tier-2 high-value Purana list mapped
- [x] Epic/Purana early-slice strategy defined to avoid waiting for whole gigantic works
- [x] Cross-corpus realization products defined: episode graph, genealogy, sacred geography, festival evidence, deity/avatar index, claim verifier
- [x] BORI/Bombay Indology/GRETIL source candidates pinned at discovery level
- [x] License policy tightened: pin terms per exact e-text file, especially GRETIL legacy vs newer TEI records
- [ ] Exact file-level source/terms manifest for Tier-1 corpora
- [ ] Generic Sanskrit hierarchical parser (`book/chapter/verse` + source-native locus)
- [ ] First certified epic slice (recommended: Sundara Kanda or Yaksha Prashna)
- [ ] First certified Purana slice (recommended: Devi Mahatmya or Bhagavata Prahlada/Narasimha)

## 2026-09-09 — Devī Māhātmya / Sundara Kāṇḍa execution
- [x] Pin Devī Māhātmya parent range: Markandeya Purana 81–93.
- [x] Pin start/end markers: `MarkP_81.1` → `MarkP_93.17`.
- [x] Pin Sundara Kāṇḍa GRETIL source and edition structure: kanda 5, sargas 1–66.
- [x] Add source contracts and episode catalog.
- [x] Keep all unverified Bhāgavata/Mahābhārata episode boundaries explicitly unresolved.
- [x] Implement MarkP extractor + Rāmāyaṇa a/c-pada combiner.
- [x] Pin Devī Māhātmya exact GRETIL licence: CC BY-NC-SA 4.0.
- [x] Pin independent Devī Māhātmya verification edition (Ved Path) and document numbering drift from counted `uvāca` cues.
- [x] Add sequence-aware Devī verifier + fail-closed certification step; synthetic drift fixture passes.
- [ ] Fetch raw source snapshots on a network-enabled runner.
- [ ] Run all 13 chapters through primary ingest + secondary alignment.
- [ ] Deterministically convert/audit GRETIL IAST into Devanagari `text_original` before public promotion.
- [x] Sundara Kāṇḍa recension guard added: critical-edition lane = 66 sargas; common 68-sarga witnesses kept separate.
- [x] 66-sarga SanskritDocuments witness discovered, but independence from the GRETIL/Bombay-Indology lineage is not yet assumed.
- [ ] Pin genuinely independent critical-edition-compatible second witness for Sundara Kāṇḍa.

## 2026-09-09 — momentum pass: Sanskrit normalization + Bhagavata episode ranges

- Added deterministic in-repo Sanskrit IAST → Devanagari transliteration (`scripts/iast_to_devanagari.py`).
- Regression fixtures reproduce paired Devī Māhātmya Devanagari witnesses exactly; no external package or LLM is required for this conversion.
- Devī certification now emits Devanagari `text_original`, retains IAST in `text_iast`, and removes the `needs_script_normalization` flag when conversion succeeds.
- `make devi-gate` is green on the edition-numbering-drift fixture (2/2 verified, schema valid).
- Promoted Bhagavata high-value offerings to chapter-range-verified status: Prahlāda–Narasimha (7.5–7.10), Gajendra Mokṣa (8.2–8.4), Dhruva (4.8–4.12), Kapila–Devahuti (3.25–3.33), Uddhava Gītā conservative lane (11.7–11.29), full Skandha 10, plus Rāsa Pañcādhyāyī (10.29–10.33).
- Exact first/last verse markers remain an ingestion-time gate against the pinned GRETIL parent source; chapter-level curation does not masquerade as exact verse-level certification.

## 2026-09-09 — exact Bhāgavata boundaries + Sundara CE witness closure
- [x] Promoted seven high-value Bhāgavata offerings from chapter-range to **exact source-locus boundaries**.
- [x] Prahlāda–Narasimha semantic end pinned to GRETIL's anomalous `BhP_07.09.047*` marker occurring inside chapter 7.10; anomaly is preserved, not repaired silently.
- [x] Full Skandha 10 exact end pinned to `BhP_10.90.050*`.
- [x] Gajendra Mokṣa exact end pinned to `BhP_08.04.026`.
- [x] Dhruva exact end pinned to `BhP_04.12.052`.
- [x] Kapila–Devahūti exact end pinned to `BhP_03.33.037`.
- [x] Uddhava Gītā conservative exact end pinned to `BhP_11.29.049*`.
- [x] Rāsa Pañcādhyāyī exact range pinned to `BhP_10.29.001`–`BhP_10.33.039`.
- [x] Sundara Kāṇḍa Baroda Critical Edition Vol. V (G. C. Jhala) classified as the preferred print constituted-text witness for GRETIL transcription verification.
- [x] Added strict episode-catalog validator and combined `make next-gate`.
- [ ] Full electronic-vs-print Sundara verse comparison remains dependent on acquiring the Baroda scan in a network-enabled/OCR-capable verification environment; no claim of row-level completion is made before that comparison.

## 2026-09-09 — Mahābhārata devotional/dharma slice execution
- [x] Pinned finalized 2026 Bombay Indology electronic Critical Edition as the parent-source lane; site states the text is considered final as of 2026-06-14 after 535 corrections.
- [x] Yakṣa Praśna framing pinned to CE `3.296–3.299`; the question core is chapter `3.297`, with crisis/revival context retained as the default episode view.
- [x] Nala–Damayantī / Nalopākhyāna pinned to CE `3.50–3.78` (29 chapters).
- [x] Sāvitrī / Sāvitryupākhyāna pinned to CE `3.277–3.283` (7 chapters).
- [x] Vidura Nīti pinned to CE `5.33–5.40` (8 chapters).
- [x] Nārāyaṇīya pinned to CE `12.321–12.339` (19 chapters); independently corroborated by dedicated GRETIL Nārāyaṇīya text.
- [x] Viṣṇu Sahasranāma pinned to CE `13.135`; exact within-chapter verse endpoints remain an extraction-time refinement.
- [x] Added finalized Mahābhārata CE source contract and strict recension policy.
- [x] Added `materialize_mahabharata_slices.py`; it materializes curated views only from a normalized CE parent corpus and fails on missing chapters.
- [x] Added synthetic parent-corpus regression fixture and `make mahabharata-gate`; gate is GREEN for all six slices.
- [ ] Fetch/normalize the 18 finalized CE parent files in a network-enabled runner.
- [ ] Promote chapter-level ranges to exact first/last verse loci where semantically useful, especially Viṣṇu Sahasranāma and Yakṣa question-only subview.

## 2026-09-09 — Mahābhārata parent-ingestion closure
- [x] Exact Viṣṇu Sahasranāma CE locus pinned to `MBh_13.135.001`–`MBh_13.135.142`.
- [x] Exact Yakṣa question/answer core derived view pinned to `MBh_03.297.026`–`MBh_03.297.061`; `3.297.062` explicitly closes the question sequence.
- [x] Added strict Bombay-Indology Unicode-Roman CE ingester for source-native `PPCCCVVV[pada]` markers.
- [x] Speaker/source cues are preserved as metadata rather than silently merged into verse text.
- [x] Same-locus pādas are combined into one canonical verse row; non-monotonic/duplicate loci fail closed.
- [x] Deterministic ISO-15919 combining-form normalization + Devanagari generation is part of the ingestion path.
- [x] Added all 18 direct Unicode-Roman parent-file URLs to the source manifest.
- [x] Upgraded Mahābhārata slice materializer to support exact verse-level endpoints as well as chapter ranges.
- [x] Added `mahabharata-parent`, `mahabharata-materialize`, and `completion-gate` Make targets.
- [x] `make completion-gate` is GREEN.
- [ ] Full 18-parva parent JSONL cannot be materialized inside this runtime until the 18 source files are physically fetched; direct source file URLs are live in the web layer but container network download is unavailable. No source text is reconstructed from model memory.

## Verified-only realization layer
- Added `rag/verified_store.py` and `rag/query.py`.
- Retrieval eligibility is hard-gated on `verified:true` + non-empty `verification_source`.
- Every hit returns stable ID, original text, source, verification witness, variants and flags.
- Zero verified hits => explicit refusal; pretrained/model memory is not a fallback.
- Added `rag/ANSWER_POLICY.md`, `MOAT_CHECK.md`, and regression test proving unverified rows cannot leak into retrieval.
- `make realization-gate` is GREEN.

### Moat check: 6/6 YES
This layer strengthens the moat because it exposes verified evidence and refusal behavior; it does not create or feed generated devotional prose back into the corpus.

## 2026-09-09 — Semantic realization layer

Implemented hybrid lexical + semantic retrieval with the verified-only authority gate applied **before** embedding/ranking.

- `rag/semantic_store.py`: optional local sentence-transformers backend plus deterministic precomputed-vector mode.
- `rag/hybrid_query.py`: reciprocal-rank fusion of lexical and semantic retrieval.
- `rag/assemble_answer.py`: auditable answer packet with per-claim `support_ids` and a generation contract.
- Unverified records are excluded before semantic ranking; a high similarity score cannot promote an unverified row.
- Generated explanations are explicitly prohibited from entering the authoritative corpus.
- `make semantic-realization-gate` is GREEN.

### Moat check
1. Ground truth: YES — retrieval authority remains verified corpus rows only.
2. Provenance: YES — evidence carries source + verification source + stable ID.
3. Verification: YES — `verified:true` and non-empty verification source are mandatory before ranking.
4. Structure: YES — answer packets expose evidence and claim→support mappings.
5. Refusal boundary: YES — no evidence means no model-memory answer.
6. Feedback-loop safety: YES — generated prose cannot become corpus data.

Result: semantic recall added without expanding the authority boundary.

## 2026-09-09 — long-session backlog burn-down
- [x] Added patikam-aware Tevaram ingester using source-native `tirumurai.patikam.verse` as canonical identity.
- [x] Displayed running-number anomalies are preserved as flags instead of silently renumbered.
- [x] Added regression fixture proving a duplicate displayed number does not corrupt structural verse identity.
- [x] Pinned IFP/EFEO Digital Tēvāram as a scholarly independent-verification candidate; exact reuse terms/text lineage still require pinning before certification/publication.
- [x] Added verified-only scripture/quote claim verifier.
- [x] Exact match in an unverified row cannot authenticate a claim.
- [x] Fuzzy similarity can suggest verified candidates but can never establish authenticity.
- [x] Added `PENDING_WORK.md` prioritized completion backlog.
- [x] `make long-session-gate` GREEN.

### Moat check
Tevaram parser: 6/6 YES — strengthens source-locus integrity and preserves anomalies.
Claim verifier: 6/6 YES — directly realizes "the moat is being able to prove the answer" and refuses unverified authenticity claims.

## 2026-09-09 — Devī full-certification + grounded synthesis pass
- Added strict full-certification auditor requiring all chapters 81–93, one verification row per primary row, no unresolved alignments, chapter-consistent secondary loci, and no blocker flags in certified output.
- Added independent Devanagari normalization spot checks against displayed witness text.
- Pinned all 13 Ved Path chapter URLs as a verification-only lane; its modern meanings/commentary are explicitly excluded from public corpus data.
- Added claim-by-claim grounded synthesis validator: every claim requires verified `support_ids`; direct quotes must be extractive; unsupported claims are rejected.
- Remaining Devī blocker: physical fetching of the complete raw primary + 13 secondary chapter pages in a network-enabled filesystem runtime, followed by full alignment/certification audit.

## 2026-09-09 — Tevaram second-source verification implementation
- [x] Qualified IFP/EFEO Digital Tēvāram as the preferred scholarly second-source lane.
- [x] Confirmed Digital Tēvāram Tamil text is based on the PIFI T.V. Gopal Iyer edition: vol. 1 Ñāṉacampantar (1984), vol. 2 Appar+Cuntarar (1985).
- [x] Confirmed IFP coverage: 798 patikams across Tirumurai 1–7 (136+122+127+113+100+99+101).
- [x] Added `parse_ifp_tevaram.py` for Tamil-script patikam witness pages.
- [x] Added strict `verify_tevaram_ifp.py`; same structural locus + conservative normalized exact Tamil is required for auto-verification.
- [x] Added `certify_tevaram_ifp.py`; missing/mismatched witnesses fail closed.
- [x] Added regression test and Tevaram verification Make gate.
- [x] Kept IFP English gloss, concordance, maps, and audio out of corpus ingestion.
- [ ] Full real-source comparison across all 798 patikams / 8,240 Project Madurai numbered units awaits local acquisition of both source sets.

## Cross-text comparison checkpoint
- Evidence-backed cross-text comparison engine implemented: `rag/cross_text_compare.py`.
- Formal comparison artifact schema implemented: `schema/comparison.schema.json`.
- First Prahlāda–Narasimha trust fixture proves an unverified tradition row cannot enter the comparison even when the source is declared.
- Missing source/dimension evidence is emitted as an explicit gap; model memory cannot fill it.
- Source/work ownership of every support ID is enforced.
- Direct quotes must be extractive from their supporting verified rows.
- `make cross-text-gate` is GREEN.

## 2026-09-09 — contradiction/variant + evidence graph expansion
- Added structured cross-source relation model for agreement, expansion, omission, textual variants, recension/scope differences, contradiction, and unresolved differences.
- Semantic relation types cannot auto-promote from model inference; they require explicit curator review.
- Both sides of every relation require verified corpus support IDs; no preferred side is selected and silent resolution is forbidden.
- Added evidence graph schema and builder for people/deities/avatars/episodes/texts/traditions/places/temples/concepts/festivals/rituals/lineages.
- Every admitted graph edge requires verified corpus evidence plus an auditable derivation basis.
- Unverified evidence and unreviewed semantic edges are rejected by regression tests.

## Real evidence graph population checkpoint — 2026-09-09
- [x] Added first non-fixture certified Sanskrit seed records from Devī Māhātmya chapter 82 (4 rows).
- [x] Each seed row is verified against a second live witness (Ved Path), with liturgical numbering offset documented.
- [x] Added first real evidence graph: 7 nodes / 4 verified edges / 0 rejected edges.
- [x] Semantic graph edges remain curator-reviewed where interpretation is required; no model-inferred authority.
- [ ] Expand next into deity/avatar ↔ episode ↔ scripture from Bhāgavata and Mahābhārata once certified rows are physically materialized.

## 2026-09-09 — real graph expansion: Bhāgavata + Viṣṇu Purāṇa + genealogy
- [x] Tightened node authority: real graph nodes, not only edges, require verified `evidence_ids` plus an auditable derivation.
- [x] Added 3 certified Bhāgavata Narasiṃha rows (7.8.29, 7.8.45, 7.8.49) and real avatar/deity/episode edges.
- [x] Added 4 certified Viṣṇu Purāṇa rows (1.17.12; 1.20.32, 35, 39), verified against a second Sanskrit witness.
- [x] Added first real genealogy edges: Hiraṇyakaśipu `father_of` Prahlāda and Prahlāda `son_of` Hiraṇyakaśipu.
- [x] Added Daitya lineage node and evidence-backed `became_lord_of` edge for Prahlāda.
- [x] Added explicit Narasiṃha `form_of` Viṣṇu and Hari `protects` Prahlāda edges from direct Sanskrit wording.
- [x] Added curator-reviewed cross-locus Narasiṃha `causes_death_of` Hiraṇyakaśipu edge; referent resolution is not treated as deterministic.
- [x] Added first real reviewed cross-source relation: Bhāgavata and Viṣṇu Purāṇa agree narrowly on Narasiṃha as divine manifestation; this does NOT assert full narrative identity.
- [x] Global graph merge/build/audit/query layer operational.
- [x] Global real graph: **18 nodes / 19 edges / 0 dangling evidence / 0 bad node refs / 0 dangling relation refs**.
- [x] Relation IDs are now audited against accepted relation sets, closing a graph-authority gap.
- [ ] Temple edges remain intentionally unpopulated until a verse-to-sthalam association is itself source-backed/curator-certified. No temple association will be inserted from general model knowledge.

## 2026-09-09 — real graph expansion: third Purāṇic witness + Śrīśaila place evidence
- [x] Added 6 certified Narasiṃha Purāṇa chapter 44 rows with second-witness checks.
- [x] Added Narasiṃha Purāṇa as a third independent Purāṇic witness for the Prahlāda–Narasiṃha cluster.
- [x] Added real evidence-backed Śrīśaila place node and two narrowly scoped edges: Narasiṃha reaches / remains at Śrīśaila in the source passage.
- [x] Did **not** promote that place reference into a claim about any specific modern temple; that requires separate historical/temple evidence.
- [x] Added two curator-reviewed cross-source agreement relations linking Narasiṃha Purāṇa with Viṣṇu Purāṇa and Bhāgavata on divine manifestation identity/status.
- [x] Fixed canonical graph identity conflict for Śrīmad Bhāgavata Purāṇa rather than allowing label drift.
- [x] Hardened the global auditor so both evidence IDs and relation IDs must resolve to certified artifacts.
- [x] Global graph now: **21 nodes / 30 edges / 3 accepted cross-source relations / 0 dangling evidence / 0 dangling relation refs / 0 schema errors**.
- [x] `make real-graph-gate` GREEN with all four real certified seed corpora validated.

### Moat check
- Ground truth: YES — all real graph evidence IDs resolve to certified rows.
- Provenance: YES — node/edge authority remains traceable to exact corpus loci and second witnesses.
- Verification: YES — new Narasiṃha Purāṇa rows pass the same verified-row contract.
- Structure: YES — deity/avatar, episode, genealogy, text, lineage and place edges are machine-queryable.
- Refusal boundary: YES — modern temple identity is intentionally *not* inferred from a textual Śrīśaila mention.
- Feedback-loop safety: YES — semantic cross-text agreement is curator-reviewed and relation IDs are audited.

## 2026-09-09 — Temple / genealogy / ritual graph tranche
- Added certified Viṣṇu Purāṇa 1.21.1 genealogy seed: Prahlāda → Virocana → Bali.
- Added certified Devī Māhātmya chapter 12 ritual evidence: Aṣṭamī/Navamī/Caturdaśī hearing/recitation and annual autumn mahāpūjā.
- Added certified Vāmana Purāṇa chapter 68 temple/ritual evidence: generic Keśava/Hari shrine construction, Vāsudeva-shrine lamp offering, Vindhyāvalī lamp offering, and tithi-based upavāsa.
- Kept generic scriptural temple evidence separate from any named modern temple identification.
- Global real graph: 30 nodes / 41 edges; audit clean (0 schema errors, 0 dangling evidence, 0 dangling relation refs).
- `make real-graph-gate`: GREEN.

## Moat proof suite — 2026-09-09

Implemented the first measurable product proof layer:

- `product/verify_claim.py`
- `product/compare_sources.py`
- `product/trace_evidence.py`
- `product/demo_suite.py`
- `benchmark/cases.json`
- `benchmark/run_native.py`
- `benchmark/RUBRIC.md`
- `benchmark/external_score_template.json`

Current native benchmark result: **5/5 cases, 16/16 checks, 100%**.

This score is intentionally not presented as a market benchmark. It confirms our own implementation satisfies the moat contract. Competitive validation requires running the identical prompts on external products/models and scoring them with the same rubric.

`make moat-proof-gate` = GREEN.


## 2026-09-09 — sizeable publication + network handoff chunk

### Completed
- Reconciled Moat Benchmark v2 into the main working tree: **25/25 cases, 82/82 checks**.
- Added `sources/LICENSE_MATRIX.json` covering **51 catalogued sources** with explicit release classifications.
- Added rights-aware release profiles and builder/checker. Current reproducible `research-nc` candidate contains **24 verified records + 29 graph nodes + 41 graph edges**. `open` correctly contains 0 records because all currently materialized verified seed text is CC BY-NC-SA 4.0.
- Added SHA-256 release manifests and graph/evidence closure validation.
- Added GitHub trust/release CI and separate raw-source acquisition workflow.
- Reworked source fetcher to support chapter-expanded sources, immutable SHA sidecars, provenance metadata, key filtering and dry-run.
- Added priority acquisition groups plus `network_materialize.py` for one-command P0 acquisition/materialization on a network-enabled host.
- Added publication policy, network handoff runbook and Hugging Face dataset-card draft.
- Productionized claim verification: exact original-script or canonical-transliteration matches can authenticate; lossy ASCII/fuzzy candidates cannot; exact matches found only in unverified rows are reported but ignored for authority.

### Gates
- `publication-gate`: GREEN
- `claim-verifier-test`: GREEN
- `moat-benchmark-v2`: GREEN (25/25, 82/82)

### Remaining primary blocker
This runtime still cannot resolve external hosts from shell/Python. Actual raw source materialization must run on a normal network-enabled laptop or GitHub workflow. The orchestration for that step is now complete; no model-generated scripture substitution is permitted.

## 2026-09-09 — local platform / realization chunk

### Completed without network access
- Added `graph/sqlite_store.py`: verified-record/evidence graph materialization into indexed SQLite. Current local store: **24 verified records / 30 nodes / 41 edges**, with evidence join tables and foreign-key closure.
- Added stable `product/service.py` contract for `health`, `verify`, `compare`, and `trace` operations.
- Added dependency-light local HTTP API (`product/http_server.py`) exposing `/v1/health`, `/v1/verify`, `/v1/compare`, `/v1/trace`.
- Added generated quality dashboard (`dist/dashboard/index.html` + `quality.json`). It explicitly shows the depth warning: only **0.2% of the already mapped 12,240 Tamil units** are materialized in this checkpoint; 100% verification applies only to the 24 seed rows.
- Added external benchmark workflow hardening: scorecard validation, provider scorecard creation, answer capture, and multi-scorecard comparison.
- Added `docs/LOCAL_PLATFORM.md` with MacBook-first run instructions.
- Added focused local platform regression gate. `make local-platform-focused-gate`: **GREEN**.

### Moat check
- SQLite/API/dashboard are delivery/index layers only; authoritative data remains verified JSONL.
- Local store build fails if graph node/edge evidence does not resolve to independently verified records.
- External competitor scores require captured answers; marketing claims cannot earn benchmark points.
- Dashboard distinguishes contract compliance from corpus depth to avoid self-deception.

## Curation + proof scaling checkpoint
- Added generated curator review queue with stable IDs, priorities and auditable resolution state.
- Current queue surfaces 48 source-policy tasks: 25 P0 + 23 P1.
- Added portable proof-bundle export with verified records, relations, graph subset, rights metadata and SHA-256 integrity.
- `make curation-proof-gate` is GREEN.
