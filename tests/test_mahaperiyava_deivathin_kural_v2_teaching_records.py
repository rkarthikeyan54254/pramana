from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"
SCHEMA = ROOT / "schema" / "teaching_record.schema.json"
CATALOG = REVIEW / "mahaperiyava_deivathin_kural_v2_catalog.json"
MANIFEST = REVIEW / "mahaperiyava_deivathin_kural_v2_curator_manifest.json"
INDEX = REVIEW / "mahaperiyava_deivathin_kural_v2_curation_index.json"
RECORDS = REVIEW / "mahaperiyava_deivathin_kural_v2_teaching_records.jsonl"
AUDIT = REVIEW / "mahaperiyava_deivathin_kural_v2_semantic_completion_audit.json"

RAMAN_1963_PROMOTED_ID = (
    "mahaperiyava.deivathin_kural.v2.c206."
    "knowledge_is_to_be_grounded_in_character_and_religious_discipline_"
    "before_broad_intellectual_exploration"
)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def test_v2_shape_authority_and_chapter_frontier():
    rows = _jsonl(RECORDS)
    assert len(rows) == 673
    assert len({r["id"] for r in rows}) == 673
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == set(range(1, 226))
    assert Counter(
        r["evidence_status"]["authority"]
        for r in rows
    ) == Counter({
        "dk_attested": 672,
        "earlier_witness_supported": 1,
    })
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)

def test_v2_records_match_teaching_record_schema_shape_and_rights():
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
        if row["id"] == RAMAN_1963_PROMOTED_ID:
            assert (
                row["attribution"]["wording_status"]
                == "earlier_witness_agrees"
            )
            earlier = [
                p for p in row["provenance"]
                if p["witness_role"] == "earlier_secondary"
            ]
            assert len(earlier) == 1
            assert (
                earlier[0]["source_key"]
                == "illustrated-weekly-as-raman-interview-1963-scan"
            )
        else:
            assert row["attribution"]["wording_status"] == "dk_wording_only"
        assert row["attribution"]["compiler_intervention_status"] == "unknown"
        assert row["claim_summary"]
        assert row["topics"] is not None
        assert isinstance(row["flags"], list)
        assert row["provenance"]
        assert re.fullmatch(r"[0-9a-f]{64}", row["provenance"][0]["snapshot_sha256"])

def test_v2_source_paragraph_accounting_is_complete_and_fail_closed():
    index = _json(INDEX)
    coverage = index["source_coverage"]
    assert coverage["paragraph_count"] == 3435
    assert coverage["covered_paragraph_count"] == 3371
    assert coverage["explicitly_excluded_source_paragraphs"] == 64
    assert coverage["overlap_instances"] == 7
    assert coverage["coverage_mode"] == "at_least_once_or_explicitly_excluded"
    assert coverage["all_source_paragraphs_accounted_for"] is True
    assert len(index["explicit_exclusions"]) == 64
    assert len(index["intentional_overlaps"]) == 7
    assert all(u["source_paragraph_ids"] for u in index["units"])
    assert all(len(u["source_paragraph_ids"]) == len(u["source_paragraph_hashes"]) for u in index["units"])
    assert all(re.fullmatch(r"[0-9a-f]{64}", h) for u in index["units"] for h in u["source_paragraph_hashes"])

def test_v2_manifest_matches_records_and_preserves_policy():
    manifest = _json(MANIFEST)
    rows = _jsonl(RECORDS)
    assert manifest["counts"]["chapters"] == 225
    assert manifest["counts"]["teaching_units"] == 673
    assert manifest["counts"]["source_paragraphs"] == 3435
    assert manifest["counts"]["covered_source_paragraphs"] == 3371
    assert manifest["counts"]["explicitly_excluded_source_paragraphs"] == 64
    assert manifest["counts"]["overlap_instances"] == 7
    assert {u["id"] for u in manifest["units"]} == {r["id"] for r in rows}
    assert manifest["policy"]["claim_summaries_are_curator_metadata_not_quotes"] is True
    assert manifest["policy"]["no_print_check_claimed"] is True
    assert manifest["policy"]["no_primary_source_verified_claimed"] is True
    assert manifest["policy"]["human_publication_review_still_required"] is True

def test_v2_catalog_is_repaired_225_chapter_catalog():
    catalog = _json(CATALOG)
    assert catalog["chapter_count"] == 225
    assert len(catalog["chapters"]) == 225
    assert [c["ordinal"] for c in catalog["chapters"]] == list(range(1, 226))

def test_v2_2dk67_archive_exception_is_explicit_and_limited():
    rows = [r for r in _jsonl(RECORDS) if r["source_locus"]["chapter_ordinal"] == 208]
    assert rows
    for row in rows:
        assert row["source_locus"]["digital_url"] == "https://www.kamakoti.org/tamil/2dk67.htm"
        assert row["provenance"][0]["url"].startswith(
            "https://web.archive.org/web/20231207125357id_/https://www.kamakoti.org/tamil/2dk67.htm"
        )
        assert row["evidence_status"]["authority"] == "dk_attested"
        assert row["evidence_status"]["print_check"] == "not_checked"
        assert row["evidence_status"]["primary_source_status"] == "unknown"

def test_v2_sensitive_historical_material_keeps_context_flags():
    rows = _jsonl(RECORDS)
    flags = {f for r in rows for f in r.get("flags", [])}
    required = {
        "self_harm_or_suicide_historical_material",
        "explicit_nonendorsement_required",
        "child_marriage_advocacy_historical_claim",
        "gender_discriminatory_norm_requires_context",
        "caste_varna_normative_claim",
        "medical_care_avoidance_claim",
    }
    assert required <= flags

def test_v2_completion_audit_passes():
    audit = _json(AUDIT)
    assert audit["result"] == "PASS"
    assert audit["checks"]["unaccounted_source_paragraph_count"] == 0
    assert audit["checks"]["source_text_embedded_in_records"] is False
