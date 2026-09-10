PYTHON ?= python3

.PHONY: validate check-catalog quality fetch ingest-tiruppavai ingest-nachiyar audit
validate:
	$(PYTHON) scripts/validate.py tests/valid_record.jsonl

check-catalog:
	$(PYTHON) scripts/validate_catalog.py

quality:
	$(PYTHON) scripts/quality_report.py data tests

fetch:
	$(PYTHON) scripts/fetch_sources.py sources/manifest.json

audit:
	$(PYTHON) scripts/validate_catalog.py
	$(PYTHON) scripts/validate_ithihasa_purana_catalog.py
	$(PYTHON) scripts/validate.py tests/valid_record.jsonl
	$(MAKE) test-sanskrit-translit

ingest-tiruppavai:
	$(PYTHON) scripts/ingest_work.py tiruppavai

ingest-nachiyar:
	$(PYTHON) scripts/ingest_work.py nachiyar_tirumozhi

source-contracts:
	$(PYTHON) scripts/validate_source_contracts.py

contracts:
	$(PYTHON) scripts/validate_source_contracts.py

test-devi-verifier:
	$(PYTHON) tests/test_network_regressions.py

test-devi-certify:
	$(PYTHON) tests/test_devi_certification_strict.py

devi-gate: test-devi-verifier test-devi-certify


test-sanskrit-translit:
	$(PYTHON) tests/test_sanskrit_translit.py


episode-catalog:
	$(PYTHON) scripts/validate_episode_catalog.py

next-gate: audit source-contracts episode-catalog devi-gate
	@echo "next-gate: GREEN"

mahabharata-slice-test:
	$(PYTHON) scripts/materialize_mahabharata_slices.py tests/mahabharata_parent_fixture.jsonl --outdir /tmp/mbh-slices

mahabharata-gate: episode-catalog source-contracts mahabharata-slice-test
	@echo "mahabharata-gate: GREEN"

mahabharata-ingest-test:
	$(PYTHON) scripts/ingest_mahabharata_ce.py tests/mahabharata_ce_raw_fixture.txt --output /tmp/mbh-ingest-fixture.jsonl
	$(PYTHON) scripts/validate.py /tmp/mbh-ingest-fixture.jsonl

mahabharata-parent:
	$(PYTHON) scripts/ingest_mahabharata_ce.py sources/raw/mahabharata/MBh*.txt --output data/staging/mahabharata_critical_edition.jsonl
	$(PYTHON) scripts/validate.py data/staging/mahabharata_critical_edition.jsonl

mahabharata-materialize:
	$(PYTHON) scripts/materialize_mahabharata_slices.py data/staging/mahabharata_critical_edition.jsonl --outdir data/staging/mahabharata_slices

completion-gate: audit source-contracts episode-catalog devi-gate mahabharata-ingest-test mahabharata-gate
	@echo "completion-gate: GREEN"

verified-rag-test:
	$(PYTHON) tests/test_verified_rag.py

realization-gate: completion-gate verified-rag-test
	@echo "realization-gate: GREEN"

semantic-rag-test:
	$(PYTHON) tests/test_semantic_rag.py

semantic-realization-gate: realization-gate semantic-rag-test
	@echo "semantic-realization-gate: GREEN"


tevaram-ingest-test:
	$(PYTHON) tests/test_tevaram_ingest.py

claim-verifier-test:
	$(PYTHON) tests/test_claim_verifier.py

long-session-gate: semantic-realization-gate tevaram-ingest-test claim-verifier-test
	@echo "long-session-gate: GREEN"

grounded-synthesis-test:
	$(PYTHON) tests/test_grounded_synthesis.py

devi-script-spotcheck:
	$(PYTHON) tests/test_devi_script_spotcheck.py

devi-certification-audit-fixture:
	$(PYTHON) tests/test_devi_full_audit.py

devi-full-gate: long-session-gate devi-script-spotcheck grounded-synthesis-test devi-certification-audit-fixture
	@echo "devi-full-gate: GREEN"

tevaram-ifp-verification-test:
	$(PYTHON) tests/test_tevaram_ifp_verification.py

tevaram-verification-gate: long-session-gate tevaram-ifp-verification-test source-contracts
	@echo "tevaram-verification-gate: GREEN"

cross-text-test:
	$(PYTHON) tests/test_cross_text_compare.py

comparison-schema-test:
	$(PYTHON) scripts/validate_comparison_schema.py

cross-text-gate: tevaram-verification-gate cross-text-test comparison-schema-test
	@echo "cross-text-gate: GREEN"

variant-relations-test:
	$(PYTHON) tests/test_variant_relations.py

evidence-graph-test:
	$(PYTHON) tests/test_evidence_graph.py

variant-graph-gate: cross-text-gate variant-relations-test evidence-graph-test
	@echo "variant-graph-gate: GREEN"

variant-graph-checkpoint-gate: cross-text-test comparison-schema-test variant-relations-test evidence-graph-test
	@echo "variant-graph-checkpoint-gate: GREEN"

real-graph-test:
	$(PYTHON) tests/test_real_graph.py

real-graph-gate: variant-graph-checkpoint-gate real-graph-test
	$(PYTHON) scripts/validate.py data/public/purana/devi_mahatmya_certified_seed.jsonl
	$(PYTHON) scripts/validate.py data/public/bhagavatam/prahlada_narasimha_certified_seed.jsonl
	$(PYTHON) scripts/validate.py data/public/purana/vishnu_purana_prahlada_certified_seed.jsonl
	$(PYTHON) scripts/validate.py data/public/purana/narasimha_purana_44_certified_seed.jsonl
	$(PYTHON) scripts/validate.py data/public/purana/vishnu_purana_genealogy_seed.jsonl
	$(PYTHON) scripts/validate.py data/public/purana/devi_mahatmya_ritual_seed.jsonl
	$(PYTHON) scripts/validate.py data/public/purana/vamana_purana_temple_ritual_seed.jsonl
	@echo "real-graph-gate: GREEN"

moat-proof-test:
	$(PYTHON) tests/test_moat_proof_suite.py

moat-benchmark:
	$(PYTHON) benchmark/run_native.py

moat-proof-gate: real-graph-gate moat-proof-test moat-benchmark
	@echo "moat-proof-gate: GREEN"

license-matrix:
	$(PYTHON) scripts/build_license_matrix.py

release-builder-test:
	$(PYTHON) tests/test_release_builder.py

release-research-nc:
	$(PYTHON) scripts/build_release.py --profile research-nc --outdir dist/research-nc
	$(PYTHON) scripts/check_release.py dist/research-nc

release-open:
	$(PYTHON) scripts/build_release.py --profile open --outdir dist/open
	$(PYTHON) scripts/check_release.py dist/open

release-readiness:
	$(PYTHON) scripts/release_readiness.py

publication-gate: license-matrix release-builder-test release-research-nc release-open release-readiness
	@echo "publication-gate: GREEN"

external-score-template:
	$(PYTHON) benchmark/build_external_template.py

moat-benchmark-v2: external-score-template
	$(PYTHON) benchmark/run_native.py
	@echo "moat-benchmark-v2: GREEN"

network-core-dry-run:
	$(PYTHON) scripts/fetch_sources.py sources/manifest.json --keys $$($(PYTHON) -c "import json; print(','.join(json.load(open('sources/PRIORITY_GROUPS.json'))['groups']['core-materialization']['keys']))") --dry-run

network-core:
	$(PYTHON) scripts/network_materialize.py --group core-materialization --fetch --materialize

network-mahabharata:
	$(PYTHON) scripts/network_materialize.py --group mahabharata-parent --fetch --materialize

sqlite-store:
	$(PYTHON) graph/sqlite_store.py build --db dist/pramana.sqlite

service-smoke:
	$(PYTHON) product/service.py health
	$(PYTHON) tests/test_sqlite_service.py

quality-dashboard:
	$(PYTHON) scripts/build_quality_dashboard.py

external-scorecard-validate:
	$(PYTHON) benchmark/validate_external_scorecard.py benchmark/external_score_template.json --allow-template-provider

local-platform-gate: real-graph-gate moat-benchmark-v2 sqlite-store service-smoke quality-dashboard external-scorecard-validate
	@echo "local-platform-gate: GREEN"

http-api-test:
	$(PYTHON) tests/test_http_api.py

local-platform-focused-gate: sqlite-store service-smoke http-api-test quality-dashboard external-scorecard-validate
	@echo "local-platform-focused-gate: GREEN"

review-queue:
	$(PYTHON) scripts/build_review_queue.py --output dist/review_queue.json

review-proof-test:
	$(PYTHON) tests/test_review_and_proof.py

proof-demo:
	$(PYTHON) scripts/export_proof_bundle.py --evidence-id bhagavatam.7.8.29 --context '{"operation":"demo"}' --output dist/proof-demo.json
	$(PYTHON) scripts/check_proof_bundle.py dist/proof-demo.json

curation-proof-gate: review-queue review-proof-test proof-demo
	@echo "curation-proof-gate: GREEN"

# Generic source-comparison triage. Machine output never grants verification.
review-work:
	@test -n "$(WORK)" || (echo "usage: make review-work WORK=<work>" && exit 2)
	$(PYTHON) scripts/review_work.py $(WORK)

review-work-test:
	$(PYTHON) tests/test_review_work.py
