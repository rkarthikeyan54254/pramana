import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"
MANIFEST = REVIEW / "mahaperiyava_dk_v1_batch_166_175_curator_manifest.json"
RECORDS = REVIEW / "mahaperiyava_dk_v1_batch_166_175_teaching_records.jsonl"
QUEUE = REVIEW / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"


def _jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_batch_166_175_manifest_accounting():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert len(m["chapters"]) == 10
    assert m["counts"]["source_paragraphs"] == 161
    assert len(m["units"]) == 36
    assert m["counts"]["covered_source_paragraphs"] == 161
    assert m["counts"]["explicitly_excluded_source_paragraphs"] == 0
    assert m["counts"]["overlap_instances"] == 0
    assert m["explicit_exclusions"] == []

    refs = Counter(
        (u["chapter_ordinal"], pid)
        for u in m["units"]
        for pid in u["source_paragraph_ids"]
    )
    assert len(refs) == 161
    assert all(v == 1 for v in refs.values())


def test_batch_166_175_records_match_manifest_and_authority():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = _jsonl(RECORDS)

    assert len(records) == 36
    assert {r["id"] for r in records} == {u["id"] for u in m["units"]}
    assert Counter(r["evidence_status"]["authority"] for r in records) == Counter({
        "dk_attested": 36
    })
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in records)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in records)


def test_queue_166_175_is_curated():
    q = _jsonl(QUEUE)
    by_ord = {r["ordinal"]: r for r in q}
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = Counter(u["chapter_ordinal"] for u in manifest["units"])

    for ordinal in range(166, 176):
        assert by_ord[ordinal]["stage"] == "batch_teaching_units_curated"
        assert by_ord[ordinal]["teaching_units_created"] == expected[ordinal]
