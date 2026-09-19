#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ask_mahaperiyava import MahaperiyavaRetriever
from mahaperiyava_hybrid_retrieval import (
    DEFAULT_MODEL,
    DEFAULT_REVISION,
    HybridMahaperiyavaRetriever,
    SentenceTransformerEmbedder,
)

BENCHMARK = ROOT / "data/review/mahaperiyava_retrieval_benchmark_v2.json"
DEFAULT_OUT = ROOT / "data/review/mahaperiyava_hybrid_retrieval_checkpoint_v1.json"


def expected_rank(case, hits):
    expected_ids = set(case.get("expected_any_ids") or [])
    expected_loci = {
        (int(x["volume"]), int(x["chapter_ordinal"]))
        for x in (case.get("expected_any_loci") or [])
    }
    for rank, hit in enumerate(hits, 1):
        if hit["support_id"] in expected_ids:
            return rank
        locus = hit["source"]
        pair = (int(locus["volume"]), int(locus["chapter_ordinal"]))
        if pair in expected_loci:
            return rank
    return None


def evaluate(cases, retrieve):
    totals = defaultdict(int)
    passes = defaultdict(int)
    reciprocal = 0.0
    supported_total = 0
    by_language = defaultdict(lambda: {"supported": 0, "top1": 0, "top5": 0, "mrr_sum": 0.0, "negatives": 0, "abstained": 0})
    rows = []

    for case in cases:
        out = retrieve(case["query"])
        lang = case["language"]
        if case["expected_status"] == "insufficient_evidence":
            totals["negative"] += 1
            by_language[lang]["negatives"] += 1
            ok = out["status"] == "insufficient_evidence"
            passes["negative"] += int(ok)
            by_language[lang]["abstained"] += int(ok)
            rank = None
        else:
            supported_total += 1
            totals["supported"] += 1
            by_language[lang]["supported"] += 1
            rank = expected_rank(case, out["hits"])
            top1 = rank == 1
            top5 = rank is not None and rank <= 5
            passes["top1"] += int(top1)
            passes["top5"] += int(top5)
            by_language[lang]["top1"] += int(top1)
            by_language[lang]["top5"] += int(top5)
            if rank:
                rr = 1.0 / rank
                reciprocal += rr
                by_language[lang]["mrr_sum"] += rr

        rows.append({
            "id": case["id"],
            "split": case["split"],
            "group": case["group"],
            "language": lang,
            "query": case["query"],
            "expected_status": case["expected_status"],
            "actual_status": out["status"],
            "rank": rank,
            "returned_ids": [h["support_id"] for h in out["hits"][:5]],
        })

    def rate(a, b):
        return round(a / b, 4) if b else 1.0

    language_metrics = {}
    for lang, m in sorted(by_language.items()):
        language_metrics[lang] = {
            "supported": m["supported"],
            "top1": rate(m["top1"], m["supported"]),
            "top5": rate(m["top5"], m["supported"]),
            "mrr": round(m["mrr_sum"] / m["supported"], 4) if m["supported"] else 1.0,
            "negatives": m["negatives"],
            "abstention": rate(m["abstained"], m["negatives"]),
        }

    metrics = {
        "cases": len(cases),
        "supported": totals["supported"],
        "negatives": totals["negative"],
        "top1": rate(passes["top1"], totals["supported"]),
        "top5": rate(passes["top5"], totals["supported"]),
        "mrr": round(reciprocal / supported_total, 4) if supported_total else 1.0,
        "abstention": rate(passes["negative"], totals["negative"]),
        "by_language": language_metrics,
    }
    return metrics, rows


def objective(metrics):
    # Abstention is a hard trust constraint.  Within that boundary prioritize
    # Top-1 and MRR while still rewarding Top-5 recall.
    if metrics["abstention"] < 1.0:
        return -1000.0 + metrics["abstention"]
    return (2.0 * metrics["top1"]) + metrics["mrr"] + (0.5 * metrics["top5"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default=str(BENCHMARK))
    ap.add_argument("--output", default=str(DEFAULT_OUT))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--revision", default=DEFAULT_REVISION)
    args = ap.parse_args()

    spec = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))
    cases = spec["cases"]
    dev = [c for c in cases if c["split"] == "dev"]
    test = [c for c in cases if c["split"] == "test"]

    lexical = MahaperiyavaRetriever()
    lexical_dev, _ = evaluate(dev, lambda q: lexical.retrieve(q, top_k=5))
    lexical_test, lexical_test_rows = evaluate(test, lambda q: lexical.retrieve(q, top_k=5))

    embedder = SentenceTransformerEmbedder(args.model, args.revision)
    hybrid = HybridMahaperiyavaRetriever(embedder=embedder)

    configs = []
    for lw in (0.7, 1.0, 1.3):
        for sw in (0.8, 1.1, 1.4, 1.7):
            for threshold in (0.32, 0.36, 0.40, 0.44):
                metrics, _ = evaluate(
                    dev,
                    lambda q, lw=lw, sw=sw, threshold=threshold: hybrid.retrieve(
                        q,
                        top_k=5,
                        lexical_weight=lw,
                        semantic_weight=sw,
                        min_semantic=threshold,
                    ),
                )
                configs.append({
                    "lexical_weight": lw,
                    "semantic_weight": sw,
                    "min_semantic": threshold,
                    "metrics": metrics,
                    "objective": round(objective(metrics), 6),
                })

    configs.sort(
        key=lambda x: (
            -x["objective"],
            -x["metrics"]["top1"],
            -x["metrics"]["mrr"],
            -x["metrics"]["top5"],
            x["lexical_weight"],
            x["semantic_weight"],
            x["min_semantic"],
        )
    )
    best = configs[0]

    hybrid_test, hybrid_test_rows = evaluate(
        test,
        lambda q: hybrid.retrieve(
            q,
            top_k=5,
            lexical_weight=best["lexical_weight"],
            semantic_weight=best["semantic_weight"],
            min_semantic=best["min_semantic"],
        ),
    )

    authority_counts = hybrid.authority_counts()
    expected_authority = {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }
    if authority_counts != expected_authority:
        raise SystemExit(f"authority frontier changed unexpectedly: {authority_counts}")

    no_regression = (
        hybrid_test["abstention"] == 1.0
        and hybrid_test["top5"] >= 0.90
        and hybrid_test["top1"] >= lexical_test["top1"] - 0.02
        and hybrid_test["mrr"] >= lexical_test["mrr"] - 0.02
    )
    improved_top1 = hybrid_test["top1"] > lexical_test["top1"]

    status = (
        "PHASE12_HYBRID_RETRIEVAL_READY_FOR_PRODUCT_INTEGRATION"
        if no_regression else
        "PHASE12_HYBRID_RETRIEVAL_FOUNDATION_RECORDED_TUNING_REQUIRED"
    )

    try:
        st_version = importlib.metadata.version("sentence-transformers")
    except importlib.metadata.PackageNotFoundError:
        st_version = None

    checkpoint = {
        "version": "1.0",
        "checkpoint": "MAHAPERIYAVA_HYBRID_RETRIEVAL_FOUNDATION_V1",
        "status": status,
        "decision": (
            "integrate_hybrid_retrieval_behind_feature_flag"
            if no_regression else
            "tune_before_product_integration"
        ),
        "benchmark": {
            "file": str(Path(args.benchmark).relative_to(ROOT)),
            "cases": len(cases),
            "dev_cases": len(dev),
            "test_cases": len(test),
        },
        "model": {
            "name": args.model,
            "revision": args.revision,
            "sentence_transformers_version": st_version,
            "document_fields": ["claim_summary", "topics", "chapter_title_ta", "record_id"],
            "restricted_source_text_embedded": False,
            "embedding_vectors_committed": False,
        },
        "selected_config": {
            "lexical_weight": best["lexical_weight"],
            "semantic_weight": best["semantic_weight"],
            "min_semantic": best["min_semantic"],
            "rrf_k": 60,
            "selected_on": "dev_only",
        },
        "metrics": {
            "lexical_dev": lexical_dev,
            "lexical_test": lexical_test,
            "hybrid_dev": best["metrics"],
            "hybrid_test": hybrid_test,
            "test_top1_delta": round(hybrid_test["top1"] - lexical_test["top1"], 4),
            "test_top5_delta": round(hybrid_test["top5"] - lexical_test["top5"], 4),
            "test_mrr_delta": round(hybrid_test["mrr"] - lexical_test["mrr"], 4),
            "improved_top1": improved_top1,
        },
        "authority_boundary": {
            "authority_counts": authority_counts,
            "authority_promotions": 0,
            "retrieval_score_changes_authority": False,
            "exact_source_text_exposed": False,
            "generated_text_may_enter_corpus": False,
            "publication_approval_implied": False,
        },
        "test_rows": {
            "lexical": lexical_test_rows,
            "hybrid": hybrid_test_rows,
        },
        "top_dev_configs": configs[:8],
        "limitations": [
            "The benchmark evaluates retrieval over curator-authored public-safe metadata, not restricted source text.",
            "Roman-Tamil normalization is heuristic and must not be treated as linguistic authority.",
            "The semantic model is a retrieval component only; its similarity score cannot alter evidence authority.",
            "Product answer generation remains on the existing Phase-9 grounding contract until explicit integration is tested.",
        ],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=" * 72)
    print("PHASE 12 HYBRID RETRIEVAL CHECKPOINT")
    print("=" * 72)
    print("status              :", status)
    print("benchmark cases     :", len(cases))
    print("selected config     :", checkpoint["selected_config"])
    print("lexical test        :", {k: lexical_test[k] for k in ("top1", "top5", "mrr", "abstention")})
    print("hybrid test         :", {k: hybrid_test[k] for k in ("top1", "top5", "mrr", "abstention")})
    print("top1 delta          :", checkpoint["metrics"]["test_top1_delta"])
    print("mrr delta           :", checkpoint["metrics"]["test_mrr_delta"])
    print("authority promotions: 0")
    print("restricted text     : NOT EMBEDDED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
