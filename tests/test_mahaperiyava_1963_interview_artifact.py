from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW = (
    ROOT
    / "sources/raw/verification/mahaperiyava/"
      "illustrated_weekly_as_raman_1963.pdf"
)


def j(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def manifest_item():
    manifest = j(ROOT / "sources/manifest.json")

    return next(
        x
        for x in manifest["sources"]
        if x["key"]
        == "illustrated-weekly-as-raman-interview-1963-scan"
    )


def test_1963_manifest_pin_is_complete():
    item = manifest_item()

    assert len(item["expected_sha256"]) == 64
    int(item["expected_sha256"], 16)

    assert item["expected_bytes"] > 100000

    assert item["path"] == (
        "sources/raw/verification/mahaperiyava/"
        "illustrated_weekly_as_raman_1963.pdf"
    )

    assert (
        item["status"]
        == "historical-periodical-scan-restricted-pinned-modern-host"
    )

    assert "do not redistribute" in item["terms"].lower()


def test_private_scan_matches_pin_when_present():
    item = manifest_item()

    if not RAW.exists():
        return

    blob = RAW.read_bytes()

    assert blob.startswith(b"%PDF-")
    assert len(blob) == item["expected_bytes"]

    assert (
        hashlib.sha256(blob).hexdigest()
        == item["expected_sha256"]
    )


def test_1963_interview_is_not_misrepresented_as_verbatim():
    registry = j(
        ROOT
        / "data/review/"
          "mahaperiyava_external_source_registry.json"
    )

    item = next(
        x
        for x in registry["items"]
        if x["id"]
        == "mahaperiyava.external.1963_as_raman_illustrated_weekly"
    )

    assert (
        item["independence_from_deivathin_kural"]
        == "independent_event"
    )

    assert (
        item["representation"]
        == "contemporaneous_editorialized_interview"
    )

    assert (
        item["verbatim_status"]
        == "editorially_reorganized_not_verbatim"
    )

    assert (
        item[
            "candidate_authority_if_item_level_provenance_is_satisfied"
        ]
        == "earlier_witness_supported"
    )

    assert (
        item["rights"]["source_text_redistribution"]
        is False
    )


def test_1963_lineage_never_auto_promotes():
    graph = j(
        ROOT
        / "data/review/"
          "mahaperiyava_source_lineage.json"
    )

    rel = next(
        x
        for x in graph["relations"]
        if x["id"]
        == "mahaperiyava.lineage.1963.as_raman_illustrated_weekly"
    )

    assert (
        rel["relation_type"]
        == "contemporaneous_report_of"
    )

    assert (
        rel["dependency_status"]
        == "established"
    )

    assert (
        rel["authority_effect"]
        == "none_without_item_level_review"
    )

    assert rel["evidence_level"] != "exact_text"


def test_1963_acquisition_stays_blocked_until_item_review():
    q = j(
        ROOT
        / "data/review/"
          "mahaperiyava_archival_acquisition_queue_v2.json"
    )

    lead = next(
        x
        for x in q["leads"]
        if x["id"]
        == "archive.illustrated_weekly.1963_interview"
    )

    assert (
        lead["artifact_status"]
        == "private_scan_pinned_integrity_verified_visual_issue_review_pending"
    )

    assert lead["promotion_readiness"] == "blocked"

    assert (
        lead["pinned_artifact"]["redistributable"]
        is False
    )
