#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ask_mahaperiyava import load_corpus

POLICY_PATH = ROOT / "data/review/mahaperiyava_hf_release_policy.json"
MANUAL_EVAL = ROOT / "data/review/mahaperiyava_v1_v7_retrieval_eval_cases.json"
CARD_PATH = ROOT / "docs/HUGGINGFACE_MAHAPERIYAVA_DATASET_CARD.md"

ALLOWED_AUTHORITY = {
    "dk_attested",
    "dk_print_checked",
    "earlier_witness_supported",
    "primary_source_verified",
}


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_provenance(record: dict[str, Any], fields: set[str]) -> list[dict[str, Any]]:
    out = []
    for witness in record.get("provenance") or []:
        item = {k: witness.get(k) for k in fields if witness.get(k) is not None}
        if item:
            out.append(item)
    return out


def export_record(record: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    rights = record.get("rights") or {}
    if rights.get("public_export") != policy["rights_contract"]["public_export_required"]:
        raise ValueError(
            f"{record['id']}: public_export={rights.get('public_export')!r}, expected metadata_only"
        )
    if not record.get("claim_summary"):
        raise ValueError(f"{record['id']}: missing curator claim_summary")
    authority = (record.get("evidence_status") or {}).get("authority")
    if authority not in ALLOWED_AUTHORITY:
        raise ValueError(f"{record['id']}: unsupported authority {authority!r}")

    locus = record["source_locus"]
    source_fields = set(policy["source_fields"])
    attribution_fields = set(policy["attribution_fields"])
    evidence_fields = set(policy["evidence_status_fields"])
    provenance_fields = set(policy["provenance_fields"])
    rights_fields = set(policy["rights_fields"])

    row = {
        "id": record["id"],
        "corpus": record["corpus"],
        "work": record["work"],
        "teacher": record["teacher"],
        "compiler": record.get("compiler"),
        "language": record["language"],
        "claim_summary": record["claim_summary"],
        "topics": list(record.get("topics") or []),
        "flags": list(record.get("flags") or []),
        "source": {k: locus.get(k) for k in source_fields if locus.get(k) is not None},
        "attribution": {
            k: (record.get("attribution") or {}).get(k)
            for k in attribution_fields
            if (record.get("attribution") or {}).get(k) is not None
        },
        "evidence_status": {
            k: (record.get("evidence_status") or {}).get(k)
            for k in evidence_fields
            if (record.get("evidence_status") or {}).get(k) is not None
        },
        "provenance": safe_provenance(record, provenance_fields),
        "rights": {
            k: rights.get(k)
            for k in rights_fields
            if rights.get(k) is not None
        },
        "citation": (
            f"Deivathin Kural, Volume {locus['volume']}, "
            f"Chapter {locus.get('chapter_ordinal')}: {locus['chapter_title_ta']}"
        ),
    }

    prehash = canonical_bytes(row)
    row["record_sha256"] = sha256_bytes(prehash)

    serialized = canonical_bytes(row).decode("utf-8")
    for marker in policy["forbidden_value_markers"]:
        if marker.casefold() in serialized.casefold():
            raise ValueError(f"{record['id']}: forbidden marker leaked: {marker}")
    return row


def build(outdir: Path, benchmark_path: Path | None = None) -> dict[str, Any]:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    rows = load_corpus()

    if len(rows) != policy["expected_record_count"]:
        raise ValueError(
            f"record count changed: {len(rows)} != {policy['expected_record_count']}"
        )

    exported = [export_record(row, policy) for row in rows]
    exported.sort(
        key=lambda r: (
            int(r["source"]["volume"]),
            int(r["source"].get("chapter_ordinal") or 10**9),
            r["id"],
        )
    )

    ids = [r["id"] for r in exported]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate exported teaching IDs")

    volume_counts = Counter(str(r["source"]["volume"]) for r in exported)
    authority_counts = Counter(r["evidence_status"]["authority"] for r in exported)
    flag_counts = Counter(flag for r in exported for flag in r["flags"])

    if dict(sorted(volume_counts.items())) != policy["expected_volume_counts"]:
        raise ValueError(
            f"volume count drift: {dict(sorted(volume_counts.items()))}"
        )
    if dict(sorted(authority_counts.items())) != policy["expected_authority_counts"]:
        raise ValueError(
            f"authority count drift: {dict(sorted(authority_counts.items()))}"
        )

    outdir.mkdir(parents=True, exist_ok=True)

    records_path = outdir / "records.jsonl"
    with records_path.open("w", encoding="utf-8") as handle:
        for row in exported:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    shutil.copy2(POLICY_PATH, outdir / "release_policy.json")
    shutil.copy2(MANUAL_EVAL, outdir / "retrieval_eval_cases.json")
    shutil.copy2(CARD_PATH, outdir / "README.md")

    benchmark_included = False
    if benchmark_path and benchmark_path.exists():
        shutil.copy2(benchmark_path, outdir / "retrieval_benchmark.json")
        benchmark_included = True

    dataset_info = {
        "dataset": "pramana_mahaperiyava_deivathin_kural_v1_v7_metadata",
        "release_kind": "metadata_only_candidate",
        "record_count": len(exported),
        "volume_counts": dict(sorted(volume_counts.items())),
        "authority_counts": dict(sorted(authority_counts.items())),
        "flag_counts": dict(flag_counts.most_common()),
        "languages": ["ta", "en"],
        "source_text_included": False,
        "curator_summary_is_quote": False,
        "publication_approval": policy["publication_approval"],
        "license": policy["rights_contract"]["dataset_license_field"],
        "benchmark_included": benchmark_included,
        "baseline_commit": policy["baseline_commit"],
    }
    (outdir / "dataset_info.json").write_text(
        json.dumps(dataset_info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    files = sorted(p for p in outdir.iterdir() if p.is_file() and p.name != "release_manifest.json")
    manifest = {
        "version": "1.0",
        "profile": policy["profile"],
        "baseline_commit": policy["baseline_commit"],
        "record_count": len(exported),
        "source_text_included": False,
        "publication_approval": policy["publication_approval"],
        "files": [
            {
                "path": p.name,
                "sha256": file_sha256(p),
                "bytes": p.stat().st_size,
            }
            for p in files
        ],
    }
    (outdir / "release_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"dataset_info": dataset_info, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        default=str(ROOT / "dist/huggingface/mahaperiyava-deivathin-kural-v1-v7"),
    )
    parser.add_argument("--benchmark")
    args = parser.parse_args()
    result = build(
        Path(args.outdir),
        Path(args.benchmark) if args.benchmark else None,
    )
    print(json.dumps(result["dataset_info"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
