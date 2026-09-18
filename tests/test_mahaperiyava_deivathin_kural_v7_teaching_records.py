from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"
SCHEMA = ROOT / "schema" / "teaching_record.schema.json"

CATALOG = REVIEW / "mahaperiyava_deivathin_kural_v7_catalog.json"
MANIFEST = REVIEW / "mahaperiyava_deivathin_kural_v7_curator_manifest.json"
INDEX = REVIEW / "mahaperiyava_deivathin_kural_v7_curation_index.json"
RECORDS = REVIEW / "mahaperiyava_deivathin_kural_v7_teaching_records.jsonl"
AUDIT = REVIEW / "mahaperiyava_deivathin_kural_v7_semantic_completion_audit.json"

BAD_GENERIC = (
    "This teaching centers on",
    "develops a distinct step",
)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_v7_shape_authority_and_chapter_frontier():
    rows = _jsonl(RECORDS)
    assert len(rows) == 342
    assert len({r["id"] for r in rows}) == 342
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == set(range(1, 343))
    assert Counter(r["evidence_status"]["authority"] for r in rows) == Counter({"dk_attested": 342})
    assert all(r["evidence_status"]["digital_attestation"] == "confirmed" for r in rows)
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)


def test_v7_records_match_schema_shape_and_rights():
    schema = _json(SCHEMA)
    rows = _jsonl(RECORDS)
    allowed = set(schema["properties"])
    required = set(schema["required"])
    id_re = re.compile(schema["properties"]["id"]["pattern"])
    for row in rows:
        assert not (required - set(row)), row["id"]
        assert not (set(row) - allowed), row["id"]
        assert id_re.fullmatch(row["id"]), row["id"]
        assert "exact_text_restricted" not in row
        assert "text" not in row
        assert row["rights"]["source_text_tier"] == "restricted"
        assert row["rights"]["public_export"] == "metadata_only"
        assert row["attribution"]["dk_attestation"] == "located"
        assert row["attribution"]["wording_status"] == "dk_wording_only"
        assert row["claim_summary"] and len(row["claim_summary"].split()) >= 8
        assert not any(x.lower() in row["claim_summary"].lower() for x in BAD_GENERIC)
        assert isinstance(row["topics"], list) and row["topics"]
        assert isinstance(row["flags"], list)
        assert row["provenance"]
        assert row["provenance"][0]["witness_role"] == "official_digital"
        assert re.fullmatch(r"[0-9a-f]{64}", row["provenance"][0]["snapshot_sha256"])


def test_v7_source_accounting_is_complete_and_fail_closed():
    index = _json(INDEX)
    cov = index["source_coverage"]
    assert cov["full_extracted_paragraph_count"] == 3999
    assert cov["curation_paragraph_count"] == 3999
    assert cov["covered_curation_paragraph_count"] == 3995
    assert cov["explicitly_excluded_curation_paragraphs"] == 4
    assert cov["unaccounted_curation_paragraphs"] == 0
    assert cov["intentional_overlap_paragraphs"] == 0
    assert cov["coverage_mode"] == "at_least_once_or_explicitly_excluded"
    assert cov["all_curation_paragraphs_accounted_for"] is True
    assert cov["paragraph_model"] == "normalized_article_content_blocks_v1"
    units = index["units"]
    assert len(units) == 342
    assert all(u["source_paragraph_ids"] for u in units)
    assert all(len(u["source_paragraph_ids"]) == len(u["source_paragraph_hashes"]) for u in units)
    assert all(re.fullmatch(r"[0-9a-f]{64}", h) for u in units for h in u["source_paragraph_hashes"])
    assert all(u["historical_witness"] is None for u in units)
    exclusions = index["explicit_exclusions"]
    assert len(exclusions) == 4
    assert {e["chapter_ordinal"] for e in exclusions} == {179, 187, 200, 339}
    assert all(e["rationale"].strip() for e in exclusions)


def test_v7_manifest_and_catalog_preserve_policy_and_source_model():
    manifest = _json(MANIFEST)
    catalog = _json(CATALOG)
    rows = _jsonl(RECORDS)
    assert manifest["counts"]["chapters"] == 342
    assert manifest["counts"]["teaching_units"] == 342
    assert manifest["counts"]["curation_source_paragraphs"] == 3999
    assert manifest["counts"]["covered_curation_paragraphs"] == 3995
    assert manifest["counts"]["explicit_editorial_exclusions"] == 4
    assert manifest["source_packet"]["source_bundle_sha256"] == "0a2cb5ead56f3e39f068efb87ec93ff7b9470911958cc671c8048682f261cb8c"
    assert manifest["source_packet"]["chapter_count"] == 342
    assert manifest["source_packet"]["live_official_page_count"] == 342
    assert {u["id"] for u in manifest["units"]} == {r["id"] for r in rows}
    assert all(u["historical_witness"] is None for u in manifest["units"])
    assert manifest["policy"]["human_publication_review_still_required"] is True
    assert manifest["policy"]["semantic_hardening_complete_but_not_publication_approved"] is True

    assert catalog["chapter_count"] == 342
    assert catalog["teaching_record_count"] == 342
    assert [c["ordinal"] for c in catalog["chapters"]] == list(range(1, 343))
    assert all(c["url"].startswith("https://www.kamakoti.org/tamil/7") for c in catalog["chapters"])
    assert all(c["source_availability"]["retrieval_mode"] == "live_official" for c in catalog["chapters"])
    assert catalog["semantic_status"] == "source_read_semantic_hardened_not_publication_approved"


def test_v7_sensitive_material_keeps_context_flags():
    rows = {r["source_locus"]["chapter_ordinal"]: r for r in _jsonl(RECORDS)}
    assert "political_social_claim_requires_context" in rows[124]["flags"]
    assert "religious_comparison_attributed_only" in rows[138]["flags"]
    assert "scientific_claim_requires_external_verification" in rows[187]["flags"]
    assert "self_harm_hagiographic_requires_context" in rows[224]["flags"]
    assert "violence_requires_context" in rows[235]["flags"]
    assert "gender_discriminatory_norm_requires_context" in rows[246]["flags"]
    assert "historical_claim_requires_external_verification" in rows[246]["flags"]
    assert "gender_discriminatory_norm_requires_context" in rows[312]["flags"]
    assert "scientific_claim_requires_external_verification" in rows[329]["flags"]


def test_v7_public_artifacts_do_not_embed_restricted_text_fields():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)
    manifest = _json(MANIFEST)
    for row in rows:
        assert "exact_text_restricted" not in row
        assert "text" not in row
    for unit in index["units"] + manifest["units"]:
        assert "text" not in unit
        assert "exact_text_restricted" not in unit


def test_v7_completion_audit_passes():
    audit = _json(AUDIT)
    checks = audit["checks"]
    assert audit["result"] == "PASS"
    assert checks["chapter_count"] == 342
    assert checks["teaching_record_count"] == 342
    assert checks["unaccounted_curation_paragraph_count"] == 0
    assert checks["all_historical_witness_null"] is True
    assert checks["generic_template_summary_count"] == 0
    assert checks["source_text_embedded_in_public_artifacts"] is False
    assert checks["publication_approved"] is False
    assert checks["explicit_exclusions_have_rationale"] is True
    assert checks["paragraph_hash_recomputation_failures"] == 0
    assert checks["record_provenance_snapshot_mismatches"] == 0
    assert checks["exact_restricted_paragraph_leak_count"] == 0
    assert checks["semantic_hardening_complete"] is True
