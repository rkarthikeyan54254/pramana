from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data/review"


def j(name):
    return json.loads(
        (R / name).read_text(encoding="utf-8")
    )


def test_1963_adjudication_counts_and_no_promotion():
    d = j(
        "mahaperiyava_1963_interview_adjudication_v1.json"
    )

    assert d["authority_promotions"] == 0

    counts = Counter(
        x["decision"]
        for x in d["decisions"]
    )

    assert counts == Counter({
        "same_teaching": 4,
        "related_teaching": 3,
        "no_same_teaching_candidate": 1,
    })

    assert (
        d["policy"][
            "maximum_possible_authority"
        ]
        == "earlier_witness_supported"
    )


def test_only_same_teaching_pairs_enter_scan_queue():
    adjudication = j(
        "mahaperiyava_1963_interview_adjudication_v1.json"
    )

    queue = j(
        "mahaperiyava_1963_scan_verification_queue_v1.json"
    )

    same = {
        x["external_claim_id"]
        for x in adjudication["decisions"]
        if x["decision"] == "same_teaching"
    }

    queued = {
        x["external_claim_id"]
        for x in queue["items"]
    }

    assert same == queued
    assert len(queued) == 4


def test_scan_queue_records_verified_item_level_promotions():
    q = j(
        "mahaperiyava_1963_scan_verification_queue_v1.json"
    )

    assert q["item_count"] == 4
    assert q["promotion_eligible_count"] == 4
    assert q["authority_promotions"] == 4

    assert (
        q["policy"][
            "editorialized_interview_authority_ceiling"
        ]
        == "earlier_witness_supported"
    )

    assert (
        q["policy"]["primary_source_verified_available"]
        is False
    )

    assert (
        q["publication_date_review"][
            "publication_issue_date"
        ]
        == "1963-08-18"
    )

    assert (
        q["publication_date_review"][
            "publication_issue_date_verified_from_scan"
        ]
        is True
    )

    assert (
        q["publication_date_review"][
            "interview_date_verified_from_scan"
        ]
        is False
    )

    for item in q["items"]:
        assert item["visual_status"] == "verified"
        assert item["page_number"] in {3, 4}
        assert item["article_page_label"] in {"26", "27"}

        assert (
            item["scan_proposition_supported"]
            is True
        )

        assert (
            item["same_teaching_confirmed_after_scan"]
            is True
        )

        assert item["promotion_eligible"] is True
        assert item["promotion_applied"] is True

        assert (
            item["authority_effect"]
            == "promoted_to_earlier_witness_supported"
        )
def test_no_private_source_text_in_review_artifacts():
    files = [
        "mahaperiyava_1963_interview_adjudication_v1.json",
        "mahaperiyava_1963_scan_verification_queue_v1.json",
    ]

    forbidden_keys = {
        "source_text",
        "exact_quote",
        "verbatim_source_text",
        "private_source_excerpt",
        "full_transcript",
    }

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key not in forbidden_keys
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for name in files:
        d = j(name)
        walk(d)

    queue = j(
        "mahaperiyava_1963_scan_verification_queue_v1.json"
    )

    assert (
        queue["policy"][
            "private_source_text_must_not_enter_git"
        ]
        is True
    )
