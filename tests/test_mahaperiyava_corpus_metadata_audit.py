#!/usr/bin/env python3
"""Regression test for Mahaperiyava corpus metadata audit."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "scripts/audit_mahaperiyava_corpus_metadata.py"


def test_audit_runs_clean():
    """Run the metadata auditor and assert clean exit."""
    result = subprocess.run(
        [sys.executable, str(AUDITOR)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    assert result.returncode == 0, f"Audit failed with exit code {result.returncode}"


def test_no_malformed_json():
    """Verify all tracked JSON/JSONL files parse correctly."""
    import json

    files = list(ROOT.glob("data/review/mahaperiyava*teaching_records.jsonl")) + \
            list(ROOT.glob("data/review/mahaperiyava*curation_index.json"))

    for f in files:
        if not f.exists():
            continue
        if f.suffix == ".jsonl":
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    raise AssertionError(f"{f}: line {i}: {e}")
        else:
            try:
                json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                raise AssertionError(f"{f}: {e}")


def test_no_duplicate_teaching_ids():
    """Verify no duplicate teaching IDs across all batches."""
    import json

    seen = set()
    dupes = []
    files = list(ROOT.glob("data/review/mahaperiyava*teaching_records.jsonl"))

    for f in files:
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rid = rec.get("id")
            if rid in seen:
                dupes.append(rid)
            seen.add(rid)

    assert not dupes, f"Duplicate teaching IDs: {dupes}"


def test_no_duplicate_curation_ids():
    """Verify no duplicate curation index IDs."""
    import json

    seen = set()
    dupes = []
    files = list(ROOT.glob("data/review/mahaperiyava*curation_index.json"))

    for f in files:
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for u in data.get("units", []):
            uid = u.get("id")
            if uid in seen:
                dupes.append(uid)
            seen.add(uid)

    assert not dupes, f"Duplicate curation IDs: {dupes}"


def test_valid_authority_values():
    """Verify all authority values are from the allowed set."""
    import json

    valid = {"dk_attested", "dk_print_checked", "earlier_witness_supported", "primary_source_verified", "unattested"}
    bad = []

    # Teaching records
    for f in ROOT.glob("data/review/mahaperiyava*teaching_records.jsonl"):
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            auth = rec.get("evidence_status", {}).get("authority")
            if auth and auth not in valid:
                bad.append(f"{rec.get('id')}: {auth}")

    # Curation index
    for f in ROOT.glob("data/review/mahaperiyava*curation_index.json"):
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for u in data.get("units", []):
            auth = u.get("authority")
            if auth and auth not in valid:
                bad.append(f"{u.get('id')}: {auth}")

    assert not bad, f"Unsupported authority values: {bad}"


def test_earlier_witness_supported_requires_earlier_secondary():
    """earlier_witness_supported must have an earlier_secondary provenance witness."""
    import json

    bad = []
    for f in ROOT.glob("data/review/mahaperiyava*teaching_records.jsonl"):
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            auth = rec.get("evidence_status", {}).get("authority")
            if auth == "earlier_witness_supported":
                prov = rec.get("provenance", [])
                has_earlier = any(p.get("witness_role") == "earlier_secondary" for p in prov)
                if not has_earlier:
                    bad.append(rec.get("id"))

    assert not bad, f"earlier_witness_supported without earlier_secondary provenance: {bad}"


def test_earlier_witness_supported_requires_wording_agrees():
    """earlier_witness_supported must have wording_status == earlier_witness_agrees."""
    import json

    bad = []
    for f in ROOT.glob("data/review/mahaperiyava*teaching_records.jsonl"):
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            auth = rec.get("evidence_status", {}).get("authority")
            if auth == "earlier_witness_supported":
                wording = rec.get("attribution", {}).get("wording_status")
                if wording != "earlier_witness_agrees":
                    bad.append(f"{rec.get('id')}: wording_status={wording}")

    assert not bad, f"earlier_witness_supported with wrong wording_status: {bad}"


def test_primary_source_verified_requires_primary_provenance():
    """primary_source_verified must have explicit primary-source provenance."""
    import json

    bad = []
    for f in ROOT.glob("data/review/mahaperiyava*teaching_records.jsonl"):
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            auth = rec.get("evidence_status", {}).get("authority")
            if auth == "primary_source_verified":
                prov = rec.get("provenance", [])
                has_primary = any(p.get("witness_role") in ("primary", "primary_source") for p in prov)
                if not has_primary:
                    bad.append(rec.get("id"))

    assert not bad, f"primary_source_verified without primary provenance: {bad}"


def test_curation_authority_matches_teaching():
    """Curation index authority must match teaching record authority."""
    import json

    teaching_auth = {}
    for f in ROOT.glob("data/review/mahaperiyava*teaching_records.jsonl"):
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            teaching_auth[rec["id"]] = rec.get("evidence_status", {}).get("authority")

    bad = []
    for f in ROOT.glob("data/review/mahaperiyava*curation_index.json"):
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for u in data.get("units", []):
            uid = u.get("id")
            c_auth = u.get("authority")
            t_auth = teaching_auth.get(uid)
            if t_auth and c_auth != t_auth:
                bad.append(f"{uid}: curation={c_auth} teaching={t_auth}")

    assert not bad, f"Curation/teaching authority mismatch: {bad}"


def test_restricted_records_not_publicly_exportable():
    """Restricted source_text_tier must have public_export = metadata_only or none."""
    import json

    bad = []
    for f in ROOT.glob("data/review/mahaperiyava*teaching_records.jsonl"):
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rights = rec.get("rights", {})
            if rights.get("source_text_tier") == "restricted":
                pub = rights.get("public_export")
                if pub not in ("metadata_only", "none"):
                    bad.append(f"{rec.get('id')}: public_export={pub}")
                if "exact_text_restricted" in rec and rec["exact_text_restricted"] is not None:
                    bad.append(f"{rec.get('id')}: contains non-null exact_text_restricted")

    assert not bad, f"Rights violations: {bad}"


def test_required_fields_present():
    """All required structural fields must be present."""
    import json

    required_teaching = [
        "id", "corpus", "work", "teacher", "compiler", "language",
        "source_locus", "claim_summary", "topics", "attribution",
        "evidence_status", "provenance", "rights", "flags", "curator_notes",
    ]
    required_curation = [
        "id", "chapter_slug", "unit_slug", "claim_summary",
        "question_intents", "source_paragraph_ids", "source_paragraph_hashes",
        "topics", "flags", "authority", "historical_witness",
    ]

    bad = []
    for f in ROOT.glob("data/review/mahaperiyava*teaching_records.jsonl"):
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            for field in required_teaching:
                if field not in rec:
                    bad.append(f"{rec.get('id')}: missing '{field}'")

    for f in ROOT.glob("data/review/mahaperiyava*curation_index.json"):
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for u in data.get("units", []):
            for field in required_curation:
                if field not in u:
                    bad.append(f"{u.get('id')}: missing '{field}'")

    assert not bad, f"Missing required fields: {bad}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))