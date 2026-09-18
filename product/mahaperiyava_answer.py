#!/usr/bin/env python3
"""Grounded Mahaperiyava answer packets over public-safe V1-V7 teaching metadata.

This module does not expose restricted Deivathin Kural text and does not speak
as Mahaperiyava. It turns Phase 8 retrieval results into an auditable product
packet with support IDs, evidence drawer data, and a provider handoff contract.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ask_mahaperiyava import MahaperiyavaRetriever

CONTRACT_VERSION = "1.0"
MAX_SYNTHESIS_ITEMS = 4


def _source_label(hit: dict[str, Any]) -> str:
    source = hit["source"]
    volume = source.get("volume")
    chapter = source.get("chapter_ordinal")
    title = source.get("chapter_title_ta")
    label = f"Deivathin Kural V{volume}"
    if chapter is not None:
        label += f", chapter {chapter}"
    if title:
        label += f" — {title}"
    return label


def _distinct_hits(hits: list[dict[str, Any]], limit: int = MAX_SYNTHESIS_ITEMS) -> list[dict[str, Any]]:
    """Prefer distinct support IDs and avoid overloading one chapter."""
    selected: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_chapters: set[tuple[int, int | None]] = set()

    for hit in hits:
        sid = hit["support_id"]
        if sid in seen_ids:
            continue
        key = (int(hit["source"]["volume"]), hit["source"].get("chapter_ordinal"))
        if key in seen_chapters and len(selected) >= 2:
            continue
        selected.append(hit)
        seen_ids.add(sid)
        seen_chapters.add(key)
        if len(selected) >= limit:
            break

    # If chapter de-duplication made the set too small, fill from remaining hits.
    if len(selected) < min(limit, len(hits)):
        for hit in hits:
            sid = hit["support_id"]
            if sid in seen_ids:
                continue
            selected.append(hit)
            seen_ids.add(sid)
            if len(selected) >= limit:
                break
    return selected


def _claim(hit: dict[str, Any], ordinal: int) -> dict[str, Any]:
    return {
        "claim_id": f"c{ordinal}",
        "claim_type": "curator_summary",
        "text": hit["claim_summary"],
        "support_ids": [hit["support_id"]],
        "source_label": _source_label(hit),
        "authority": hit["evidence_status"]["authority"],
        "wording_status": hit["evidence_status"].get("wording_status"),
        "context_required": bool(hit.get("context_required")),
        "flags": list(hit.get("flags") or []),
        "is_verbatim_quote": False,
    }


def _display_text(question_type: str, claims: list[dict[str, Any]]) -> str:
    if question_type == "source_lookup":
        lead = "Relevant attested evidence was located in Deivathin Kural:"
    elif question_type == "personal_guidance":
        lead = (
            "Relevant teachings attested in Deivathin Kural are listed below. "
            "Any present-day application must be labeled as app-generated, not as Mahaperiyava's words:"
        )
    elif question_type == "broad_question":
        lead = "The retrieved Deivathin Kural teachings point to these themes:"
    else:
        lead = "The retrieved Deivathin Kural teachings support the following explanation:"

    lines = [lead]
    for claim in claims:
        lines.append(f"• {claim['text']} [{claim['source_label']}]")
    return "\n".join(lines)


def _generation_request(query: str, question_type: str, claims: list[dict[str, Any]]) -> dict[str, Any]:
    evidence = [
        {
            "support_id": c["support_ids"][0],
            "curator_summary": c["text"],
            "source_label": c["source_label"],
            "authority": c["authority"],
            "context_required": c["context_required"],
            "flags": c["flags"],
        }
        for c in claims
    ]
    return {
        "provider_safe_payload": True,
        "restricted_source_text_included": False,
        "query": query,
        "question_type": question_type,
        "evidence": evidence,
        "instructions": [
            "Never speak as Mahaperiyava.",
            "Use only the supplied curator summaries as evidence.",
            "Do not present curator summaries as verbatim quotations.",
            "Every substantive claim must cite one or more supplied support_id values.",
            "If evidence is insufficient for part of the question, say so.",
            "Keep historical, scientific, political-social, caste, gender, violence, and hagiographic context flags visible when relevant.",
            "Any present-day application must be labeled app-generated and must not be attributed to Mahaperiyava.",
            "Do not reconstruct or invent Deivathin Kural source wording.",
        ],
        "required_output": {
            "answer_text": "string",
            "claims": [
                {
                    "text": "string",
                    "support_ids": ["support_id from supplied evidence"]
                }
            ],
            "modern_application": {
                "label": "app_generated",
                "text": "optional string",
                "derived_from_support_ids": ["optional supplied support IDs"]
            },
            "speaks_as_mahaperiyava": False,
            "claims_mahaperiyava_verbatim": False,
        },
    }


def build_answer(query: str, top_k: int = 8) -> dict[str, Any]:
    retrieved = MahaperiyavaRetriever().retrieve(query, top_k)

    policy = {
        "authority_source": "public-safe Deivathin Kural teaching metadata",
        "retrieval_score_changes_authority": False,
        "curator_summary_is_verbatim_quote": False,
        "exact_source_text_exposed": False,
        "model_memory_is_evidence": False,
        "generated_text_may_enter_corpus": False,
        "modern_application_requires_app_generated_label": True,
        "publication_approval_implied": False,
    }

    if not retrieved["answerable"]:
        return {
            "contract_version": CONTRACT_VERSION,
            "query": query,
            "question_type": retrieved["question_type"],
            "status": "insufficient_evidence",
            "answerable": False,
            "answer": None,
            "claims": [],
            "evidence": [],
            "generation_request": None,
            "policy": policy,
            "message": retrieved["message"],
        }

    selected = _distinct_hits(retrieved["hits"])
    claims = [_claim(hit, i) for i, hit in enumerate(selected, 1)]

    mode = {
        "source_lookup": "source_lookup",
        "personal_guidance": "personal_guidance_grounding",
        "broad_question": "themes",
        "doctrinal": "doctrinal_explanation",
    }[retrieved["question_type"]]

    answer = {
        "mode": mode,
        "display_text": _display_text(retrieved["question_type"], claims),
        "items": [
            {
                "text": c["text"],
                "support_ids": c["support_ids"],
                "source_label": c["source_label"],
                "context_required": c["context_required"],
            }
            for c in claims
        ],
        "modern_application": None,
        "modern_application_status": (
            "requires_separate_app_generated_layer"
            if retrieved["question_type"] == "personal_guidance"
            else "not_requested"
        ),
    }

    return {
        "contract_version": CONTRACT_VERSION,
        "query": query,
        "question_type": retrieved["question_type"],
        "status": "grounded_answer_packet",
        "answerable": True,
        "answer": answer,
        "claims": claims,
        "evidence": selected,
        "generation_request": _generation_request(
            query, retrieved["question_type"], claims
        ),
        "policy": policy,
        "message": None,
    }


def validate_generated_answer(packet: dict[str, Any], proposed: dict[str, Any]) -> dict[str, Any]:
    """Structural grounding validation for optional provider-generated prose.

    Passing this check means the proposal obeys support-ID and attribution
    boundaries. It does not turn generated prose into corpus evidence.
    """
    errors: list[str] = []

    if not packet.get("answerable"):
        errors.append("packet_not_answerable")

    allowed = {
        hit["support_id"]
        for hit in packet.get("evidence") or []
    }

    if proposed.get("speaks_as_mahaperiyava") is not False:
        errors.append("must_not_speak_as_mahaperiyava")

    if proposed.get("claims_mahaperiyava_verbatim") is not False:
        errors.append("must_not_claim_verbatim_wording")

    answer_text = proposed.get("answer_text")
    if not isinstance(answer_text, str) or not answer_text.strip():
        errors.append("missing_answer_text")

    claims = proposed.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("missing_claims")
        claims = []

    for idx, claim in enumerate(claims):
        ids = claim.get("support_ids") if isinstance(claim, dict) else None
        if not isinstance(ids, list) or not ids:
            errors.append(f"claim_{idx}_missing_support_ids")
            continue
        if any(sid not in allowed for sid in ids):
            errors.append(f"claim_{idx}_support_not_in_retrieved_evidence")
        if isinstance(claim, dict) and claim.get("quote"):
            errors.append(f"claim_{idx}_quote_not_allowed_from_metadata_only_packet")

    application = proposed.get("modern_application")
    if application is not None:
        if not isinstance(application, dict):
            errors.append("modern_application_must_be_object_or_null")
        else:
            if application.get("label") != "app_generated":
                errors.append("modern_application_requires_app_generated_label")
            for sid in application.get("derived_from_support_ids") or []:
                if sid not in allowed:
                    errors.append("modern_application_support_not_in_retrieved_evidence")

    return {
        "valid": not errors,
        "errors": errors,
        "structurally_grounded": not errors,
        "semantic_entailment_verified": False,
        "generated_text_may_enter_corpus": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a grounded Mahaperiyava answer packet.")
    ap.add_argument("query")
    ap.add_argument("--top", type=int, default=8, dest="top_k")
    args = ap.parse_args()
    print(json.dumps(build_answer(args.query, args.top_k), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
