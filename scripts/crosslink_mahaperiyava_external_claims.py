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

CLAIMS = ROOT / "data/review/mahaperiyava_external_source_pilot_claims.json"
REGISTRY = ROOT / "data/review/mahaperiyava_external_source_registry.json"


def canonical_sha(obj) -> str:
    payload = json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def topic_overlap(ext_topics, dk_topics):
    a = {str(x).casefold() for x in ext_topics or []}
    b = {str(x).casefold() for x in dk_topics or []}
    return sorted(a & b)


def build(output: Path, top_k: int = 10) -> dict:
    claims_doc = json.loads(CLAIMS.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    source_map = {x["id"]: x for x in registry["items"]}
    retriever = MahaperiyavaRetriever()

    rows = []

    for ext in claims_doc["claims"]:
        source = source_map[ext["source_id"]]

        # Retrieval query intentionally combines curator summary + topic labels.
        # This is candidate generation only; it never decides equivalence.
        query = ext["claim_summary"]
        if ext.get("topics"):
            query += " " + " ".join(ext["topics"])

        result = retriever.retrieve(query, top_k=top_k)

        candidates = []

        for rank, hit in enumerate(result.get("hits") or [], 1):
            dk_summary = hit.get("claim_summary") or ""
            dk_topics = hit.get("topics") or []

            candidate = {
                "rank": rank,
                "dk_teaching_id": hit["support_id"],
                "dk_source": hit["source"],
                "dk_claim_summary": dk_summary,
                "dk_topics": dk_topics,
                "dk_authority": hit.get("authority"),
                "retrieval_score": hit.get("score"),
                "matched_terms": hit.get("matched_terms") or [],
                "topic_overlap": topic_overlap(
                    ext.get("topics") or [],
                    dk_topics,
                ),
                "machine_role": "candidate_only",
                "human_decision": "unreviewed",
                "decision_options": [
                    "same_teaching",
                    "related_teaching",
                    "possible_tension",
                    "contradiction",
                    "not_same_teaching",
                    "insufficient_to_decide",
                ],
                "authority_effect": "none_without_item_level_review",
            }
            candidates.append(candidate)

        rows.append({
            "external_claim_id": ext["id"],
            "external_source_id": ext["source_id"],
            "source_family_id": source["source_family_id"],
            "source_representation": source["representation"],
            "source_verbatim_status": source["verbatim_status"],
            "source_independence_from_dk":
                source["independence_from_deivathin_kural"],
            "external_claim_summary": ext["claim_summary"],
            "external_topics": ext.get("topics") or [],
            "external_flags": ext.get("flags") or [],
            "retrieval_query_sha256": hashlib.sha256(
                query.encode("utf-8")
            ).hexdigest(),
            "retrieval_status": result["status"],
            "candidate_count": len(candidates),
            "candidates": candidates,
            "human_review_status": "pending",
            "authority_promotions": 0,
            "source_text_included": False,
        })

    report = {
        "version": "1.0",
        "checkpoint":
            "MAHAPERIYAVA_EXTERNAL_DK_CROSSLINK_CANDIDATES_V1",
        "status": "CANDIDATE_MATRIX_READY_FOR_ITEM_LEVEL_REVIEW",
        "policy": {
            "machine_retrieval_never_grants_equivalence": True,
            "topic_overlap_never_grants_equivalence": True,
            "same_source_family_is_not_independent_vote": True,
            "translated_or_gist_sources_do_not_prove_exact_wording": True,
            "candidate_generation_never_changes_authority": True,
            "human_same_claim_review_required": True,
            "primary_source_verified_not_available_from_this_matrix": True,
            "source_text_included": False,
        },
        "input_claim_count": len(rows),
        "top_k": top_k,
        "authority_promotions": 0,
        "source_text_included": False,
        "input_claims_sha256": canonical_sha(claims_doc),
        "input_registry_sha256": canonical_sha(registry),
        "rows": rows,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(
            ROOT
            / "data/review/"
            "mahaperiyava_external_dk_crosslink_candidates.json"
        ),
    )
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    report = build(Path(args.output), top_k=args.top_k)

    print(json.dumps({
        "status": report["status"],
        "input_claim_count": report["input_claim_count"],
        "authority_promotions": report["authority_promotions"],
        "candidate_counts": {
            row["external_claim_id"]: row["candidate_count"]
            for row in report["rows"]
        },
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
