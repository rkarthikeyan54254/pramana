#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ask_mahaperiyava import MahaperiyavaRetriever

CLAIMS = (
    ROOT
    / "data/review/"
      "mahaperiyava_1963_interview_propositions_v1.json"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--output",
        default=str(
            ROOT
            / "data/review/"
              "mahaperiyava_1963_interview_dk_candidates_v1.json"
        ),
    )
    ap.add_argument("--top-k", type=int, default=10)
    args = ap.parse_args()

    doc = json.loads(
        CLAIMS.read_text(encoding="utf-8")
    )

    retriever = MahaperiyavaRetriever()
    rows = []

    for claim in doc["claims"]:
        query = (
            claim["claim_summary"]
            + " "
            + " ".join(claim["topics"])
        )

        result = retriever.retrieve(
            query,
            top_k=args.top_k,
        )

        rows.append({
            "external_claim_id": claim["id"],
            "source_locus": claim["source_locus"],
            "external_claim_summary":
                claim["claim_summary"],
            "external_flags":
                claim["flags"],
            "retrieval_status":
                result["status"],
            "candidates": [
                {
                    "rank": rank,
                    "dk_teaching_id":
                        hit["support_id"],
                    "dk_source":
                        hit["source"],
                    "dk_claim_summary":
                        hit.get("claim_summary") or "",
                    "dk_authority":
                        hit.get("authority"),
                    "retrieval_score":
                        hit.get("score"),
                    "decision": "unreviewed",
                    "scan_locus_verified": False,
                    "authority_effect":
                        "none_without_item_level_review",
                }
                for rank, hit
                in enumerate(
                    result.get("hits") or [],
                    1,
                )
            ],
            "authority_promotions": 0,
        })

    out = {
        "version": "1.0",
        "checkpoint":
            "MAHAPERIYAVA_1963_RAMAN_DK_CANDIDATES_V1",
        "status":
            "CANDIDATES_READY_FOR_ITEM_LEVEL_ADJUDICATION",
        "policy": {
            "retrieval_never_grants_same_teaching": True,
            "scan_locus_verification_required": True,
            "authority_promotions": 0,
        },
        "claim_count": len(rows),
        "authority_promotions": 0,
        "rows": rows,
    }

    path = Path(args.output)
    path.write_text(
        json.dumps(
            out,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "status": out["status"],
        "claim_count": out["claim_count"],
        "authority_promotions": 0,
        "candidate_counts": {
            r["external_claim_id"]:
                len(r["candidates"])
            for r in rows
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
