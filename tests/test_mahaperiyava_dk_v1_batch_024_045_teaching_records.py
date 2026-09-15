from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_curation_index.json"
QUEUE = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"

EXPECTED = {24,26,27,28,29,30,31,33,34,35,36,37,38,39,40,41,42,43,44,45}


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_batch_shape_and_authority():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)

    assert len(rows) == 130
    assert index["unit_count"] == 130
    assert len({r["id"] for r in rows}) == 130
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == EXPECTED
    assert Counter(r["evidence_status"]["authority"] for r in rows) == {"dk_attested": 130}
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)
    assert all(r["attribution"]["wording_status"] == "dk_wording_only" for r in rows)


def test_rights_and_private_hash_mapping():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)

    assert index["source_packet"]["tracked"] is False
    assert index["policy"]["no_exact_source_text_in_tracked_artifacts"] is True

    for row in rows:
        assert "text" not in row
        assert "exact_text_restricted" not in row
        assert row["rights"]["source_text_tier"] == "restricted"
        assert row["rights"]["public_export"] == "metadata_only"

    for unit in index["units"]:
        assert unit["question_intents"]
        assert len(unit["source_paragraph_ids"]) == len(unit["source_paragraph_hashes"])
        assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in unit["source_paragraph_hashes"])


def test_editorial_apparatus_is_explicitly_excluded():
    index = _json(INDEX)
    excluded = {
        (x["chapter_ordinal"], x["paragraph_id"])
        for x in index["excluded_source_blocks"]
    }
    assert excluded == {
        (34, "p017"),
        (39, "p042"),
        (42, "p023"),
        (42, "p024"),
    }
    assert len(index["excluded_source_blocks"]) == 4
    assert all(
        re.fullmatch(r"[0-9a-f]{64}", x["paragraph_sha256"])
        for x in index["excluded_source_blocks"]
    )

    for unit in index["units"]:
        assert not any(
            (unit["chapter_ordinal"], pid) in excluded
            for pid in unit["source_paragraph_ids"]
        )


def test_sensitive_material_remains_at_dk_attested():
    rows = _jsonl(RECORDS)
    sensitive = {
        "caste_varna_normative_claim",
        "historical_claim_requires_external_verification",
        "scientific_claim_requires_external_verification",
        "religious_comparison_attributed_only",
        "medical_or_effect_claim_attributed_only",
        "linguistic_etymology_claim_requires_external_verification",
        "political_historical_claim",
        "social_generalization",
        "cultural_generalization",
        "speculative_historical_claim",
    }

    flagged = [r for r in rows if sensitive.intersection(r.get("flags", []))]
    assert flagged
    assert all(r["evidence_status"]["authority"] == "dk_attested" for r in flagged)


def test_varna_material_has_context_flag():
    rows = _jsonl(RECORDS)
    varna = [r for r in rows if "caste_varna_normative_claim" in r.get("flags", [])]
    assert len(varna) >= 25
    assert all(r["evidence_status"]["authority"] == "dk_attested" for r in varna)


def test_replacement_decoded_chapters_are_flagged():
    rows = _jsonl(RECORDS)
    for ordinal in (27, 41, 44):
        selected = [r for r in rows if r["source_locus"]["chapter_ordinal"] == ordinal]
        assert selected
        assert all("source_decode_replacement" in r.get("flags", []) for r in selected)


def test_queue_counts_match_index():
    queue = _jsonl(QUEUE)
    index = _json(INDEX)
    counts = {int(k): v for k, v in index["chapter_unit_counts"].items()}
    selected = [q for q in queue if q["ordinal"] in EXPECTED]

    assert len(selected) == 20
    assert all(q["stage"] == "batch_teaching_units_curated" for q in selected)
    assert all(q["teaching_units_created"] == counts[q["ordinal"]] for q in selected)


def test_policy_separates_attestation_from_external_truth():
    policy = _json(INDEX)["policy"]
    assert policy["historical_witness_comparison_deferred"] is True
    assert policy["sensitive_external_fact_claims_are_flagged"] is True
    assert policy["religious_and_social_comparisons_are_attributed_only"] is True
    assert policy["varna_caste_normative_material_requires_contextual_answering"] is True
    assert policy["every_source_block_accounted_for_or_explicitly_excluded"] is True
