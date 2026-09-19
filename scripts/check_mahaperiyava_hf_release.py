#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "data/review/mahaperiyava_hf_release_policy.json"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def walk_keys(obj: Any):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from walk_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk_keys(item)


def validate_release(outdir: Path) -> dict:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    manifest = json.loads((outdir / "release_manifest.json").read_text(encoding="utf-8"))
    info = json.loads((outdir / "dataset_info.json").read_text(encoding="utf-8"))

    manifest_names = {entry["path"] for entry in manifest["files"]}
    actual_names = {
        p.name for p in outdir.iterdir()
        if p.is_file() and p.name != "release_manifest.json"
    }
    if manifest_names != actual_names:
        raise ValueError(
            f"manifest file set mismatch: manifest={sorted(manifest_names)} actual={sorted(actual_names)}"
        )

    for entry in manifest["files"]:
        path = outdir / entry["path"]
        if file_sha256(path) != entry["sha256"]:
            raise ValueError(f"SHA mismatch for {entry['path']}")
        if path.stat().st_size != entry["bytes"]:
            raise ValueError(f"byte-size mismatch for {entry['path']}")

    records = [
        json.loads(line)
        for line in (outdir / "records.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(records) != policy["expected_record_count"]:
        raise ValueError(f"unexpected record count: {len(records)}")
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("duplicate IDs in release")

    allowed_top = set(policy["public_record_fields"])
    prohibited = set(policy["prohibited_record_fields"])
    volume_counts = Counter()
    authority_counts = Counter()

    for record in records:
        extra = set(record) - allowed_top
        missing = allowed_top - set(record)
        if extra or missing:
            raise ValueError(
                f"{record.get('id')}: top-level field mismatch extra={sorted(extra)} missing={sorted(missing)}"
            )
        all_keys = set(walk_keys(record))
        bad = prohibited.intersection(all_keys)
        if bad:
            raise ValueError(f"{record['id']}: prohibited keys present: {sorted(bad)}")

        serialized = json.dumps(record, ensure_ascii=False)
        for marker in policy["forbidden_value_markers"]:
            if marker.casefold() in serialized.casefold():
                raise ValueError(f"{record['id']}: forbidden marker {marker}")

        if record["rights"].get("public_export") != "metadata_only":
            raise ValueError(f"{record['id']}: not metadata_only")
        if record["claim_summary"].strip() == "":
            raise ValueError(f"{record['id']}: empty summary")

        stored_record_sha = record["record_sha256"]
        unhashed = dict(record)
        unhashed.pop("record_sha256", None)
        recomputed_record_sha = hashlib.sha256(
            json.dumps(
                unhashed,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        if stored_record_sha != recomputed_record_sha:
            raise ValueError(f"{record['id']}: record_sha256 mismatch")

        volume_counts[str(record["source"]["volume"])] += 1
        authority_counts[record["evidence_status"]["authority"]] += 1

    if dict(sorted(volume_counts.items())) != policy["expected_volume_counts"]:
        raise ValueError(f"volume count mismatch: {volume_counts}")
    if dict(sorted(authority_counts.items())) != policy["expected_authority_counts"]:
        raise ValueError(f"authority count mismatch: {authority_counts}")

    if info["source_text_included"] is not False:
        raise ValueError("dataset_info incorrectly claims source text is included")
    if info["curator_summary_is_quote"] is not False:
        raise ValueError("dataset_info incorrectly treats summaries as quotations")
    if info["publication_approval"] is not False:
        raise ValueError("publication approval must remain false until human release decision")
    if info["license"] != "other":
        raise ValueError("Hugging Face candidate must use license=other until metadata terms are chosen")

    benchmark = outdir / "retrieval_benchmark.json"
    if benchmark.exists():
        report = json.loads(benchmark.read_text(encoding="utf-8"))
        if report.get("status") != "RELEASE_BENCHMARK_GREEN":
            raise ValueError("bundled retrieval benchmark is not green")

    readme = (outdir / "README.md").read_text(encoding="utf-8")
    required_card_phrases = [
        "metadata-only",
        "not verbatim",
        "source text",
        "dk_attested",
        "publication approval",
    ]
    lowered = readme.casefold()
    for phrase in required_card_phrases:
        if phrase.casefold() not in lowered:
            raise ValueError(f"dataset card missing required disclosure: {phrase}")

    return {
        "status": "HUGGINGFACE_METADATA_RELEASE_CANDIDATE_GREEN",
        "record_count": len(records),
        "volume_counts": dict(sorted(volume_counts.items())),
        "authority_counts": dict(sorted(authority_counts.items())),
        "source_text_included": False,
        "publication_approval": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("outdir")
    args = parser.parse_args()
    result = validate_release(Path(args.outdir))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
