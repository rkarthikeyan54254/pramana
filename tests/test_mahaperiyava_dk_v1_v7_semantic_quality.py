from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"

BAD = (
    "This teaching centers on",
    "develops a distinct step",
)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_v1_v7_have_a_closed_semantic_frontier_without_publication_promotion():
    v1 = _json(REVIEW / "mahaperiyava_dk_v1_release_checkpoint.json")
    assert v1["status"] == "PASS"
    assert v1["counts"]["chapters"] == 175
    assert v1["guardrails"]["no_exact_source_text_in_tracked_teaching_records"] is True
    assert v1["guardrails"]["authority_not_auto_upgraded"] is True
    assert v1["guardrails"]["publication_review_still_required"] is True

    expected_chapters = {2:225, 3:289, 4:450, 5:298, 6:208, 7:342}
    for volume, chapters in expected_chapters.items():
        audit = _json(REVIEW / f"mahaperiyava_deivathin_kural_v{volume}_semantic_completion_audit.json")
        assert audit["result"] == "PASS"
        checks = audit["checks"]
        assert checks["chapter_count"] == chapters
        unaccounted = checks.get(
            "unaccounted_curation_paragraph_count",
            checks.get("unaccounted_source_paragraph_count"),
        )
        assert unaccounted == 0
        assert checks.get("primary_source_verified_count", 0) == 0
        if volume >= 4:
            assert checks["publication_approved"] is False
            assert checks["generic_template_summary_count"] == 0
            assert checks["exact_restricted_paragraph_leak_count"] == 0


def test_v2_v7_record_ids_are_unique_and_authority_promotions_are_allowlisted():
    promoted = {
        "mahaperiyava.deivathin_kural.v2.c206.knowledge_is_to_be_grounded_in_character_and_religious_discipline_before_broad_intellectual_exploration",
        "mahaperiyava.deivathin_kural.v3.c110.ritual_observances_shared_across_different_doctrines_preparatory",
    }

    ids = set()
    seen_promoted = set()

    for volume in range(2, 8):
        rows = _jsonl(
            REVIEW
            / f"mahaperiyava_deivathin_kural_v{volume}_teaching_records.jsonl"
        )

        for row in rows:
            assert row["id"] not in ids
            ids.add(row["id"])

            authority = row["evidence_status"]["authority"]

            if row["id"] in promoted:
                assert authority == "earlier_witness_supported"
                seen_promoted.add(row["id"])

                witnesses = [
                    witness
                    for witness in row.get("provenance", [])
                    if witness.get("source_key")
                    == "illustrated-weekly-as-raman-interview-1963-scan"
                ]

                assert len(witnesses) == 1

                witness = witnesses[0]

                assert witness["witness_role"] == "earlier_secondary"
                assert witness["locus"]
                assert len(witness["snapshot_sha256"]) == 64
                assert (
                    witness["rights_status"]
                    == "restricted_private_research"
                )

                assert (
                    row["attribution"]["wording_status"]
                    == "earlier_witness_agrees"
                )
            else:
                assert authority == "dk_attested"

            assert (
                row["evidence_status"]["print_check"]
                == "not_checked"
            )

            assert (
                row["evidence_status"]["primary_source_status"]
                == "unknown"
            )

            assert "exact_text_restricted" not in row

            summary = row.get("claim_summary") or ""
            assert summary.strip()

            assert not any(
                x.lower() in summary.lower()
                for x in BAD
            )

    assert seen_promoted == promoted
def test_v4_v7_are_source_read_hardened_and_not_publication_approved():
    for volume in range(4, 8):
        index = _json(REVIEW / f"mahaperiyava_deivathin_kural_v{volume}_curation_index.json")
        manifest = _json(REVIEW / f"mahaperiyava_deivathin_kural_v{volume}_curator_manifest.json")
        assert index["semantic_status"] == "source_read_semantic_hardened_not_publication_approved"
        assert manifest["semantic_status"] == "source_read_semantic_hardened_not_publication_approved"
        assert index["source_coverage"]["all_curation_paragraphs_accounted_for"] is True
        assert index["source_coverage"]["unaccounted_curation_paragraphs"] == 0
        assert manifest["policy"]["human_publication_review_still_required"] is True
        assert all(u["historical_witness"] is None for u in index["units"])
