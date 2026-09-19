from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data/review"

sys.path.insert(0, str(ROOT))

from scripts.ask_mahaperiyava import load_corpus
from scripts.validate_mahaperiyava_evidence_depth import (
    validate_review_item,
)

SOURCE_KEY = "preceptors-of-advaita-1968-scan"

TEMPLE = (
    "mahaperiyava.deivathin_kural.v1."
    "alayamum_deivika_kalaigalum."
    "preserving_temple_presence_and_arts_benefits_society"
)

UNITY = (
    "mahaperiyava.deivathin_kural.v1."
    "bhagavan_yaar_bhagavatpadhar_badhil."
    "ishta_devata_without_denigration_and_reciprocal_worship"
)

EPIC = (
    "mahaperiyava.deivathin_kural.v1."
    "maha_bharatham."
    "repeated_epic_hearing_shapes_moral_imagination"
)

PROMOTED = {
    TEMPLE,
    UNITY,
}


def j(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def test_1968_visual_review_has_two_promotions_and_one_hold():
    d = j(
        R
        / "mahaperiyava_preceptors_of_advaita_1968_visual_review_v1.json"
    )

    assert d["source_key"] == SOURCE_KEY
    assert d["source_text_included"] is False

    assert d["decision_counts"] == {
        "same_teaching": 2,
        "related_teaching": 1,
        "no_same_teaching_candidate": 0,
    }

    assert d["promotion_eligible_count"] == 2
    assert d["authority_promotions"] == 2
    assert d["primary_source_promotions"] == 0

    by = {
        x["dk_teaching_id"]: x
        for x in d["items"]
    }

    assert set(by) == {
        TEMPLE,
        UNITY,
        EPIC,
    }

    for rid in PROMOTED:
        assert by[rid]["decision"] == "same_teaching"
        assert by[rid]["visual_status"] == "verified"
        assert by[rid]["promotion_eligible"] is True

    assert by[EPIC]["decision"] == "related_teaching"
    assert by[EPIC]["promotion_eligible"] is False


def test_two_formal_reviews_pass_evidence_depth_schema():
    d = j(
        R
        / "mahaperiyava_preceptors_of_advaita_1968_promotion_reviews_v1.json"
    )

    assert d["review_count"] == 2
    assert d["authority_promotions"] == 2
    assert d["primary_source_promotions"] == 0

    assert {
        x["teaching_id"]
        for x in d["reviews"]
    } == PROMOTED

    for review in d["reviews"]:
        assert validate_review_item(review)

        assert review["authority_before"] == "dk_attested"
        assert (
            review["authority_after"]
            == "earlier_witness_supported"
        )
        assert review["decision"] == "supported"

        ev = review["evidence"]
        assert len(ev) == 1
        assert ev[0]["source_key"] == SOURCE_KEY
        assert ev[0]["witness_role"] == "earlier_secondary"
        assert ev[0]["match_level"] == "same_claim"
        assert (
            ev[0]["relation_to_dk"]
            == "earlier_attestation"
        )

        assert (
            review["guardrails"]["verbatim_wording_claimed"]
            is False
        )
        assert (
            review["guardrails"][
                "primary_source_claimed_without_primary_evidence"
            ]
            is False
        )


def test_corpus_contains_exactly_two_preceptors_promotions():
    rows = load_corpus()
    by = {
        x["id"]: x
        for x in rows
    }

    for rid in PROMOTED:
        row = by[rid]

        assert (
            row["evidence_status"]["authority"]
            == "earlier_witness_supported"
        )

        assert (
            row["evidence_status"]["primary_source_status"]
            == "unknown"
        )

        assert (
            row["attribution"]["wording_status"]
            == "earlier_witness_agrees"
        )

        witnesses = [
            x
            for x in row["provenance"]
            if x.get("source_key") == SOURCE_KEY
        ]

        assert len(witnesses) == 1

        w = witnesses[0]

        assert w["witness_role"] == "earlier_secondary"
        assert len(w["snapshot_sha256"]) == 64
        assert w["locus"]
        assert (
            w["rights_status"]
            == "restricted_private_research"
        )

    # Deliberate negative control.
    assert (
        by[EPIC]["evidence_status"]["authority"]
        == "dk_attested"
    )

    assert not any(
        x.get("source_key") == SOURCE_KEY
        for x in by[EPIC]["provenance"]
    )

    counts = Counter(
        x["evidence_status"]["authority"]
        for x in rows
    )

    assert counts["dk_attested"] == 3329
    assert counts["earlier_witness_supported"] == 39
    assert counts["dk_print_checked"] == 0
    assert counts["primary_source_verified"] == 0


def test_curation_indexes_are_synchronized():
    found = set()
    touched_files = set()

    for path in R.glob(
        "mahaperiyava*curation_index.json"
    ):
        d = j(path)

        file_has_1968_witness = False

        for unit in d.get("units", []):
            witness = unit.get(
                "historical_witness"
            )

            if not isinstance(
                witness,
                dict,
            ):
                continue

            if (
                witness.get("source_key")
                != SOURCE_KEY
            ):
                continue

            file_has_1968_witness = True

            assert (
                unit["authority"]
                == "earlier_witness_supported"
            )

            assert (
                witness["witness_role"]
                == "earlier_secondary"
            )

            assert (
                witness["match_level"]
                == "same_claim"
            )

            assert len(
                witness["snapshot_sha256"]
            ) == 64

            found.add(
                unit["id"]
            )

        if file_has_1968_witness:
            touched_files.add(path.name)

            actual = Counter(
                x["authority"]
                for x in d.get("units", [])
            )

            if "authority_counts" in d:
                assert (
                    d["authority_counts"]
                    == dict(actual)
                )

    assert found == PROMOTED

    # Exactly two V1 curation indexes are touched:
    # C102 and C142 live in different V1 batches.
    assert len(touched_files) == 2
def test_current_state_and_volume1_counts_are_current():
    d = j(
        R
        / "mahaperiyava_evidence_depth_current_state.json"
    )

    assert d["authority_counts"] == {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
        "dk_print_checked": 0,
        "primary_source_verified": 0,
    }

    assert d["foundation_earlier_witness_supported"] == 33
    assert d["new_1963_raman_promotions"] == 4
    assert d["new_1968_preceptors_promotions"] == 2

    assert d["volume_authority_counts"]["1"] == {
        "dk_attested": 890,
        "earlier_witness_supported": 37,
    }

    assert d["publication_approved"] is False


def test_manifest_and_registry_preserve_secondary_source_boundary():
    manifest = j(
        ROOT / "sources/manifest.json"
    )

    src = next(
        x
        for x in manifest["sources"]
        if x["key"] == SOURCE_KEY
    )

    assert (
        src["expected_sha256"]
        == "660397607107975459f04ada26d58120506d03d30831ee6eb82bf8709049c388"
    )

    assert src["expected_bytes"] == 42482043

    registry = j(
        R
        / "mahaperiyava_external_source_registry.json"
    )

    item = next(
        x
        for x in registry["items"]
        if x["source_key"] == SOURCE_KEY
    )

    assert item["official_host"] is False

    assert (
        item["source_kind"]
        == "near_contemporary_biographical_monograph"
    )

    assert (
        item["representation"]
        == "near_contemporary_secondary_synthesis"
    )

    assert (
        item["candidate_authority_if_item_level_provenance_is_satisfied"]
        == "earlier_witness_supported"
    )

    assert (
        item["authority_effect"]
        == "none_without_item_level_review"
    )

    assert (
        item["rights"]["source_text_redistribution"]
        is False
    )
