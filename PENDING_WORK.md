# Pending Work — prioritized completion backlog

## P0 — blockers to real verified corpus materialization
These are the highest-value unfinished items because current infrastructure cannot become a large public/verified corpus without them.

1. **Fetch preserved raw source snapshots on a network-enabled runner**
   - Project Madurai Divya Prabandham four blocks
   - Project Madurai Tevaram 14 blocks
   - GRETIL Devī Māhātmya / Bhagavata files
   - Bombay-Indology Mahābhārata 18 files
   - Ramayana/Sundara source + Baroda print witness
   - Record SHA-256 checksums and access dates

2. **Materialize the Tamil parent staging corpora**
   - Divya Prabandham: 4,000 staging rows
   - Andal: confirm 173 row slice
   - Tevaram 1–7: 8,240 staging rows through `ingest_tevaram.py`
   - Preserve source anomalies; do not auto-repair

3. **Run full Devī Māhātmya certification**
   - all Markandeya 81–93 substantive verses
   - sequence-aware secondary alignment
   - deterministic Devanagari normalization
   - review every non-match / counted `uvāca` divergence

4. **Run Sundara Kāṇḍa full CE transcription comparison**
   - 66-sarga critical-edition lane
   - compare electronic text against Baroda Critical Edition vol. V witness
   - retain 68-sarga traditional witnesses as separate recension evidence

5. **Independent verification at scale**
   - Divya Prabandham: pin and ingest a genuinely independent witness
   - Tevaram: evaluate IFP/EFEO Digital Tēvāram as verification lane; pin exact reuse terms and text lineage
   - Mahābhārata: pin independent CE/print witness strategy before setting `verified:true`
   - Bhagavata: pin independent second witness per selected episode/full parent

## P1 — high-value corpus breadth
6. **Bhāgavata parent materialization + episode views**
   - full 12-skandha parent
   - materialize the seven exact high-value episode ranges already pinned
   - independent verification before promotion

7. **Mahābhārata full parent materialization**
   - ingest MBh01–MBh18 once
   - materialize seven curated views
   - exact-locus validation and second-source promotion

8. **Complete Valmiki Ramayana parent contract**
   - all seven kāṇḍas
   - preserve recension/critical-edition identity
   - Sundara becomes a derived view, not a duplicate corpus

9. **Vishnu Purana + Harivamsha**
   - prioritize genealogy/avatar material because of cross-corpus graph value
   - pin file-level terms + stable loci + second witness

10. **Sanskrit core: Bhagavad Gita + principal Upanishads**
    - pin publication-compatible primary sources
    - map chapter/unit counts and recension identities
    - ingest Gita 700 + principal Upanishads

## P2 — Tamil breadth after core lanes are moving
11. **Finish Divya Prabandham verification in batches**
    - Tiruppavai → Andal 173 → work-by-work through 4,000

12. **Finish Tevaram verification in patikam batches**
    - use structural `tirumurai.patikam.verse` identity
    - preserve running-number discrepancies as source anomalies
    - capture paṇ, talam/sthalam and variant readings when sourced

13. **Periya Puranam and remaining Tirumurai**
    - story/hagiography layer after Tevaram source discipline is proven

## P3 — realization/product moat
14. **Claim verifier — productionize** ✅ COMPLETE
    - exact verified original-script and canonical-transliteration lookup
    - fuzzy/lossy transliteration candidates never authenticate
    - unverified exact matches are explicitly ignored for authority
    - structured JSON + “popular quote not found” Markdown report format

15. **Claim-by-claim grounded synthesis**
    - every generated statement must carry `support_ids`
    - unsupported clauses rejected before rendering

16. **Cross-text comparison packet**
    - e.g. Narasimha across Bhagavata / Vishnu Purana / Alwar corpus
    - organize evidence by corpus without harmonizing disagreements

17. **Variant-aware response renderer**
    - show primary reading, attested alternatives, recension/source, confidence/status

18. **Evidence graph**
    - episode, genealogy, sacred geography, deity/avatar, festival/vrata edges
    - every edge requires verified corpus IDs

19. **Verified-only multilingual semantic index**
    - production embeddings (BGE-M3 or multilingual-e5)
    - index build must filter verified rows first
    - benchmark Tamil/Sanskrit/English query recall

20. **Evaluation suite / moat scorecard**
    - quote authenticity tests
    - locus attribution tests
    - variant surfacing tests
    - “no evidence” refusal tests
    - compare error rate vs frontier freestyle answers

## P4 — publication and operations
21. **Licensing/publication matrix per exact source file** ✅ COMPLETE (`sources/LICENSE_MATRIX.json`)
22. **Dataset release builder (public vs restricted rows)** ✅ COMPLETE (`open` / `research-nc` / `internal` profiles)
23. **CI pipeline: fetch/checksum → ingest → validate → verify → publish gate** ✅ COMPLETE (network acquisition + trust/release workflows)
24. **Hugging Face dataset card + provenance documentation** ✅ COMPLETE as pre-release draft
25. **Optional private commentary RAG** (strictly isolated from public corpus)
26. **Fine-tuning only after corpus/evaluation maturity** — low priority by design

---

## Recommended burn-down order
**Raw acquisition → Devī full certification → DP/Tevaram staging → Sundara comparison → Bhagavata parent + episodes → Mahābhārata parent → second-source verification batches → claim/comparison product → evidence graph → Gita/Upanishads → remaining parent corpora.**

## Moat rule
Every item above must pass `MOAT_CHECK.md`. Infrastructure can remain neutral, but no data or claim is promoted unless it strengthens verified, cited, structured ground truth and preserves refusal boundaries.


## Devī Māhātmya — remaining execution-only blocker
- [x] Full 13-chapter certification contract
- [x] Edition-aware second-source aligner
- [x] Deterministic Devanagari normalization + spot checks
- [x] Certification auditor requiring 1:1 coverage
- [x] Claim-by-claim grounded synthesis/refusal gate
- [x] Secondary rights boundary: verification only; meanings/commentary excluded
- [ ] Fetch GRETIL raw file + Ved Path chapters 1–13 into local raw-source store
- [ ] Run full alignment and inspect every `needs_review` mismatch
- [ ] Promote only rows passing audit to `data/public/`

**Moat rule:** the unchecked items must not be bypassed by model-generated reconstruction.

## Completed product capability — variants + evidence graph
- [x] Structured contradiction/variant relation schema.
- [x] Semantic contradiction/expansion/omission classifications require curator review; text difference alone cannot auto-promote a semantic conclusion.
- [x] Both sides retain verified support IDs; no preferred side or silent reconciliation.
- [x] Evidence graph schema + builder with verified-evidence-only edges.
- [x] Graph semantic edges require curator review or an accepted cross-source relation.
- [x] Regression tests reject unverified evidence and unreviewed semantic edges.

Next graph expansion work: populate real entities/edges from fully materialized verified corpora (deity↔episode, episode↔text, temple↔verse, genealogy, festival/ritual) once real source rows are locally acquired and certified.

## Real evidence graph — next population tranches
1. **Prahlāda lineage continuation:** certify independent witnesses for Viṣṇu Purāṇa 1.21.1 before adding Virocana → Bali; do not use a derivative mirror as the second witness.
2. **Bhāgavata Prahlāda person node:** certify a primary+independent witness for a verse directly naming Prahlāda in the Narasiṃha scene (e.g. 7.9.x) before merging person evidence across texts.
3. **Temple ↔ verse:** start only with verses whose stalam association is explicit in authoritative metadata/edition; temple lore from model memory is inadmissible.
4. **Cross-text episode relations:** add reviewed agreement/expansion/scope-difference relations one dimension at a time; never label whole narratives 'same' or 'contradictory' wholesale.

## Highest-priority next work after moat proof suite

1. Run `benchmark/cases.json` unchanged against Vedapath, DharmaChat, Gemini, Claude, and ChatGPT; save dated outputs and score with `benchmark/RUBRIC.md`.
2. Expand the benchmark from 5 to ~25 adversarial cases covering textual variants, recension mismatches, misattributed quotes, cross-language Tamil/Sanskrit parallels, genealogy, ritual overclaim, and temple identity overclaim. ✅ COMPLETE: 25 cases / 82 native checks.
3. Materialize substantially more fully verified rows. The current demo is deliberately narrow; architecture breadth must not be mistaken for corpus depth.
4. Add a small web/API surface only after competitive benchmark results show a real delta users can see.


## 2026-09-09 publication/network handoff completion
- [x] Rights-aware file-level license matrix for all 51 currently catalogued sources.
- [x] Release profiles: `open`, `research-nc`, `internal`; default-deny for unresolved/restricted sources.
- [x] Research-NC release candidate currently: 24 verified rows + 29 evidence nodes + 41 evidence edges.
- [x] Open release candidate currently: 0 rows (correctly excludes current CC-NC-only verified seed).
- [x] SHA-256 release manifests and closed-loop graph evidence audit.
- [x] GitHub CI for trust gates and release candidates.
- [x] Network acquisition workflow with checksummed raw snapshots and provenance sidecars.
- [x] One-command `network_materialize.py` orchestration for the P0 core and Mahabharata parent.
- [x] Benchmark v2 reconciled into main repo: 25/25 cases, 82/82 checks.
- [x] Claim verifier productionized with exact transliteration search + non-authoritative candidate handling.
- [ ] Actual raw snapshot fetch remains blocked only in this ChatGPT runtime; run `python scripts/network_materialize.py --group core-materialization --fetch --materialize` on a normal network-enabled host.

## 2026-09-09 — local realization/platform items completed
- [x] Indexed local evidence store (SQLite) over verified records + graph evidence joins.
- [x] Stable Pramāṇa service contract (`health` / `verify` / `compare` / `trace`).
- [x] Dependency-light local HTTP API suitable for MacBook prototype work.
- [x] Corpus/graph/benchmark quality dashboard with explicit materialization-depth warning.
- [x] Competitor benchmark operations: provider scorecard creation, captured-answer ingestion, validation, and side-by-side score summaries.

**Still deliberately pending:** production semantic embeddings, public UI, and real competitor scoring. These should follow larger verified materialization / benchmark runs, not precede them.

## Curation throughput
- [x] Curator review queue architecture and CLI.
- [x] Proof-bundle export and integrity checker.
- [ ] Burn down 25 P0 source-rights review items.
- [ ] Bulk materialization will populate row-level verification/variant review debt automatically.
