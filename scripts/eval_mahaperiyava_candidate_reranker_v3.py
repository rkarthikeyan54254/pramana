#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mahaperiyava_candidate_reranker_v3 import (
    CandidateReranker,
    PROFILES,
    SentenceTransformerFieldEmbedder,
    DEFAULT_PROFILE,
)

BENCHMARK = ROOT / "data/review/mahaperiyava_retrieval_benchmark_v3.json"
OUT = ROOT / "data/review/mahaperiyava_candidate_reranker_checkpoint_v3.json"
PHASE13 = ROOT / "data/review/mahaperiyava_hybrid_retrieval_checkpoint_v2.json"

QUALITY_TARGET = {
    "test_top1": 0.75,
    "test_top5": 0.90,
    "test_abstention": 1.0,
    "test_tamil_top5": 0.75,
    "test_roman_tamil_top5": 0.80,
    "candidate_recall_at_cap": 0.95,
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


def expected_in_candidates(case, candidate_ids, records):
    expected_ids = set(case.get("expected_any_ids") or [])
    if expected_ids & candidate_ids:
        return True
    loci = {
        (int(x["volume"]), int(x["chapter_ordinal"]))
        for x in (case.get("expected_any_loci") or [])
    }
    if not loci:
        return False
    for r in records:
        if r["id"] not in candidate_ids:
            continue
        loc = r["source_locus"]
        pair = (int(loc["volume"]), int(loc.get("chapter_ordinal") or -1))
        if pair in loci:
            return True
    return False


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
            "actual_status": out["status"],
            "rank": rank,
            "returned_ids": [h["support_id"] for h in out["hits"][:5]],
            "retrieval_mode": out.get("retrieval_mode"),
            "profile": out.get("rerank_profile"),
            "concept_query": out.get("concept_query"),
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
    return 2.5 * m["top1"] + 1.0 * m["mrr"] + 0.5 * m["top5"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default=str(BENCHMARK))
    ap.add_argument("--output", default=str(OUT))
    args = ap.parse_args()

    spec = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))
    cases = spec["cases"]
    dev = [c for c in cases if c["split"] == "dev"]
    test = [c for c in cases if c["split"] == "test"]

    embedder = SentenceTransformerFieldEmbedder(DEFAULT_PROFILE)
    retriever = CandidateReranker(embedder=embedder)

    candidate_rows = []
    for case in cases:
        if case["expected_status"] == "insufficient_evidence":
            continue
        cids = retriever.candidate_ids(case["query"])
        ok = expected_in_candidates(case, cids, retriever.records)
        candidate_rows.append({
            "id": case["id"],
            "split": case["split"],
            "language": case["language"],
            "candidate_count": len(cids),
            "expected_present": ok,
        })

    def candidate_rate(split):
        rows = [r for r in candidate_rows if r["split"] == split]
        return round(sum(r["expected_present"] for r in rows) / len(rows), 4)

    languages = sorted({c["language"] for c in dev})
    selection = {}
    profile_dev_metrics = {}

    for lang in languages:
        lang_cases = [c for c in dev if c["language"] == lang]
        scored = []
        for name in PROFILES:
            m, _ = evaluate(
                lang_cases,
                lambda c, name=name: retriever.retrieve(
                    c["query"], top_k=5, profile=name
                ),
            )
            scored.append((objective(m), name, m))
        scored.sort(key=lambda x: (-x[0], -x[2]["top1"], -x[2]["top5"], x[1]))
        best = scored[0]
        selection[lang] = best[1]
        profile_dev_metrics[lang] = [
            {"profile": name, "objective": round(obj, 6), "metrics": m}
            for obj, name, m in scored
        ]

    def selected_retrieve(case):
        profile = selection.get(case["language"], "balanced")
        return retriever.retrieve(case["query"], top_k=5, profile=profile)

    dev_metrics, dev_rows = evaluate(dev, selected_retrieve)
    test_metrics, test_rows = evaluate(test, selected_retrieve)

    phase13 = json.loads(PHASE13.read_text(encoding="utf-8"))
    phase13_test = phase13["metrics"]["tuned_test"]

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
        and candidate_rate("test") >= QUALITY_TARGET["candidate_recall_at_cap"]
    )

    checkpoint = {
        "version": "3.0",
        "checkpoint": "MAHAPERIYAVA_LANGUAGE_AWARE_CANDIDATE_RERANKER_V3",
        "status": (
            "PHASE14_CANDIDATE_RERANKER_READY_FOR_SHADOW_INTEGRATION"
            if ready else
            "PHASE14_CANDIDATE_RERANKER_RECORDED_MORE_WORK_REQUIRED"
        ),
        "decision": (
            "allow_shadow_only_integration_not_product_switch"
            if ready else
            "continue_retrieval_work_before_product_switch"
        ),
        "benchmark": {
            "file": str(Path(args.benchmark).relative_to(ROOT)),
            "cases": len(cases),
            "dev_cases": len(dev),
            "test_cases": len(test),
            "quality_target": QUALITY_TARGET,
        },
        "architecture": {
            "candidate_generation": [
                "original lexical",
                "augmented lexical",
                "concept-only lexical",
                "claim semantic",
                "title semantic",
            ],
            "reranking": "language-specific profile selected on dev only",
            "semantic_model_profile": DEFAULT_PROFILE,
            "restricted_source_text_embedded": False,
            "embedding_vectors_committed": False,
            "product_retriever_switched": False,
        },
        "selected_profiles": selection,
        "metrics": {
            "candidate_recall_dev": candidate_rate("dev"),
            "candidate_recall_test": candidate_rate("test"),
            "dev": dev_metrics,
            "test": test_metrics,
            "phase13_test": phase13_test,
            "vs_phase13_top1_delta": round(test_metrics["top1"] - phase13_test["top1"], 4),
            "vs_phase13_top5_delta": round(test_metrics["top5"] - phase13_test["top5"], 4),
            "vs_phase13_mrr_delta": round(test_metrics["mrr"] - phase13_test["mrr"], 4),
        },
        "authority_boundary": {
            "authority_counts": authority,
            "authority_promotions": 0,
            "retrieval_score_changes_authority": False,
            "exact_source_text_exposed": False,
            "generated_text_may_enter_corpus": False,
            "publication_approval_implied": False,
        },
        "profile_dev_metrics": profile_dev_metrics,
        "candidate_rows": candidate_rows,
        "test_rows": test_rows,
        "limitations": [
            "Concept normalization is heuristic query understanding, not translation authority.",
            "Semantic similarity is used for retrieval only and cannot change evidence authority.",
            "The benchmark remains the Phase-13 v3 benchmark for direct comparability; test labels are never used for profile selection.",
            "Product retrieval remains unchanged even if the shadow-integration threshold is met.",
        ],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=" * 72)
    print("PHASE 14 LANGUAGE-AWARE CANDIDATE/RERANKER CHECKPOINT")
    print("=" * 72)
    print("status             :", checkpoint["status"])
    print("selected profiles  :", selection)
    print("candidate recall   :", {"dev": candidate_rate("dev"), "test": candidate_rate("test")})
    print("phase13 test       :", {k: phase13_test[k] for k in ("top1", "top5", "mrr", "abstention")})
    print("phase14 test       :", {k: test_metrics[k] for k in ("top1", "top5", "mrr", "abstention")})
    print("Tamil test         :", test_metrics["by_language"]["ta"])
    print("Roman-Tamil test   :", test_metrics["by_language"]["roman_ta"])
    print("English test       :", test_metrics["by_language"]["en"])
    print("authority changes  : 0")
    print("restricted text    : NOT EMBEDDED")
    print("product retriever  : NOT SWITCHED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
