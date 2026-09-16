#!/usr/bin/env python3
"""
tests/test_apply_dk_curator_manifest.py

Comprehensive tests for scripts/apply_dk_curator_manifest.py.

Verifies:
- deterministic output
- idempotency
- schema-compliant records
- no source text leakage
- exact curator claim summaries retained
- exact question intents retained
- exact topics retained
- exact flags retained
- exact paragraph IDs/hashes retained
- explicit exclusion handling
- overlap permitted
- source anomalies preserved
- queue updates scoped only to target ordinals
- dry-run changes nothing
- check changes nothing
- apply changes only approved paths
- synthetic test manifest overlapping pilot chapter 100:
    * tool detects the overlap
    * tool reports existing authority distribution
    * tool refuses automatic replacement
    * stronger pilot evidence cannot be silently downgraded
    * approved carry-forward artifact is required
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Dict

import pytest

# Dynamic import to support execution via pytest or direct python runner
ROOT = Path(__file__).resolve().parents[1]
APPLIER_SCRIPT = ROOT / "scripts/apply_dk_curator_manifest.py"

spec = importlib.util.spec_from_file_location("apply_dk_curator_manifest", APPLIER_SCRIPT)
applier_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(applier_mod)

DKManifestApplier = applier_mod.DKManifestApplier

MANIFEST_066_085 = ROOT / "data/review/mahaperiyava_dk_v1_batch_066_085_curator_manifest.json"
SCHEMA_FILE = ROOT / "schema/teaching_record.schema.json"
QUEUE_FILE = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"
PILOT_FILE = ROOT / "data/review/mahaperiyava_dk_v1_pilot_teaching_records.jsonl"


def _make_066_085_carry_forward() -> Dict[str, Any]:
    return {
        "version": "1.0",
        "curator": "human_curator",
        "approved": True,
        "batch": "066_085",
        "chapter_decisions": [
            {
                "chapter_ordinal": 68,
                "action": "replace_with_batch",
                "curator_note": "Pilot records are dk_attested without stronger witnesses; full batch units supersede them.",
            },
            {
                "chapter_ordinal": 85,
                "action": "replace_with_batch",
                "curator_note": "Pilot records are dk_attested without stronger witnesses; full batch units supersede them.",
            },
        ],
    }


def test_deterministic_output():
    """Verify that generating records and curation index twice produces identical output."""
    with tempfile.TemporaryDirectory() as td:
        cf_path = Path(td) / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))

        applier1 = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=Path(td) / "run1",
        )
        applier2 = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=Path(td) / "run2",
        )

        recs1 = applier1.generate_teaching_records()
        recs2 = applier2.generate_teaching_records()
        assert recs1 == recs2, "Records must be deterministically identical"

        idx1 = applier1.generate_curation_index(timestamp="2026-09-16T00:00:00+00:00")
        idx2 = applier2.generate_curation_index(timestamp="2026-09-16T00:00:00+00:00")
        assert idx1 == idx2, "Curation index must be deterministically identical"


def test_idempotency():
    """Verify that running apply multiple times leaves output files identical and stable."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cf_path = td_path / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))
        out_dir = td_path / "out"

        applier = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=out_dir,
        )

        assert applier.run("apply") == 0

        rec_file = out_dir / "mahaperiyava_dk_v1_batch_066_085_teaching_records.jsonl"
        idx_file = out_dir / "mahaperiyava_dk_v1_batch_066_085_curation_index.json"
        q_file = out_dir / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"

        first_rec_content = rec_file.read_text(encoding="utf-8")
        first_idx_content = idx_file.read_text(encoding="utf-8")
        first_q_content = q_file.read_text(encoding="utf-8")

        # Second apply run
        applier_second = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=out_dir,
        )
        assert applier_second.run("apply") == 0

        assert rec_file.read_text(encoding="utf-8") == first_rec_content
        assert idx_file.read_text(encoding="utf-8") == first_idx_content
        assert q_file.read_text(encoding="utf-8") == first_q_content


def test_schema_compliant_records():
    """Verify all generated teaching records strictly conform to repository schema."""
    import jsonschema

    with tempfile.TemporaryDirectory() as td:
        cf_path = Path(td) / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))

        applier = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=Path(td) / "out",
        )

        schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)

        records = applier.generate_teaching_records()
        assert len(records) == 110

        for r in records:
            errors = list(validator.iter_errors(r))
            assert not errors, f"Record {r['id']} schema error: {[e.message for e in errors]}"


def test_no_source_text_leakage():
    """Verify no restricted source text exists in generated records or curation index."""
    with tempfile.TemporaryDirectory() as td:
        cf_path = Path(td) / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))

        applier = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=Path(td) / "out",
        )

        records = applier.generate_teaching_records()
        for r in records:
            assert "text" not in r
            assert "exact_text_restricted" not in r
            assert "raw_text" not in r
            assert r["rights"]["source_text_tier"] == "restricted"
            assert r["rights"]["public_export"] == "metadata_only"
            assert "historical_witness" not in r
            assert "candidate_witness" not in r

        index = applier.generate_curation_index()
        assert index["policy"]["no_exact_source_text_in_tracked_artifacts"] is True
        assert index["policy"]["claim_summaries_are_not_quotes"] is True


def test_exact_curator_metadata_retained():
    """Verify exact claim summaries, question intents, topics, and flags are retained."""
    manifest_data = json.loads(MANIFEST_066_085.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        cf_path = Path(td) / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))

        applier = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=Path(td) / "out",
        )

        records = applier.generate_teaching_records()
        index = applier.generate_curation_index()

        for u_manifest, r_gen, u_index in zip(manifest_data["units"], records, index["units"]):
            # Claim summaries
            assert r_gen["claim_summary"] == u_manifest["claim_summary"]
            assert u_index["claim_summary"] == u_manifest["claim_summary"]

            # Question intents
            assert u_index["question_intents"] == u_manifest["question_intents"]

            # Topics
            assert r_gen["topics"] == u_manifest["topics"]
            assert u_index["topics"] == u_manifest["topics"]

            # Flags
            assert r_gen["flags"] == u_manifest["flags"]
            assert u_index["flags"] == u_manifest["flags"]

            # Paragraph IDs & hashes
            p_ids = ",".join(u_manifest["source_paragraph_ids"])
            p_hashes = ",".join(u_manifest["source_paragraph_hashes"])
            assert f"paragraph(s) {p_ids}" in r_gen["provenance"][0]["locus"]
            assert f"paragraph_sha256={p_hashes}" in r_gen["curator_notes"]


def test_overlap_permitted_and_not_forced_exact_once():
    """Verify multi-unit paragraph usage (overlap) is permitted per repository policy."""
    manifest_data = json.loads(MANIFEST_066_085.read_text(encoding="utf-8"))
    # In Chapter 70, p005 is used in two separate units (intentional semantic overlap)
    units_with_p005 = [
        u for u in manifest_data["units"]
        if u["chapter_ordinal"] == 70 and "p005" in u["source_paragraph_ids"]
    ]
    assert len(units_with_p005) == 2, "Fixture must contain overlapping paragraph"

    with tempfile.TemporaryDirectory() as td:
        cf_path = Path(td) / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))

        applier = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=Path(td) / "out",
        )
        assert applier.run("check") == 0


def test_explicit_exclusion_handling():
    """Verify explicit exclusions are preserved without reinterpretation."""
    manifest_data = json.loads(MANIFEST_066_085.read_text(encoding="utf-8"))
    manifest_data["counts"]["explicitly_excluded_source_paragraphs"] = 2
    manifest_data["policy"]["source_paragraph_accounting"] = "at_least_once_or_explicitly_excluded"

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        man_path = td_path / "manifest.json"
        man_path.write_text(json.dumps(manifest_data))

        cf_path = td_path / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))

        applier = DKManifestApplier(
            manifest_path=man_path,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=td_path / "out",
        )
        index = applier.generate_curation_index()
        assert index["source_coverage"]["excluded_source_blocks"] == 2
        assert index["source_coverage"]["coverage_mode"] == "at_least_once_or_explicitly_excluded"


def test_source_anomalies_preserved():
    """Verify source anomalies in manifest are preserved in curation index."""
    manifest_data = json.loads(MANIFEST_066_085.read_text(encoding="utf-8"))
    manifest_data["source_anomalies"] = [
        {
            "chapter_ordinal": 68,
            "anomaly_type": "title_spelling_variation",
            "source_value": "எளிய வாழ்வு",
            "note": "Preserved exactly pending curator QC.",
        }
    ]

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        man_path = td_path / "manifest.json"
        man_path.write_text(json.dumps(manifest_data))

        cf_path = td_path / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))

        applier = DKManifestApplier(
            manifest_path=man_path,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=td_path / "out",
        )
        index = applier.generate_curation_index()
        assert index["source_anomalies"] == manifest_data["source_anomalies"]


def test_queue_updates_scoped_only_to_target_ordinals():
    """Verify extraction queue updates touch only targeted chapter ordinals."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cf_path = td_path / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))

        out_dir = td_path / "out"
        applier = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=out_dir,
        )

        original_queue = [
            json.loads(line)
            for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        updated_queue = applier.update_extraction_queue(original_queue)
        target_ordinals = set(range(66, 86))

        for orig_row, updated_row in zip(original_queue, updated_queue):
            ord_val = orig_row["ordinal"]
            if ord_val not in target_ordinals:
                assert orig_row == updated_row, f"Row {ord_val} outside target range was modified"
            else:
                if orig_row.get("pilot"):
                    # Pilot chapters 68 and 85 retain pilot queue status by default
                    assert updated_row["pilot"] is True
                else:
                    assert updated_row["stage"] == "batch_teaching_units_curated"


def test_dry_run_and_check_change_nothing():
    """Verify --dry-run and --check do not write or modify any files."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cf_path = td_path / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))
        out_dir = td_path / "out"

        applier = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=out_dir,
        )

        assert applier.run("check") == 0
        assert not out_dir.exists(), "--check must not create output directory"

        assert applier.run("dry-run") == 0
        assert not out_dir.exists(), "--dry-run must not create output directory"


def test_apply_changes_only_approved_paths():
    """Verify --apply writes only teaching_records, curation_index, and extraction_queue."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cf_path = td_path / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))
        out_dir = td_path / "out"

        applier = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=out_dir,
        )

        assert applier.run("apply") == 0
        files = {p.name for p in out_dir.iterdir()}
        expected_files = {
            "mahaperiyava_dk_v1_batch_066_085_teaching_records.jsonl",
            "mahaperiyava_dk_v1_batch_066_085_curation_index.json",
            "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl",
        }
        assert files == expected_files, f"Unexpected files written: {files - expected_files}"


def test_pilot_overlap_detection_chapter_100_fails_closed():
    """
    Synthetic regression test for Pilot Overlap Guard on Chapter 100:
    - Chapter 100 exists in pilot records with earlier_witness_supported records
    - Tool MUST detect overlap
    - Tool MUST report existing authority distribution
    - Tool MUST refuse automatic replacement without carry-forward artifact
    - Tool MUST refuse carry-forward artifact that attempts silent downgrade
    - Tool MUST succeed when carry-forward explicitly accounts for stronger evidence

    This test is SELF-CONTAINED - it creates a synthetic pilot file with Chapter 100
    records in a temporary directory, so it does not depend on production pilot state.
    """
    # Create synthetic manifest for chapter 100 (synthetic batch_100_100)
    synthetic_manifest = {
        "version": "1.0",
        "corpus": "mahaperiyava_teachings",
        "work": "deivathin_kural",
        "volume": 1,
        "batch": "100_100",
        "source_packet": {
            "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "chapter_count": 1,
            "paragraph_count": 10,
        },
        "chapters": [
            {
                "ordinal": 100,
                "title_ta": "ஆலய வழிபாடு",
                "url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                "source_key": "kamakoti-dk-v1-part1kurall08",
                "snapshot_sha256": "1111222233334444555566667777888811112222333344445555666677778888",
            }
        ],
        "units": [
            {
                "id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.synthetic_unit_1",
                "chapter_ordinal": 100,
                "chapter_slug": "alaya_vazhipadu",
                "unit_slug": "synthetic_unit_1",
                "claim_summary": "Synthetic summary for chapter 100 testing.",
                "question_intents": ["What is temple worship purpose?"],
                "source_paragraph_ids": ["p001"],
                "source_paragraph_hashes": ["hash001"],
                "topics": ["temple_worship"],
                "flags": ["traditional_normative_claim"],
                "authority": "dk_attested",
            }
        ],
    }

    # Create synthetic pilot records for chapter 100 that simulate the old state
    # with 6 records: 3 dk_attested + 3 earlier_witness_supported (with earlier_secondary provenance)
    synthetic_pilot_records = [
        {
            "id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.pilot_unit_1",
            "corpus": "mahaperiyava_teachings",
            "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati",
            "compiler": "ra_ganapathi",
            "language": "tamil",
            "source_locus": {
                "volume": 1,
                "section_title_ta": None,
                "chapter_title_ta": "alaya vazhipadu",
                "chapter_ordinal": 100,
                "print_edition": None,
                "print_page_start": None,
                "print_page_end": None,
                "digital_url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                "digital_anchor": None,
            },
            "claim_summary": "Pilot unit 1 - temple worship purpose.",
            "topics": ["temple_worship"],
            "attribution": {
                "dk_attestation": "located",
                "wording_status": "earlier_witness_agrees",
                "compiler_intervention_status": "unknown",
                "note": "Test record"
            },
            "evidence_status": {
                "digital_attestation": "confirmed",
                "print_check": "not_checked",
                "primary_source_status": "unknown",
                "authority": "earlier_witness_supported"
            },
            "provenance": [
                {
                    "source_key": "kamakoti-dk-v1-part1kurall08",
                    "witness_role": "official_digital",
                    "url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                    "locus": "private batch review packet paragraph(s) p001",
                    "snapshot_sha256": "1111222233334444555566667777888811112222333344445555666677778888",
                    "lineage_note": "Test",
                    "rights_status": "restricted_private_research"
                },
                {
                    "source_key": "acharya-upanyasangal-part1-1957-58-scan",
                    "witness_role": "earlier_secondary",
                    "locus": "ஆலய வணக்கம், printed p. 39 ff.; PDF pp. 54-56",
                    "snapshot_sha256": "ace3c1cca4c3077d9e15080365741f541d471274c28d11e07d85f2b372901f7e",
                    "lineage_note": "Test",
                    "rights_status": "restricted_private_research"
                }
            ],
            "rights": {
                "source_text_tier": "restricted",
                "public_export": "metadata_only",
                "terms_url": None,
                "note": "Test"
            },
            "flags": ["traditional_normative_claim"],
            "curator_notes": "Test"
        },
        {
            "id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.pilot_unit_2",
            "corpus": "mahaperiyava_teachings",
            "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati",
            "compiler": "ra_ganapathi",
            "language": "tamil",
            "source_locus": {
                "volume": 1,
                "section_title_ta": None,
                "chapter_title_ta": "alaya vazhipadu",
                "chapter_ordinal": 100,
                "print_edition": None,
                "print_page_start": None,
                "print_page_end": None,
                "digital_url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                "digital_anchor": None,
            },
            "claim_summary": "Pilot unit 2 - temple worship purpose.",
            "topics": ["temple_worship"],
            "attribution": {
                "dk_attestation": "located",
                "wording_status": "earlier_witness_agrees",
                "compiler_intervention_status": "unknown",
                "note": "Test record"
            },
            "evidence_status": {
                "digital_attestation": "confirmed",
                "print_check": "not_checked",
                "primary_source_status": "unknown",
                "authority": "earlier_witness_supported"
            },
            "provenance": [
                {
                    "source_key": "kamakoti-dk-v1-part1kurall08",
                    "witness_role": "official_digital",
                    "url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                    "locus": "private batch review packet paragraph(s) p002",
                    "snapshot_sha256": "1111222233334444555566667777888811112222333344445555666677778888",
                    "lineage_note": "Test",
                    "rights_status": "restricted_private_research"
                },
                {
                    "source_key": "acharya-upanyasangal-part1-1957-58-scan",
                    "witness_role": "earlier_secondary",
                    "locus": "ஆலய வணக்கம், printed p. 39 ff.; PDF pp. 54-56",
                    "snapshot_sha256": "ace3c1cca4c3077d9e15080365741f541d471274c28d11e07d85f2b372901f7e",
                    "lineage_note": "Test",
                    "rights_status": "restricted_private_research"
                }
            ],
            "rights": {
                "source_text_tier": "restricted",
                "public_export": "metadata_only",
                "terms_url": None,
                "note": "Test"
            },
            "flags": ["traditional_normative_claim"],
            "curator_notes": "Test"
        },
        {
            "id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.pilot_unit_3",
            "corpus": "mahaperiyava_teachings",
            "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati",
            "compiler": "ra_ganapathi",
            "language": "tamil",
            "source_locus": {
                "volume": 1,
                "section_title_ta": None,
                "chapter_title_ta": "alaya vazhipadu",
                "chapter_ordinal": 100,
                "print_edition": None,
                "print_page_start": None,
                "print_page_end": None,
                "digital_url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                "digital_anchor": None,
            },
            "claim_summary": "Pilot unit 3 - temple worship purpose.",
            "topics": ["temple_worship"],
            "attribution": {
                "dk_attestation": "located",
                "wording_status": "earlier_witness_agrees",
                "compiler_intervention_status": "unknown",
                "note": "Test record"
            },
            "evidence_status": {
                "digital_attestation": "confirmed",
                "print_check": "not_checked",
                "primary_source_status": "unknown",
                "authority": "earlier_witness_supported"
            },
            "provenance": [
                {
                    "source_key": "kamakoti-dk-v1-part1kurall08",
                    "witness_role": "official_digital",
                    "url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                    "locus": "private batch review packet paragraph(s) p003",
                    "snapshot_sha256": "1111222233334444555566667777888811112222333344445555666677778888",
                    "lineage_note": "Test",
                    "rights_status": "restricted_private_research"
                },
                {
                    "source_key": "acharya-upanyasangal-part1-1957-58-scan",
                    "witness_role": "earlier_secondary",
                    "locus": "ஆலய வணக்கம், printed p. 39 ff.; PDF pp. 54-56",
                    "snapshot_sha256": "ace3c1cca4c3077d9e15080365741f541d471274c28d11e07d85f2b372901f7e",
                    "lineage_note": "Test",
                    "rights_status": "restricted_private_research"
                }
            ],
            "rights": {
                "source_text_tier": "restricted",
                "public_export": "metadata_only",
                "terms_url": None,
                "note": "Test"
            },
            "flags": ["traditional_normative_claim"],
            "curator_notes": "Test"
        },
        {
            "id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.pilot_unit_4",
            "corpus": "mahaperiyava_teachings",
            "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati",
            "compiler": "ra_ganapathi",
            "language": "tamil",
            "source_locus": {
                "volume": 1,
                "section_title_ta": None,
                "chapter_title_ta": "alaya vazhipadu",
                "chapter_ordinal": 100,
                "print_edition": None,
                "print_page_start": None,
                "print_page_end": None,
                "digital_url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                "digital_anchor": None,
            },
            "claim_summary": "Pilot unit 4 - temple worship purpose.",
            "topics": ["temple_worship"],
            "attribution": {
                "dk_attestation": "located",
                "wording_status": "dk_wording_only",
                "compiler_intervention_status": "unknown",
                "note": "Test record"
            },
            "evidence_status": {
                "digital_attestation": "confirmed",
                "print_check": "not_checked",
                "primary_source_status": "unknown",
                "authority": "dk_attested"
            },
            "provenance": [
                {
                    "source_key": "kamakoti-dk-v1-part1kurall08",
                    "witness_role": "official_digital",
                    "url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                    "locus": "private batch review packet paragraph(s) p004",
                    "snapshot_sha256": "1111222233334444555566667777888811112222333344445555666677778888",
                    "lineage_note": "Test",
                    "rights_status": "restricted_private_research"
                }
            ],
            "rights": {
                "source_text_tier": "restricted",
                "public_export": "metadata_only",
                "terms_url": None,
                "note": "Test"
            },
            "flags": ["traditional_normative_claim"],
            "curator_notes": "Test"
        },
        {
            "id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.pilot_unit_5",
            "corpus": "mahaperiyava_teachings",
            "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati",
            "compiler": "ra_ganapathi",
            "language": "tamil",
            "source_locus": {
                "volume": 1,
                "section_title_ta": None,
                "chapter_title_ta": "alaya vazhipadu",
                "chapter_ordinal": 100,
                "print_edition": None,
                "print_page_start": None,
                "print_page_end": None,
                "digital_url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                "digital_anchor": None,
            },
            "claim_summary": "Pilot unit 5 - temple worship purpose.",
            "topics": ["temple_worship"],
            "attribution": {
                "dk_attestation": "located",
                "wording_status": "dk_wording_only",
                "compiler_intervention_status": "unknown",
                "note": "Test record"
            },
            "evidence_status": {
                "digital_attestation": "confirmed",
                "print_check": "not_checked",
                "primary_source_status": "unknown",
                "authority": "dk_attested"
            },
            "provenance": [
                {
                    "source_key": "kamakoti-dk-v1-part1kurall08",
                    "witness_role": "official_digital",
                    "url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                    "locus": "private batch review packet paragraph(s) p005",
                    "snapshot_sha256": "1111222233334444555566667777888811112222333344445555666677778888",
                    "lineage_note": "Test",
                    "rights_status": "restricted_private_research"
                }
            ],
            "rights": {
                "source_text_tier": "restricted",
                "public_export": "metadata_only",
                "terms_url": None,
                "note": "Test"
            },
            "flags": ["traditional_normative_claim"],
            "curator_notes": "Test"
        },
        {
            "id": "mahaperiyava.deivathin_kural.v1.alaya_vazhipadu.pilot_unit_6",
            "corpus": "mahaperiyava_teachings",
            "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati",
            "compiler": "ra_ganapathi",
            "language": "tamil",
            "source_locus": {
                "volume": 1,
                "section_title_ta": None,
                "chapter_title_ta": "alaya vazhipadu",
                "chapter_ordinal": 100,
                "print_edition": None,
                "print_page_start": None,
                "print_page_end": None,
                "digital_url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                "digital_anchor": None,
            },
            "claim_summary": "Pilot unit 6 - temple worship purpose.",
            "topics": ["temple_worship"],
            "attribution": {
                "dk_attestation": "located",
                "wording_status": "dk_wording_only",
                "compiler_intervention_status": "unknown",
                "note": "Test record"
            },
            "evidence_status": {
                "digital_attestation": "confirmed",
                "print_check": "not_checked",
                "primary_source_status": "unknown",
                "authority": "dk_attested"
            },
            "provenance": [
                {
                    "source_key": "kamakoti-dk-v1-part1kurall08",
                    "witness_role": "official_digital",
                    "url": "https://www.kamakoti.org/tamil/part1kurall08.htm",
                    "locus": "private batch review packet paragraph(s) p006",
                    "snapshot_sha256": "1111222233334444555566667777888811112222333344445555666677778888",
                    "lineage_note": "Test",
                    "rights_status": "restricted_private_research"
                }
            ],
            "rights": {
                "source_text_tier": "restricted",
                "public_export": "metadata_only",
                "terms_url": None,
                "note": "Test"
            },
            "flags": ["traditional_normative_claim"],
            "curator_notes": "Test"
        },
    ]

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        man_path = td_path / "synthetic_manifest_100.json"
        man_path.write_text(json.dumps(synthetic_manifest))

        # Create synthetic pilot file in the temp repo root
        synthetic_pilot_file = td_path / "data" / "review" / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
        synthetic_pilot_file.parent.mkdir(parents=True, exist_ok=True)
        with open(synthetic_pilot_file, "w", encoding="utf-8") as f:
            for rec in synthetic_pilot_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        # 1. No carry-forward provided -> MUST FAIL CLOSED
        applier_no_cf = DKManifestApplier(
            manifest_path=man_path,
            repo_root=td_path,
            carry_forward_path=None,
            output_dir=td_path / "out",
        )
        overlaps, err = applier_no_cf.check_pilot_overlap()
        assert len(overlaps) == 1, "Must detect overlap on chapter 100"
        o = overlaps[0]
        assert o.chapter_ordinal == 100
        assert o.pilot_record_count == 6
        assert o.has_earlier_witness_supported is True
        assert o.has_earlier_secondary_provenance is True
        assert o.authority_distribution["earlier_witness_supported"] == 3
        assert o.authority_distribution["dk_attested"] == 3
        assert err is not None, "Must return error when carry-forward artifact is missing"
        assert applier_no_cf.run("check") != 0, "Must exit non-zero without carry-forward artifact"

        # 2. Carry-forward artifact that attempts SILENT DOWNGRADE -> MUST FAIL CLOSED
        silent_downgrade_cf = {
            "version": "1.0",
            "batch": "100_100",
            "chapter_decisions": [
                {
                    "chapter_ordinal": 100,
                    "action": "replace_with_batch",
                    # Missing carry_forward_stronger_evidence and missing curator_downgrade_approved
                }
            ],
        }
        cf_silent_path = td_path / "cf_silent.json"
        cf_silent_path.write_text(json.dumps(silent_downgrade_cf))

        applier_silent = DKManifestApplier(
            manifest_path=man_path,
            repo_root=td_path,
            carry_forward_path=cf_silent_path,
            output_dir=td_path / "out",
        )
        _, err_silent = applier_silent.check_pilot_overlap()
        assert err_silent is not None, "Must reject silent downgrade of stronger evidence"
        assert "earlier_witness_supported=True" in err_silent
        assert applier_silent.run("check") != 0, "Must exit non-zero on silent downgrade attempt"

        # 3. Carry-forward artifact that EXPLICITLY preserves stronger evidence -> MUST SUCCEED
        approved_cf = {
            "version": "1.0",
            "batch": "100_100",
            "chapter_decisions": [
                {
                    "chapter_ordinal": 100,
                    "action": "carry_forward_stronger_evidence",
                    "carry_forward_stronger_evidence": True,
                    "curator_note": "Stronger witness evidence from pilot records 1, 3, 4 carried forward.",
                }
            ],
        }
        cf_approved_path = td_path / "cf_approved.json"
        cf_approved_path.write_text(json.dumps(approved_cf))

        applier_approved = DKManifestApplier(
            manifest_path=man_path,
            repo_root=td_path,
            carry_forward_path=cf_approved_path,
            output_dir=td_path / "out",
        )
        _, err_approved = applier_approved.check_pilot_overlap()
        assert err_approved is None, f"Must pass with approved carry-forward: {err_approved}"
        assert applier_approved.run("check") == 0, "Must pass check with approved carry-forward"


def test_positive_regression_066_085_reproduces_exact_tracked_artifacts():
    """Verify that applying 066-085 reproduces the exact tracked production records and index."""
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        cf_path = td_path / "cf.json"
        cf_path.write_text(json.dumps(_make_066_085_carry_forward()))
        out_dir = td_path / "out"

        applier = DKManifestApplier(
            manifest_path=MANIFEST_066_085,
            repo_root=ROOT,
            carry_forward_path=cf_path,
            output_dir=out_dir,
        )
        assert applier.run("apply") == 0

        gen_records = (out_dir / "mahaperiyava_dk_v1_batch_066_085_teaching_records.jsonl").read_text(
            encoding="utf-8"
        )
        tracked_records = (
            ROOT / "data/review/mahaperiyava_dk_v1_batch_066_085_teaching_records.jsonl"
        ).read_text(encoding="utf-8")
        assert gen_records == tracked_records, "Generated teaching records must exactly match tracked file"

        gen_index = json.loads(
            (out_dir / "mahaperiyava_dk_v1_batch_066_085_curation_index.json").read_text(encoding="utf-8")
        )
        tracked_index = json.loads(
            (ROOT / "data/review/mahaperiyava_dk_v1_batch_066_085_curation_index.json").read_text(
                encoding="utf-8"
            )
        )
        assert gen_index == tracked_index, "Generated curation index must exactly match tracked file"
