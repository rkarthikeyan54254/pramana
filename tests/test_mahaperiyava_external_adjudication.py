from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data/review"


def j(name):
    return json.loads((R / name).read_text(encoding="utf-8"))


def test_external_adjudication_is_semantic_only_and_nonpromoting():
    d = j("mahaperiyava_external_dk_adjudication_v1.json")

    assert d["status"] == (
        "SEMANTIC_ADJUDICATION_COMPLETE_NO_AUTHORITY_CHANGE"
    )
    assert d["authority_promotions"] == 0
    assert d["source_text_included"] is False

    counts = Counter(
        x["decision"]
        for x in d["decisions"]
    )

    assert counts == Counter({
        "same_teaching": 4,
        "related_teaching": 4,
        "no_same_teaching_candidate": 1,
        "compound_needs_atomization": 3,
    })

    assert d["policy"][
        "same_teaching_means_semantic_proposition_match_not_textual_identity"
    ] is True

    assert d["policy"][
        "owner_or_designated_human_approval_required_before_authority_change"
    ] is True


def test_compound_claims_were_atomized_without_creating_evidence():
    atom = j(
        "mahaperiyava_external_source_atomic_claims_v1.json"
    )

    assert atom["claim_count"] == 7
    assert atom["policy"]["authority_promotions"] == 0
    assert atom["policy"]["atomization_does_not_create_new_evidence"] is True

    parents = Counter(
        x["parent_claim_id"]
        for x in atom["claims"]
    )

    assert parents[
        "external.1947.inner_freedom_and_mind_control"
    ] == 2

    assert parents[
        "external.1947.truth_kindness_and_social_amity"
    ] == 3

    assert parents[
        "external.elder.truthfulness_and_limits_on_consumption"
    ] == 2

    assert all(
        x["source_text_included"] is False
        for x in atom["claims"]
    )

    assert all(
        x["authority_effect"]
        == "none_without_item_level_review"
        for x in atom["claims"]
    )


def test_provenance_review_blocks_promotion_until_stronger_artifact():
    p = j(
        "mahaperiyava_external_source_provenance_review_v1.json"
    )

    assert (
        p["status"]
        == "SEMANTIC_CORROBORATION_PRESENT_PROMOTION_BLOCKED"
    )

    assert p["authority_promotions"] == 0
    assert len(p["items"]) == 4

    assert all(
        x["promotion_readiness"] == "blocked"
        for x in p["items"]
    )

    assert all(
        x["original_artifact_status"] == "not_located"
        for x in p["items"]
    )

    assert p["policy"]["event_date_is_not_witness_date"] is True
    assert p["policy"][
        "later_web_reproduction_is_not_automatically_an_earlier_witness"
    ] is True
    assert p["policy"][
        "original_or_near_contemporaneous_artifact_required_for_promotion_review"
    ] is True


def test_atomic_crosslink_matrix_is_nonpromoting():
    d = j(
        "mahaperiyava_external_atomic_dk_crosslink_candidates_v1.json"
    )

    assert (
        d["status"]
        == "ATOMIC_CANDIDATES_READY_FOR_SEMANTIC_REVIEW"
    )

    assert d["claim_count"] == 7
    assert d["authority_promotions"] == 0

    for row in d["rows"]:
        assert row["authority_promotions"] == 0
        assert row["source_text_included"] is False

        for c in row["candidates"]:
            assert c["decision"] == "unreviewed"
            assert (
                c["authority_effect"]
                == "none_without_item_level_review"
            )


def test_no_private_source_text_markers_enter_new_review_artifacts():
    names = (
        "mahaperiyava_external_dk_adjudication_v1.json",
        "mahaperiyava_external_source_atomic_claims_v1.json",
        "mahaperiyava_external_source_provenance_review_v1.json",
        "mahaperiyava_external_atomic_dk_crosslink_candidates_v1.json",
    )

    forbidden = (
        "exact_text_restricted",
        "private_curation_blocks:",
        "paragraph_sha256=",
        "source_packet_sha256=",
    )

    for name in names:
        text = (R / name).read_text(
            encoding="utf-8"
        ).casefold()

        for marker in forbidden:
            assert marker.casefold() not in text
