#!/usr/bin/env python3
"""Regression test for Mahaperiyava DK V1 batch 086-105 teaching records."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_086_105_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_086_105_curation_index.json"
QUEUE = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"
SCHEMA = ROOT / "schema/teaching_record.schema.json"

EXPECTED = set(range(86, 106))
REPLACEMENT_DECODED = {48, 49, 50, 51, 52, 53, 54, 59, 60, 61, 63, 64, 65}

# Curator-approved manifest
MANIFEST = ROOT / "data/review/mahaperiyava_dk_v1_batch_086_105_curator_manifest.json"

# Expected counts
EXPECTED_COUNTS = {
    "total": 161,
    "chapters": 20,
    "teaching_units": 95,
    "promoted": 0,
    "partial": 0,
    "not_evaluated": 160,
}

# Batch authority totals
EXPECTED_BATCH_AUTHORITY = {
    "dk_attested": 93,
    "earlier_witness_supported": 2,
}

# Corpus-wide totals after this batch
EXPECTED_CORPUS_AUTHORITY = {
    "total": 592,
    "dk_attested": 559,
    "earlier_witness_supported": 33,
    "dk_print_checked": 0,
    "primary_source_verified": 0,
}

# Carry-forward manifest
CARRYFORWARD = ROOT / "data/review/mahaperiyava_dk_v1_batch_086_105_witness_carryforward.json"
CARRYFORWARD_SHA256 = "40afc68bf7b3e0509d44eab107d18facbfe606fca4a2b587ccdc0b2a764feb7a"

# Expected carry-forward IDs
CARRYFORWARD_IDS = {
    "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.temple_as_communal_gratitude_and_offering",
    "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.regular_attendance_sustains_temple_worship",
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

    assert len(rows) == 95
    assert index["unit_count"] == 95
    assert len({r["id"] for r in rows}) == 95
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == EXPECTED

    # Batch authority: 95 dk_attested, 0 earlier_witness_supported
    authority_counts = Counter(r["evidence_status"]["authority"] for r in rows)
    assert authority_counts == EXPECTED_BATCH_AUTHORITY
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)

    # Wording status: mostly dk_wording_only, but 2 carry-forward are earlier_witness_agrees
    for r in rows:
        if r["id"] in CARRYFORWARD_IDS:
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


def test_all_161_source_paragraphs_are_accounted_for():
    """
    Curator policy: Every substantive source paragraph must be accounted for by at least
    one teaching unit, or explicitly classified as editorial/apparatus.
    Legitimate overlap between teaching units is allowed.
    This test verifies the current 086-105 mapping covers 160/161 paragraphs,
    with 1 explicitly classified as editorial/apparatus.
    """
    index = _json(INDEX)
    coverage = index["source_coverage"]

    assert coverage["paragraph_count"] == 161
    assert coverage["covered_paragraph_count"] == 160
    assert coverage["excluded_source_blocks"] == 1
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

    assert len(seen) == 160
    # Exactly one explicit exclusion (chapter 86, p023)
    assert len(set(seen)) == 160


def test_replacement_decoded_units_are_flagged():
    rows = _jsonl(RECORDS)
    for row in rows:
        ordinal = row["source_locus"]["chapter_ordinal"]
        flagged = "source_decode_replacement" in row.get("flags", [])
        assert flagged is (ordinal in REPLACEMENT_DECODED)


def test_chapter_105_title_anomaly_preserved():
    """Chapter 105 title 'நாக மகிமை' has a source-title anomaly noted in manifest."""
    index = _json(INDEX)
    anomaly = next((a for a in index.get("source_anomalies", []) if a["chapter_ordinal"] == 105), None)
    assert anomaly is not None
    assert anomaly["field"] == "title_ta"
    assert anomaly["observed"] == "நாக மகிமை"
    assert anomaly["action"] == "preserved_exactly_as_source_pending_source_qc"


def test_chapter_86_p023_explicitly_excluded():
    """Chapter 86 paragraph p023 is explicitly excluded as editorial/apparatus."""
    manifest = _json(MANIFEST)
    exclusions = manifest.get("explicit_exclusions", [])
    assert len(exclusions) == 1
    excl = exclusions[0]
    assert excl["chapter_ordinal"] == 86
    assert excl["source_paragraph_id"] == "p023"
    assert excl["classification"] == "editorial_apparatus"


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


def test_explicit_exclusion_is_not_in_teaching_records():
    """Explicitly excluded paragraph p023 must not appear in any teaching record."""
    rows = _jsonl(RECORDS)
    for r in rows:
        assert "p023" not in r.get("source_paragraph_ids", []), \
            f"{r['id']}: excluded paragraph p023 appears in teaching record"


def test_queue_counts_match_index():
    queue = _jsonl(QUEUE)
    index = _json(INDEX)
    counts = {int(k): v for k, v in index["chapter_unit_counts"].items()}
    # Select non-pilot chapters 86-105
    pilot_chapters = {100}
    selected = [q for q in queue if q["ordinal"] in range(86, 106) and q["ordinal"] not in pilot_chapters]

    assert len(selected) == 19  # 20 chapters minus 2 pilot chapters
    assert all(q["stage"] == "batch_teaching_units_curated" for q in selected)
    assert all(q["teaching_units_created"] == counts[q["ordinal"]] for q in selected)


def test_historical_witness_policy_current():
    """The targeted 1957-58 witness pass is deferred for this batch."""
    index = _json(INDEX)
    policy = index["policy"]

    assert policy["historical_witness_comparison_deferred"] is True
    assert policy["no_print_check_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True
    assert policy["claim_summaries_are_not_quotes"] is True

    source_coverage = _json(INDEX)["source_coverage"]
    assert source_coverage["paragraph_count"] == 161
    assert source_coverage["covered_paragraph_count"] == 160
    assert source_coverage["covered_paragraph_count"] == source_coverage["paragraph_count"] - 1

    assert index["policy"]["historical_witness_comparison_deferred"] is True
    assert index["policy"]["historical_witness_comparison_completed_for_promoted"] is False


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
    assert policy["source_paragraph_accounting_policy"] == "at_least_once_or_explicitly_excluded"
    assert policy["claim_summaries_are_not_quotes"] is True
    assert policy["no_print_check_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True




def test_chapter100_has_five_batch_records():
    """Chapter 100 has exactly 5 regular-batch teaching records."""
    rows = _jsonl(RECORDS)
    ch100 = [r for r in rows if r["source_locus"]["chapter_ordinal"] == 100]
    assert len(ch100) == 5


def test_chapter100_absent_from_pilot():
    """Chapter 100 records no longer remain in pilot teaching records."""
    PILOT_RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
    pilot_rows = _jsonl(PILOT_RECORDS)
    ch100 = [r for r in pilot_rows if r["source_locus"]["chapter_ordinal"] == 100]
    assert len(ch100) == 0


def test_chapter100_absent_from_pilot_curation():
    """Chapter 100 absent from pilot curation units."""
    PILOT_INDEX = ROOT / "data/review/mahaperiyava_dk_v1_pilot_curation_index.json"
    pilot_index = _json(PILOT_INDEX)
    ch100 = [u for u in pilot_index["units"] if u.get("chapter_ordinal") == 100 or u.get("chapter_slug") == "alaya_vazhipadu"]
    assert len(ch100) == 0


def test_chapter100_two_earlier_witness_supported():
    """Exactly 2 chapter 100 batch records are earlier_witness_supported."""
    rows = _jsonl(RECORDS)
    ch100 = [r for r in rows if r["source_locus"]["chapter_ordinal"] == 100]
    supported = [r for r in ch100 if r["evidence_status"]["authority"] == "earlier_witness_supported"]
    assert len(supported) == 2


def test_carryforward_ids_match_manifest():
    """The two earlier_witness_supported IDs equal the curator carry-forward manifest."""
    rows = _jsonl(RECORDS)
    ch100 = [r for r in rows if r["source_locus"]["chapter_ordinal"] == 100]
    supported = [r for r in ch100 if r["evidence_status"]["authority"] == "earlier_witness_supported"]
    supported_ids = {r["id"] for r in supported}
    assert supported_ids == CARRYFORWARD_IDS


def test_carryforward_has_earlier_secondary_provenance():
    """Each carry-forward record has earlier_secondary provenance."""
    rows = _jsonl(RECORDS)
    for r in rows:
        if r["id"] in CARRYFORWARD_IDS:
            ew = [p for p in r["provenance"] if p["witness_role"] == "earlier_secondary"]
            assert len(ew) == 1, f"{r['id']}: missing earlier_secondary provenance"
            p = ew[0]
            assert p["source_key"] == "acharya-upanyasangal-part1-1957-58-scan"
            assert p["witness_role"] == "earlier_secondary"
            assert p["locus"] == "ஆலய வணக்கம், printed p. 39 ff.; PDF pp. 54-56"
            assert p["snapshot_sha256"] == "ace3c1cca4c3077d9e15080365741f541d471274c28d11e07d85f2b372901f7e"


def test_carryforward_wording_status():
    """Each carry-forward record uses earlier_witness_agrees."""
    rows = _jsonl(RECORDS)
    for r in rows:
        if r["id"] in CARRYFORWARD_IDS:
            assert r["attribution"]["wording_status"] == "earlier_witness_agrees"


def test_carryforward_print_check_not_checked():
    """Each carry-forward record remains print_check=not_checked."""
    rows = _jsonl(RECORDS)
    for r in rows:
        if r["id"] in CARRYFORWARD_IDS:
            assert r["evidence_status"]["print_check"] == "not_checked"


def test_carryforward_primary_source_unknown():
    """Each carry-forward record remains primary_source_status=unknown."""
    rows = _jsonl(RECORDS)
    for r in rows:
        if r["id"] in CARRYFORWARD_IDS:
            assert r["evidence_status"]["primary_source_status"] == "unknown"


def test_no_duplicate_ids_corpus_wide():
    """No duplicate IDs corpus-wide."""
    import glob
    all_ids = []
    for f in glob.glob(str(ROOT / "data/review/mahaperiyava*teaching_records.jsonl")):
        for line in open(f, encoding='utf-8'):
            if line.strip():
                all_ids.append(json.loads(line)["id"])
    assert len(all_ids) == len(set(all_ids)), f"Duplicate IDs found: {[x for x in all_ids if all_ids.count(x) > 1]}"


def test_no_top_level_historical_witness_in_batch_records():
    """No top-level historical_witness/candidate_witness in teaching records."""
    rows = _jsonl(RECORDS)
    for r in rows:
        assert "historical_witness" not in r
        assert "candidate_witness" not in r


def test_no_unrelated_authority_changes():
    """No unrelated authority changes in other chapters."""
    rows = _jsonl(RECORDS)
    for r in rows:
        if r["source_locus"]["chapter_ordinal"] != 100:
            assert r["evidence_status"]["authority"] == "dk_attested"


def test_carryforward_manifest_sha256_locked():
    """Carry-forward manifest SHA256 is locked."""
    import hashlib
    content = CARRYFORWARD.read_bytes()
    sha256 = hashlib.sha256(content).hexdigest()
    assert sha256 == CARRYFORWARD_SHA256


def test_batch_authority_totals():
    """Batch 086-105 authority: 93 dk_attested, 2 earlier_witness_supported."""
    rows = _jsonl(RECORDS)
    authority = Counter(r["evidence_status"]["authority"] for r in rows)
    assert authority["dk_attested"] == 93
    assert authority["earlier_witness_supported"] == 2
    assert sum(authority.values()) == 95


def test_corpus_authority_totals():
    """Corpus-wide authority invariants; exact frontier totals live in the newest batch regression."""
    import glob
    all_rows = []
    for f in glob.glob(str(ROOT / "data/review/mahaperiyava*teaching_records.jsonl")):
        for line in open(f, encoding='utf-8'):
            if line.strip():
                all_rows.append(json.loads(line))
    authority = Counter(r["evidence_status"]["authority"] for r in all_rows)
    assert authority["dk_attested"] + authority["earlier_witness_supported"] == len(all_rows)
    assert authority["dk_print_checked"] == 0
    assert authority["primary_source_verified"] == 0


if __name__ == "__main__":
    import pytest
    import sys
    import re
    sys.exit(pytest.main([__file__, "-v"]))