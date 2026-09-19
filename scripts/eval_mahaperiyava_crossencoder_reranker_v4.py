#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mahaperiyava_crossencoder_reranker_v4 import (
    CROSS_ENCODER_MODEL,
    CROSS_ENCODER_REVISION,
    CrossEncoderCandidateReranker,
    CrossEncoderScorer,
    detect_language_v4,
)

BENCHMARK = ROOT / "data/review/mahaperiyava_retrieval_benchmark_v3.json"
PHASE14 = ROOT / "data/review/mahaperiyava_candidate_reranker_checkpoint_v3.json"
OUT = ROOT / "data/review/mahaperiyava_crossencoder_reranker_checkpoint_v4.json"

QUALITY_TARGET = {
    "test_top1": 0.75,
    "test_top5": 0.90,
    "test_abstention": 1.0,
    "test_tamil_top5": 0.75,
    "test_roman_tamil_top5": 0.80,
}


def expected_rank(case, hits):
    expected_ids = set(case.get("expected_any_ids") or [])
    expected_loci = {
        (int(x["volume"]), int(x["chapter_ordinal"]))
        for x in (case.get("expected_any_loci") or [])
    }
    for rank, hit in enumerate(hits, 1):
        if hit["support_id"] in expected_ids:
            return rank
        loc = hit["source"]
        if loc.get("chapter_ordinal") is not None:
            pair = (int(loc["volume"]), int(loc["chapter_ordinal"]))
            if pair in expected_loci:
                return rank
    return None


def evaluate(cases, retrieve):
    totals = defaultdict(int)
    passed = defaultdict(int)
    rr_sum = 0.0
    by_language = defaultdict(lambda: {
        "supported": 0, "top1": 0, "top5": 0, "rr_sum": 0.0,
        "negatives": 0, "abstained": 0,
    })
    rows = []

    for case in cases:
        out = retrieve(case)
        lang = case["language"]
        rank = None
        if case["expected_status"] == "insufficient_evidence":
            totals["negative"] += 1
            by_language[lang]["negatives"] += 1
            ok = out["status"] == "insufficient_evidence"
            passed["negative"] += int(ok)
            by_language[lang]["abstained"] += int(ok)
        else:
            totals["supported"] += 1
            by_language[lang]["supported"] += 1
            rank = expected_rank(case, out["hits"])
            top1 = rank == 1
            top5 = rank is not None and rank <= 5
            passed["top1"] += int(top1)
            passed["top5"] += int(top5)
            by_language[lang]["top1"] += int(top1)
            by_language[lang]["top5"] += int(top5)
            if rank:
                rr = 1.0 / rank
                rr_sum += rr
                by_language[lang]["rr_sum"] += rr

        rows.append({
            "id": case["id"],
            "split": case["split"],
            "language": lang,
            "group": case["group"],
            "query": case["query"],
            "detected_language": detect_language_v4(case["query"]),
            "actual_status": out["status"],
            "rank": rank,
            "returned_ids": [h["support_id"] for h in out["hits"][:5]],
            "retrieval_mode": out.get("retrieval_mode"),
            "crossencoder_used": out.get("crossencoder_used"),
            "fusion_config": out.get("fusion_config"),
        })

    def rate(a, b):
        return round(a / b, 4) if b else 1.0

    lang_metrics = {}
    for lang, m in sorted(by_language.items()):
        lang_metrics[lang] = {
            "supported": m["supported"],
            "top1": rate(m["top1"], m["supported"]),
            "top5": rate(m["top5"], m["supported"]),
            "mrr": round(m["rr_sum"] / m["supported"], 4) if m["supported"] else 1.0,
            "negatives": m["negatives"],
            "abstention": rate(m["abstained"], m["negatives"]),
        }

    return {
        "cases": len(cases),
        "supported": totals["supported"],
        "negatives": totals["negative"],
        "top1": rate(passed["top1"], totals["supported"]),
        "top5": rate(passed["top5"], totals["supported"]),
        "mrr": round(rr_sum / totals["supported"], 4) if totals["supported"] else 1.0,
        "abstention": rate(passed["negative"], totals["negative"]),
        "by_language": lang_metrics,
    }, rows


def objective(m):
    if m["abstention"] < 1.0:
        return -1000 + m["abstention"]
    return 3.0 * m["top1"] + 1.0 * m["mrr"] + 0.5 * m["top5"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default=str(BENCHMARK))
    ap.add_argument("--output", default=str(OUT))
    args = ap.parse_args()

    spec = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))
    cases = spec["cases"]
    dev = [c for c in cases if c["split"] == "dev"]
    test = [c for c in cases if c["split"] == "test"]

    scorer = CrossEncoderScorer()
    retriever = CrossEncoderCandidateReranker(scorer=scorer)

    detection = {
        "correct": sum(detect_language_v4(c["query"]) == c["language"] for c in cases),
        "total": len(cases),
    }
    detection["accuracy"] = round(detection["correct"] / detection["total"], 4)

    languages = sorted({c["language"] for c in dev})
    selected = {}
    tuning = {}

    # Prewarm every DEV query exactly once. This is the expensive portion:
    # candidate generation plus cross-encoder scoring. Results are cached in
    # memory/disk, so the subsequent fusion sweep is cheap. Emit progress so
    # a CPU-bound Mac run no longer looks hung.
    print("[phase15] Prewarming DEV cross-encoder scores...", flush=True)
    for i, case in enumerate(dev, 1):
        retriever.retrieve(
            case["query"],
            top_k=5,
            language=case["language"],
            heuristic_weight=1.0,
            cross_weight=1.0,
            rrf_k=30,
        )
        if i == 1 or i % 5 == 0 or i == len(dev):
            print(
                f"[phase15] DEV prewarm {i}/{len(dev)} "
                f"({case['language']} :: {case['id']})",
                flush=True,
            )

    # All expensive cross-encoder scores are cached by scorer. Repeated DEV
    # configs only change rank fusion and therefore become cheap after first pass.
    for lang in languages:
        lang_cases = [c for c in dev if c["language"] == lang]
        options = []
        for hw in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0):
            for xw in (0.5, 1.0, 1.5, 2.0, 3.0):
                for k in (10, 30, 60):
                    m, _ = evaluate(
                        lang_cases,
                        lambda c, hw=hw, xw=xw, k=k: retriever.retrieve(
                            c["query"],
                            top_k=5,
                            language=c["language"],
                            heuristic_weight=hw,
                            cross_weight=xw,
                            rrf_k=k,
                        ),
                    )
                    options.append({
                        "heuristic_weight": hw,
                        "cross_weight": xw,
                        "rrf_k": k,
                        "objective": round(objective(m), 6),
                        "metrics": m,
                    })
        options.sort(
            key=lambda x: (
                -x["objective"],
                -x["metrics"]["top1"],
                -x["metrics"]["mrr"],
                -x["metrics"]["top5"],
                x["heuristic_weight"],
                x["cross_weight"],
                x["rrf_k"],
            )
        )
        best = options[0]
        selected[lang] = {
            "heuristic_weight": best["heuristic_weight"],
            "cross_weight": best["cross_weight"],
            "rrf_k": best["rrf_k"],
        }
        tuning[lang] = options[:12]

    def selected_retrieve(case):
        cfg = selected[case["language"]]
        return retriever.retrieve(
            case["query"],
            top_k=5,
            language=case["language"],
            **cfg,
        )

    dev_metrics, dev_rows = evaluate(dev, selected_retrieve)

    print("[phase15] Prewarming held-out TEST cross-encoder scores...", flush=True)
    for i, case in enumerate(test, 1):
        selected_retrieve(case)
        if i == 1 or i % 5 == 0 or i == len(test):
            print(
                f"[phase15] TEST prewarm {i}/{len(test)} "
                f"({case['language']} :: {case['id']})",
                flush=True,
            )

    test_metrics, test_rows = evaluate(test, selected_retrieve)

    phase14 = json.loads(PHASE14.read_text(encoding="utf-8"))
    p14test = phase14["metrics"]["test"]

    authority = retriever.authority_counts()
    expected_authority = {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }
    if authority != expected_authority:
        raise SystemExit(f"authority frontier changed: {authority}")

    ready = (
        test_metrics["top1"] >= QUALITY_TARGET["test_top1"]
        and test_metrics["top5"] >= QUALITY_TARGET["test_top5"]
        and test_metrics["abstention"] == QUALITY_TARGET["test_abstention"]
        and test_metrics["by_language"]["ta"]["top5"] >= QUALITY_TARGET["test_tamil_top5"]
        and test_metrics["by_language"]["roman_ta"]["top5"] >= QUALITY_TARGET["test_roman_tamil_top5"]
    )

    cp = {
        "version": "4.0",
        "checkpoint": "MAHAPERIYAVA_CROSSENCODER_RERANKER_V4",
        "status": (
            "PHASE15_CROSSENCODER_RERANKER_READY_FOR_SHADOW_INTEGRATION"
            if ready else
            "PHASE15_CROSSENCODER_RERANKER_RECORDED_MORE_WORK_REQUIRED"
        ),
        "decision": (
            "allow_shadow_only_integration_not_product_switch"
            if ready else
            "continue_ranking_work_before_product_switch"
        ),
        "benchmark": {
            "file": str(Path(args.benchmark).relative_to(ROOT)),
            "cases": len(cases),
            "dev_cases": len(dev),
            "test_cases": len(test),
            "quality_target": QUALITY_TARGET,
        },
        "model": {
            "name": CROSS_ENCODER_MODEL,
            "revision": CROSS_ENCODER_REVISION,
            "document_fields": [
                "claim_summary",
                "topics",
                "chapter_title_ta",
            ],
            "non_english_query_view": "public-safe concept-normalized English query view",
            "restricted_source_text_embedded_or_reranked": False,
            "model_weights_committed": False,
            "score_cache_committed": False,
        },
        "selected_fusion_by_language": selected,
        "language_detection": detection,
        "metrics": {
            "phase14_test": p14test,
            "dev": dev_metrics,
            "test": test_metrics,
            "vs_phase14_top1_delta": round(test_metrics["top1"] - p14test["top1"], 4),
            "vs_phase14_top5_delta": round(test_metrics["top5"] - p14test["top5"], 4),
            "vs_phase14_mrr_delta": round(test_metrics["mrr"] - p14test["mrr"], 4),
        },
        "authority_boundary": {
            "authority_counts": authority,
            "authority_promotions": 0,
            "retrieval_score_changes_authority": False,
            "exact_source_text_exposed": False,
            "generated_text_may_enter_corpus": False,
            "publication_approval_implied": False,
            "product_retriever_switched": False,
        },
        "dev_tuning_top_configs": tuning,
        "test_rows": test_rows,
        "limitations": [
            "Cross-encoder ranking is applied only after Phase-14 candidate generation and fail-closed checks.",
            "Tamil and Roman-Tamil queries use a heuristic public-safe English concept view; this is query normalization, not translation authority.",
            "The same 154-case benchmark is retained for direct Phase-14 comparison.",
            "Product retrieval remains unchanged even if the shadow threshold is met.",
        ],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=" * 72)
    print("PHASE 15 CROSS-ENCODER RERANKER CHECKPOINT")
    print("=" * 72)
    print("status             :", cp["status"])
    print("language detection :", detection)
    print("selected fusion    :", selected)
    print("phase14 test       :", {k: p14test[k] for k in ("top1", "top5", "mrr", "abstention")})
    print("phase15 test       :", {k: test_metrics[k] for k in ("top1", "top5", "mrr", "abstention")})
    print("Tamil test         :", test_metrics["by_language"]["ta"])
    print("Roman-Tamil test   :", test_metrics["by_language"]["roman_ta"])
    print("English test       :", test_metrics["by_language"]["en"])
    print("restricted text    : NOT USED")
    print("authority changes  : 0")
    print("product retriever  : NOT SWITCHED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
