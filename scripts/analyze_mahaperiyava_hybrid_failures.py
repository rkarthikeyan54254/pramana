#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "data/review/mahaperiyava_hybrid_retrieval_checkpoint_v1.json"
DEFAULT_OUT = ROOT / "data/review/mahaperiyava_hybrid_failure_analysis_v1.json"


def bucket(lex_rank, hy_rank, hy_status):
    if hy_status == "insufficient_evidence":
        return "hybrid_abstained_supported"
    if hy_rank == 1:
        if lex_rank == 1:
            return "both_top1"
        return "hybrid_top1_rescue"
    if hy_rank is not None and hy_rank <= 5:
        if lex_rank is not None and lex_rank <= 5:
            return "both_top5_hybrid_not_top1"
        return "hybrid_top5_rescue"
    if lex_rank is not None and lex_rank <= 5:
        return "hybrid_regression_from_lexical_top5"
    return "miss_both"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=str(DEFAULT_IN))
    ap.add_argument("--output", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    cp = json.loads(Path(args.checkpoint).read_text(encoding="utf-8"))
    lex = {x["id"]: x for x in cp["test_rows"]["lexical"]}
    hy = {x["id"]: x for x in cp["test_rows"]["hybrid"]}

    rows = []
    totals = Counter()
    by_language = defaultdict(Counter)
    for cid in sorted(set(lex) & set(hy)):
        l = lex[cid]
        h = hy[cid]
        if l["expected_status"] == "insufficient_evidence":
            continue
        b = bucket(l.get("rank"), h.get("rank"), h.get("actual_status"))
        totals[b] += 1
        by_language[h["language"]][b] += 1
        rows.append({
            "id": cid,
            "language": h["language"],
            "query": h["query"],
            "bucket": b,
            "lexical_rank": l.get("rank"),
            "hybrid_rank": h.get("rank"),
            "hybrid_status": h.get("actual_status"),
            "lexical_returned_ids": l.get("returned_ids", []),
            "hybrid_returned_ids": h.get("returned_ids", []),
        })

    out = {
        "version": "1.0",
        "source_checkpoint": str(Path(args.checkpoint).relative_to(ROOT)),
        "summary": dict(totals),
        "by_language": {k: dict(v) for k, v in sorted(by_language.items())},
        "rows": rows,
        "diagnosis": [
            "English held-out retrieval is already comparatively strong.",
            "Tamil-script retrieval is the dominant weakness and must be improved without weakening abstention.",
            "Roman-Tamil benefits from lexical augmentation but still has avoidable misses.",
            "Phase 13 therefore uses field-separated semantic retrieval, broader language normalization, and dev-only model/config selection.",
        ],
    }
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": out["summary"], "by_language": out["by_language"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
