from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_historical_witness_review.json"
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_teaching_records.jsonl"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path):
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def test_witness_review_has_one_row_per_teaching_unit():
    review = _json(REVIEW)
    rows = _jsonl(RECORDS)

    assert review["matrix_count"] == 102
    assert len(review["rows"]) == 102
    assert {r["id"] for r in review["rows"]} == {r["id"] for r in rows}


def test_review_is_explicitly_targeted_not_exhaustive():
    review = _json(REVIEW)

    assert review["review_type"] == "targeted_historical_witness_matching"
    assert review["review_scope"]["exhaustive_across_all_102_units"] is False
    assert review["policy"]["no_chapter_wide_promotion"] is True
    assert review["policy"]["no_verbatim_claim"] is True
    assert review["policy"]["no_primary_source_upgrade"] is True


def test_exactly_13_supported_and_4_partial():
    review = _json(REVIEW)
    counts = Counter(r["review_status"] for r in review["rows"])

    assert counts["supported_for_claim_level_promotion"] == 13
    assert counts["partial_match_not_sufficient"] == 4
    assert counts["not_evaluated_in_targeted_sections"] == 85
    assert review["promotion_count"] == 13


def test_supported_rows_have_locus_and_guardrails():
    review = _json(REVIEW)
    supported = [
        r for r in review["rows"]
        if r["review_status"] == "supported_for_claim_level_promotion"
    ]

    for row in supported:
        witness = row["historical_witness"]
        assert witness["source_key"].startswith("acharya-upanyasangal-")
        assert "printed p" in witness["locus"]
        assert witness["match_level"] in {
            "same_doctrinal_claim",
            "same_traditional_explanation",
            "close_paraphrase",
        }
        assert row["guardrails"]["verbatim_wording_claimed"] is False
        assert row["guardrails"]["primary_source_verified_claimed"] is False
        assert row["guardrails"]["textual_dependency_claimed"] is False


def test_partial_matches_do_not_promote():
    review = _json(REVIEW)
    partial = [
        r for r in review["rows"]
        if r["review_status"] == "partial_match_not_sufficient"
    ]

    assert partial
    assert all(r["authority_after"] == "dk_attested" for r in partial)
