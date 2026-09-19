#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ask_mahaperiyava import MahaperiyavaRetriever, _tokens

MANUAL = ROOT / "data/review/mahaperiyava_v1_v7_retrieval_eval_cases.json"

NEGATIVE_QUERIES = [
    "What did Mahaperiyava say about smartphone push notifications?",
    "What did Mahaperiyava teach about Kubernetes autoscaling policies?",
    "Did Mahaperiyava recommend Bitcoin cold storage wallets?",
    "What was Mahaperiyava's view on React Server Components?",
    "How did Mahaperiyava configure Wi-Fi 7 routers?",
    "What did Mahaperiyava say about GPU tensor cores?",
    "Did Mahaperiyava discuss electric vehicle battery management systems?",
    "What was Mahaperiyava's opinion of QR-code payment fraud?",
    "Did Mahaperiyava recommend password managers and passkeys?",
    "What did Mahaperiyava teach about cloud container orchestration?",
    "How should I tune a PostgreSQL query planner according to Mahaperiyava?",
    "What did Mahaperiyava say about 5G millimeter-wave antennas?",
    "Did Mahaperiyava discuss CRISPR gene editing protocols?",
    "What was Mahaperiyava's advice on airline dynamic pricing algorithms?",
    "Did Mahaperiyava recommend index funds and exchange-traded funds?",
    "What did Mahaperiyava say about video game ray tracing?",
    "How did Mahaperiyava compare USB-C and Thunderbolt ports?",
    "What was Mahaperiyava's view on ransomware incident response?",
    "Did Mahaperiyava discuss large-language-model prompt injection?",
    "What did Mahaperiyava recommend for Docker image layer caching?",
]

TARGETS = {
    "manual_top5": 1.0,
    "manual_abstention": 1.0,
    "record_anchored_top5": 0.90,
    "title_lookup_top5": 0.80,
    "modern_negative_abstention": 1.0,
}


def evenly_spaced(rows, n):
    if len(rows) <= n:
        return list(rows)
    if n == 1:
        return [rows[len(rows) // 2]]
    indices = [round(i * (len(rows) - 1) / (n - 1)) for i in range(n)]
    return [rows[i] for i in indices]


def expected_match(case, hits):
    ids = {h["support_id"] for h in hits}
    if set(case.get("expected_any_ids") or []).intersection(ids):
        return True
    loci = {
        (int(h["source"]["volume"]), int(h["source"]["chapter_ordinal"]))
        for h in hits
        if h["source"].get("chapter_ordinal") is not None
    }
    expected_loci = {
        (int(x["volume"]), int(x["chapter_ordinal"]))
        for x in (case.get("expected_any_loci") or [])
    }
    return bool(expected_loci.intersection(loci))


def anchored_query(summary: str) -> str:
    tokens = _tokens(summary)
    if len(tokens) <= 5:
        return " ".join(tokens)
    # Deterministic token deletion makes this less trivial than reusing the
    # exact curator sentence while keeping the expected proposition identifiable.
    kept = [
        token for idx, token in enumerate(tokens[:24])
        if idx % 3 != 1
    ]
    return " ".join(kept[:14])


def rate(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else 1.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(ROOT / "dist/mahaperiyava/retrieval_release_benchmark.json"),
    )
    args = parser.parse_args()

    retriever = MahaperiyavaRetriever()
    manual_spec = json.loads(MANUAL.read_text(encoding="utf-8"))

    results = []
    metrics = defaultdict(lambda: {"passed": 0, "total": 0, "top1": 0})

    # 14 curated Phase-8 cases, including the unsupported negative.
    for case in manual_spec["cases"]:
        out = retriever.retrieve(case["query"], top_k=5)
        if case["expected_status"] == "insufficient_evidence":
            passed = out["status"] == "insufficient_evidence"
            top1 = False
            category = "manual_abstention"
        else:
            passed = out["status"] == "retrieved_evidence" and expected_match(case, out["hits"])
            top1 = bool(out["hits"]) and expected_match(case, out["hits"][:1])
            category = "manual_supported"
        metrics[category]["total"] += 1
        metrics[category]["passed"] += int(passed)
        metrics[category]["top1"] += int(top1)
        results.append({
            "id": case["id"],
            "category": category,
            "query": case["query"],
            "pass": passed,
            "top1": top1,
        })

    # 56 proposition-anchored robustness cases, eight per volume.
    by_volume = defaultdict(list)
    for record in retriever.records:
        by_volume[int(record["source_locus"]["volume"])].append(record)
    for volume in by_volume:
        by_volume[volume].sort(
            key=lambda r: (
                int(r["source_locus"].get("chapter_ordinal") or 10**9),
                r["id"],
            )
        )

    for volume in range(1, 8):
        for index, record in enumerate(evenly_spaced(by_volume[volume], 8), 1):
            query = anchored_query(record["claim_summary"])
            out = retriever.retrieve(query, top_k=5)
            ids = [hit["support_id"] for hit in out["hits"]]
            passed = record["id"] in ids
            top1 = bool(ids) and ids[0] == record["id"]
            metrics["record_anchored"]["total"] += 1
            metrics["record_anchored"]["passed"] += int(passed)
            metrics["record_anchored"]["top1"] += int(top1)
            results.append({
                "id": f"record_anchor_v{volume}_{index:02d}",
                "category": "record_anchored",
                "query": query,
                "expected_id": record["id"],
                "pass": passed,
                "top1": top1,
            })

    # 21 exact Tamil chapter-title lookups, three per volume, locus-scored.
    for volume in range(1, 8):
        chapters = {}
        for record in by_volume[volume]:
            ordinal = record["source_locus"].get("chapter_ordinal")
            title = record["source_locus"].get("chapter_title_ta")
            if ordinal is not None and title and ordinal not in chapters:
                chapters[ordinal] = title
        selected = evenly_spaced(sorted(chapters.items()), 3)
        for index, (ordinal, title) in enumerate(selected, 1):
            out = retriever.retrieve(title, top_k=5)
            loci = [
                (int(hit["source"]["volume"]), int(hit["source"]["chapter_ordinal"]))
                for hit in out["hits"]
                if hit["source"].get("chapter_ordinal") is not None
            ]
            expected = (volume, int(ordinal))
            passed = expected in loci
            top1 = bool(loci) and loci[0] == expected
            metrics["title_lookup"]["total"] += 1
            metrics["title_lookup"]["passed"] += int(passed)
            metrics["title_lookup"]["top1"] += int(top1)
            results.append({
                "id": f"title_lookup_v{volume}_{index:02d}",
                "category": "title_lookup",
                "query": title,
                "expected_locus": {"volume": volume, "chapter_ordinal": ordinal},
                "pass": passed,
                "top1": top1,
            })

    # 20 intentionally out-of-domain modern-attribution negatives.
    for index, query in enumerate(NEGATIVE_QUERIES, 1):
        out = retriever.retrieve(query, top_k=5)
        passed = out["status"] == "insufficient_evidence"
        metrics["modern_negative"]["total"] += 1
        metrics["modern_negative"]["passed"] += int(passed)
        results.append({
            "id": f"modern_negative_{index:02d}",
            "category": "modern_negative",
            "query": query,
            "pass": passed,
            "returned_ids": [hit["support_id"] for hit in out["hits"]],
        })

    summary = {
        category: {
            "cases": value["total"],
            "pass_rate": rate(value["passed"], value["total"]),
            "top1_rate": rate(value["top1"], value["total"])
            if category not in {"manual_abstention", "modern_negative"}
            else None,
        }
        for category, value in sorted(metrics.items())
    }

    ready = (
        summary["manual_supported"]["pass_rate"] >= TARGETS["manual_top5"]
        and summary["manual_abstention"]["pass_rate"] >= TARGETS["manual_abstention"]
        and summary["record_anchored"]["pass_rate"] >= TARGETS["record_anchored_top5"]
        and summary["title_lookup"]["pass_rate"] >= TARGETS["title_lookup_top5"]
        and summary["modern_negative"]["pass_rate"] >= TARGETS["modern_negative_abstention"]
    )

    report = {
        "version": "1.0",
        "benchmark": "mahaperiyava_v1_v7_release_retrieval",
        "status": "RELEASE_BENCHMARK_GREEN" if ready else "RELEASE_BENCHMARK_NOT_GREEN",
        "scope": (
            "Release regression benchmark over public-safe curator metadata. "
            "It measures retrieval/refusal behavior, not verbatim source accuracy or final prose quality."
        ),
        "targets": TARGETS,
        "case_count": len(results),
        "summary": summary,
        "results": results,
        "limitations": [
            "The 56 record-anchored cases are deterministic metadata-retrieval robustness tests, not independent human paraphrase judgments.",
            "The 21 title cases test Tamil source-locus retrieval.",
            "The 20 modern negatives test fail-closed attribution behavior.",
            "The 14 manual Phase-8 cases remain the curated semantic core.",
            "A separate embedding-model benchmark is still required before claiming a specific semantic-vector model is production-qualified.",
        ],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "case_count": report["case_count"],
        "summary": report["summary"],
    }, ensure_ascii=False, indent=2))
    if not ready:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
