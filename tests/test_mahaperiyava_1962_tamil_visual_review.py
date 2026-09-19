from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data/review"

KEY = (
    "kamakoti-ilayathangudi-sadas-"
    "tamil-witness-1962"
)


def j(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def test_three_visual_same_teaching_matches_are_pinned():
    d = j(
        R
        / "mahaperiyava_1962_tamil_visual_review_v1.json"
    )

    assert d["decision_counts"] == {
        "same_teaching": 3,
        "related_teaching": 0,
        "no_same_teaching_candidate": 0,
    }

    assert len(d["items"]) == 3

    for item in d["items"]:
        assert item["decision"] == "same_teaching"
        assert item["visual_status"] == "verified"
        assert item["pdf_pages"]
        assert item["promotion_eligible"] is False
        assert item["source_text_included"] is False


def test_source_identity_is_strong_but_transmission_age_is_not():
    d = j(
        R
        / "mahaperiyava_1962_tamil_visual_review_v1.json"
    )

    s = d["source_identity_review"]

    assert s["visual_identity_confirmed"] is True
    assert s["original_language"] == "Tamil"

    assert (
        s["digital_publication_date_established"]
        is False
    )

    assert (
        s["contemporaneous_1962_artifact_established"]
        is False
    )

    assert (
        s["verbatim_transcript_established"]
        is False
    )


def test_no_authority_promotion_occurs():
    d = j(
        R
        / "mahaperiyava_1962_tamil_visual_review_v1.json"
    )

    assert d["promotion_eligible_count"] == 0
    assert d["authority_promotions"] == 0
    assert d["primary_source_promotions"] == 0

    assert (
        d["policy"][
            "visual_semantic_match_never_grants_authority"
        ]
        is True
    )

    assert (
        d["policy"][
            "original_language_does_not_equal_original_artifact"
        ]
        is True
    )


def test_manifest_contains_hash_pinned_private_witness():
    manifest = j(
        ROOT / "sources/manifest.json"
    )

    src = next(
        x
        for x in manifest["sources"]
        if x["key"] == KEY
    )

    assert len(src["expected_sha256"]) == 64
    assert src["expected_bytes"] > 1000

    assert (
        src["status"]
        == "official-linked-tamil-witness-restricted-pinned-"
           "transmission-age-unresolved"
    )


def test_registry_keeps_representation_fail_closed():
    registry = j(
        R
        / "mahaperiyava_external_source_registry.json"
    )

    row = next(
        x
        for x in registry["items"]
        if x["source_key"] == KEY
    )

    assert row["language"] == "Tamil"

    assert (
        row["representation"]
        == "later_official_web_reproduction"
    )

    assert row["verbatim_status"] == "not_established"

    assert (
        row["original_artifact_status"]
        == "not_located"
    )

    assert (
        row["authority_effect"]
        == "none_without_item_level_review"
    )
