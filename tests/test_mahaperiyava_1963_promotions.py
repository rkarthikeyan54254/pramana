from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ask_mahaperiyava import load_corpus
from scripts.validate_mahaperiyava_evidence_depth import validate_review_item


def j(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_four_visual_reviews_are_complete():
    q = j(
        ROOT
        / "data/review/"
          "mahaperiyava_1963_scan_verification_queue_v1.json"
    )

    assert q["promotion_eligible_count"] == 4
    assert q["authority_promotions"] == 4

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
        assert item["scan_proposition_supported"] is True
        assert (
            item["same_teaching_confirmed_after_scan"]
            is True
        )
        assert item["promotion_eligible"] is True
        assert item["promotion_applied"] is True


def test_promotion_reviews_are_valid_item_level_reviews():
    d = j(
        ROOT
        / "data/review/"
          "mahaperiyava_1963_promotion_reviews_v1.json"
    )

    assert d["review_count"] == 4
    assert d["authority_promotions"] == 4
    assert d["primary_source_promotions"] == 0

    for review in d["reviews"]:
        assert validate_review_item(review)
        assert review["decision"] == "supported"
        assert review["authority_before"] == "dk_attested"
        assert (
            review["authority_after"]
            == "earlier_witness_supported"
        )
        assert (
            review["guardrails"]["verbatim_wording_claimed"]
            is False
        )


def test_corpus_has_exactly_four_new_earlier_witness_promotions():
    rows = load_corpus()
    by = {x["id"]: x for x in rows}

    expected = {
        "mahaperiyava.deivathin_kural.v2.c206.knowledge_is_to_be_grounded_in_character_and_religious_discipline_before_broad_intellectual_exploration",
        "mahaperiyava.deivathin_kural.v1.sadangugal.ritual_cultivates_concentration_and_discipline",
        "mahaperiyava.deivathin_kural.v1.advaitamum_anu_vignaanamum.science_matter_energy_unity_as_analogy",
        "mahaperiyava.deivathin_kural.v3.c110.ritual_observances_shared_across_different_doctrines_preparatory",
    }

    for rid in expected:
        row = by[rid]

        assert (
            row["evidence_status"]["authority"]
            == "earlier_witness_supported"
        )

        assert (
            row["evidence_status"]["primary_source_status"]
            != "verified"
        )

        witnesses = [
            p
            for p in row["provenance"]
            if p.get("source_key")
            == "illustrated-weekly-as-raman-interview-1963-scan"
        ]

        assert len(witnesses) == 1
        witness = witnesses[0]

        assert witness["witness_role"] == "earlier_secondary"
        assert len(witness["snapshot_sha256"]) == 64
        assert witness["locus"]
        assert (
            witness["rights_status"]
            == "restricted_private_research"
        )

    counts = Counter(
        x["evidence_status"]["authority"]
        for x in rows
    )

    assert counts["dk_attested"] == 3331
    assert counts["earlier_witness_supported"] == 37
    assert counts["primary_source_verified"] == 0


def test_current_state_matches_promoted_corpus():
    s = j(
        ROOT
        / "data/review/"
          "mahaperiyava_evidence_depth_current_state.json"
    )

    assert s["authority_counts"] == {
        "dk_attested": 3331,
        "earlier_witness_supported": 37,
        "dk_print_checked": 0,
        "primary_source_verified": 0,
    }

    assert s["foundation_earlier_witness_supported"] == 33
    assert s["new_1963_raman_promotions"] == 4
    assert s["publication_approved"] is False
