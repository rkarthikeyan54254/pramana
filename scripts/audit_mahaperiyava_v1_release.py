#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"
RESEARCH = ROOT / "data" / "research"

EXPECTED = {
    "records": 927,
    "dk_attested": 892,
    "earlier_witness_supported": 35,
    "chapters": 175,
    "pilot_records": 28,
    "pilot_ordinals": {4, 21, 23, 25, 32},
}

FORBIDDEN_TEACHING_KEYS = {
    "historical_witness",
    "candidate_witness",
    "match_level",
    "witness_decision",
    "partial_reason",
    "targeted_pass",
}
FORBIDDEN_SOURCE_TEXT_KEYS = {
    "text",
    "raw_text",
    "exact_text_restricted",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def has_forbidden_key(value: Any, forbidden: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            if k in forbidden:
                found.append(k)
            found.extend(has_forbidden_key(v, forbidden))
    elif isinstance(value, list):
        for v in value:
            found.extend(has_forbidden_key(v, forbidden))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    all_rows: list[dict[str, Any]] = []
    files = sorted(REVIEW.glob("mahaperiyava_dk_v1_*_teaching_records.jsonl"))
    for path in files:
        all_rows.extend(load_jsonl(path))

    ids = [r.get("id") for r in all_rows]
    if len(all_rows) != EXPECTED["records"]:
        errors.append(f"record count {len(all_rows)} != {EXPECTED['records']}")
    if len(ids) != len(set(ids)):
        errors.append("duplicate teaching-record IDs found")

    ordinals = {
        r.get("source_locus", {}).get("chapter_ordinal")
        for r in all_rows
    }
    if ordinals != set(range(1, EXPECTED["chapters"] + 1)):
        errors.append("chapter semantic frontier is not exactly 1..175")

    auth = Counter(
        r.get("evidence_status", {}).get("authority")
        for r in all_rows
    )
    if auth["dk_attested"] != EXPECTED["dk_attested"]:
        errors.append(f"dk_attested={auth['dk_attested']}")
    if auth["earlier_witness_supported"] != EXPECTED["earlier_witness_supported"]:
        errors.append(f"earlier_witness_supported={auth['earlier_witness_supported']}")
    if auth["dk_print_checked"] != 0:
        errors.append("unexpected dk_print_checked authority present")
    if auth["primary_source_verified"] != 0:
        errors.append("unexpected primary_source_verified authority present")

    for r in all_rows:
        rid = r.get("id", "<missing>")
        bad_top = FORBIDDEN_TEACHING_KEYS & set(r)
        if bad_top:
            errors.append(f"{rid}: review-only teaching fields leaked: {sorted(bad_top)}")

        leaked = has_forbidden_key(r, FORBIDDEN_SOURCE_TEXT_KEYS)
        if leaked:
            errors.append(f"{rid}: restricted source-text field(s) leaked: {sorted(set(leaked))}")

        evidence = r.get("evidence_status", {})
        provenance = r.get("provenance", [])
        roles = [p.get("witness_role") for p in provenance]
        authority = evidence.get("authority")

        if evidence.get("print_check") != "not_checked":
            errors.append(f"{rid}: print_check must remain not_checked in V1 checkpoint")
        if evidence.get("primary_source_status") != "unknown":
            errors.append(f"{rid}: primary_source_status must remain unknown in V1 checkpoint")

        if authority == "earlier_witness_supported":
            if r.get("attribution", {}).get("wording_status") != "earlier_witness_agrees":
                errors.append(f"{rid}: earlier-supported record lacks earlier_witness_agrees")
            if "official_digital" not in roles or "earlier_secondary" not in roles:
                errors.append(f"{rid}: earlier-supported record lacks dual provenance")
        elif authority == "dk_attested":
            if "earlier_secondary" in roles:
                errors.append(f"{rid}: DK-only record has earlier_secondary provenance")
        else:
            errors.append(f"{rid}: unexpected authority {authority!r}")

    pilot_path = REVIEW / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
    pilot = load_jsonl(pilot_path)
    pilot_ordinals = {
        r["source_locus"]["chapter_ordinal"] for r in pilot
    }
    if len(pilot) != EXPECTED["pilot_records"]:
        errors.append(f"pilot count {len(pilot)} != {EXPECTED['pilot_records']}")
    if pilot_ordinals != EXPECTED["pilot_ordinals"]:
        errors.append(f"pilot ordinals are {sorted(pilot_ordinals)}")

    batch_ordinals: set[int] = set()
    for path in sorted(REVIEW.glob("mahaperiyava_dk_v1_batch_*_teaching_records.jsonl")):
        batch_ordinals.update(
            r["source_locus"]["chapter_ordinal"]
            for r in load_jsonl(path)
        )
    overlap = pilot_ordinals & batch_ordinals
    if overlap:
        errors.append(f"pilot/batch chapter overlap: {sorted(overlap)}")

    queue = load_jsonl(REVIEW / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl")
    if len(queue) != 175:
        errors.append(f"queue length {len(queue)} != 175")
    if any(row.get("teaching_units_created", 0) <= 0 for row in queue):
        errors.append("one or more queue chapters lack teaching units")

    manifest_coverage = []
    for path in sorted(REVIEW.glob("mahaperiyava_dk_v1_*_curator_manifest.json")):
        m = json.loads(path.read_text(encoding="utf-8"))
        counts = m.get("counts", {})
        source = counts.get("source_paragraphs")
        covered = counts.get("covered_source_paragraphs")
        excluded = counts.get("explicitly_excluded_source_paragraphs")
        if source is None:
            continue
        # Coverage is at-least-once; explicit overlap can make covered references
        # exceed unique paragraphs, so only require covered + excluded >= source.
        if covered is None or excluded is None or covered + excluded < source:
            errors.append(f"{path.name}: incomplete paragraph accounting")
        manifest_coverage.append({
            "manifest": path.name,
            "source_paragraphs": source,
            "covered": covered,
            "excluded": excluded,
            "units": len(m.get("units", [])),
        })

    intake_path = RESEARCH / "mahaperiyava_acharyas_call_source_intake.json"
    intake_summary = None
    if not intake_path.exists():
        errors.append("Acharya's Call source intake metadata missing")
    else:
        intake = json.loads(intake_path.read_text(encoding="utf-8"))
        if intake.get("source_family", {}).get("primary_source") is not False:
            errors.append("Acharya's Call incorrectly classified as primary source")
        if intake.get("source_family", {}).get("authority_effect") != "none_until_item_level_comparison_and_snapshot":
            errors.append("Acharya's Call authority guard changed")
        target_ids = [
            tid
            for candidate in intake.get("targeted_item_level_candidates", [])
            for tid in candidate.get("dk_target_ids", [])
        ]
        by_id = {r["id"]: r for r in all_rows}
        missing = [tid for tid in target_ids if tid not in by_id]
        if missing:
            errors.append(f"Acharya's Call candidate target IDs missing: {missing}")
        wrongly_promoted = [
            tid for tid in target_ids
            if tid in by_id and by_id[tid]["evidence_status"]["authority"] != "dk_attested"
        ]
        if wrongly_promoted:
            errors.append(
                "Acharya's Call candidates were promoted before snapshot/item review: "
                + ", ".join(wrongly_promoted)
            )
        intake_summary = {
            "candidate_count": len(intake.get("targeted_item_level_candidates", [])),
            "target_record_count": len(target_ids),
            "acquisition_status": "pending_local_snapshot",
            "authority_effect": intake.get("source_family", {}).get("authority_effect"),
        }

    report = {
        "version": "0.1",
        "corpus": "mahaperiyava_teachings",
        "work": "deivathin_kural",
        "volume": 1,
        "checkpoint": "V1_SEMANTIC_FRONTIER_HARDENED_NOT_PUBLICATION_APPROVED",
        "semantic_frontier_commit": "5f73c61337f3ee4ec811637684f9412b1781ef66",
        "counts": {
            "teaching_records": len(all_rows),
            "chapters": len(ordinals),
            "dk_attested": auth["dk_attested"],
            "earlier_witness_supported": auth["earlier_witness_supported"],
            "pilot_records": len(pilot),
            "print_checked": auth["dk_print_checked"],
            "primary_source_verified": auth["primary_source_verified"],
        },
        "guardrails": {
            "no_exact_source_text_in_tracked_teaching_records": not any(
                has_forbidden_key(r, FORBIDDEN_SOURCE_TEXT_KEYS) for r in all_rows
            ),
            "review_only_witness_fields_excluded_from_teaching_records": not any(
                FORBIDDEN_TEACHING_KEYS & set(r) for r in all_rows
            ),
            "pilot_regular_batch_disjoint": not overlap,
            "authority_not_auto_upgraded": True,
            "publication_review_still_required": True,
        },
        "acharyas_call_intake": intake_summary,
        "manifest_coverage": manifest_coverage,
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }

    if args.write:
        out = REVIEW / "mahaperiyava_dk_v1_release_checkpoint.json"
        out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {out.relative_to(ROOT)}")

    print("=" * 60)
    print("V1 RELEASE HARDENING:", report["status"])
    print("=" * 60)
    print(json.dumps(report["counts"], indent=2))
    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
