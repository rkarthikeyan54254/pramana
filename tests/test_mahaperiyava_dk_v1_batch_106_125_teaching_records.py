import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"

MANIFEST = REVIEW / "mahaperiyava_dk_v1_batch_106_125_curator_manifest.json"
RECORDS = REVIEW / "mahaperiyava_dk_v1_batch_106_125_teaching_records.jsonl"
INDEX = REVIEW / "mahaperiyava_dk_v1_batch_106_125_curation_index.json"
PILOT = REVIEW / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl"

CH108_IDS = {
    "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.karma_and_phaladata",
    "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.prayer_for_relief_and_acceptance",
    "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.ordinary_prayer_has_partial_value",
    "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.surrender_as_deeper_bhakti",
    "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.love_of_god_as_enduring_love",
    "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.mature_love_becomes_universal_love",
    "mahaperiyava.deivathin_kural.v1.bhakti_seyvathu_etharkaga.bhakti_culminates_in_grace_and_moksha",
}
STRONG_ID = (
    "mahaperiyava.deivathin_kural.v1."
    "bhakti_seyvathu_etharkaga.karma_and_phaladata"
)


def _jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_batch_106_125_manifest_accounting():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(m["chapters"]) == 20
    assert m["counts"]["source_paragraphs"] == 262
    assert len(m["units"]) == 123
    assert m["counts"]["covered_source_paragraphs"] == 261
    assert m["counts"]["explicitly_excluded_source_paragraphs"] == 1

    assert m["explicit_exclusions"] == [{
        "chapter_ordinal": 113,
        "source_paragraph_id": "p010",
        "source_paragraph_sha256": "e24ebe6275258659edf57525bc3217f37f37d1b6c20a058537c6390c4c301b98",
        "classification": "editorial_apparatus",
        "reason": (
            "Editorial cross-reference directing the reader to later "
            "Shiva-Vishnu-abheda sections; not curated as a Mahaperiyava teaching unit."
        ),
    }]

    refs = Counter(
        (u["chapter_ordinal"], pid)
        for u in m["units"]
        for pid in u["source_paragraph_ids"]
    )
    assert refs[(108, "p005")] == 2
    assert sum(1 for count in refs.values() if count > 1) == 1


def test_batch_106_125_authority_and_chapter_108_migration():
    records = _jsonl(RECORDS)
    assert len(records) == 123
    auth = Counter(r["evidence_status"]["authority"] for r in records)
    assert auth == Counter({
        "dk_attested": 122,
        "earlier_witness_supported": 1,
    })

    ch108 = [
        r for r in records
        if r["source_locus"]["chapter_ordinal"] == 108
    ]
    assert len(ch108) == 7
    assert {r["id"] for r in ch108} == CH108_IDS

    strong = next(r for r in ch108 if r["id"] == STRONG_ID)
    assert strong["evidence_status"]["authority"] == "earlier_witness_supported"
    assert strong["attribution"]["wording_status"] == "earlier_witness_agrees"
    assert strong["evidence_status"]["print_check"] == "not_checked"
    assert strong["evidence_status"]["primary_source_status"] == "unknown"

    earlier = [
        p for p in strong["provenance"]
        if p["witness_role"] == "earlier_secondary"
    ]
    assert len(earlier) == 1
    assert earlier[0]["source_key"] == "acharya-upanyasangal-part1-1957-58-scan"
    assert earlier[0]["locus"] == (
        "ஈசுவர பக்தி ஏன் செய்யவேண்டும்?, printed p. 117 ff.; PDF pp. 132-135"
    )
    assert earlier[0]["snapshot_sha256"] == (
        "ace3c1cca4c3077d9e15080365741f541d471274c28d11e07d85f2b372901f7e"
    )

    for r in ch108:
        if r["id"] != STRONG_ID:
            assert r["evidence_status"]["authority"] == "dk_attested"
        assert "packet_reextract_required" not in r.get("flags", [])


def test_batch_106_125_curation_index_matches_record_authority():
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    by_id = {u["id"]: u for u in idx["units"]}
    assert by_id[STRONG_ID]["authority"] == "earlier_witness_supported"
    assert by_id[STRONG_ID]["historical_witness"] is not None


def test_no_pilot_regular_batch_ordinal_overlap():
    pilot = _jsonl(PILOT)
    pilot_ordinals = {
        r["source_locus"]["chapter_ordinal"]
        for r in pilot
    }

    batch_ordinals = set()
    for path in REVIEW.glob(
        "mahaperiyava_dk_v1_batch_*_teaching_records.jsonl"
    ):
        for r in _jsonl(path):
            batch_ordinals.add(r["source_locus"]["chapter_ordinal"])

    assert pilot_ordinals.isdisjoint(batch_ordinals), (
        f"pilot/regular overlap remains: "
        f"{sorted(pilot_ordinals & batch_ordinals)}"
    )
