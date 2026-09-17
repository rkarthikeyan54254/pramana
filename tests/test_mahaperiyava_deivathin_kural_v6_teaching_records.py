from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"
SCHEMA = ROOT / "schema" / "teaching_record.schema.json"

CATALOG = REVIEW / "mahaperiyava_deivathin_kural_v6_catalog.json"
MANIFEST = REVIEW / "mahaperiyava_deivathin_kural_v6_curator_manifest.json"
INDEX = REVIEW / "mahaperiyava_deivathin_kural_v6_curation_index.json"
RECORDS = REVIEW / "mahaperiyava_deivathin_kural_v6_teaching_records.jsonl"
AUDIT = REVIEW / "mahaperiyava_deivathin_kural_v6_semantic_completion_audit.json"
UNUSED_LEGACY_NUMBERS = {201, 202, 203, 204, 205, 206, 207, 208, 209, 146, 147, 148, 149, 150, 210, 211, 212}

def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def test_v6_shape_authority_and_chapter_frontier():
    rows = _jsonl(RECORDS)
    assert len(rows) == 331
    assert len({r["id"] for r in rows}) == 331
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == set(range(1, 209))
    assert Counter(r["evidence_status"]["authority"] for r in rows) == Counter({"dk_attested": 331})
    assert all(r["evidence_status"]["digital_attestation"] == "confirmed" for r in rows)
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)

def test_v6_records_match_teaching_record_schema_shape_and_rights():
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
        assert row["attribution"]["compiler_intervention_status"] == "unknown"
        assert row["claim_summary"]
        assert isinstance(row["topics"], list) and row["topics"]
        assert isinstance(row["flags"], list)
        assert row["provenance"]
        assert row["provenance"][0]["witness_role"] == "official_digital"
        assert re.fullmatch(r"[0-9a-f]{64}", row["provenance"][0]["snapshot_sha256"])

def test_v6_source_paragraph_accounting_is_complete_and_fail_closed():
    index = _json(INDEX)
    cov = index["source_coverage"]
    assert cov["full_extracted_paragraph_count"] == 25827
    assert cov["mechanically_excluded_chrome_paragraph_count"] == 22667
    assert cov["curation_paragraph_count"] == 3160
    assert cov["covered_curation_paragraph_count"] == 3160
    assert cov["explicitly_excluded_curation_paragraphs"] == 0
    assert cov["unaccounted_curation_paragraphs"] == 0
    assert cov["intentional_overlap_paragraphs"] == 0
    assert cov["coverage_mode"] == "at_least_once_or_explicitly_excluded"
    assert cov["all_curation_paragraphs_accounted_for"] is True
    units = index["units"]
    assert len(units) == 331
    assert all(u["source_paragraph_ids"] for u in units)
    assert all(len(u["source_paragraph_ids"]) == len(u["source_paragraph_hashes"]) for u in units)
    assert all(re.fullmatch(r"[0-9a-f]{64}", h) for u in units for h in u["source_paragraph_hashes"])
    assert all("historical_witness" in u for u in units)
    assert all(u["historical_witness"] is None for u in units)
    assert index["explicit_exclusions"] == []

def test_v6_manifest_matches_records_and_preserves_policy():
    manifest = _json(MANIFEST)
    rows = _jsonl(RECORDS)
    assert manifest["counts"]["chapters"] == 208
    assert manifest["counts"]["teaching_units"] == 331
    assert manifest["counts"]["curation_source_paragraphs"] == 3160
    assert manifest["counts"]["covered_curation_paragraphs"] == 3160
    assert manifest["counts"]["explicit_editorial_exclusions"] == 0
    assert manifest["counts"]["mechanically_excluded_raw_paragraphs"] == 22667
    assert {u["id"] for u in manifest["units"]} == {r["id"] for r in rows}
    assert all(u["historical_witness"] is None for u in manifest["units"])
    assert manifest["policy"]["claim_summaries_are_curator_metadata_not_quotes"] is True
    assert manifest["policy"]["historical_witness_comparison_deferred"] is True
    assert manifest["policy"]["no_print_check_claimed"] is True
    assert manifest["policy"]["no_primary_source_verified_claimed"] is True
    assert manifest["policy"]["human_publication_review_still_required"] is True
    assert manifest["source_packet"]["snapshot_count_after_volume_6"] == 1725
    assert manifest["source_packet"]["live_official_page_count"] == 208
    assert manifest["source_packet"]["archive_recovery_count"] == 0

def test_v6_catalog_preserves_exact_208_article_legacy_model():
    catalog = _json(CATALOG)
    assert catalog["chapter_count"] == 208
    assert len(catalog["chapters"]) == 208
    assert [c["ordinal"] for c in catalog["chapters"]] == list(range(1, 209))
    legacy = [c["legacy_file_number"] for c in catalog["chapters"]]
    expected = [n for n in range(1, 226) if n not in UNUSED_LEGACY_NUMBERS]
    assert legacy == expected
    assert all(c["legacy_filename"] == f"dk6-{c['legacy_file_number']}.htm" for c in catalog["chapters"])
    assert all(c["url"] == f"https://www.kamakoti.org/tamil/{c['legacy_filename']}" for c in catalog["chapters"])
    assert all(c["source_availability"]["retrieval_mode"] == "live_official" for c in catalog["chapters"])
    assert catalog["semantic_status"] == "chatgpt_semantic_complete_not_publication_approved"
    assert catalog["teaching_record_count"] == 331

def test_v6_sensitive_historical_material_keeps_context_flags():
    rows = _jsonl(RECORDS)
    flags = {f for r in rows for f in r.get("flags", [])}
    required = {
        "caste_varna_normative_claim",
        "gender_discriminatory_norm_requires_context",
        "hagiographic_tradition",
        "historical_claim_requires_external_verification",
        "historical_linguistic_claim_requires_external_verification",
        "political_social_claim_requires_context",
        "religious_comparison_attributed_only",
        "religious_normative_claim",
        "ritual_effect_claim_attributed_only",
        "scientific_claim_requires_external_verification",
        "violence_requires_context",
    }
    assert required <= flags

def test_v6_public_artifacts_do_not_embed_restricted_source_text_fields():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)
    manifest = _json(MANIFEST)
    for row in rows:
        assert "exact_text_restricted" not in row
        assert "text" not in row
    for unit in index["units"]:
        assert "text" not in unit
        assert "exact_text_restricted" not in unit
    for unit in manifest["units"]:
        assert "text" not in unit
        assert "exact_text_restricted" not in unit

def test_v6_completion_audit_passes():
    audit = _json(AUDIT)
    assert audit["result"] == "PASS"
    assert audit["checks"]["chapter_count"] == 208
    assert audit["checks"]["teaching_record_count"] == 331
    assert audit["checks"]["unaccounted_curation_paragraph_count"] == 0
    assert audit["checks"]["all_historical_witness_null"] is True
    assert audit["checks"]["source_text_embedded_in_public_artifacts"] is False
    assert audit["checks"]["snapshot_count_after_volume_6"] == 1725
