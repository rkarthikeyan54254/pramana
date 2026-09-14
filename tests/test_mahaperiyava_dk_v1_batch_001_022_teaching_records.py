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
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def test_batch_shape_and_authority():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)
    assert len(rows) == 102
    assert index["unit_count"] == 102
    assert len({r["id"] for r in rows}) == 102
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == EXPECTED
    assert Counter(r["evidence_status"]["authority"] for r in rows) == {"dk_attested": 102}
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)
    assert all(r["attribution"]["wording_status"] == "dk_wording_only" for r in rows)
    assert all([p["witness_role"] for p in r["provenance"]] == ["official_digital"] for r in rows)

def test_no_restricted_source_text_is_tracked():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)
    assert index["source_packet"]["tracked"] is False
    assert index["policy"]["no_exact_source_text_in_tracked_artifacts"] is True
    for r in rows:
        assert "text" not in r
        assert "exact_text_restricted" not in r
        assert r["rights"]["source_text_tier"] == "restricted"
        assert r["rights"]["public_export"] == "metadata_only"

def test_private_hash_mapping_and_question_intents_exist():
    index = _json(INDEX)
    assert len(index["units"]) == 102
    for u in index["units"]:
        assert u["question_intents"]
        assert len(u["source_paragraph_ids"]) == len(u["source_paragraph_hashes"])
        assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in u["source_paragraph_hashes"])

def test_queue_marks_exactly_this_batch_curated():
    queue = _jsonl(QUEUE)
    selected = [q for q in queue if q["ordinal"] in EXPECTED]
    assert len(selected) == 20
    assert all(not q["pilot"] for q in selected)
    assert all(q["stage"] == "batch_teaching_units_curated" for q in selected)
    assert all(q["teaching_units_created"] > 0 for q in selected)

def test_sensitive_math_health_science_claims_remain_attributed():
    rows = _jsonl(RECORDS)
    sensitive = {
        "health_claim_attributed_only",
        "astrology_claim_attributed_only",
        "scientific_claim_requires_external_verification",
        "scientific_comparison_requires_external_verification",
        "mathematical_analogy_not_literal",
        "mathematical_claim_inaccurate_as_modern_arithmetic",
        "etymology_claim_requires_external_verification",
        "comparative_doctrinal_simplification",
    }
    flagged = [r for r in rows if sensitive.intersection(r.get("flags", []))]
    assert flagged
    assert all(r["evidence_status"]["authority"] == "dk_attested" for r in flagged)
    assert any("health_claim_attributed_only" in r["flags"] for r in flagged)
    assert any("mathematical_claim_inaccurate_as_modern_arithmetic" in r["flags"] for r in flagged)
