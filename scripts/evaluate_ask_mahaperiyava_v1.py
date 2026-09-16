#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from ask_mahaperiyava_v1 import V1Retriever

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data" / "review" / "mahaperiyava_dk_v1_retrieval_eval_cases.json"
OUTPUT = ROOT / "data" / "review" / "mahaperiyava_dk_v1_retrieval_checkpoint.json"


def main() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    retriever = V1Retriever()

    details = []
    supported = 0
    top1 = 0
    top5 = 0
    unsupported = 0
    abstained = 0

    for case in cases:
        result = retriever.retrieve(case["query"], top_k=5)
        entry = {
            "id": case["id"],
            "query": case["query"],
            "expected_chapter": case.get("expected_chapter"),
            "expected_status": case.get("expected_status", "retrieved_evidence"),
            "actual_status": result["status"],
            "returned_chapters": [h["chapter_ordinal"] for h in result["hits"]],
            "returned_ids": [h["id"] for h in result["hits"]],
        }

        if case.get("expected_status") == "insufficient_evidence":
            unsupported += 1
            if result["status"] == "insufficient_evidence":
                abstained += 1
                entry["pass"] = True
            else:
                entry["pass"] = False
        else:
            supported += 1
            target = case["expected_chapter"]
            chapters = entry["returned_chapters"]
            if chapters and chapters[0] == target:
                top1 += 1
            if target in chapters:
                top5 += 1
                entry["pass"] = True
            else:
                entry["pass"] = False

        details.append(entry)

    metrics = {
        "supported_cases": supported,
        "top1_accuracy": round(top1 / supported, 4) if supported else 0.0,
        "top5_recall": round(top5 / supported, 4) if supported else 0.0,
        "unsupported_cases": unsupported,
        "abstention_accuracy": round(abstained / unsupported, 4) if unsupported else 0.0,
    }

    quality_target = {
        "top5_recall": 0.85,
        "abstention_accuracy": 1.0,
    }
    ready = (
        metrics["top5_recall"] >= quality_target["top5_recall"]
        and metrics["abstention_accuracy"] >= quality_target["abstention_accuracy"]
    )

    checkpoint = {
        "version": "0.2",
        "checkpoint": "THIN_V1_RETRIEVAL_BASELINE",
        "status": (
            "RETRIEVAL_CHECKPOINT_READY"
            if ready
            else "BASELINE_RECORDED_RETRIEVAL_NOT_READY"
        ),
        "decision": (
            "checkpoint_meets_current_retrieval_gate"
            if ready
            else "do_not_use_as_production_answerer"
        ),
        "scope": "Deterministic lexical/concept retrieval over curator metadata; no LLM answer generation.",
        "quality_target": quality_target,
        "metrics": metrics,
        "failed_case_ids": [d["id"] for d in details if not d["pass"]],
        "cases": details,
        "limitations": [
            "This is a retrieval checkpoint, not a production conversational answerer.",
            "Claim summaries are metadata, not verbatim Mahaperiyava quotations.",
            "Tamil support is limited to a small transparent concept-alias layer.",
            "Authority labels are displayed but do not determine relevance ranking.",
            "Broad-topic queries can have several valid V1 chapters; the current single-target evaluation is diagnostic rather than proof that other relevant chapters are wrong.",
        ],
    }

    OUTPUT.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(metrics, indent=2))
    failed = [d["id"] for d in details if not d["pass"]]
    if failed:
        print("FAILED CASES:", ", ".join(failed))

    # This command records a baseline. Retrieval quality is a product metric,
    # not a corpus-integrity gate. Weakness must remain visible in the checkpoint.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
