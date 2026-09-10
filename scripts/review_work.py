#!/usr/bin/env python3
"""Generate a conservative, ranked source-comparison review for one work.

This is a triage engine, not a verifier.

It may:
- re-materialize a primary staging work,
- extract a pinned comparison witness,
- compare unit-by-unit,
- detect simple witness defects,
- rank likely review effort.

It must never:
- set ``verified=true``,
- silently repair source text,
- infer witness independence,
- turn similarity or Tamil projection into authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from witness_extractors import extract

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "schema/review_policy.json"
MANIFEST = ROOT / "sources/manifest.json"

SAFE_PUNCT = re.compile(r"""[\s,;:!?.\-–—"“”'‘’()\[\]{}]+""")

# Conservative Tamil sandhi/word-joining folds used ONLY for triage ranking.
# These never modify stored source text and never grant verification authority.
TAMIL_RANKING_FOLDS = (
    ("்எ", "ெ"),
    ("்ஏ", "ே"),
    ("ுஎ", "ெ"),
    ("ுஏ", "ே"),
    ("்இ", "ி"),
    ("ுஇ", "ி"),
    ("்ஆ", "ா"),
    ("ுஆ", "ா"),
    ("்உ", "ு"),
    ("ுஒ", "ொ"),
    ("ுஅ", ""),
    ("்அ", ""),
)


def strip_terminal_unit_marker(text: str, unit_no: int | None = None) -> str:
    text = text.rstrip()
    if unit_no is None:
        return text
    return re.sub(rf"\s*\(\s*{unit_no}\s*\)\s*$", "", text)


def safe_norm(text: str, unit_no: int | None = None) -> str:
    text = strip_terminal_unit_marker(text, unit_no)
    text = unicodedata.normalize("NFC", text)
    return SAFE_PUNCT.sub("", text)


def tamil_ranking_projection(text: str, unit_no: int | None = None) -> str:
    text = safe_norm(text, unit_no)
    for src, dst in TAMIL_RANKING_FOLDS:
        text = text.replace(src, dst)
    return text


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_snapshot(manifest_entry: dict) -> tuple[Path, str]:
    path = ROOT / manifest_entry["path"]
    side = path.with_suffix(path.suffix + ".sha256")
    if not path.exists() or not side.exists():
        raise ValueError(f"missing checksummed witness snapshot: {path}")
    expected = side.read_text(encoding="utf-8").strip()
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"witness checksum mismatch: {path}")
    return path, actual


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def repeated_lines(lines: list[str]) -> list[str]:
    seen = set()
    repeated = []
    for line in lines:
        key = safe_norm(line)
        if key and key in seen:
            repeated.append(line)
        seen.add(key)
    return repeated


def edit_metrics(a: str, b: str) -> dict:
    sm = SequenceMatcher(None, a, b, autojunk=False)
    edits = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        edits.append(
            {
                "tag": tag,
                "primary_span": i2 - i1,
                "secondary_span": j2 - j1,
                "primary": a[i1:i2],
                "secondary": b[j1:j2],
            }
        )

    max_span = max(
        (max(x["primary_span"], x["secondary_span"]) for x in edits),
        default=0,
    )
    edited_primary = sum(x["primary_span"] for x in edits)
    edited_secondary = sum(x["secondary_span"] for x in edits)
    replacements = sum(x["tag"] == "replace" for x in edits)
    insertions = sum(x["tag"] == "insert" for x in edits)
    deletions = sum(x["tag"] == "delete" for x in edits)
    denom = max(len(a), len(b), 1)

    return {
        "edit_block_count": len(edits),
        "replacement_block_count": replacements,
        "insertion_block_count": insertions,
        "deletion_block_count": deletions,
        "max_edit_span": max_span,
        "edited_primary_chars": edited_primary,
        "edited_secondary_chars": edited_secondary,
        "normalized_length_delta": abs(len(a) - len(b)),
        "edit_burden": round(max(edited_primary, edited_secondary) / denom, 6),
        "edit_preview": edits[:8],
    }


def machine_classify(
    primary_text: str,
    witness_text: str,
    witness_lines: list[str],
    *,
    high_similarity: float,
    unit_no: int | None = None,
) -> dict:
    a = safe_norm(primary_text, unit_no)
    b = safe_norm(witness_text, unit_no)
    pa = tamil_ranking_projection(primary_text, unit_no)
    pb = tamil_ranking_projection(witness_text, unit_no)

    exact = strip_terminal_unit_marker(primary_text, unit_no) == strip_terminal_unit_marker(
        witness_text, unit_no
    )
    normalized_exact = a == b
    similarity = SequenceMatcher(None, a, b, autojunk=False).ratio()
    projected_similarity = SequenceMatcher(None, pa, pb, autojunk=False).ratio()
    repeats = repeated_lines(witness_lines)
    metrics = edit_metrics(a, b)
    projected_metrics = edit_metrics(pa, pb)

    flags = ["comparison_only", "needs_review"]
    if repeats:
        flags.append("secondary_repeated_line")
        classification = "source_anomaly"
    elif exact:
        classification = "byte_text_match"
    elif normalized_exact:
        classification = "safe_normalized_match"
    elif similarity >= high_similarity:
        classification = "high_similarity_review_candidate"
    else:
        classification = "textual_review_required"

    return {
        "machine_classification": classification,
        "similarity": round(similarity, 6),
        "ranking_projected_similarity": round(projected_similarity, 6),
        "normalized_exact": normalized_exact,
        "source_exact": exact,
        "repeated_secondary_lines": repeats,
        **metrics,
        "ranking_projected_replacement_blocks": projected_metrics["replacement_block_count"],
        "ranking_projected_max_edit_span": projected_metrics["max_edit_span"],
        "ranking_projected_edit_burden": projected_metrics["edit_burden"],
        "flags": flags,
    }


def risk_key(row: dict) -> tuple:
    mandatory = row["machine_classification"] in {
        "source_anomaly",
        "textual_review_required",
    }
    anomaly = row["machine_classification"] == "source_anomaly"
    return (
        1 if mandatory else 0,
        1 if anomaly else 0,
        row.get("ranking_projected_replacement_blocks", 0),
        row.get("ranking_projected_max_edit_span", 0),
        row.get("ranking_projected_edit_burden", 0.0),
        1.0 - row.get("ranking_projected_similarity", row["similarity"]),
        row.get("normalized_length_delta", 0),
    )


def load_existing_human_fields(path: Path) -> dict[int, dict]:
    if not path.exists():
        return {}
    keep = {}
    for row in read_jsonl(path):
        unit = int(row["unit_no"])
        human = {}
        for key in (
            "classification",
            "variant_candidates",
            "curator_decision",
            "curator_notes",
            "reviewed_by",
            "reviewed_at",
        ):
            if key in row:
                human[key] = row[key]
        manual_flags = [
            f
            for f in row.get("flags", [])
            if f
            not in {
                "comparison_only",
                "needs_review",
                "secondary_independence_unproven",
                "secondary_repeated_line",
                "spot_check_candidate",
            }
        ]
        if manual_flags:
            human["_manual_flags"] = manual_flags
        if human:
            keep[unit] = human
    return keep


def materialize_primary(work: str, output: Path) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts/ingest_work.py"),
        work,
        "--output",
        str(output),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)


def audit_snapshots() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/audit_snapshots.py")],
        cwd=ROOT,
        check=True,
    )


def run(work: str, policy_path: Path, *, no_materialize: bool = False) -> dict:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    try:
        cfg = policy["works"][work]
    except KeyError as exc:
        raise SystemExit(
            f"work {work!r} has no review policy in {policy_path.relative_to(ROOT)}"
        ) from exc

    audit_snapshots()

    expected_units = int(cfg["expected_units"])
    primary_path = ROOT / cfg["primary"]["path"]
    if not no_materialize:
        materialize_primary(work, primary_path)
    if not primary_path.exists():
        raise SystemExit(f"missing primary staging file: {primary_path}")

    primary_rows = read_jsonl(primary_path)
    by_unit = {int(r["unit_no"]): r for r in primary_rows}
    expected = set(range(1, expected_units + 1))
    if set(by_unit) != expected or len(primary_rows) != expected_units:
        raise ValueError(
            f"primary unit coverage mismatch: rows={len(primary_rows)} "
            f"unique={len(by_unit)} expected={expected_units}"
        )
    if any(r.get("verified") is True for r in primary_rows):
        raise ValueError(
            "review engine refuses a primary staging file containing verified=true"
        )

    witness_cfg = cfg["witness"]
    manifest = {
        x["key"]: x
        for x in json.loads(MANIFEST.read_text(encoding="utf-8"))["sources"]
    }
    try:
        manifest_entry = manifest[witness_cfg["key"]]
    except KeyError as exc:
        raise ValueError(
            f"comparison witness missing from manifest: {witness_cfg['key']}"
        ) from exc

    witness_path, witness_sha = checked_snapshot(manifest_entry)
    witness_units = extract(
        witness_cfg["extractor"],
        witness_path,
        expected_units,
        **witness_cfg.get("extractor_options", {}),
    )

    out_path = ROOT / cfg["outputs"]["review_jsonl"]
    summary_path = ROOT / cfg["outputs"]["summary_json"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    existing_human = load_existing_human_fields(out_path)
    high_similarity = float(
        cfg.get("thresholds", {}).get("high_similarity_review_candidate", 0.97)
    )
    spot_check_fraction = float(
        cfg.get("review_sampling", {}).get("spot_check_fraction", 0.05)
    )
    spot_check_minimum = int(
        cfg.get("review_sampling", {}).get("spot_check_minimum", 3)
    )

    rows = []
    for unit_no in range(1, expected_units + 1):
        primary = by_unit[unit_no]
        secondary = witness_units[unit_no]
        machine = machine_classify(
            primary["text_original"],
            secondary["text"],
            secondary["lines"],
            high_similarity=high_similarity,
            unit_no=unit_no,
        )

        flags = list(machine.pop("flags"))
        independence = witness_cfg.get("independence", "unproven")
        if independence != "established":
            flags.append("secondary_independence_unproven")

        row = {
            "work": work,
            "unit_no": unit_no,
            "primary_record_id": primary["id"],
            "primary_source": primary.get("source"),
            "comparison_source_key": witness_cfg["key"],
            "comparison_source": manifest_entry.get("url"),
            "comparison_source_sha256": witness_sha,
            "primary_text": primary["text_original"],
            "comparison_text": secondary["text"],
            **machine,
            "authority_status": "unverified",
            "review_status": "needs_review",
            "flags": flags,
        }

        human = existing_human.get(unit_no, {})
        manual_flags = human.pop("_manual_flags", [])
        row.update(human)
        for flag in manual_flags:
            if flag not in row["flags"]:
                row["flags"].append(flag)
        rows.append(row)

    mandatory = [
        r for r in rows
        if r["machine_classification"] in {"source_anomaly", "textual_review_required"}
    ]
    triaged = [
        r for r in rows
        if r["machine_classification"]
        in {"high_similarity_review_candidate", "safe_normalized_match", "byte_text_match"}
    ]

    desired_spot_checks = max(
        spot_check_minimum,
        math.ceil(expected_units * spot_check_fraction),
    )
    spot_checks = sorted(triaged, key=risk_key, reverse=True)[:desired_spot_checks]
    spot_units = {r["unit_no"] for r in spot_checks}
    for row in rows:
        if row["unit_no"] in spot_units and "spot_check_candidate" not in row["flags"]:
            row["flags"].append("spot_check_candidate")

    ranked = sorted(rows, key=risk_key, reverse=True)
    for priority, row in enumerate(ranked, start=1):
        row["manual_review_priority"] = priority

    counts = Counter(r["machine_classification"] for r in rows)
    human_classified = sum("classification" in r for r in rows)

    out_path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )

    summary = {
        "work": work,
        "authority": (
            "Comparison/triage only. Similarity, Tamil ranking projection, risk "
            "ranking, and sampling never grant verification authority."
        ),
        "primary_rows": len(primary_rows),
        "comparison_rows": len(witness_units),
        "comparison_witness": witness_cfg["key"],
        "comparison_sha256": witness_sha,
        "witness_independence": witness_cfg.get("independence", "unproven"),
        "machine_classification_counts": dict(sorted(counts.items())),
        "human_classified_rows_preserved": human_classified,
        "mandatory_manual_review": len(mandatory),
        "spot_check_count": len(spot_checks),
        "machine_triaged_without_spot_check": max(0, len(triaged) - len(spot_checks)),
        "spot_check_units": [r["unit_no"] for r in spot_checks],
        "lowest_similarity": [
            {
                "unit_no": r["unit_no"],
                "similarity": r["similarity"],
                "machine_classification": r["machine_classification"],
            }
            for r in sorted(rows, key=lambda x: x["similarity"])[:10]
        ],
        "highest_risk_machine_triaged": [
            {
                "unit_no": r["unit_no"],
                "similarity": r["similarity"],
                "ranking_projected_similarity": r["ranking_projected_similarity"],
                "projected_replacement_blocks": r["ranking_projected_replacement_blocks"],
                "projected_max_edit_span": r["ranking_projected_max_edit_span"],
                "projected_edit_burden": r["ranking_projected_edit_burden"],
            }
            for r in sorted(triaged, key=risk_key, reverse=True)[:10]
        ],
        "review_jsonl": str(out_path.relative_to(ROOT)),
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--policy", default=str(DEFAULT_POLICY))
    ap.add_argument("--no-materialize", action="store_true")
    args = ap.parse_args()

    summary = run(args.work, Path(args.policy), no_materialize=args.no_materialize)

    print()
    print("=== REVIEW SUMMARY ===")
    print("work:", summary["work"])
    print("primary:", summary["primary_rows"])
    print("secondary:", summary["comparison_rows"])
    for key, value in summary["machine_classification_counts"].items():
        print(f"{key}: {value}")
    print("human classifications preserved:", summary["human_classified_rows_preserved"])
    print("mandatory manual review:", summary["mandatory_manual_review"])
    print("QA spot-check:", summary["spot_check_count"], "units", summary["spot_check_units"])
    print("machine-triaged without spot-check:", summary["machine_triaged_without_spot_check"])
    print("lowest similarity:")
    for row in summary["lowest_similarity"][:5]:
        print(
            f"  {row['unit_no']:>3}  {row['similarity']:.6f}  "
            f"{row['machine_classification']}"
        )
    print("authority: UNVERIFIED comparison/triage only")


if __name__ == "__main__":
    main()
