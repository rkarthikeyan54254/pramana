#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ask_mahaperiyava import MahaperiyavaRetriever

ATOMIC = ROOT / "data/review/mahaperiyava_external_source_atomic_claims_v1.json"
REGISTRY = ROOT / "data/review/mahaperiyava_external_source_registry.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(
            ROOT
            / "data/review/"
            "mahaperiyava_external_atomic_dk_crosslink_candidates_v1.json"
        ),
    )
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    atom = json.loads(ATOMIC.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sources = {x["id"]: x for x in registry["items"]}

    retriever = MahaperiyavaRetriever()

    rows = []

    for claim in atom["claims"]:
        src = sources[claim["source_id"]]

        query = claim["claim_summary"]
        if claim.get("topics"):
            query += " " + " ".join(claim["topics"])

        out = retriever.retrieve(query, top_k=args.top_k)

        rows.append({
            "atomic_claim_id": claim["id"],
            "parent_claim_id": claim["parent_claim_id"],
            "source_id": claim["source_id"],
            "source_family_id": src["source_family_id"],
            "claim_summary": claim["claim_summary"],
            "retrieval_query_sha256": hashlib.sha256(
                query.encode("utf-8")
            ).hexdigest(),
            "retrieval_status": out["status"],
            "candidates": [
                {
                    "rank": idx,
                    "dk_teaching_id": hit["support_id"],
                    "dk_source": hit["source"],
                    "dk_claim_summary":
                        hit.get("claim_summary") or "",
                    "dk_topics": hit.get("topics") or [],
                    "dk_authority": hit.get("authority"),
                    "retrieval_score": hit.get("score"),
                    "matched_terms":
                        hit.get("matched_terms") or [],
                    "decision": "unreviewed",
                    "authority_effect":
                        "none_without_item_level_review",
                }
                for idx, hit in enumerate(out.get("hits") or [], 1)
            ],
            "authority_promotions": 0,
            "source_text_included": False,
        })

    report = {
        "version": "1.0",
        "checkpoint":
            "MAHAPERIYAVA_EXTERNAL_ATOMIC_DK_CROSSLINK_V1",
        "status":
            "ATOMIC_CANDIDATES_READY_FOR_SEMANTIC_REVIEW",
        "policy": {
            "machine_similarity_never_grants_equivalence": True,
            "candidate_generation_never_changes_authority": True,
            "source_text_included": False,
        },
        "claim_count": len(rows),
        "authority_promotions": 0,
        "rows": rows,
    }

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "status": report["status"],
        "claim_count": report["claim_count"],
        "authority_promotions": 0,
        "candidate_counts": {
            x["atomic_claim_id"]: len(x["candidates"])
            for x in rows
        },
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
