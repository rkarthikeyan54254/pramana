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
    HybridMahaperiyavaRetriever,
    SentenceTransformerEmbedder,
)
from mahaperiyava_hybrid_retrieval_v2 import (
    FieldedHybridRetriever,
    MODEL_PROFILES,
    SentenceTransformerFieldEmbedder,
)

BENCHMARK = ROOT / "data/review/mahaperiyava_retrieval_benchmark_v3.json"
DEFAULT_OUT = ROOT / "data/review/mahaperiyava_hybrid_retrieval_checkpoint_v2.json"
V1_CHECKPOINT = ROOT / "data/review/mahaperiyava_hybrid_retrieval_checkpoint_v1.json"


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
        if locus.get("chapter_ordinal") is None:
            continue
        pair = (int(locus["volume"]), int(locus["chapter_ordinal"]))
        if pair in expected_loci:
            return rank
    return None


def evaluate(cases, retrieve):
    totals = defaultdict(int)
    passes = defaultdict(int)
    rr_sum = 0.0
    by_language = defaultdict(lambda: {
        "supported": 0, "top1": 0, "top5": 0, "rr_sum": 0.0,
        "negatives": 0, "abstained": 0,
    })
    rows = []

    for case in cases:
        out = retrieve(case["query"])
        lang = case["language"]
        rank = None
        if case["expected_status"] == "insufficient_evidence":
            totals["negative"] += 1
            by_language[lang]["negatives"] += 1
            ok = out["status"] == "insufficient_evidence"
            passes["negative"] += int(ok)
            by_language[lang]["abstained"] += int(ok)
        else:
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
                rr_sum += rr
                by_language[lang]["rr_sum"] += rr

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

    metrics = {
        "cases": len(cases),
        "supported": totals["supported"],
        "negatives": totals["negative"],
        "top1": rate(passes["top1"], totals["supported"]),
        "top5": rate(passes["top5"], totals["supported"]),
        "mrr": round(rr_sum / totals["supported"], 4) if totals["supported"] else 1.0,
        "abstention": rate(passes["negative"], totals["negative"]),
        "by_language": lang_metrics,
    }
    return metrics, rows


def objective(m):
    if m["abstention"] < 1.0:
        return -1000.0 + m["abstention"]
    ta = m["by_language"].get("ta", {})
    roman = m["by_language"].get("roman_ta", {})
    return (
        4.0 * m["top1"]
        + 2.0 * m["top5"]
        + 2.0 * m["mrr"]
        + 1.6 * ta.get("top1", 0.0)
        + 1.0 * ta.get("top5", 0.0)
        + 1.2 * roman.get("top1", 0.0)
        + 0.8 * roman.get("top5", 0.0)
    )


def compact(m):
    return {k: m[k] for k in ("top1", "top5", "mrr", "abstention")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default=str(BENCHMARK))
    ap.add_argument("--output", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    spec = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))
    cases = spec["cases"]
    dev = [x for x in cases if x["split"] == "dev"]
    test = [x for x in cases if x["split"] == "test"]

    lexical = MahaperiyavaRetriever()
    lexical_dev, _ = evaluate(dev, lambda q: lexical.retrieve(q, top_k=5))
    lexical_test, lexical_test_rows = evaluate(test, lambda q: lexical.retrieve(q, top_k=5))

    # Phase-12 retriever on the expanded benchmark is a useful baseline but is
    # not allowed to influence Phase-13 parameter selection on test.
    v1cp = json.loads(V1_CHECKPOINT.read_text(encoding="utf-8"))
    v1cfg = v1cp["selected_config"]
    v1embedder = SentenceTransformerEmbedder(
        v1cp["model"]["name"], v1cp["model"]["revision"]
    )
    v1hybrid = HybridMahaperiyavaRetriever(embedder=v1embedder)
    phase12_dev, _ = evaluate(
        dev,
        lambda q: v1hybrid.retrieve(
            q, top_k=5,
            lexical_weight=v1cfg["lexical_weight"],
            semantic_weight=v1cfg["semantic_weight"],
            min_semantic=v1cfg["min_semantic"],
            rrf_k=v1cfg.get("rrf_k", 60),
        ),
    )
    phase12_test, phase12_test_rows = evaluate(
        test,
        lambda q: v1hybrid.retrieve(
            q, top_k=5,
            lexical_weight=v1cfg["lexical_weight"],
            semantic_weight=v1cfg["semantic_weight"],
            min_semantic=v1cfg["min_semantic"],
            rrf_k=v1cfg.get("rrf_k", 60),
        ),
    )

    leaderboard = []
    retrievers = {}

    # Model selection and fusion tuning use DEV ONLY.
    for profile in MODEL_PROFILES:
        print(f"\nLoading profile: {profile}")
        retriever = FieldedHybridRetriever(
            SentenceTransformerFieldEmbedder(profile)
        )
        retrievers[profile] = retriever

        for lw in (0.7, 1.0, 1.3, 1.6):
            for cw in (0.8, 1.1, 1.4):
                for tw in (0.3, 0.6, 0.9):
                    for ow in (0.0, 0.35, 0.70):
                        for threshold in (0.40, 0.46, 0.52):
                            metrics, _ = evaluate(
                                dev,
                                lambda q, lw=lw, cw=cw, tw=tw, ow=ow, threshold=threshold, r=retriever: r.retrieve(
                                    q,
                                    top_k=5,
                                    lexical_weight=lw,
                                    claim_weight=cw,
                                    title_weight=tw,
                                    overlap_weight=ow,
                                    min_semantic=threshold,
                                    rrf_k=60,
                                ),
                            )
                            leaderboard.append({
                                "profile": profile,
                                "lexical_weight": lw,
                                "claim_weight": cw,
                                "title_weight": tw,
                                "overlap_weight": ow,
                                "min_semantic": threshold,
                                "rrf_k": 60,
                                "metrics": metrics,
                                "objective": round(objective(metrics), 6),
                            })

    leaderboard.sort(
        key=lambda x: (
            -x["objective"],
            -x["metrics"]["top1"],
            -x["metrics"]["top5"],
            -x["metrics"]["mrr"],
            x["profile"],
            x["lexical_weight"],
            x["claim_weight"],
            x["title_weight"],
            x["overlap_weight"],
            x["min_semantic"],
        )
    )
    best = leaderboard[0]
    selected = retrievers[best["profile"]]

    tuned_test, tuned_test_rows = evaluate(
        test,
        lambda q: selected.retrieve(
            q,
            top_k=5,
            lexical_weight=best["lexical_weight"],
            claim_weight=best["claim_weight"],
            title_weight=best["title_weight"],
            overlap_weight=best["overlap_weight"],
            min_semantic=best["min_semantic"],
            rrf_k=best["rrf_k"],
        ),
    )

    expected_authority = {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }
    if selected.authority_counts() != expected_authority:
        raise SystemExit(f"authority frontier changed: {selected.authority_counts()}")

    target = spec["quality_target"]
    ta = tuned_test["by_language"].get("ta", {})
    roman = tuned_test["by_language"].get("roman_ta", {})
    ready = (
        tuned_test["top1"] >= target["test_top1"]
        and tuned_test["top5"] >= target["test_top5"]
        and tuned_test["abstention"] == target["test_abstention"]
        and ta.get("top5", 0.0) >= target["test_tamil_top5"]
        and roman.get("top5", 0.0) >= target["test_roman_tamil_top5"]
    )

    status = (
        "PHASE13_HYBRID_RETRIEVAL_TUNED_READY_FOR_FEATURE_FLAG"
        if ready else
        "PHASE13_HYBRID_RETRIEVAL_TUNING_RECORDED_MORE_WORK_REQUIRED"
    )

    try:
        st_version = importlib.metadata.version("sentence-transformers")
    except importlib.metadata.PackageNotFoundError:
        st_version = None

    checkpoint = {
        "version": "2.0",
        "checkpoint": "MAHAPERIYAVA_HYBRID_RETRIEVAL_TUNING_V2",
        "status": status,
        "decision": (
            "integrate_behind_feature_flag_only"
            if ready else
            "do_not_switch_product_retriever"
        ),
        "benchmark": {
            "file": str(Path(args.benchmark).relative_to(ROOT)),
            "cases": len(cases),
            "dev_cases": len(dev),
            "test_cases": len(test),
            "quality_target": target,
        },
        "selection": {
            "selected_on": "dev_only",
            "profile": best["profile"],
            "model": MODEL_PROFILES[best["profile"]],
            "sentence_transformers_version": st_version,
            "config": {
                k: best[k]
                for k in (
                    "lexical_weight", "claim_weight", "title_weight",
                    "overlap_weight", "min_semantic", "rrf_k"
                )
            },
            "document_fields": [
                "claim_summary+topics",
                "chapter_title_ta+topics",
            ],
            "restricted_source_text_embedded": False,
            "embedding_vectors_committed": False,
        },
        "metrics": {
            "lexical_dev": lexical_dev,
            "lexical_test": lexical_test,
            "phase12_dev_on_v3": phase12_dev,
            "phase12_test_on_v3": phase12_test,
            "tuned_dev": best["metrics"],
            "tuned_test": tuned_test,
            "vs_phase12_test_top1_delta": round(tuned_test["top1"] - phase12_test["top1"], 4),
            "vs_phase12_test_top5_delta": round(tuned_test["top5"] - phase12_test["top5"], 4),
            "vs_phase12_test_mrr_delta": round(tuned_test["mrr"] - phase12_test["mrr"], 4),
        },
        "authority_boundary": {
            "authority_counts": expected_authority,
            "authority_promotions": 0,
            "retrieval_score_changes_authority": False,
            "exact_source_text_exposed": False,
            "generated_text_may_enter_corpus": False,
            "publication_approval_implied": False,
        },
        "test_rows": {
            "lexical": lexical_test_rows,
            "phase12": phase12_test_rows,
            "tuned": tuned_test_rows,
        },
        "top_dev_configs": leaderboard[:20],
        "limitations": [
            "Model and fusion selection were performed on dev only; test was evaluated after selection.",
            "Tamil and Roman-Tamil normalization is heuristic and is not treated as source evidence.",
            "Embedding inputs contain curator-authored public-safe metadata only.",
            "No retrieval score or model output changes evidence authority.",
            "Product integration remains disabled unless the held-out target is met and a separate answer-layer gate is passed.",
        ],
    }

    out = Path(args.output)
    out.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=" * 72)
    print("PHASE 13 HYBRID RETRIEVAL TUNING V2")
    print("=" * 72)
    print("status           :", status)
    print("benchmark cases  :", len(cases))
    print("selected profile :", best["profile"])
    print("selected config  :", checkpoint["selection"]["config"])
    print("lexical test     :", compact(lexical_test))
    print("phase12 test     :", compact(phase12_test))
    print("tuned test       :", compact(tuned_test))
    print("Tamil test       :", tuned_test["by_language"].get("ta"))
    print("Roman-Tamil test :", tuned_test["by_language"].get("roman_ta"))
    print("vs P12 top1 delta:", checkpoint["metrics"]["vs_phase12_test_top1_delta"])
    print("vs P12 top5 delta:", checkpoint["metrics"]["vs_phase12_test_top5_delta"])
    print("authority changes: 0")
    print("restricted text  : NOT EMBEDDED")
    print("product switch   : NO")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
