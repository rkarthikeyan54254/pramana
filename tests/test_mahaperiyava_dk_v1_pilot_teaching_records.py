from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_pilot_curation_index.json"
SCHEMA = ROOT / "schema/teaching_record.schema.json"


def _jsonl(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_pilot_has_56_unique_teaching_units_across_10_chapters():
    records = _jsonl(RECORDS)
    index = _load(INDEX)

    assert len(records) == 56
    assert index["unit_count"] == 56
    assert len({r["id"] for r in records}) == 56
    assert len(index["chapter_unit_counts"]) == 10

    counts = Counter(
        r["source_locus"]["chapter_title_ta"]
        for r in records
    )
    assert len(counts) == 10


def test_authority_is_fail_closed_and_claim_level():
    records = _jsonl(RECORDS)
    counts = Counter(r["evidence_status"]["authority"] for r in records)

    assert counts == {
        "dk_attested": 50,
        "earlier_witness_supported": 6,
    }
    assert all(
        r["evidence_status"]["print_check"] == "not_checked"
        for r in records
    )
    assert all(
        r["evidence_status"]["primary_source_status"] == "unknown"
        for r in records
    )
    assert not any(
        r["evidence_status"]["authority"] == "primary_source_verified"
        for r in records
    )


def test_earlier_supported_records_have_two_provenance_witnesses():
    records = _jsonl(RECORDS)

    supported = [
        r for r in records
        if r["evidence_status"]["authority"] == "earlier_witness_supported"
    ]
    assert len(supported) == 6

    for r in supported:
        roles = {p["witness_role"] for p in r["provenance"]}
        assert roles == {"official_digital", "earlier_secondary"}
        assert r["attribution"]["wording_status"] == "earlier_witness_agrees"
        assert "verbatim" in r["attribution"]["note"].lower()


def test_dk_only_records_do_not_gain_independent_witnesses():
    records = _jsonl(RECORDS)

    dk_only = [
        r for r in records
        if r["evidence_status"]["authority"] == "dk_attested"
    ]
    assert len(dk_only) == 50

    for r in dk_only:
        assert [p["witness_role"] for p in r["provenance"]] == [
            "official_digital"
        ]
        assert r["attribution"]["wording_status"] == "dk_wording_only"


def test_teaching_records_match_schema_shape_without_new_dependency():
    schema = _load(SCHEMA)
    records = _jsonl(RECORDS)

    top_allowed = set(schema["properties"])
    top_required = set(schema["required"])
    id_re = re.compile(schema["properties"]["id"]["pattern"])

    for r in records:
        assert not (top_required - set(r))
        assert not (set(r) - top_allowed)
        assert id_re.match(r["id"])

        for field in (
            "source_locus",
            "attribution",
            "evidence_status",
            "rights",
        ):
            spec = schema["properties"][field]
            obj = r[field]
            assert not (set(spec.get("required", [])) - set(obj))
            if spec.get("additionalProperties") is False:
                assert not (set(obj) - set(spec["properties"]))

        assert r["evidence_status"]["authority"] in (
            schema["properties"]["evidence_status"]["properties"]
            ["authority"]["enum"]
        )
        assert r["attribution"]["wording_status"] in (
            schema["properties"]["attribution"]["properties"]
            ["wording_status"]["enum"]
        )

        if r["rights"]["source_text_tier"] == "restricted":
            assert r["rights"]["public_export"] in {"metadata_only", "none"}


def test_no_restricted_dk_source_text_is_tracked_in_records_or_index():
    records = _jsonl(RECORDS)
    index = _load(INDEX)

    for r in records:
        assert "exact_text_restricted" not in r
        assert "text" not in r
        assert r["rights"]["source_text_tier"] == "restricted"
        assert r["rights"]["public_export"] == "metadata_only"

    assert index["policy"]["no_exact_source_text_in_tracked_artifacts"] is True
    assert index["source_packet"]["tracked"] is False


def test_curation_index_maps_every_record_to_hashed_private_paragraphs():
    records = _jsonl(RECORDS)
    index = _load(INDEX)

    by_record = {r["id"]: r for r in records}
    by_unit = {u["id"]: u for u in index["units"]}

    assert set(by_record) == set(by_unit)

    for unit_id, unit in by_unit.items():
        assert unit["source_paragraph_ids"]
        assert len(unit["source_paragraph_ids"]) == len(
            unit["source_paragraph_hashes"]
        )
        assert all(
            re.fullmatch(r"[0-9a-f]{64}", h)
            for h in unit["source_paragraph_hashes"]
        )
        assert unit["authority"] == (
            by_record[unit_id]["evidence_status"]["authority"]
        )
        assert unit["question_intents"]


def test_context_sensitive_historical_claims_stay_at_dk_attested():
    records = _jsonl(RECORDS)
    risky_flags = {
        "historical_claim_requires_external_verification",
        "quantitative_historical_claim_requires_verification",
        "context_sensitive_identity_claim",
        "historical_generalization",
        "cultural_generalization",
    }

    for r in records:
        if risky_flags.intersection(r.get("flags", [])):
            assert r["evidence_status"]["authority"] == "dk_attested"
