from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]


def _load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_source_lineage_schema_supports_shorthand_without_authority_upgrade():
    schema = _load("schema/source_lineage_relation.schema.json")
    relation_types = schema["properties"]["relation_type"]["enum"]
    assert "shorthand_rendering_of" in relation_types
    assert schema["properties"]["authority_effect"]["const"] == (
        "none_without_item_level_review"
    )


def test_shorthand_relation_is_provisional_and_non_verbatim():
    graph = _load("data/review/mahaperiyava_source_lineage.json")
    relation = next(
        r for r in graph["relations"]
        if r["id"] == "mahaperiyava.lineage.1957_58.acharya_upanyasangal_shorthand"
    )
    assert relation["relation_type"] == "shorthand_rendering_of"
    assert relation["dependency_status"] == "plausible"
    assert relation["status"] == "needs_review"
    assert relation["evidence_level"] == "collection"
    assert relation["authority_effect"] == "none_without_item_level_review"
    assert "not verbatim" in relation["notes"].lower()


def test_historical_witness_acquisition_policy_fails_closed():
    data = _load("data/review/mahaperiyava_historical_witness_acquisition.json")
    assert data["authority"] == "NO_CLAIM_AUTHORITY_UPGRADE_YET"
    assert data["policy"]["shorthand_capture_does_not_equal_verbatim_print"]
    assert data["policy"]["prose_rendering_implies_editorial_normalization"]
    assert data["policy"]["part3_url_must_not_be_guessed"]
    conflict = next(
        f for f in data["provenance_findings"]
        if f["finding"] == "shorthand_manual_publication_year_conflict"
    )
    assert conflict["status"] == "unresolved"
    part3 = next(
        w for w in data["witnesses"]
        if w["id"] == "acharya_upanyasangal_part3"
    )
    assert part3["source_key"] is None
    assert part3["snapshot_status"] == "missing"


def test_historical_scan_manifest_entries_are_private_raw_only():
    manifest = _load("sources/manifest.json")
    by_key = {s["key"]: s for s in manifest["sources"]}
    for key in (
        "acharya-upanyasangal-part1-1957-58-scan",
        "acharya-upanyasangal-part2-1957-58-scan",
    ):
        entry = by_key[key]
        assert entry["path"].startswith("sources/raw/")
        assert "restricted" in entry["status"]
        assert "Do not redistribute" in entry["terms"]


def test_all_lineage_relations_still_validate():
    schema = _load("schema/source_lineage_relation.schema.json")
    graph = _load("data/review/mahaperiyava_source_lineage.json")
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    for relation in graph["relations"]:
        validator.validate(relation)
