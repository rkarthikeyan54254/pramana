from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data/review"


def j(name):
    return json.loads((R / name).read_text(encoding="utf-8"))


def test_archival_acquisition_queue_is_nonpromoting():
    d = j("mahaperiyava_archival_acquisition_queue_v2.json")

    assert d["status"] == (
        "ARCHIVAL_LEADS_PINNED_NO_AUTHORITY_PROMOTION"
    )
    assert len(d["leads"]) == 4
    assert d["promotion_eligible_count"] == 0
    assert d["authority_promotions"] == 0

    assert d["policy"][
        "event_date_is_distinct_from_publication_date"
    ] is True

    assert d["policy"][
        "scan_locator_is_not_a_pinned_scan"
    ] is True

    assert d["policy"][
        "no_authority_change_without_item_level_artifact"
    ] is True

    for lead in d["leads"]:
        assert lead["promotion_readiness"] == "blocked"
        assert (
            lead["authority_effect"]
            == "none_without_item_level_review"
        )


def test_1963_interview_preserves_date_disambiguation():
    d = j("mahaperiyava_archival_acquisition_queue_v2.json")

    lead = next(
        x for x in d["leads"]
        if x["id"] == "archive.illustrated_weekly.1963_interview"
    )

    dates = lead["date_evidence"]

    assert dates["later_kanchi_interview_date_claim"] == "1963-08-11"
    assert dates["scan_locator_publication_issue_date"] == "1963-08-18"
    assert dates["status"] == "date_disambiguation_pending"

    assert (
        lead["artifact_status"]
        == "private_scan_pinned_integrity_verified_visual_issue_review_pending"
    )

    assert lead["promotion_readiness"] == "blocked"

    assert "pinned_artifact" in lead
    assert lead["pinned_artifact"]["redistributable"] is False
    assert len(lead["pinned_artifact"]["sha256"]) == 64
    assert lead["pinned_artifact"]["bytes"] > 100000


def test_bhavans_archive_is_not_misrepresented_as_pinned_issue():
    d = j("mahaperiyava_archival_acquisition_queue_v2.json")

    lead = next(
        x for x in d["leads"]
        if x["id"]
        == "archive.bhavans.1961.what_life_has_taught_me"
    )

    assert lead["date_evidence"]["year"] == "1961"
    assert lead["date_evidence"]["exact_issue"] is None
    assert (
        lead["institutional_archive"]["exact_item_status"]
        == "not_yet_identified"
    )
    assert (
        lead["artifact_status"]
        == "institutional_archive_confirmed_item_unpinned"
    )


def test_1962_tamil_and_1947_original_remain_unlocated():
    d = j("mahaperiyava_archival_acquisition_queue_v2.json")

    rows = {x["id"]: x for x in d["leads"]}

    assert rows[
        "archive.ilayathangudi.1962.tamil_address"
    ]["artifact_status"] == (
        "underlying_tamil_witness_asserted_locator_unresolved"
    )

    assert rows[
        "archive.independence_message.1947.original"
    ]["artifact_status"] == (
        "original_or_near_contemporaneous_artifact_not_located"
    )


def test_registry_no_longer_encodes_unresolved_1963_date_in_id():
    d = j("mahaperiyava_external_source_registry.json")

    ids = {x["id"] for x in d["candidate_queue"]}

    assert "candidate.illustrated_weekly.1963_interview" in ids
    assert (
        "candidate.illustrated_weekly.1963_08_11_interview"
        not in ids
    )

    item = next(
        x for x in d["candidate_queue"]
        if x["id"] == "candidate.illustrated_weekly.1963_interview"
    )

    assert item["date_disambiguation"]["resolved"] is False
