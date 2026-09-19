#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CP = ROOT / "data/review/mahaperiyava_candidate_reranker_checkpoint_v3.json"
OUT = ROOT / "data/review/mahaperiyava_candidate_reranker_failure_analysis_v2.json"


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
    buckets = Counter(bucket(r) for r in rows if r["group"] != "hard_negative")
    by_lang = defaultdict(Counter)
    failures = []
    for row in rows:
        if row["group"] == "hard_negative":
            continue
        b = bucket(row)
        by_lang[row["language"]][b] += 1
        if b != "top1":
            failures.append({
                "id": row["id"],
                "language": row["language"],
                "bucket": b,
                "query": row["query"],
                "rank": row["rank"],
                "profile": row["profile"],
                "concept_query": row.get("concept_query"),
                "returned_ids": row["returned_ids"],
            })

    out = {
        "version": "2.0",
        "source_checkpoint": str(CP.relative_to(ROOT)),
        "summary": dict(buckets),
        "by_language": {k: dict(v) for k, v in sorted(by_lang.items())},
        "failures": failures,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))


if __name__ == "__main__":
    main()
