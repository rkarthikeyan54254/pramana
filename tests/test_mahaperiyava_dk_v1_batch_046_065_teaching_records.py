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
    assert Counter(r["evidence_status"]["authority"] for r in rows) == {
        "dk_attested": 105
    }
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)
    assert all(r["attribution"]["wording_status"] == "dk_wording_only" for r in rows)


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


def test_all_212_source_paragraphs_are_mapped_once():
    index = _json(INDEX)
    coverage = index["source_coverage"]

    assert coverage == {
        "paragraph_count": 212,
        "covered_paragraph_count": 212,
        "coverage_mode": "exactly_once",
        "excluded_source_blocks": 0,
    }

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
    assert len(set(seen)) == 212


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


def test_context_sensitive_material_stays_at_dk_attested():
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
    assert all(r["evidence_status"]["authority"] == "dk_attested" for r in flagged)


def test_ahimsa_force_and_sacrifice_claim_is_contextualized():
    rows = _jsonl(RECORDS)
    target = next(
        r for r in rows
        if r["id"].endswith(".contextual_exceptions_to_absolute_ahimsa")
    )
    assert target["evidence_status"]["authority"] == "dk_attested"
    assert "traditional_normative_claim" in target["flags"]
    assert "religious_comparison_attributed_only" in target["flags"]


def test_political_chapters_remain_attributed():
    rows = _jsonl(RECORDS)
    selected = [
        r for r in rows
        if r["source_locus"]["chapter_ordinal"] in {62,63,64}
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
    assert policy["historical_witness_comparison_deferred"] is True
    assert policy["every_source_paragraph_mapped_exactly_once"] is True
    assert policy["sensitive_external_fact_claims_are_flagged"] is True
    assert policy["caste_varna_material_requires_contextual_answering"] is True
    assert policy["political_material_requires_source_attribution"] is True
    assert policy["violence_punishment_and_sacrifice_material_requires_context"] is True
