#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data/review/mahaperiyava_evidence_depth_pilot_queue.json"
RETRIEVAL = ROOT / "data/review/mahaperiyava_v1_v7_retrieval_checkpoint.json"

WEIGHTS = [
    ("potentially_harmful", 12),
    ("medical", 10),
    ("scientific", 9),
    ("child_marriage", 12),
    ("gender", 8),
    ("caste", 8),
    ("political", 7),
    ("historical_claim", 6),
    ("historical_textual", 5),
    ("social_generalization", 5),
    ("supernatural", 4),
    ("hagiographic", 3),
    ("source_decode", 2),
]


def flag_score(flags):
    joined = " ".join(flags).casefold()
    score = 0
    matched = []
    for needle, weight in WEIGHTS:
        if needle in joined:
            score += weight
            matched.append(needle)
    return score, matched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(ROOT / "dist/mahaperiyava/evidence_depth_triage.json"),
    )
    args = parser.parse_args()

    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    retrieval = json.loads(RETRIEVAL.read_text(encoding="utf-8"))

    retrieval_use = Counter()
    for case in retrieval.get("cases", []):
        for sid in case.get("returned_ids") or []:
            retrieval_use[sid] += 1

    items = []
    for item in queue["items"]:
        base, matched = flag_score(item.get("flags") or [])
        usage = retrieval_use[item["teaching_id"]]
        score = base + 5 * usage
        if score >= 18:
            tier = "A"
        elif score >= 8:
            tier = "B"
        else:
            tier = "C"

        items.append({
            "teaching_id": item["teaching_id"],
            "volume": item["volume"],
            "chapter_ordinal": item["chapter_ordinal"],
            "chapter_title_ta": item["chapter_title_ta"],
            "current_authority": item["current_authority"],
            "priority_tier": tier,
            "priority_score": score,
            "retrieval_top5_appearances": usage,
            "risk_signals": matched,
            "flags": item.get("flags") or [],
            "target_review_stages": item["target_review_stages"],
            "recommended_first_action": (
                "perform item-level print-edition check with pinned edition/page/hash"
                if "dk_print_check" in item["target_review_stages"]
                else item["target_review_stages"][0]
            ),
            "authority_changed": False,
            "source_text_included": False,
        })

    items.sort(
        key=lambda x: (
            {"A": 0, "B": 1, "C": 2}[x["priority_tier"]],
            -x["priority_score"],
            x["volume"],
            x["chapter_ordinal"],
            x["teaching_id"],
        )
    )

    report = {
        "version": "1.0",
        "queue": "mahaperiyava_evidence_depth_pilot_queue",
        "input_count": queue["count"],
        "output_count": len(items),
        "authority_promotions": 0,
        "source_text_included": False,
        "policy": (
            "Triage prioritizes human evidence review; it never grants authority. "
            "Retrieval usage only affects review order."
        ),
        "tier_counts": dict(Counter(item["priority_tier"] for item in items)),
        "items": items,
    }

    if len(items) != 30:
        raise SystemExit(f"expected 30 triage items, got {len(items)}")
    if any(item["authority_changed"] for item in items):
        raise SystemExit("triage must not change authority")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "count": len(items),
        "tier_counts": report["tier_counts"],
        "authority_promotions": 0,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
