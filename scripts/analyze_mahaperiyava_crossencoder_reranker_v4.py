#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CP = ROOT / "data/review/mahaperiyava_crossencoder_reranker_checkpoint_v4.json"
OUT = ROOT / "data/review/mahaperiyava_crossencoder_failure_analysis_v3.json"


def bucket(row):
    rank = row.get("rank")
    if row["actual_status"] == "insufficient_evidence":
        return "false_abstention"
    if rank == 1:
        return "top1"
    if rank is not None and rank <= 5:
        return "top5_not_top1"
    return "miss_top5"


def main():
    cp = json.loads(CP.read_text(encoding="utf-8"))
    rows = cp["test_rows"]

    summary = Counter()
    by_language = defaultdict(Counter)
    failures = []

    for row in rows:
        if row["group"] == "hard_negative":
            continue
        b = bucket(row)
        summary[b] += 1
        by_language[row["language"]][b] += 1
        if b != "top1":
            failures.append({
                "id": row["id"],
                "language": row["language"],
                "bucket": b,
                "query": row["query"],
                "rank": row["rank"],
                "returned_ids": row["returned_ids"],
                "fusion_config": row["fusion_config"],
            })

    payload = {
        "version": "3.0",
        "source_checkpoint": str(CP.relative_to(ROOT)),
        "summary": dict(summary),
        "by_language": {k: dict(v) for k, v in sorted(by_language.items())},
        "failures": failures,
    }
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
