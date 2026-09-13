#!/usr/bin/env python3
"""Fetch immutable raw source snapshots with provenance sidecars.

Designed for a network-enabled laptop/CI runner.

Raw snapshots are not committed to the public repository. Therefore a manifest
entry may pin expected_sha256 / expected_bytes. When present, fetching fails
closed if the remote resource changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def expanded(entry):
    if entry.get("url_template") and entry.get("chapters"):
        for chapter in entry["chapters"]:
            e = dict(entry)
            e["key"] = f"{entry['key']}-ch{chapter}"
            e["url"] = entry["url_template"].format(
                chapter=chapter,
                CHAPTER=chapter,
            )
            e["path"] = entry["path"].format(
                chapter=chapter,
                CHAPTER=chapter,
            )
            e["parent_key"] = entry["key"]
            e["chapter"] = chapter
            yield e
    else:
        yield entry


def enforce_expected_snapshot(entry, data: bytes) -> str:
    """Return SHA-256 and fail closed against an optional manifest lock."""

    actual_sha = hashlib.sha256(data).hexdigest()
    actual_bytes = len(data)

    expected_sha = entry.get("expected_sha256")
    if expected_sha and actual_sha != expected_sha:
        raise ValueError(
            f"source hash mismatch for {entry['key']}: "
            f"expected {expected_sha}, got {actual_sha}"
        )

    expected_bytes = entry.get("expected_bytes")
    if expected_bytes is not None and actual_bytes != expected_bytes:
        raise ValueError(
            f"source byte-length mismatch for {entry['key']}: "
            f"expected {expected_bytes}, got {actual_bytes}"
        )

    return actual_sha


def fetch(entry, force=False, timeout=45):
    out = Path(entry["path"])
    out.parent.mkdir(parents=True, exist_ok=True)

    side = out.with_suffix(out.suffix + ".sha256")
    meta_path = out.with_suffix(out.suffix + ".meta.json")

    if out.exists() and not force:
        data = out.read_bytes()
        sha = enforce_expected_snapshot(entry, data)

        if not side.exists() or not meta_path.exists():
            raise ValueError(
                f"unprovenanced existing snapshot: {out}"
            )

        if side.read_text().strip() != sha:
            raise ValueError(
                f"snapshot checksum mismatch: {out}"
            )

        meta = json.loads(
            meta_path.read_text(encoding="utf-8")
        )

        if meta["sha256"] != sha:
            raise ValueError(
                f"snapshot metadata checksum mismatch: {out}"
            )

        if meta["url"] != entry["url"]:
            raise ValueError(
                f"snapshot provenance URL mismatch: {out}"
            )

        print(
            "SKIP",
            entry["key"],
            len(data),
            "bytes",
            sha,
        )
        return meta

    req = urllib.request.Request(
        entry["url"],
        headers={
            "User-Agent":
                "bhakthi-corpus/0.2 "
                "provenance-preserving research fetch"
        },
    )

    with urllib.request.urlopen(
        req,
        timeout=timeout,
    ) as response:
        data = response.read()
        content_type = response.headers.get(
            "Content-Type"
        )
        final_url = response.geturl()

    # Critical: validate before writing changed remote bytes locally.
    sha = enforce_expected_snapshot(entry, data)

    out.write_bytes(data)

    side.write_text(
        sha + "\n",
        encoding="utf-8",
    )

    meta = {
        "key": entry["key"],
        "parent_key": entry.get("parent_key"),
        "url": entry["url"],
        "path": str(out),
        "sha256": sha,
        "bytes": len(data),
        "final_url": final_url,
        "content_type": content_type,
        "fetched_or_checked_at_utc":
            datetime.now(timezone.utc).isoformat(),
        "source_status": entry.get("status"),
        "recorded_terms": entry.get("terms"),
        "covers": entry.get("covers"),
    }

    meta_path.write_text(
        json.dumps(
            meta,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "FETCHED",
        entry["key"],
        len(data),
        "bytes",
        sha,
    )

    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--keys",
        help="comma-separated manifest keys",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--index",
        default="sources/SNAPSHOT_INDEX.json",
    )
    args = ap.parse_args()

    manifest = json.loads(
        Path(args.manifest).read_text(
            encoding="utf-8"
        )
    )

    wanted = (
        set(args.keys.split(","))
        if args.keys
        else None
    )

    entries = []

    for base in manifest["sources"]:
        if wanted and base["key"] not in wanted:
            continue
        entries.extend(expanded(base))

    if wanted:
        found = {
            e.get("parent_key", e["key"])
            for e in entries
        }
        missing = wanted - found

        if missing:
            raise SystemExit(
                f"unknown source keys: {sorted(missing)}"
            )

    if args.dry_run:
        for e in entries:
            print(
                e["key"],
                e["url"],
                "->",
                e["path"],
            )
        return

    index_path = Path(args.index)
    index_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if index_path.exists():
        existing = json.loads(
            index_path.read_text(
                encoding="utf-8"
            )
        ).get("snapshots", [])
    else:
        existing = []

    merged = {
        s["key"]: s
        for s in existing
    }

    failures = []

    for e in entries:
        try:
            merged[e["key"]] = fetch(e)
        except Exception as error:
            failures.append({
                "key": e["key"],
                "error": str(error),
            })
            print(
                "FAILED",
                e["key"],
                str(error),
            )

    snapshots = sorted(
        merged.values(),
        key=lambda s: s["key"],
    )

    index_path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "snapshot_count": len(snapshots),
                "snapshots": snapshots,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "snapshot-index",
        index_path,
        len(snapshots),
    )

    if failures:
        index_path.with_name(
            "FETCH_FAILURES.json"
        ).write_text(
            json.dumps(
                failures,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
