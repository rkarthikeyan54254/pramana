import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"


def _jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_volume1_semantic_frontier_is_complete_through_175():
    all_rows = []
    for path in REVIEW.glob("mahaperiyava_dk_v1_*_teaching_records.jsonl"):
        all_rows.extend(_jsonl(path))

    assert len(all_rows) == 927
    ids = [r["id"] for r in all_rows]
    assert len(ids) == len(set(ids))

    auth = Counter(r["evidence_status"]["authority"] for r in all_rows)
    assert auth["dk_attested"] == 890
    assert auth["earlier_witness_supported"] == 37
    assert auth["dk_print_checked"] == 0
    assert auth["primary_source_verified"] == 0

    covered_ordinals = {
        r["source_locus"]["chapter_ordinal"]
        for r in all_rows
    }
    assert covered_ordinals == set(range(1, 176))


def test_pilot_remains_disjoint_from_regular_batches():
    pilot = _jsonl(REVIEW / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl")
    assert len(pilot) == 28

    pilot_ordinals = {
        r["source_locus"]["chapter_ordinal"]
        for r in pilot
    }
    assert pilot_ordinals == {4, 21, 23, 25, 32}

    batch_ordinals = set()
    for path in REVIEW.glob("mahaperiyava_dk_v1_batch_*_teaching_records.jsonl"):
        batch_ordinals |= {
            r["source_locus"]["chapter_ordinal"]
            for r in _jsonl(path)
        }

    assert pilot_ordinals.isdisjoint(batch_ordinals)


def test_every_catalog_chapter_has_semantic_representation():
    catalog = json.loads(
        (REVIEW / "mahaperiyava_deivathin_kural_v1_catalog.json")
        .read_text(encoding="utf-8")
    )
    queue = _jsonl(REVIEW / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl")

    assert catalog["chapter_count"] == 175
    assert len(queue) == 175

    represented = set()
    for path in REVIEW.glob("mahaperiyava_dk_v1_*_teaching_records.jsonl"):
        represented |= {
            r["source_locus"]["chapter_ordinal"]
            for r in _jsonl(path)
        }

    assert represented == set(range(1, 176))
    assert all(
        row["teaching_units_created"] > 0
        for row in queue
    )
