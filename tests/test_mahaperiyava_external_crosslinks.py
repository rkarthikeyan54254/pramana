from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_external_dk_crosslink_generator_is_bounded_and_nonpromoting():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "matrix.json"

        subprocess.run(
            [
                sys.executable,
                str(
                    ROOT
                    / "scripts/"
                    "crosslink_mahaperiyava_external_claims.py"
                ),
                "--output",
                str(out),
                "--top-k",
                "10",
            ],
            check=True,
        )

        report = _json(out)

        assert (
            report["status"]
            == "CANDIDATE_MATRIX_READY_FOR_ITEM_LEVEL_REVIEW"
        )
        assert report["input_claim_count"] == 12
        assert report["top_k"] == 10
        assert report["authority_promotions"] == 0
        assert report["source_text_included"] is False

        assert (
            report["policy"][
                "machine_retrieval_never_grants_equivalence"
            ]
            is True
        )
        assert (
            report["policy"][
                "candidate_generation_never_changes_authority"
            ]
            is True
        )
        assert (
            report["policy"]["human_same_claim_review_required"]
            is True
        )

        ids = set()

        for row in report["rows"]:
            assert row["external_claim_id"] not in ids
            ids.add(row["external_claim_id"])

            assert row["human_review_status"] == "pending"
            assert row["authority_promotions"] == 0
            assert row["source_text_included"] is False
            assert row["candidate_count"] <= 10

            for candidate in row["candidates"]:
                assert candidate["machine_role"] == "candidate_only"
                assert candidate["human_decision"] == "unreviewed"
                assert (
                    candidate["authority_effect"]
                    == "none_without_item_level_review"
                )
                assert candidate["dk_teaching_id"].startswith(
                    "mahaperiyava.deivathin_kural.v"
                )


def test_tracked_crosslink_matrix_matches_inputs_and_has_no_decisions():
    report = _json(
        REVIEW
        / "mahaperiyava_external_dk_crosslink_candidates.json"
    )
    claims = _json(
        REVIEW
        / "mahaperiyava_external_source_pilot_claims.json"
    )

    assert report["input_claim_count"] == claims["claim_count"] == 12
    assert len(report["rows"]) == 12
    assert report["authority_promotions"] == 0

    for row in report["rows"]:
        assert row["human_review_status"] == "pending"

        for candidate in row["candidates"]:
            assert candidate["human_decision"] == "unreviewed"


def test_crosslink_matrix_preserves_source_family_and_representation():
    report = _json(
        REVIEW
        / "mahaperiyava_external_dk_crosslink_candidates.json"
    )

    rows = {
        x["external_claim_id"]: x
        for x in report["rows"]
    }

    ilayathangudi = [
        row
        for row in rows.values()
        if row["source_family_id"]
        == "family.mahaperiyava.1962_ilayathangudi_sadas"
    ]

    assert ilayathangudi

    assert all(
        x["source_representation"]
        == "translated_official_web_transcription"
        for x in ilayathangudi
    )

    assert all(
        x["source_verbatim_status"]
        == "translated_not_original_wording"
        for x in ilayathangudi
    )

    elder = [
        row
        for row in rows.values()
        if row["source_family_id"]
        == "family.mahaperiyava.jw_elder_interview"
    ]

    assert elder

    assert all(
        x["source_verbatim_status"] == "gist_not_verbatim"
        for x in elder
    )


def test_candidate_matrix_contains_no_private_or_exact_source_text_fields():
    path = (
        REVIEW
        / "mahaperiyava_external_dk_crosslink_candidates.json"
    )

    text = path.read_text(encoding="utf-8").casefold()

    for forbidden in (
        "exact_text_restricted",
        "private_curation_blocks:",
        "paragraph_sha256=",
        "source_packet_sha256=",
    ):
        assert forbidden not in text
