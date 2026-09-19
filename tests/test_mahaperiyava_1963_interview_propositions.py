from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data/review"


def j(name):
    return json.loads(
        (R / name).read_text(encoding="utf-8")
    )


def test_1963_propositions_are_public_safe_and_unpromoted():
    d = j(
        "mahaperiyava_1963_interview_propositions_v1.json"
    )

    assert d["claim_count"] == 8
    assert d["policy"]["authority_promotions"] == 0
    assert (
        d["policy"][
            "visual_scan_locus_required_before_promotion"
        ]
        is True
    )
    assert (
        d["policy"][
            "authority_ceiling_after_successful_item_review"
        ]
        == "earlier_witness_supported"
    )

    for row in d["claims"]:
        assert row["source_text_included"] is False
        assert row["scan_locus_verified"] is False
        assert (
            row["authority_effect"]
            == "none_without_item_level_review"
        )


def test_1963_candidate_matrix_never_promotes():
    d = j(
        "mahaperiyava_1963_interview_dk_candidates_v1.json"
    )

    assert d["claim_count"] == 8
    assert d["authority_promotions"] == 0

    for row in d["rows"]:
        assert row["authority_promotions"] == 0

        for c in row["candidates"]:
            assert c["decision"] == "unreviewed"
            assert c["scan_locus_verified"] is False
            assert (
                c["authority_effect"]
                == "none_without_item_level_review"
            )


def test_sensitive_propositions_keep_context_flags():
    d = j(
        "mahaperiyava_1963_interview_propositions_v1.json"
    )

    rows = {
        x["id"]: x
        for x in d["claims"]
    }

    law = rows[
        "external.1963.raman.inner_virtue_beyond_legislation"
    ]

    assert (
        "political_social_claim_requires_context"
        in law["flags"]
    )

    science = rows[
        "external.1963.raman.energy_advaita_analogy"
    ]

    assert (
        "science_religion_analogy_not_equivalence"
        in science["flags"]
    )

    assert (
        "scientific_claim_requires_external_verification"
        in science["flags"]
    )
