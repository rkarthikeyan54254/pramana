#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ask_mahaperiyava import MahaperiyavaRetriever

CASES = ROOT / "data/review/mahaperiyava_v1_v7_retrieval_eval_cases.json"
DEFAULT_CHECKPOINT = ROOT / "data/review/mahaperiyava_v1_v7_retrieval_checkpoint.json"


def _matches(case, hits):
    ids = {x["support_id"] for x in hits}
    expected_ids = set(case.get("expected_any_ids") or [])
    if expected_ids and expected_ids.intersection(ids):
        return True
    expected_loci = {
        (int(x["volume"]), int(x["chapter_ordinal"]))
        for x in (case.get("expected_any_loci") or [])
    }
    actual_loci = {
        (int(x["source"]["volume"]), int(x["source"]["chapter_ordinal"]))
        for x in hits
        if x["source"].get("chapter_ordinal") is not None
    }
    return bool(expected_loci.intersection(actual_loci))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(DEFAULT_CHECKPOINT))
    args = ap.parse_args()

    spec = json.loads(CASES.read_text(encoding="utf-8"))
    retriever = MahaperiyavaRetriever()

    results = []
    supported_passes = supported_total = top1_passes = 0
    abstain_passes = abstain_total = 0
    represented_expected_volumes = set()

    for case in spec["cases"]:
        out = retriever.retrieve(case["query"], top_k=5)
        hits = out["hits"]
        ids = [x["support_id"] for x in hits]
        loci = [
            {"volume": x["source"]["volume"], "chapter_ordinal": x["source"]["chapter_ordinal"]}
            for x in hits
        ]

        if case["expected_status"] == "insufficient_evidence":
            abstain_total += 1
            passed = out["status"] == "insufficient_evidence"
            abstain_passes += int(passed)
            top1 = False
        else:
            supported_total += 1
            passed = out["status"] == "retrieved_evidence" and _matches(case, hits)
            supported_passes += int(passed)
            top1 = bool(hits) and _matches(case, hits[:1])
            top1_passes += int(top1)
            if passed:
                for locus in case.get("expected_any_loci") or []:
                    represented_expected_volumes.add(int(locus["volume"]))
                for hit in hits:
                    if hit["support_id"] in set(case.get("expected_any_ids") or []):
                        represented_expected_volumes.add(int(hit["source"]["volume"]))

        results.append({
            "id": case["id"],
            "query": case["query"],
            "expected_status": case["expected_status"],
            "expected_any_ids": case.get("expected_any_ids", []),
            "expected_any_loci": case.get("expected_any_loci", []),
            "actual_status": out["status"],
            "question_type": out["question_type"],
            "returned_ids": ids,
            "returned_loci": loci,
            "top5_pass": passed,
            "top1_pass": top1,
        })

    top5 = supported_passes / supported_total if supported_total else 0.0
    top1 = top1_passes / supported_total if supported_total else 0.0
    abst = abstain_passes / abstain_total if abstain_total else 1.0
    target = spec["quality_target"]
    ready = (
        top5 >= target["top5_recall"]
        and abst >= target["abstention_accuracy"]
        and len(represented_expected_volumes) >= target["minimum_distinct_volumes_hit"]
    )

    checkpoint = {
        "version": "1.0",
        "checkpoint": "MAHAPERIYAVA_V1_V7_RETRIEVAL_FOUNDATION",
        "status": "PHASE8_RETRIEVAL_READY_FOR_GROUNDED_SYNTHESIS" if ready else "PHASE8_RETRIEVAL_FOUNDATION_RECORDED_NOT_YET_READY",
        "decision": "proceed_to_grounded_synthesis_contract" if ready else "improve_retrieval_before_production_answering",
        "scope": "Deterministic retrieval over 3,368 public-safe teaching records from Deivathin Kural Volumes 1-7. No source-text generation and no authority promotion.",
        "quality_target": target,
        "metrics": {
            "supported_cases": supported_total,
            "top1_accuracy": round(top1, 4),
            "top5_recall": round(top5, 4),
            "unsupported_cases": abstain_total,
            "abstention_accuracy": round(abst, 4),
            "distinct_expected_volumes_hit": len(represented_expected_volumes),
        },
        "authority_boundary": {
            "retrieval_score_changes_authority": False,
            "answer_generation_changes_authority": False,
            "exact_source_text_exposed": False,
            "publication_approval_implied": False,
        },
        "cases": results,
        "limitations": [
            "This checkpoint evaluates metadata retrieval, not final prose quality.",
            "Curator summaries are not verbatim Mahaperiyava quotations.",
            "Broad questions use relevance sets rather than a forced single chapter.",
            "Semantic embeddings and model synthesis remain separate product layers.",
        ],
    }
    Path(args.output).write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checkpoint, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
