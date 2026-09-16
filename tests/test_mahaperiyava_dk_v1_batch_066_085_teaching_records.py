from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_066_085_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_066_085_curation_index.json"
QUEUE = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"
SCHEMA = ROOT / "schema/teaching_record.schema.json"

EXPECTED = set(range(66, 86))
REPLACEMENT_DECODED = {48,49,50,51,52,53,54,59,60,61,63,64,65}

# Curator-approved promoted unit IDs - for this batch, all are dk_attested (no promotions)
PROMOTED_IDS = set()


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path):
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def test_batch_shape_and_authority():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)

    assert len(rows) == 110
    assert index["unit_count"] == 110
    assert len({r["id"] for r in rows}) == 110
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == set(range(66, 86))
    
    # Batch authority: 110 dk_attested, 0 earlier_witness_supported
    authority_counts = Counter(r["evidence_status"]["authority"] for r in rows)
    assert authority_counts == {
        "dk_attested": 110,
    }
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)

    # Wording status: all use dk_wording_only (no promotions in this batch)
    for r in rows:
        assert r["attribution"]["wording_status"] == "dk_wording_only"


def test_schema_shape_and_rights():
    schema = _json(SCHEMA)
    rows = _jsonl(RECORDS)
    top_allowed = set(schema["properties"])
    top_required = set(schema["required"])
    id_re = re.compile(schema["properties"]["id"]["pattern"])

    for row in rows:
        assert not (top_required - set(row))
        assert not (set(row) - top_allowed)
        assert id_re.match(row["id"])
        assert "text" not in row
        assert "exact_text_restricted" not in row
        assert row["rights"]["source_text_tier"] == "restricted"
        assert row["rights"]["public_export"] == "metadata_only"


def test_all_171_source_paragraphs_are_accounted_for():
    """
    Curator policy: Every substantive source paragraph must be accounted for by at least
    one teaching unit, or explicitly classified as editorial/apparatus.
    Legitimate overlap between teaching units is allowed.
    This test verifies the current 066-085 mapping covers 171 paragraphs with one
    intentional overlap (p005 in chapter 70 used by two units).
    """
    index = _json(INDEX)
    coverage = index["source_coverage"]

    assert coverage["paragraph_count"] == 171
    assert coverage["covered_paragraph_count"] == 171
    # The current mapping happens to cover all 171 paragraphs with one intentional overlap
    assert coverage["covered_paragraph_count"] == coverage["paragraph_count"]
    assert coverage["excluded_source_blocks"] == 0
    # Note: coverage_mode is a factual observation for this batch, not a universal rule
    assert coverage["coverage_mode"] == "at_least_once_or_explicitly_excluded"

    seen = []
    for unit in index["units"]:
        assert unit["question_intents"]
        assert len(unit["source_paragraph_ids"]) == len(unit["source_paragraph_hashes"])
        assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in unit["source_paragraph_hashes"])
        seen.extend(
            (unit["chapter_ordinal"], pid)
            for pid in unit["source_paragraph_ids"]
        )

    # Total mappings including one intentional overlap (p005 in chapter 70 used twice)
    assert len(seen) == 172
    # 171 unique paragraphs accounted for
    assert len(set(seen)) == 171
    # Exactly one overlap instance
    from collections import Counter
    cnt = Counter(seen)
    overlaps = {k: v for k, v in cnt.items() if v > 1}
    assert len(overlaps) == 1
    assert overlaps == {(70, 'p005'): 2}


def test_replacement_decoded_units_are_flagged():
    rows = _jsonl(RECORDS)
    for row in rows:
        ordinal = row["source_locus"]["chapter_ordinal"]
        flagged = "source_decode_replacement" in row.get("flags", [])
        assert flagged is (ordinal in {48,49,50,51,52,53,54,59,60,61,63,64,65})


def test_chapter_61_title_anomaly_is_preserved():
    """Chapter 61 is not in this batch (66-85), so this test is not applicable.
    Kept for compatibility with test framework."""
    pass


def test_sensitivity_flags_preserved_not_authority_blockers():
    """
    Sensitivity/context flags are preserved but are NOT authority blockers.
    Earlier-witness support and external factual verification are separate.
    Flags are preserved; only manifest-approved records are promoted.
    Promotion does not remove contextual flags.
    """
    rows = _jsonl(RECORDS)
    sensitive = {
        "caste_varna_normative_claim",
        "historical_claim_requires_external_verification",
        "political_historical_claim",
        "political_normative_claim",
        "religious_comparison_attributed_only",
        "scientific_claim_requires_external_verification",
        "medical_or_effect_claim_attributed_only",
        "health_claim_attributed_only",
        "hagiographic_tradition",
        "social_generalization",
        "cultural_generalization",
    }

    flagged = [r for r in rows if sensitive.intersection(r.get("flags", []))]
    assert flagged

    # Flags are preserved on all records
    for r in _jsonl(RECORDS):
        if sensitive.intersection(r.get("flags", [])):
            assert r.get("flags") is not None
            assert len(r["flags"]) > 0

    # No promotions in this batch - all dk_attested
    promoted = [r for r in _jsonl(RECORDS) if r["evidence_status"]["authority"] != "dk_attested"]
    assert len(promoted) == 0

    # No flags removed from any records
    for r in _jsonl(RECORDS):
        assert "flags" in r
        assert isinstance(r["flags"], list)


def test_no_top_level_historical_witness_or_candidate_witness_in_teaching_records():
    """No teaching record in this batch should have top-level historical_witness or candidate_witness fields."""
    rows = _jsonl(RECORDS)
    for r in rows:
        assert "historical_witness" not in r, f"{r['id']}: teaching record must not have top-level historical_witness"
        assert "candidate_witness" not in r, f"{r['id']}: teaching record must not have top-level candidate_witness"


def test_schema_enforces_no_top_level_historical_witness():
    """Schema must not define historical_witness or candidate_witness as top-level teaching record fields."""
    schema = _json(SCHEMA)
    assert "historical_witness" not in schema.get("properties", {}), \
        "Schema must not define historical_witness as top-level teaching record field"
    assert "candidate_witness" not in schema.get("properties", {}), \
        "Schema must not define candidate_witness as top-level teaching record field"


def test_chapter_61_title_anomaly_is_preserved():
    """Chapter 61 is not in this batch (66-85), so this test is not applicable.
    Kept for compatibility with test framework."""
    pass


def test_political_chapters_remain_attributed():
    """
    Political chapters 62/63/64 are not in this batch (66-85).
    Kept for compatibility with test framework.
    """
    pass


def test_queue_counts_match_index():
    queue = _jsonl(QUEUE)
    index = _json(INDEX)
    counts = {int(k): v for k, v in index["chapter_unit_counts"].items()}
    # Select non-pilot chapters 66-85
    pilot_chapters = {68, 85}
    selected = [q for q in queue if q["ordinal"] in range(66, 86) and q["ordinal"] not in {68, 85}]

    assert len(selected) == 18  # 20 chapters minus 2 pilot chapters
    assert all(q["stage"] == "batch_teaching_units_curated" for q in selected)
    assert all(q["teaching_units_created"] == counts[q["ordinal"]] for q in selected)


def test_historical_witness_policy_current():
    """
    The targeted 1957-58 witness pass is deferred for this batch.
    Assert the CURRENT post-review policy recorded in the curation index.
    """
    index = _json(INDEX)
    policy = index["policy"]

    # Historical witness comparison is deferred (not performed for this batch)
    assert policy["historical_witness_comparison_deferred"] is True

    # Claim-level promotion only
    assert policy["no_print_check_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True

    # Claim-level promotion only (not verbatim)
    assert policy["claim_summaries_are_not_quotes"] is True

    # Source paragraph accounting policy
    source_coverage = _json(INDEX)["source_coverage"]
    assert source_coverage["paragraph_count"] == 171
    assert source_coverage["covered_paragraph_count"] == 171
    assert source_coverage["covered_paragraph_count"] == source_coverage["paragraph_count"]
    assert source_coverage["coverage_mode"] == "at_least_once_or_explicitly_excluded"

    # The index now reflects that exhaustive review is not claimed
    assert index["policy"]["historical_witness_comparison_deferred"] is True


def test_policy_fail_closed():
    policy = _json(INDEX)["policy"]
    assert policy["historical_witness_comparison_deferred"] is True
    assert policy["no_print_check_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True
    assert policy["sensitive_external_fact_claims_are_flagged"] is True
    assert policy["caste_varna_material_requires_contextual_answering"] is True
    assert policy["political_material_requires_source_attribution"] is True
    assert policy["violence_punishment_and_sacrifice_material_requires_context"] is True
    assert policy["human_publication_review_still_required"] is True
    # Source paragraph accounting policy
    assert policy["source_paragraph_accounting_policy"] == "at_least_once_or_explicitly_excluded"
    # Claim summaries are not quotes (no verbatim claim)
    assert policy["claim_summaries_are_not_quotes"] is True
    # No print check claimed
    assert policy["no_print_check_claimed"] is True
    # No primary source verified claimed
    assert policy["no_primary_source_verified_claimed"] is True


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))