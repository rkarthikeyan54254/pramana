import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"

MANIFEST = REVIEW / "mahaperiyava_dk_v1_batch_126_145_curator_manifest.json"
RECORDS = REVIEW / "mahaperiyava_dk_v1_batch_126_145_teaching_records.jsonl"
INDEX = REVIEW / "mahaperiyava_dk_v1_batch_126_145_curation_index.json"
PILOT = REVIEW / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
QUEUE = REVIEW / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"

CH136_IDS = {
    "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.gunas_and_trimurti_symbolism",
    "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.sectarian_readings_of_shiva_and_vishnu",
    "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.smarta_view_no_higher_or_lower_deity",
    "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.simple_guna_labels_do_not_separate_shiva_vishnu",
    "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.shiva_vishnu_essential_unity",
}

CANDIDATE_IDS = {
    "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.smarta_view_no_higher_or_lower_deity",
    "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.shiva_vishnu_essential_unity",
}


PRECEPTORS_1968_IDS = {
    "mahaperiyava.deivathin_kural.v1.bhagavan_yaar_bhagavatpadhar_badhil.ishta_devata_without_denigration_and_reciprocal_worship",
}


def _jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_batch_126_145_manifest_accounting():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert len(m["chapters"]) == 20
    assert m["counts"]["source_paragraphs"] == 340
    assert len(m["units"]) == 98
    assert m["counts"]["covered_source_paragraphs"] == 339
    assert m["counts"]["explicitly_excluded_source_paragraphs"] == 1

    assert m["explicit_exclusions"] == [{
        "chapter_ordinal": 133,
        "source_paragraph_ids": ["p026"],
        "classification": "editorial_apparatus",
        "reason": (
            "Editorial forward-reference to the next discourse, not part of the "
            "substantive teaching claim set."
        ),
        "source_paragraph_hashes": [
            "ed9cb42cd860ad341e5040b2bcb09d7fee6e9bbabdb94acf6b9457e7755c55a2"
        ],
    }]

    refs = Counter(
        (u["chapter_ordinal"], pid)
        for u in m["units"]
        for pid in u["source_paragraph_ids"]
    )
    assert all(count == 1 for count in refs.values())
    assert (133, "p026") not in refs


def test_batch_126_145_authority_and_chapter_136_migration():
    records = _jsonl(RECORDS)
    assert len(records) == 98

    auth = Counter(r["evidence_status"]["authority"] for r in records)
    assert auth == Counter({"dk_attested": 97, "earlier_witness_supported": 1})

    ch136 = [
        r for r in records
        if r["source_locus"]["chapter_ordinal"] == 136
    ]
    assert len(ch136) == 5
    assert {r["id"] for r in ch136} == CH136_IDS
    assert all(r["evidence_status"]["authority"] == "dk_attested" for r in ch136)
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in ch136)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in ch136)

    # Candidate historical leads remain review-only, never teaching-record fields/flags.
    for r in ch136:
        assert "candidate_witness" not in r
        assert "historical_witness" not in r
        assert "match_level" not in r
        assert "historical_match_candidate_external_1927" not in r.get("flags", [])


def test_chapter_136_candidate_witnesses_are_review_only():
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    by_id = {u["id"]: u for u in idx["units"]}

    for record_id in CANDIDATE_IDS:
        unit = by_id[record_id]
        assert unit["authority"] == "dk_attested"
        assert unit.get("candidate_witness")

    smarta = by_id[
        "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.smarta_view_no_higher_or_lower_deity"
    ]
    assert any(
        c["source_key"] == "kamakoti-acharyas-call-part2-ch64"
        and c["status"] == "candidate_requires_snapshot_and_item_level_review"
        for c in smarta["candidate_witness"]
    )

    unity = by_id[
        "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.shiva_vishnu_essential_unity"
    ]
    keys = {c["source_key"] for c in unity["candidate_witness"]}
    assert "kamakoti-acharyas-call-part2-ch64" in keys
    assert "kamakoti-sage-of-kanchi-1927-coimbatore" in keys


def test_chapter_136_removed_from_pilot_and_queue_migrated():
    pilot = _jsonl(PILOT)
    assert not any(
        r["source_locus"]["chapter_ordinal"] == 136
        for r in pilot
    )

    queue = _jsonl(QUEUE)
    q136 = next(row for row in queue if row["ordinal"] == 136)
    assert q136["stage"] == "batch_teaching_units_curated"
    assert q136["teaching_units_created"] == 5


def test_no_pilot_regular_batch_ordinal_overlap_after_145():
    pilot = _jsonl(PILOT)
    pilot_ordinals = {
        r["source_locus"]["chapter_ordinal"]
        for r in pilot
    }

    batch_ordinals = set()
    for path in REVIEW.glob("mahaperiyava_dk_v1_batch_*_teaching_records.jsonl"):
        for r in _jsonl(path):
            batch_ordinals.add(r["source_locus"]["chapter_ordinal"])

    assert pilot_ordinals.isdisjoint(batch_ordinals), (
        f"pilot/regular overlap remains: "
        f"{sorted(pilot_ordinals & batch_ordinals)}"
    )

def test_preceptors_1968_promotion_is_the_only_new_batch_authority():
    records = _jsonl(RECORDS)

    promoted = {
        r["id"]
        for r in records
        if r["evidence_status"]["authority"]
        == "earlier_witness_supported"
    }

    assert promoted == PRECEPTORS_1968_IDS

    row = next(
        r for r in records
        if r["id"] in PRECEPTORS_1968_IDS
    )

    assert (
        row["attribution"]["wording_status"]
        == "earlier_witness_agrees"
    )

    witnesses = [
        x for x in row["provenance"]
        if x.get("source_key")
        == "preceptors-of-advaita-1968-scan"
    ]

    assert len(witnesses) == 1
    assert witnesses[0]["witness_role"] == "earlier_secondary"
    assert len(witnesses[0]["snapshot_sha256"]) == 64
