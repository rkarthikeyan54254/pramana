from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"
SCHEMA = ROOT / "schema" / "mahaperiyava_external_source_item.schema.json"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_external_source_registry_validates_and_is_metadata_only():
    schema = _json(SCHEMA)
    registry = _json(REVIEW / "mahaperiyava_external_source_registry.json")
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )

    assert registry["checkpoint"] == "MAHAPERIYAVA_EXTERNAL_SOURCE_FAMILY_PILOT_V1"
    assert registry["status"] == "SOURCE_FAMILIES_PINNED_NO_AUTHORITY_PROMOTION"
    assert len(registry["items"]) == 7

    ids = set()
    keys = set()

    for item in registry["items"]:
        validator.validate(item)

        assert item["id"] not in ids
        assert item["source_key"] not in keys
        ids.add(item["id"])
        keys.add(item["source_key"])

        if item["id"] == "mahaperiyava.external.1963_as_raman_illustrated_weekly":
            assert item["official_host"] is False
            assert item["host"] == "mahaperiyavaa.blog"
            assert item["acquisition_status"] == "private_research_snapshot_pinned"
            assert item["verbatim_status"] == "editorially_reorganized_not_verbatim"
        else:
            assert item["official_host"] is True
            assert item["host"] == "kamakoti.org"

        assert item["rights"]["source_text_redistribution"] is False
        assert item["rights"]["registry_public_export"] == "metadata_only"
        assert item["authority_effect"] == "none_without_item_level_review"
        assert item["original_artifact_status"] != "verified"

    assert (
        registry["policy"]["primary_source_verified_requires_original_primary_artifact"]
        is True
    )
    assert registry["policy"]["same_source_family_is_not_independent_vote"] is True
    assert registry["policy"]["registry_presence_never_changes_teaching_authority"] is True


def test_representation_boundaries_are_explicit():
    registry = _json(REVIEW / "mahaperiyava_external_source_registry.json")
    rows = {r["id"]: r for r in registry["items"]}

    assert (
        rows["mahaperiyava.external.1962_ilayathangudi_part1"]["verbatim_status"]
        == "translated_not_original_wording"
    )
    assert (
        rows["mahaperiyava.external.1962_ilayathangudi_part2"]["verbatim_status"]
        == "translated_not_original_wording"
    )
    assert (
        rows["mahaperiyava.external.jw_elder_interview_gist"]["verbatim_status"]
        == "gist_not_verbatim"
    )
    assert (
        rows["mahaperiyava.external.acharyas_call_1995_preface"][
            "candidate_for_item_level_crosslink"
        ]
        is False
    )

    p1 = rows["mahaperiyava.external.1962_ilayathangudi_part1"]
    p2 = rows["mahaperiyava.external.1962_ilayathangudi_part2"]
    assert p1["source_family_id"] == p2["source_family_id"]
    assert p1["event"]["id"] == p2["event"]["id"]


def test_pilot_claims_are_nonverbatim_nonpromoting_and_context_aware():
    doc = _json(REVIEW / "mahaperiyava_external_source_pilot_claims.json")
    registry = _json(REVIEW / "mahaperiyava_external_source_registry.json")

    source_ids = {x["id"] for x in registry["items"]}

    assert doc["status"] == "SOURCE_READ_CLAIMS_PENDING_DK_CROSSLINK"
    assert doc["claim_count"] == 12
    assert doc["policy"]["authority_promotions"] == 0
    assert doc["policy"]["source_text_included"] is False

    ids = set()
    for row in doc["claims"]:
        assert row["id"] not in ids
        ids.add(row["id"])

        assert row["source_id"] in source_ids
        assert row["claim_summary"].strip()
        assert row["topics"]
        assert row["source_text_included"] is False
        assert row["authority_effect"] == "none_without_item_level_review"
        assert row["crosslink_status"] == "pending_dk_item_level_review"
        assert row["public_export"] == "none_pending_rights_and_review"

    elder_ahimsa = next(
        x for x in doc["claims"]
        if x["id"] == "external.elder.ahimsa_and_role_specific_duty"
    )
    assert "caste_varna_normative_claim" in elder_ahimsa["flags"]
    assert "violence_requires_context" in elder_ahimsa["flags"]
    assert "political_social_claim_requires_context" in elder_ahimsa["flags"]


def test_external_sources_are_connected_to_lineage_without_authority_inflation():
    registry = _json(REVIEW / "mahaperiyava_external_source_registry.json")
    graph = _json(REVIEW / "mahaperiyava_source_lineage.json")

    relations = {r["id"]: r for r in graph["relations"]}

    expected = {
        "mahaperiyava.lineage.1947.independence_message_official_page",
        "mahaperiyava.lineage.1962.ilayathangudi_part1_official_page",
        "mahaperiyava.lineage.1962.ilayathangudi_part2_official_page",
        "mahaperiyava.lineage.elder_interview.official_gist",
        "mahaperiyava.lineage.1995.acharyas_call_reprint_editing",
    }
    assert expected.issubset(relations)

    registry_keys = {r["source_key"] for r in registry["items"]}
    relation_source_keys = {
        ev["source_key"]
        for rel in graph["relations"]
        for ev in rel["evidence"]
    }
    assert registry_keys.issubset(relation_source_keys)

    for rid in expected:
        rel = relations[rid]
        assert rel["authority_effect"] == "none_without_item_level_review"
        assert rel["evidence_level"] != "exact_text"

    assert graph["authority"] == "UNVERIFIED_ITEM_LEVEL_PROVENANCE"
    assert graph["policy"]["no_primary_source_upgrade_without_item_level_evidence"] is True


def test_candidate_queue_prioritizes_original_or_contemporaneous_artifacts():
    registry = _json(REVIEW / "mahaperiyava_external_source_registry.json")
    queue = registry["candidate_queue"]

    assert len(queue) >= 5
    assert all(x["priority"] == "A" for x in queue)
    ids = {x["id"] for x in queue}

    assert "candidate.the_hindu.1957_60_original_reports" in ids
    assert "candidate.the_hindu.1932_original_reports" in ids
    assert "candidate.bhavans_journal.what_life_has_taught_me" in ids
    assert "candidate.illustrated_weekly.1963_interview" in ids
