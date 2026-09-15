#!/usr/bin/env python3
"""Regression test for Mahaperiyava corpus metadata audit."""
import json
import subprocess
import sys
import tempfile
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
    valid = {"dk_attested", "dk_print_checked", "earlier_witness_supported", "primary_source_verified", "unattested"}
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
            if auth and auth not in valid:
                bad.append(f"{rec.get('id')}: {auth}")

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


# --- New regression tests for hardened auditor ---

def _write_jsonl(path: Path, records):
    """Write records as JSONL with proper newlines."""
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_json(path: Path, data):
    """Write JSON with proper newlines."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_dynamic_discovery_uses_git_ls_files():
    """Prove the auditor uses tracked-file discovery rather than a hardcoded batch list."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)

    teaching_files, curation_files = auditor.discover_tracked_files()

    assert len(teaching_files) >= 4, f"Expected >=4 teaching files, got {len(teaching_files)}"
    assert len(curation_files) >= 4, f"Expected >=4 curation files, got {len(curation_files)}"

    for f in teaching_files + curation_files:
        assert f.is_relative_to(ROOT / "data/review"), f"File outside data/review: {f}"

    result = subprocess.run(
        ["git", "ls-files", "data/review/mahaperiyava*teaching_records.jsonl",
         "data/review/mahaperiyava*curation_index.json"],
        cwd=ROOT, capture_output=True, text=True, check=True
    )
    git_files = [ROOT / line for line in result.stdout.strip().splitlines() if line]
    assert set(teaching_files + curation_files) == set(git_files), "Discovery != git ls-files"


def test_stable_chapter_identity_different_ordinal():
    """Two records with same Tamil title but different (volume, chapter_ordinal) count as two chapters."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)

    rec1 = {"id": "test.1", "source_locus": {"volume": 1, "chapter_ordinal": 4, "chapter_title_ta": "அத்வைதம்"}}
    rec2 = {"id": "test.2", "source_locus": {"volume": 1, "chapter_ordinal": 5, "chapter_title_ta": "அத்வைதம்"}}
    rec3 = {"id": "test.3", "source_locus": {"volume": 1, "chapter_ordinal": 4, "chapter_title_ta": "அத்வைதம்"}}

    id1 = auditor.chapter_identity(rec1)
    id2 = auditor.chapter_identity(rec2)
    id3 = auditor.chapter_identity(rec3)

    assert id1 != id2, f"Different ordinal should give different identity: {id1} vs {id2}"
    assert id1 == id3, f"Same ordinal should give same identity: {id1} vs {id3}"


def test_fallback_chapter_identity_uses_digital_url():
    """When chapter_ordinal is absent, (volume, digital_url) is the fallback identity."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)

    rec1 = {"id": "test.1", "source_locus": {"volume": 1, "digital_url": "https://example.com/ch4"}}
    rec2 = {"id": "test.2", "source_locus": {"volume": 1, "digital_url": "https://example.com/ch4"}}
    rec3 = {"id": "test.3", "source_locus": {"volume": 1, "digital_url": "https://example.com/ch5"}}

    id1 = auditor.chapter_identity(rec1)
    id2 = auditor.chapter_identity(rec2)
    id3 = auditor.chapter_identity(rec3)

    assert id1 == id2, f"Same digital_url should give same identity: {id1} vs {id2}"
    assert id1 != id3, f"Different digital_url should give different identity: {id1} vs {id3}"
    rec_ordinal = {"id": "test.4", "source_locus": {"volume": 1, "chapter_ordinal": 4}}
    id_ordinal = auditor.chapter_identity(rec_ordinal)
    assert id1 != id_ordinal, f"Ordinal vs URL should be different: {id1} vs {id_ordinal}"


def test_explicit_source_anomalies_reported():
    """Prove source_anomalies recorded in curation-index metadata are surfaced by audit without being corrected."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        curation_file = td_path / "test_curation_index.json"
        _write_json(curation_file, {
            "units": [
                {"id": "test.unit.1", "source_anomalies": ["chapter_title_ta contains Latin 'u'"],
                 "authority": "dk_attested", "chapter_slug": "test", "unit_slug": "u1",
                 "claim_summary": "test", "question_intents": [], "source_paragraph_ids": [],
                 "source_paragraph_hashes": [], "topics": [], "flags": [], "historical_witness": None},
                {"id": "test.unit.2", "source_anomalies": [],
                 "authority": "dk_attested", "chapter_slug": "test", "unit_slug": "u2",
                 "claim_summary": "test", "question_intents": [], "source_paragraph_ids": [],
                 "source_paragraph_hashes": [], "topics": [], "flags": [], "historical_witness": None},
            ]
        })

        original_discover = auditor.discover_tracked_files
        def test_discover():
            return [], [curation_file]
        auditor.discover_tracked_files = test_discover

        try:
            curation = auditor.audit_curation_index([curation_file])
            anomalies = curation.get("source_anomalies", [])
            assert len(anomalies) == 1, f"Expected 1 anomaly, got {len(anomalies)}: {anomalies}"
            assert "chapter_title_ta contains Latin 'u'" in anomalies[0]
        finally:
            auditor.discover_tracked_files = original_discover


def test_missing_teaching_curation_counterparts_blocking():
    """Missing teaching/index counterparts are blocking failures."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        teaching_file = td_path / "teaching.jsonl"
        curation_file = td_path / "curation.json"

        _write_jsonl(teaching_file, [{
            "id": "test.orphan.teaching", "corpus": "mahaperiyava_teachings", "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati", "compiler": "ra_ganapathi", "language": "tamil",
            "source_locus": {"volume": 1, "chapter_ordinal": 1, "digital_url": "https://example.com"},
            "claim_summary": "test", "topics": [], "attribution": {},
            "evidence_status": {"authority": "dk_attested"}, "provenance": [],
            "rights": {}, "flags": [], "curator_notes": ""
        }])

        _write_json(curation_file, {
            "units": [
                {"id": "test.orphan.curation", "chapter_slug": "test", "unit_slug": "u1",
                 "claim_summary": "test", "question_intents": [], "source_paragraph_ids": [],
                 "source_paragraph_hashes": [], "topics": [], "flags": [],
                 "authority": "dk_attested", "historical_witness": None}
            ]
        })

        original_discover = auditor.discover_tracked_files
        def test_discover():
            return [teaching_file], [curation_file]
        auditor.discover_tracked_files = test_discover

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
            auditor = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(auditor)
            auditor.discover_tracked_files = test_discover
            teaching, curation = auditor.audit_teaching_records([teaching_file]), auditor.audit_curation_index([curation_file])
            missing = curation.get("missing_counterparts", [])
            assert len(missing) == 2, f"Expected 2 missing counterparts, got {len(missing)}: {missing}"
            assert any("orphan.teaching" in m for m in missing)
            assert any("orphan.curation" in m for m in missing)
        finally:
            auditor.discover_tracked_files = original_discover


def test_malformed_provenance_missing_witness_role_blocking():
    """Provenance entries missing witness_role are blocking."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        teaching_file = td_path / "teaching.jsonl"

        _write_jsonl(teaching_file, [{
            "id": "test.bad.provenance1", "corpus": "mahaperiyava_teachings", "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati", "compiler": "ra_ganapathi", "language": "tamil",
            "source_locus": {"volume": 1, "chapter_ordinal": 1},
            "claim_summary": "test", "topics": [], "attribution": {},
            "evidence_status": {"authority": "dk_attested"},
            "provenance": [{"url": "https://example.com", "snapshot_sha256": "abc123"}],
            "rights": {}, "flags": [], "curator_notes": ""
        }])

        original_discover = auditor.discover_tracked_files
        def test_discover():
            return [teaching_file], []
        auditor.discover_tracked_files = test_discover

        try:
            teaching = auditor.audit_teaching_records([teaching_file])
            prov_issues = teaching.get("provenance_issues", [])
            assert len(prov_issues) >= 1, f"Expected provenance issue for missing witness_role, got {prov_issues}"
            assert any("witness_role" in p for p in prov_issues)
        finally:
            auditor.discover_tracked_files = original_discover


def test_malformed_provenance_missing_snapshot_sha256_blocking():
    """Provenance entries missing snapshot_sha256 are blocking."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        teaching_file = td_path / "teaching.jsonl"

        _write_jsonl(teaching_file, [{
            "id": "test.bad.provenance2", "corpus": "mahaperiyava_teachings", "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati", "compiler": "ra_ganapathi", "language": "tamil",
            "source_locus": {"volume": 1, "chapter_ordinal": 1},
            "claim_summary": "test", "topics": [], "attribution": {},
            "evidence_status": {"authority": "dk_attested"},
            "provenance": [{"url": "https://example.com", "witness_role": "official_digital"}],
            "rights": {}, "flags": [], "curator_notes": ""
        }])

        original_discover = auditor.discover_tracked_files
        def test_discover():
            return [teaching_file], []
        auditor.discover_tracked_files = test_discover

        try:
            teaching = auditor.audit_teaching_records([teaching_file])
            prov_issues = teaching.get("provenance_issues", [])
            assert len(prov_issues) >= 1, f"Expected provenance issue for missing sha256, got {prov_issues}"
            assert any("snapshot_sha256" in p for p in prov_issues)
        finally:
            auditor.discover_tracked_files = original_discover


def test_authority_mismatch_blocking():
    """Curation-index authority != teaching-record authority => blocking."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        teaching_file = td_path / "teaching.jsonl"
        curation_file = td_path / "curation.json"

        _write_jsonl(teaching_file, [{
            "id": "test.mismatch.1", "corpus": "mahaperiyava_teachings", "work": "deivathin_kural",
            "teacher": "chandrasekharendra_saraswati", "compiler": "ra_ganapathi", "language": "tamil",
            "source_locus": {"volume": 1, "chapter_ordinal": 1},
            "claim_summary": "test", "topics": [], "attribution": {},
            "evidence_status": {"authority": "dk_attested"}, "provenance": [],
            "rights": {}, "flags": [], "curator_notes": ""
        }])

        _write_json(curation_file, {
            "units": [
                {"id": "test.mismatch.1", "chapter_slug": "test", "unit_slug": "u1",
                 "claim_summary": "test", "question_intents": [], "source_paragraph_ids": [],
                 "source_paragraph_hashes": [], "topics": [], "flags": [],
                 "authority": "earlier_witness_supported", "historical_witness": None}
            ]
        })

        original_discover = auditor.discover_tracked_files
        def test_discover():
            return [teaching_file], [curation_file]
        auditor.discover_tracked_files = test_discover

        try:
            teaching, curation = auditor.audit_teaching_records([teaching_file]), auditor.audit_curation_index([curation_file])
            mismatches = curation.get("authority_mismatches", [])
            assert len(mismatches) == 1, f"Expected 1 authority mismatch, got {len(mismatches)}: {mismatches}"
            assert "test.mismatch.1" in mismatches[0]
        finally:
            auditor.discover_tracked_files = original_discover


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))