from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_curation_index.json"
QUEUE = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"

EXPECTED = {1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,22}


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path):
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def test_batch_shape_and_claim_level_authority():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)

    assert len(rows) == 102
    assert index["unit_count"] == 102
    assert len({r["id"] for r in rows}) == 102
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == EXPECTED

    assert Counter(
        r["evidence_status"]["authority"] for r in rows
    ) == {
        "dk_attested": 88,
        "earlier_witness_supported": 14,
    }

    assert all(
        r["evidence_status"]["print_check"] == "not_checked"
        for r in rows
    )
    assert all(
        r["evidence_status"]["primary_source_status"] == "unknown"
        for r in rows
    )


def test_earlier_supported_rows_have_independent_witness_edge():
    rows = _jsonl(RECORDS)
    supported = [
        r for r in rows
        if r["evidence_status"]["authority"] == "earlier_witness_supported"
    ]
    assert len(supported) == 14

    for row in supported:
        roles = [p["witness_role"] for p in row["provenance"]]
        assert roles == ["official_digital", "earlier_secondary"]
        assert row["attribution"]["wording_status"] == "earlier_witness_agrees"
        lineage_note = row["provenance"][1]["lineage_note"].casefold()
        assert "verbatim" in lineage_note
        assert row["evidence_status"]["primary_source_status"] == "unknown"


def test_dk_only_rows_remain_fail_closed():
    rows = _jsonl(RECORDS)
    dk_only = [
        r for r in rows
        if r["evidence_status"]["authority"] == "dk_attested"
    ]
    assert len(dk_only) == 88
    assert all(
        r["attribution"]["wording_status"] == "dk_wording_only"
        for r in dk_only
    )
    assert all(
        [p["witness_role"] for p in r["provenance"]] == ["official_digital"]
        for r in dk_only
    )


def test_no_restricted_source_text_is_tracked():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)

    assert index["source_packet"]["tracked"] is False
    assert index["policy"]["no_exact_source_text_in_tracked_artifacts"] is True

    for row in rows:
        assert "text" not in row
        assert "exact_text_restricted" not in row
        assert row["rights"]["source_text_tier"] == "restricted"
        assert row["rights"]["public_export"] == "metadata_only"


def test_private_hash_mapping_and_question_intents_exist():
    index = _json(INDEX)
    assert len(index["units"]) == 102

    for unit in index["units"]:
        assert unit["question_intents"]
        assert len(unit["source_paragraph_ids"]) == len(
            unit["source_paragraph_hashes"]
        )
        assert all(
            re.fullmatch(r"[0-9a-f]{64}", h)
            for h in unit["source_paragraph_hashes"]
        )


def test_queue_stays_semantically_curated():
    queue = _jsonl(QUEUE)
    selected = [q for q in queue if q["ordinal"] in EXPECTED]

    assert len(selected) == 20
    assert all(not q["pilot"] for q in selected)
    assert all(
        q["stage"] == "batch_teaching_units_curated"
        for q in selected
    )
    assert all(q["teaching_units_created"] > 0 for q in selected)


def test_sensitive_claims_can_gain_attestation_without_losing_flags():
    rows = _jsonl(RECORDS)
    thoppu = next(
        r for r in rows
        if r["id"].endswith(".thoppukaranam_story_and_etymology")
    )

    assert thoppu["evidence_status"]["authority"] == "earlier_witness_supported"
    assert "etymology_claim_requires_external_verification" in thoppu["flags"]
    assert "hagiographic_tradition" in thoppu["flags"]


def test_index_records_targeted_not_exhaustive_review():
    index = _json(INDEX)
    policy = index["policy"]

    assert policy["targeted_historical_witness_pass_completed"] is True
    assert policy["historical_witness_exhaustive_review_completed"] is False
    assert policy["historical_witness_support_is_claim_level"] is True
    assert policy["no_verbatim_wording_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True
