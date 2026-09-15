from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_curation_index.json"
def _json(path): return json.loads(path.read_text(encoding="utf-8"))
def _jsonl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def test_batch_authority_after_targeted_witness_pass():
    rows = _jsonl(RECORDS); index = _json(INDEX)
    assert len(rows) == 130 and index["unit_count"] == 130
    assert Counter(r["evidence_status"]["authority"] for r in rows) == {"dk_attested": 124, "earlier_witness_supported": 6}
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)
def test_supported_rows_have_earlier_secondary_provenance():
    rows = _jsonl(RECORDS); supported = [r for r in rows if r["evidence_status"]["authority"] == "earlier_witness_supported"]
    assert len(supported) == 6
    for row in supported:
        assert [p["witness_role"] for p in row["provenance"]] == ["official_digital", "earlier_secondary"]
        assert row["attribution"]["wording_status"] == "earlier_witness_agrees"
        assert "not treated as verbatim" in row["provenance"][1]["lineage_note"]
def test_dk_only_rows_remain_fail_closed():
    rows = _jsonl(RECORDS); dk_only = [r for r in rows if r["evidence_status"]["authority"] == "dk_attested"]
    assert len(dk_only) == 124
    assert all(r["attribution"]["wording_status"] == "dk_wording_only" for r in dk_only)
def test_context_flags_survive_promotion():
    rows = _jsonl(RECORDS)
    karma = next(r for r in rows if r["id"].endswith(".karma_as_moral_cause_and_effect"))
    assert karma["evidence_status"]["authority"] == "earlier_witness_supported"
    assert "scientific_analogy_not_literal" in karma["flags"]
    paths = next(r for r in rows if r["id"].endswith(".hindu_nonexclusive_path_claim"))
    assert paths["evidence_status"]["authority"] == "earlier_witness_supported"
    assert "historical_claim_requires_external_verification" in paths["flags"]
def test_index_records_targeted_not_exhaustive_review():
    policy = _json(INDEX)["policy"]
    assert policy["targeted_historical_witness_pass_completed"] is True
    assert policy["historical_witness_exhaustive_review_completed"] is False
    assert policy["historical_witness_support_is_claim_level"] is True
    assert policy["no_verbatim_wording_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True
