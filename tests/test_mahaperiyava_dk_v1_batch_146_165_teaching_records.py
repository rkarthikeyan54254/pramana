import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"
MANIFEST = REVIEW / "mahaperiyava_dk_v1_batch_146_165_curator_manifest.json"
RECORDS = REVIEW / "mahaperiyava_dk_v1_batch_146_165_teaching_records.jsonl"
QUEUE = REVIEW / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"


def _jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_batch_146_165_manifest_accounting():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert len(m["chapters"]) == 20
    assert m["counts"]["source_paragraphs"] == 286
    assert len(m["units"]) == 100
    assert m["counts"]["covered_source_paragraphs"] == 284
    assert m["counts"]["explicitly_excluded_source_paragraphs"] == 2
    assert m["counts"]["overlap_instances"] == 0

    exclusions = {
        (e["chapter_ordinal"], tuple(e["source_paragraph_ids"]), e["classification"])
        for e in m["explicit_exclusions"]
    }
    assert exclusions == {
        (146, ("p005",), "editorial_apparatus"),
        (157, ("p010",), "editorial_transition"),
    }

    refs = Counter(
        (u["chapter_ordinal"], pid)
        for u in m["units"]
        for pid in u["source_paragraph_ids"]
    )
    assert all(v == 1 for v in refs.values())
    assert (146, "p005") not in refs
    assert (157, "p010") not in refs


def test_batch_146_165_records_match_manifest_and_authority():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = _jsonl(RECORDS)

    assert len(records) == 100
    assert {r["id"] for r in records} == {u["id"] for u in m["units"]}
    assert Counter(r["evidence_status"]["authority"] for r in records) == Counter({
        "dk_attested": 100
    })
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in records)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in records)


def test_queue_146_165_is_curated():
    q = _jsonl(QUEUE)
    by_ord = {r["ordinal"]: r for r in q}
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = Counter(u["chapter_ordinal"] for u in manifest["units"])

    for ordinal in range(146, 166):
        assert by_ord[ordinal]["stage"] == "batch_teaching_units_curated"
        assert by_ord[ordinal]["teaching_units_created"] == expected[ordinal]
