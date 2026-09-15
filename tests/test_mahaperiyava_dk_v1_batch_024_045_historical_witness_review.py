from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_historical_witness_review.json"
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_teaching_records.jsonl"
def _json(path): return json.loads(path.read_text(encoding="utf-8"))
def _jsonl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def test_review_has_one_row_per_teaching_unit():
    review = _json(REVIEW); rows = _jsonl(RECORDS)
    assert review["matrix_count"] == 130 and len(review["rows"]) == 130
    assert {r["id"] for r in review["rows"]} == {r["id"] for r in rows}
def test_review_is_targeted_not_exhaustive():
    review = _json(REVIEW)
    assert review["review_type"] == "targeted_historical_witness_matching"
    assert review["review_scope"]["exhaustive_across_all_130_units"] is False
    assert review["policy"]["no_chapter_wide_promotion"] is True
    assert review["policy"]["no_verbatim_claim"] is True
def test_exactly_six_supported_six_partial():
    review = _json(REVIEW); counts = Counter(r["review_status"] for r in review["rows"])
    assert counts["supported_for_claim_level_promotion"] == 6
    assert counts["partial_match_not_sufficient"] == 6
    assert counts["not_evaluated_in_targeted_sections"] == 118
    assert review["promotion_count"] == 6
def test_partial_matches_do_not_promote():
    review = _json(REVIEW); partial = [r for r in review["rows"] if r["review_status"] == "partial_match_not_sufficient"]
    assert len(partial) == 6
    assert all(r["authority_after"] == "dk_attested" for r in partial)
