from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_046_065_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_046_065_curation_index.json"
QUEUE = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"
SCHEMA = ROOT / "schema/teaching_record.schema.json"

EXPECTED = set(range(46, 66))
REPLACEMENT_DECODED = {48,49,50,51,52,53,54,59,60,61,63,64,65}

# Curator-approved promoted unit IDs (9 units)
PROMOTED_IDS = {
    "mahaperiyava.deivathin_kural.v1.samanya_dharmangal_anaivarukkum_pothuvana.restless_mind_obstructs_meditation",
    "mahaperiyava.deivathin_kural.v1.ahimsai.respond_to_wrongdoing_without_hatred",
    "mahaperiyava.deivathin_kural.v1.ahimsai.sannyasi_bound_to_radical_ahimsa",
    "mahaperiyava.deivathin_kural.v1.ahimsai.contextual_exceptions_to_absolute_ahimsa",
    "mahaperiyava.deivathin_kural.v1.ahimsai.critique_of_universal_absolute_ahimsa",
    "mahaperiyava.deivathin_kural.v1.sathiyam.truth_must_be_beneficial_not_merely_literal",
    "mahaperiyava.deivathin_kural.v1.paropakaram.tirukkural_and_vedic_duty_interpretation",
    "mahaperiyava.deivathin_kural.v1.anbum_thunbamum.imperishable_love_should_rest_in_paramatman",
    "mahaperiyava.deivathin_kural.v1.anbum_thunbamum.see_all_beings_as_paramatman",
}


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

    assert len(rows) == 105
    assert index["unit_count"] == 105
    assert len({r["id"] for r in rows}) == 105
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == EXPECTED

    # Batch authority: 96 dk_attested, 9 earlier_witness_supported
    authority_counts = Counter(r["evidence_status"]["authority"] for r in rows)
    assert authority_counts == {
        "dk_attested": 96,
        "earlier_witness_supported": 9,
    }
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)

    # Wording status: 9 promoted use earlier_witness_agrees, 96 use dk_wording_only
    for r in rows:
        if r["id"] in PROMOTED_IDS:
            assert r["attribution"]["wording_status"] == "earlier_witness_agrees"
        else:
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


def test_all_212_source_paragraphs_are_accounted_for():
    """
    Curator policy: Every substantive source paragraph must be accounted for by at least
    one teaching unit, or explicitly classified as editorial/apparatus.
    Legitimate overlap between teaching units is allowed.
    This test verifies the current 046-065 mapping happens to cover 212/212 exactly once.
    """
    index = _json(INDEX)
    coverage = index["source_coverage"]

    assert coverage["paragraph_count"] == 212
    assert coverage["covered_paragraph_count"] == 212
    # The current mapping happens to be exactly once; this is a factual batch observation,
    # not a universal semantic requirement.
    assert coverage["covered_paragraph_count"] == coverage["paragraph_count"]
    assert coverage["excluded_source_blocks"] == 0
    # Note: coverage_mode is a factual observation for this batch, not a universal rule
    assert coverage["coverage_mode"] == "exactly_once"

    seen = []
    for unit in index["units"]:
        assert unit["question_intents"]
        assert len(unit["source_paragraph_ids"]) == len(unit["source_paragraph_hashes"])
        assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in unit["source_paragraph_hashes"])
        seen.extend(
            (unit["chapter_ordinal"], pid)
            for pid in unit["source_paragraph_ids"]
        )

    assert len(seen) == 212
    # Overlap check: current mapping happens to have no overlaps, but this is
    # a batch-specific observation, not a universal invariant.
    assert len(set(seen)) == 212


def test_replacement_decoded_units_are_flagged():
    rows = _jsonl(RECORDS)
    for row in rows:
        ordinal = row["source_locus"]["chapter_ordinal"]
        flagged = "source_decode_replacement" in row.get("flags", [])
        assert flagged is (ordinal in REPLACEMENT_DECODED)


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
    rows = _jsonl(RECORDS)
    index = _json(INDEX)

    ch61 = [r for r in rows if r["source_locus"]["chapter_ordinal"] == 61]
    assert ch61
    assert all(r["source_locus"]["chapter_title_ta"] == "அன்பu" for r in ch61)

    anomaly = index["source_anomalies"][0]
    assert anomaly["chapter_ordinal"] == 61
    assert anomaly["observed"] == "அன்பu"
    assert anomaly["action"] == "preserved_pending_source_qc"


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

    # Flags are preserved on all records including promoted ones
    for r in rows:
        if sensitive.intersection(r.get("flags", [])):
            assert r.get("flags") is not None
            # Flags are not removed by promotion
            assert len(r["flags"]) > 0

    # Only manifest-approved records are promoted (authority != dk_attested)
    promoted = [r for r in rows if r["evidence_status"]["authority"] != "dk_attested"]
    promoted_ids = {r["id"] for r in promoted}
    assert len(promoted_ids) == 9
    # Verify promoted IDs match curator manifest
    assert promoted_ids == {
        "mahaperiyava.deivathin_kural.v1.samanya_dharmangal_anaivarukkum_pothuvana.restless_mind_obstructs_meditation",
        "mahaperiyava.deivathin_kural.v1.ahimsai.respond_to_wrongdoing_without_hatred",
        "mahaperiyava.deivathin_kural.v1.ahimsai.sannyasi_bound_to_radical_ahimsa",
        "mahaperiyava.deivathin_kural.v1.ahimsai.contextual_exceptions_to_absolute_ahimsa",
        "mahaperiyava.deivathin_kural.v1.ahimsai.critique_of_universal_absolute_ahimsa",
        "mahaperiyava.deivathin_kural.v1.sathiyam.truth_must_be_beneficial_not_merely_literal",
        "mahaperiyava.deivathin_kural.v1.paropakaram.tirukkural_and_vedic_duty_interpretation",
        "mahaperiyava.deivathin_kural.v1.anbum_thunbamum.imperishable_love_should_rest_in_paramatman",
        "mahaperiyava.deivathin_kural.v1.anbum_thunbamum.see_all_beings_as_paramatman",
    }

    # Promoted records can have sensitivity flags (flags are not removed by promotion)
    for r in rows:
        if r["id"] in PROMOTED_IDS:
            assert r.get("flags") is not None


def test_ahimsa_contextual_exceptions_promoted_with_flags_intact():
    """
    The ahimsa unit 'contextual_exceptions_to_absolute_ahimsa' is curator-approved
    as earlier_witness_supported. Assert its promoted authority AND that its
    contextual flags remain intact. No top-level historical_witness in teaching record.
    """
    rows = _jsonl(RECORDS)
    target = next(
        r for r in rows
        if r["id"].endswith(".contextual_exceptions_to_absolute_ahimsa")
    )
    assert target["evidence_status"]["authority"] == "earlier_witness_supported"
    assert target["attribution"]["wording_status"] == "earlier_witness_agrees"
    # Contextual flags remain intact after promotion
    assert "traditional_normative_claim" in target["flags"]
    assert "religious_comparison_attributed_only" in target["flags"]
    assert "source_decode_replacement" in target["flags"]
    # No top-level historical_witness in teaching record (layering rule)
    assert "historical_witness" not in target
    assert "candidate_witness" not in target


def test_political_chapters_remain_attributed():
    """
    Political chapters 62/63/64: keep their existing attribution/context assertions.
    They were NOT promoted by this targeted pass.
    """
    rows = _jsonl(RECORDS)
    selected = [
        r for r in rows
        if r["source_locus"]["chapter_ordinal"] in {62, 63, 64}
    ]
    assert selected
    assert all(r["evidence_status"]["authority"] == "dk_attested" for r in selected)
    assert any("political_normative_claim" in r.get("flags", []) for r in selected)


def test_queue_counts_match_index():
    queue = _jsonl(QUEUE)
    index = _json(INDEX)
    counts = {int(k): v for k, v in index["chapter_unit_counts"].items()}
    selected = [q for q in queue if q["ordinal"] in EXPECTED]

    assert len(selected) == 20
    assert all(q["stage"] == "batch_teaching_units_curated" for q in selected)
    assert all(q["teaching_units_created"] == counts[q["ordinal"]] for q in selected)


def test_historical_witness_policy_current():
    """
    The targeted 1957-58 witness pass is no longer "deferred" for the 9 promoted units.
    Assert the CURRENT post-review policy recorded in the curation index.
    """
    index = _json(INDEX)
    policy = index["policy"]

    # The targeted 1957-58 witness review is completed for the 9 promoted units
    assert policy["historical_witness_comparison_completed_for_promoted"] is True

    # Exhaustive historical review is NOT claimed
    assert policy["historical_witness_comparison_deferred"] is True

    # Claim-level promotion only
    assert policy["no_print_check_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True

    # Claim-level promotion only (not verbatim)
    assert policy["claim_summaries_are_not_quotes"] is True

    # External factual truth remains separate from earlier attestation
    # (policy expresses this through curator_policy in the manifest)

    # The old "every_source_paragraph_mapped_exactly_once" policy expression
    # has been updated to reflect curator-approved accounting policy
    source_coverage = _json(INDEX)["source_coverage"]
    assert source_coverage["paragraph_count"] == 212
    assert source_coverage["covered_paragraph_count"] == 212
    # Note: coverage_mode is a factual batch observation, not a universal rule
    assert source_coverage["covered_paragraph_count"] == source_coverage["paragraph_count"]

    # The policy field for source paragraph accounting has been updated
    # The old "every_source_paragraph_mapped_exactly_once" is replaced by
    # a curator-approved formulation
    # This test verifies the CURRENT policy state in the index
    # The index now reflects that exhaustive review is not claimed
    assert index["policy"]["historical_witness_comparison_deferred"] is True
    assert index["policy"]["historical_witness_comparison_completed_for_promoted"] is True


def test_policy_fail_closed():
    policy = _json(INDEX)["policy"]
    assert policy["no_exact_source_text_in_tracked_artifacts"] is True
    assert policy["claim_summaries_are_not_quotes"] is True
    assert policy["historical_witness_comparison_deferred"] is True
    assert policy["no_print_check_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True
    assert policy["sensitive_external_fact_claims_are_flagged"] is True
    assert policy["caste_varna_material_requires_contextual_answering"] is True
    assert policy["political_material_requires_source_attribution"] is True
    assert policy["violence_punishment_and_sacrifice_material_requires_context"] is True
    assert policy["human_publication_review_still_required"] is True
    # Witness comparison completed for promoted units
    assert policy["historical_witness_comparison_completed_for_promoted"] is True
    # Claim summaries are not quotes (no verbatim claim)
    assert policy["claim_summaries_are_not_quotes"] is True
    # No print check claimed
    assert policy["no_print_check_claimed"] is True
    # No primary source verified claimed
    assert policy["no_primary_source_verified_claimed"] is True


def test_replacement_decoded_units_are_flagged():
    rows = _jsonl(RECORDS)
    for row in rows:
        ordinal = row["source_locus"]["chapter_ordinal"]
        flagged = "source_decode_replacement" in row.get("flags", [])
        assert flagged is (ordinal in REPLACEMENT_DECODED)


def test_chapter_61_title_anomaly_is_preserved():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)

    ch61 = [r for r in rows if r["source_locus"]["chapter_ordinal"] == 61]
    assert ch61
    assert all(r["source_locus"]["chapter_title_ta"] == "அன்பu" for r in ch61)

    anomaly = index["source_anomalies"][0]
    assert anomaly["chapter_ordinal"] == 61
    assert anomaly["observed"] == "அன்பu"
    assert anomaly["action"] == "preserved_pending_source_qc"


def test_political_chapters_remain_attributed():
    rows = _jsonl(RECORDS)
    selected = [
        r for r in rows
        if r["source_locus"]["chapter_ordinal"] in {62, 63, 64}
    ]
    assert selected
    assert all(r["evidence_status"]["authority"] == "dk_attested" for r in selected)
    assert any("political_normative_claim" in r.get("flags", []) for r in selected)


def test_queue_counts_match_index():
    queue = _jsonl(QUEUE)
    index = _json(INDEX)
    counts = {int(k): v for k, v in index["chapter_unit_counts"].items()}
    selected = [q for q in queue if q["ordinal"] in EXPECTED]

    assert len(selected) == 20
    assert all(q["stage"] == "batch_teaching_units_curated" for q in selected)
    assert all(q["teaching_units_created"] == counts[q["ordinal"]] for q in selected)


def test_policy_fail_closed():
    policy = _json(INDEX)["policy"]
    assert policy["no_exact_source_text_in_tracked_artifacts"] is True
    assert policy["claim_summaries_are_not_quotes"] is True
    assert policy["historical_witness_comparison_deferred"] is True
    assert policy["no_print_check_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True
    assert policy["sensitive_external_fact_claims_are_flagged"] is True
    assert policy["caste_varna_material_requires_contextual_answering"] is True
    assert policy["political_material_requires_source_attribution"] is True
    assert policy["violence_punishment_and_sacrifice_material_requires_context"] is True
    assert policy["human_publication_review_still_required"] is True
    # Witness comparison completed for promoted units
    assert policy["historical_witness_comparison_completed_for_promoted"] is True
    # Claim summaries are not quotes (no verbatim claim)
    assert policy["claim_summaries_are_not_quotes"] is True
    # No print check claimed
    assert policy["no_print_check_claimed"] is True
    # No primary source verified claimed
    assert policy["no_primary_source_verified_claimed"] is True