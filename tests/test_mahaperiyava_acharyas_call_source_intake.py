import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "data/research/mahaperiyava_acharyas_call_source_intake.json"
LINEAGE = ROOT / "data/review/mahaperiyava_source_lineage.json"
REVIEW = ROOT / "data/review"


def _all_records():
    rows = []
    for path in REVIEW.glob("mahaperiyava_dk_v1_*_teaching_records.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_acharyas_call_intake_is_fail_closed():
    data = json.loads(INTAKE.read_text(encoding="utf-8"))
    family = data["source_family"]

    assert family["primary_source"] is False
    assert family["independent_of_dk"] is True
    assert family["authority_effect"] == "none_until_item_level_comparison_and_snapshot"

    for src in data["user_supplied_sources"] + data["supporting_provenance_pages"]:
        assert src["snapshot_sha256"] is None
        assert src["acquisition_status"] == "pending_local_snapshot"


def test_acharyas_call_candidate_targets_exist_but_are_not_promoted():
    data = json.loads(INTAKE.read_text(encoding="utf-8"))
    targets = [
        target
        for candidate in data["targeted_item_level_candidates"]
        for target in candidate["dk_target_ids"]
    ]
    records = {r["id"]: r for r in _all_records()}

    assert targets
    assert all(target in records for target in targets)
    assert all(
        records[target]["evidence_status"]["authority"] == "dk_attested"
        for target in targets
    )


def test_acharyas_call_source_family_already_has_lineage_relation():
    lineage = json.loads(LINEAGE.read_text(encoding="utf-8"))
    ids = {r["id"] for r in lineage["relations"]}
    assert "mahaperiyava.lineage.1964.acharyas_call" in ids
