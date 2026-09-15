#!/usr/bin/env python3
"""
Mahaperiyava Corpus Metadata Auditor

Inspects TRACKED metadata only. Does NOT open data/private/ or sources/raw/.
Audits all tracked Mahaperiyava teaching-record JSONL and curation-index JSON files.
"""
from __future__ import annotations
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Tracked files to audit
TEACHING_FILES = [
    ROOT / "data/review/mahaperiyava_dk_v1_pilot_teaching_records.jsonl",
    ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_teaching_records.jsonl",
    ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_teaching_records.jsonl",
    ROOT / "data/review/mahaperiyava_dk_v1_batch_046_065_teaching_records.jsonl",
]

CURATION_FILES = [
    ROOT / "data/review/mahaperiyava_dk_v1_pilot_curation_index.json",
    ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_curation_index.json",
    ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_curation_index.json",
    ROOT / "data/review/mahaperiyava_dk_v1_batch_046_065_curation_index.json",
]

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


def audit_teaching_records(files: list[Path]) -> dict[str, Any]:
    all_records = []
    seen_ids = set()
    duplicate_ids = []
    authority_counts = Counter()
    flag_counts = Counter()
    chapter_counts = Counter()
    missing_fields = []
    malformed = []
    rights_violations = []
    authority_issues = []
    provenance_issues = []
    source_title_anomalies = []
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
                # Check exact_text_restricted not in tracked
                if "exact_text_restricted" in r and r["exact_text_restricted"] is not None:
                    rights_violations.append(f"{rid}: tracked record contains non-null exact_text_restricted")

            # Flags
            for f in r.get("flags", []):
                flag_counts[f] += 1
                if "source_decode_replacement" in f.lower():
                    decode_replacements += 1

            # Chapter tracking
            chapter = r.get("source_locus", {}).get("chapter_title_ta")
            if chapter:
                chapter_counts[chapter] += 1

            # Provenance consistency
            prov = r.get("provenance", [])
            for p in prov:
                if "snapshot_sha256" not in p:
                    provenance_issues.append(f"{rid}: provenance entry missing snapshot_sha256")
                if "witness_role" not in p:
                    provenance_issues.append(f"{rid}: provenance entry missing witness_role")

            # Source title anomalies (already recorded in metadata)
            source_locus = r.get("source_locus", {})
            digital_url = source_locus.get("digital_url", "")
            if digital_url and "kamakoti.org" in digital_url:
                if "part1kural" not in digital_url:
                    source_title_anomalies.append(f"{rid}: unexpected digital_url pattern: {digital_url}")

    return {
        "total_records": len(all_records),
        "by_batch": {str(f): len(load_jsonl(f)) for f in files if f.exists()},
        "duplicate_ids": duplicate_ids,
        "authority_counts": dict(authority_counts),
        "flag_counts": dict(flag_counts),
        "chapter_count": len(chapter_counts),
        "chapters": dict(chapter_counts),
        "missing_fields": missing_fields,
        "authority_issues": authority_issues,
        "rights_violations": rights_violations,
        "provenance_issues": provenance_issues,
        "source_title_anomalies": source_title_anomalies,
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

    # Build teaching record authority map
    teaching_by_id = {}
    for tf in TEACHING_FILES:
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

            for f in u.get("flags", []):
                flag_counts[f] += 1

    return {
        "total_units": len(all_units),
        "duplicate_ids": duplicate_ids,
        "authority_counts": dict(authority_counts),
        "flag_counts": dict(flag_counts),
        "missing_fields": missing_fields,
        "authority_mismatches": authority_mismatches,
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

    # 3. Unique chapter count
    print(f"\n3. UNIQUE CHAPTERS: {teaching['chapter_count']}")
    for ch, cnt in sorted(teaching['chapters'].items()):
        print(f"   {ch}: {cnt}")

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

    # 9. Source-title anomalies
    print(f"\n9. SOURCE-TITLE ANOMALIES: {len(teaching['source_title_anomalies'])}")
    for a in teaching['source_title_anomalies']:
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

    # Summary
    print("\n" + "=" * 60)
    if has_failures:
        print("AUDIT: FAIL (see issues above)")
    else:
        print("AUDIT: PASS (no blocking issues)")
    print("=" * 60)

    return 1 if has_failures else 0


def main() -> int:
    teaching = audit_teaching_records(TEACHING_FILES)
    curation = audit_curation_index(CURATION_FILES)
    return print_report(teaching, curation)


if __name__ == "__main__":
    sys.exit(main())