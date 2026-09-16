from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _queue():
    p = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"
    return [
        json.loads(line)
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_complete_v1_catalog_is_large_and_unique():
    data = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    chapters = data["chapters"]
    assert data["volume"] == 1
    assert data["chapter_count"] == len(chapters)
    assert len(chapters) >= 100
    urls = [c["url"] for c in chapters]
    keys = [c["source_key"] for c in chapters]
    assert len(urls) == len(set(urls))
    assert len(keys) == len(set(keys))


def test_v1_catalog_is_official_kamakoti_and_metadata_only():
    data = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    assert data["official_index_url"] == (
        "https://www.kamakoti.org/tamil/part1index.htm"
    )
    assert data["rights_policy"]["source_text_tracked"] is False
    assert data["rights_policy"]["public_export"] == "metadata_only"

    for c in data["chapters"]:
        assert c["url"].startswith(
            "https://www.kamakoti.org/tamil/part1kural"
        )
        assert c["raw_path"].startswith(
            "sources/raw/verification/mahaperiyava/deivathin_kural/v1/"
        )
        assert c["snapshot_status"] == "pinned"
        assert len(c["snapshot_sha256"]) == 64
        assert "exact_text" not in c
        assert "text" not in c


def test_existing_ten_chapter_pilot_survives_in_complete_catalog():
    pilot = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_pilot.json"
    )
    catalog = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    by_url = {c["url"]: c for c in catalog["chapters"]}
    assert len(pilot["chapters"]) == 10

    for p in pilot["chapters"]:
        assert p["url"] in by_url
        c = by_url[p["url"]]
        assert c["pilot"] is True
        assert c["pilot_slug"] == p["slug"]


def test_extraction_queue_covers_every_catalog_chapter_once():
    catalog = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    queue = _queue()

    assert len(queue) == catalog["chapter_count"]
    assert [q["ordinal"] for q in queue] == list(
        range(1, catalog["chapter_count"] + 1)
    )
    assert {q["source_key"] for q in queue} == {
        c["source_key"] for c in catalog["chapters"]
    }
    pilot_rows = [q for q in queue if q["pilot"]]
    nonpilot_rows = [q for q in queue if not q["pilot"]]

    assert len(pilot_rows) == 8
    assert all(
        q["stage"] == "pilot_teaching_units_curated"
        for q in pilot_rows
    )
    assert all(q["teaching_units_created"] > 0 for q in pilot_rows)

    allowed_nonpilot_stages = {
        "needs_teaching_unit_review",
        "batch_teaching_units_curated",
    }
    assert all(q["stage"] in allowed_nonpilot_stages for q in nonpilot_rows)
    assert all(
        (q["stage"] == "needs_teaching_unit_review" and q["teaching_units_created"] == 0)
        or (q["stage"] == "batch_teaching_units_curated" and q["teaching_units_created"] > 0)
        for q in nonpilot_rows
    )


def test_every_v1_catalog_source_resolves_in_manifest():
    catalog = _load(
        "data/review/mahaperiyava_deivathin_kural_v1_catalog.json"
    )
    manifest = _load("sources/manifest.json")
    by_key = {s["key"]: s for s in manifest["sources"]}

    assert "kamakoti-dk-v1-index" in by_key

    for c in catalog["chapters"]:
        entry = by_key[c["source_key"]]
        assert entry["url"] == c["url"]
        assert entry["path"] == c["raw_path"]
        assert "restricted" in entry["status"]
        assert entry["expected_sha256"] == c["snapshot_sha256"]
        assert entry["expected_bytes"] == c["snapshot_bytes"]
