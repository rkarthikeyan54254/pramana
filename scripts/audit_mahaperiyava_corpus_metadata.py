#!/usr/bin/env python3
"""
Mahaperiyava Corpus Metadata Auditor

Inspects TRACKED metadata only. Does NOT open data/private/ or sources/raw/.
Audits all tracked Mahaperiyava teaching-record JSONL and curation-index JSON files.
Discovers files dynamically via git ls-files.
"""
from __future__ import annotations
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

VALID_AUTHORITIES = {
    "dk_attested",
    "dk_print_checked",
    "earlier_witness_supported",
    "primary_source_verified",
    "unattested",
}

REQUIRED_TEACHING_FIELDS = [
    "id", "corpus", "work", "teacher", "compiler", "language",
    "source_locus", "claim_summary", "topics", "attribution",
    "evidence_status", "provenance", "rights", "flags", "curator_notes",
]

REQUIRED_CURATION_UNIT_FIELDS = [
    "id", "chapter_slug", "unit_slug", "claim_summary",
    "question_intents", "source_paragraph_ids", "source_paragraph_hashes",
    "topics", "flags", "authority", "historical_witness",
]


def load_jsonl(path: Path) -> list[dict]:
    records = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}: line {i}: malformed JSON: {e}")
    return records


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{path}: malformed JSON: {e}")


def discover_tracked_files() -> tuple[list[Path], list[Path]]:
    """Discover tracked Mahaperiyava files via git ls-files."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "data/review/mahaperiyava*teaching_records.jsonl",
             "data/review/mahaperiyava*curation_index.json"],
            cwd=ROOT, capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git ls-files failed: {e.stderr}")

    teaching_files = []
    curation_files = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        p = ROOT / line
        if p.suffix == ".jsonl":
            teaching_files.append(p)
        else:
            curation_files.append(p)

    if not teaching_files and not curation_files:
        raise RuntimeError("No tracked Mahaperiyava metadata files found")

    return sorted(teaching_files), sorted(curation_files)


def chapter_identity(record: dict) -> tuple:
    """
    Stable chapter identity: (volume, chapter_ordinal) when available,
    else (volume, digital_url) as fallback.
    Tamil title is display metadata only.
    """
    locus = record.get("source_locus", {})
    volume = locus.get("volume")
    ordinal = locus.get("chapter_ordinal")
    if volume is not None and ordinal is not None:
        return (volume, ordinal)
    digital_url = locus.get("digital_url", "")
    return (volume, digital_url)


def audit_teaching_records(files: list[Path]) -> dict[str, Any]:
    all_records = []
    seen_ids = set()
    duplicate_ids = []
    authority_counts = Counter()
    flag_counts = Counter()
    chapter_identities = Counter()
    missing_fields = []
    rights_violations = []
    authority_issues = []
    provenance_issues = []
    source_anomalies = []
    decode_replacements = 0

    for path in files:
        if not path.exists():
            print(f"WARNING: {path} does not exist, skipping")
            continue
        records = load_jsonl(path)
        for r in records:
            all_records.append(r)

            # Duplicate ID check
            rid = r.get("id")
            if rid in seen_ids:
                duplicate_ids.append(rid)
            seen_ids.add(rid)

            # Missing required fields
            for field in REQUIRED_TEACHING_FIELDS:
                if field not in r:
                    missing_fields.append(f"{rid}: missing '{field}'")

            # Authority validation
            auth = r.get("evidence_status", {}).get("authority")
            if auth:
                authority_counts[auth] += 1
                if auth not in VALID_AUTHORITIES:
                    authority_issues.append(f"{rid}: unsupported authority '{auth}'")
            else:
                authority_issues.append(f"{rid}: missing evidence_status.authority")

            # earlier_witness_supported checks
            if auth == "earlier_witness_supported":
                wording = r.get("attribution", {}).get("wording_status")
                if wording != "earlier_witness_agrees":
                    authority_issues.append(f"{rid}: earlier_witness_supported but wording_status='{wording}' (must be 'earlier_witness_agrees')")
                prov = r.get("provenance", [])
                has_earlier_secondary = any(p.get("witness_role") == "earlier_secondary" for p in prov)
                if not has_earlier_secondary:
                    authority_issues.append(f"{rid}: earlier_witness_supported but no earlier_secondary provenance witness")

            # primary_source_verified checks
            if auth == "primary_source_verified":
                prov = r.get("provenance", [])
                has_primary = any(p.get("witness_role") in ("primary", "primary_source") for p in prov)
                if not has_primary:
                    authority_issues.append(f"{rid}: primary_source_verified but no primary-source provenance witness")

            # Rights check
            rights = r.get("rights", {})
            if rights.get("source_text_tier") == "restricted":
                pub = rights.get("public_export")
                if pub not in ("metadata_only", "none"):
                    rights_violations.append(f"{rid}: restricted source_text_tier but public_export='{pub}' (must be metadata_only/none)")
                if "exact_text_restricted" in r and r["exact_text_restricted"] is not None:
                    rights_violations.append(f"{rid}: tracked record contains non-null exact_text_restricted")

            # Flags
            for f in r.get("flags", []):
                flag_counts[f] += 1
                if "source_decode_replacement" in f.lower():
                    decode_replacements += 1

            # Chapter identity (stable key)
            ch_key = chapter_identity(r)
            chapter_identities[ch_key] += 1

            # Provenance consistency
            prov = r.get("provenance", [])
            for p in prov:
                if "snapshot_sha256" not in p:
                    provenance_issues.append(f"{rid}: provenance entry missing snapshot_sha256")
                if "witness_role" not in p:
                    provenance_issues.append(f"{rid}: provenance entry missing witness_role")

            # Record explicit source_anomalies if present in record
            # (These come from curation-index metadata, not inferred)
            for anomaly in r.get("source_anomalies", []):
                source_anomalies.append(f"{rid}: {anomaly}")

    return {
        "total_records": len(all_records),
        "by_batch": {str(f): len(load_jsonl(f)) for f in files if f.exists()},
        "duplicate_ids": duplicate_ids,
        "authority_counts": dict(authority_counts),
        "flag_counts": dict(flag_counts),
        "chapter_count": len(chapter_identities),
        "chapters": dict(chapter_identities),
        "missing_fields": missing_fields,
        "authority_issues": authority_issues,
        "rights_violations": rights_violations,
        "provenance_issues": provenance_issues,
        "source_anomalies": source_anomalies,
        "decode_replacements": decode_replacements,
    }


def audit_curation_index(files: list[Path]) -> dict[str, Any]:
    all_units = []
    seen_ids = set()
    duplicate_ids = []
    authority_counts = Counter()
    flag_counts = Counter()
    missing_fields = []
    authority_mismatches = []
    missing_counterparts = []
    source_anomalies = []

    # Build teaching record authority map
    teaching_by_id = {}
    teaching_files, _ = discover_tracked_files()
    for tf in teaching_files:
        if tf.exists():
            for r in load_jsonl(tf):
                teaching_by_id[r["id"]] = r.get("evidence_status", {}).get("authority")

    for path in files:
        if not path.exists():
            print(f"WARNING: {path} does not exist, skipping")
            continue
        data = load_json(path)
        units = data.get("units", [])
        for u in units:
            all_units.append(u)
            uid = u.get("id")
            if uid in seen_ids:
                duplicate_ids.append(uid)
            seen_ids.add(uid)

            for field in REQUIRED_CURATION_UNIT_FIELDS:
                if field not in u:
                    missing_fields.append(f"{uid}: missing '{field}'")

            auth = u.get("authority")
            if auth:
                authority_counts[auth] += 1
                if auth not in VALID_AUTHORITIES:
                    authority_mismatches.append(f"{uid}: unsupported authority '{auth}'")
            else:
                authority_mismatches.append(f"{uid}: missing authority")

            # Cross-check with teaching record
            if uid in teaching_by_id:
                t_auth = teaching_by_id[uid]
                if t_auth != auth:
                    authority_mismatches.append(f"{uid}: curation authority='{auth}' vs teaching authority='{t_auth}'")
            else:
                missing_counterparts.append(f"{uid}: no corresponding teaching record")

            for f in u.get("flags", []):
                flag_counts[f] += 1

            # Collect explicit source_anomalies from curation index
            for anomaly in u.get("source_anomalies", []):
                source_anomalies.append(f"{uid}: {anomaly}")

    # Check for teaching records with no curation counterpart
    for tid, t_auth in teaching_by_id.items():
        if tid not in seen_ids:
            missing_counterparts.append(f"{tid}: no corresponding curation-index unit")

    return {
        "total_units": len(all_units),
        "duplicate_ids": duplicate_ids,
        "authority_counts": dict(authority_counts),
        "flag_counts": dict(flag_counts),
        "missing_fields": missing_fields,
        "authority_mismatches": authority_mismatches,
        "missing_counterparts": missing_counterparts,
        "source_anomalies": source_anomalies,
    }


def print_report(teaching: dict, curation: dict) -> int:
    """Print audit report. Returns exit code (0=clean, 1=has failures)."""
    has_failures = False

    print("=" * 60)
    print("MAHAPERIYAVA CORPUS METADATA AUDIT")
    print("=" * 60)

    # 1. Total teaching records
    print(f"\n1. TOTAL TEACHING RECORDS: {teaching['total_records']}")
    for batch, count in teaching['by_batch'].items():
        print(f"   {Path(batch).name}: {count}")

    # 2. Records by authority
    print("\n2. RECORDS BY AUTHORITY:")
    for auth in ["dk_attested", "dk_print_checked", "earlier_witness_supported", "primary_source_verified", "unattested"]:
        count = teaching['authority_counts'].get(auth, 0)
        if count:
            print(f"   {auth}: {count}")

    # 3. Unique chapter count (by stable identity)
    print(f"\n3. UNIQUE CHAPTERS (by volume+ordinal/url): {teaching['chapter_count']}")
    for ch_key, cnt in sorted(teaching['chapters'].items()):
        vol, ordinal_or_url = ch_key
        if isinstance(ordinal_or_url, int):
            print(f"   volume={vol}, chapter_ordinal={ordinal_or_url}: {cnt}")
        else:
            print(f"   volume={vol}, digital_url={ordinal_or_url}: {cnt}")

    # 4. Flag vocabulary
    print(f"\n4. UNIQUE FLAGS ({len(teaching['flag_counts'])}):")
    for flag, cnt in sorted(teaching['flag_counts'].items()):
        print(f"   {flag}: {cnt}")

    # 5. Duplicate teaching IDs
    print(f"\n5. DUPLICATE TEACHING IDs: {len(teaching['duplicate_ids'])}")
    for did in teaching['duplicate_ids']:
        print(f"   {did}")
    if teaching['duplicate_ids']:
        has_failures = True

    # 6. Curation-index authority mismatches
    print(f"\n6. CURATION-INDEX AUTHORITY MISMATCHES: {len(curation['authority_mismatches'])}")
    for m in curation['authority_mismatches']:
        print(f"   {m}")
    if curation['authority_mismatches']:
        has_failures = True

    # 7. Rights-policy violations
    print(f"\n7. RIGHTS-POLICY VIOLATIONS: {len(teaching['rights_violations'])}")
    for v in teaching['rights_violations']:
        print(f"   {v}")
    if teaching['rights_violations']:
        has_failures = True

    # 8. Provenance inconsistencies
    print(f"\n8. PROVENANCE INCONSISTENCIES: {len(teaching['provenance_issues'])}")
    for p in teaching['provenance_issues']:
        print(f"   {p}")
    if teaching['provenance_issues']:
        has_failures = True

    # 9. Recorded source anomalies
    print(f"\n9. RECORDED SOURCE ANOMALIES: {len(curation['source_anomalies'])}")
    for a in curation['source_anomalies']:
        print(f"   {a}")

    # 10. Source decode replacements
    print(f"\n10. SOURCE_DECODE_REPLACEMENT FLAGS: {teaching['decode_replacements']}")

    # 11. Missing required fields
    print(f"\n11. MISSING REQUIRED FIELDS (teaching): {len(teaching['missing_fields'])}")
    for m in teaching['missing_fields']:
        print(f"   {m}")
    if teaching['missing_fields']:
        has_failures = True

    print(f"\n12. MISSING REQUIRED FIELDS (curation): {len(curation['missing_fields'])}")
    for m in curation['missing_fields']:
        print(f"   {m}")
    if curation['missing_fields']:
        has_failures = True

    # 13. Authority validation issues
    print(f"\n13. AUTHORITY VALIDATION ISSUES: {len(teaching['authority_issues'])}")
    for a in teaching['authority_issues']:
        print(f"   {a}")
    if teaching['authority_issues']:
        has_failures = True

    # 14. Duplicate curation IDs
    print(f"\n14. DUPLICATE CURATION IDs: {len(curation['duplicate_ids'])}")
    for d in curation['duplicate_ids']:
        print(f"   {d}")
    if curation['duplicate_ids']:
        has_failures = True

    # 15. Missing counterparts
    print(f"\n15. MISSING TEACHING/CURATION COUNTERPARTS: {len(curation['missing_counterparts'])}")
    for m in curation['missing_counterparts']:
        print(f"   {m}")
    if curation['missing_counterparts']:
        has_failures = True

    # Summary
    print("\n" + "=" * 60)
    if has_failures:
        print("AUDIT: FAIL (see issues above)")
    else:
        print("AUDIT: PASS (no blocking issues)")
    print("=" * 60)

    return 1 if has_failures else 0


def main() -> int:
    teaching_files, curation_files = discover_tracked_files()
    teaching = audit_teaching_records(teaching_files)
    curation = audit_curation_index(curation_files)
    return print_report(teaching, curation)


if __name__ == "__main__":
    sys.exit(main())