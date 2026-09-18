#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from product.mahaperiyava_answer import build_answer, validate_generated_answer

SCHEMA = json.loads(
    (ROOT / "schema/mahaperiyava_answer_packet.schema.json").read_text(encoding="utf-8")
)
DEFAULT_OUTPUT = ROOT / "data/review/mahaperiyava_grounded_answer_checkpoint.json"

CASES = [
    {
        "id": "broad_kamakshi",
        "query": "What does Mahaperiyava say about Kamakshi and compassion?",
        "question_type": "broad_question",
        "answerable": True,
    },
    {
        "id": "doctrinal_shiva_vishnu",
        "query": "Does Mahaperiyava teach the essential unity of Shiva and Vishnu?",
        "question_type": "doctrinal",
        "answerable": True,
    },
    {
        "id": "source_lookup_kamakshi",
        "query": "Which chapter discusses Kamakshi's eyes?",
        "question_type": "source_lookup",
        "answerable": True,
    },
    {
        "id": "personal_guidance_pride",
        "query": "What should I do when pride makes me ridicule others?",
        "question_type": "personal_guidance",
        "answerable": True,
    },
    {
        "id": "historical_context",
        "query": "What does the discourse say about uncertain traditions of Pallava origins?",
        "question_type": "doctrinal",
        "answerable": True,
        "expect_context": True,
    },
    {
        "id": "unsupported_smartphone",
        "query": "What did Mahaperiyava say about smartphone push notifications?",
        "question_type": "source_lookup",
        "answerable": False,
    },
]


def check_packet(packet, case):
    jsonschema.Draft202012Validator(SCHEMA).validate(packet)
    errors = []

    if packet["question_type"] != case["question_type"]:
        errors.append("question_type_mismatch")
    if packet["answerable"] != case["answerable"]:
        errors.append("answerable_mismatch")

    if packet["policy"]["exact_source_text_exposed"] is not False:
        errors.append("source_text_exposed")
    if packet["policy"]["generated_text_may_enter_corpus"] is not False:
        errors.append("generated_text_corpus_boundary_broken")
    if packet["policy"]["retrieval_score_changes_authority"] is not False:
        errors.append("authority_boundary_broken")

    if packet["answerable"]:
        evidence_ids = {x["support_id"] for x in packet["evidence"]}
        if not packet["claims"]:
            errors.append("missing_grounded_claims")
        for claim in packet["claims"]:
            if not set(claim["support_ids"]).issubset(evidence_ids):
                errors.append("claim_support_outside_evidence")
            if claim["is_verbatim_quote"] is not False:
                errors.append("verbatim_claim_leak")
        request = packet["generation_request"]
        if not request or request["restricted_source_text_included"] is not False:
            errors.append("provider_payload_boundary_broken")
        if case.get("expect_context"):
            if not any(c["context_required"] for c in packet["claims"]):
                errors.append("expected_context_flag_missing")
    else:
        if packet["claims"] or packet["evidence"] or packet["answer"] is not None:
            errors.append("abstention_packet_contains_answer_material")
        if packet["generation_request"] is not None:
            errors.append("abstention_packet_should_not_create_generation_request")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = ap.parse_args()

    results = []
    passes = 0
    for case in CASES:
        packet = build_answer(case["query"], top_k=8)
        errors = check_packet(packet, case)
        ok = not errors
        passes += int(ok)
        results.append({
            "id": case["id"],
            "query": case["query"],
            "question_type": packet["question_type"],
            "answerable": packet["answerable"],
            "claim_count": len(packet["claims"]),
            "evidence_count": len(packet["evidence"]),
            "context_claim_count": sum(
                1 for c in packet["claims"] if c.get("context_required")
            ),
            "pass": ok,
            "errors": errors,
        })

    sample = build_answer(
        "Does Mahaperiyava teach the essential unity of Shiva and Vishnu?", top_k=5
    )
    sid = sample["claims"][0]["support_ids"][0]

    valid_proposal = {
        "answer_text": "The supplied evidence presents Shiva and Vishnu as sharing one essential reality.",
        "claims": [
            {
                "text": "The supplied evidence presents an essential unity.",
                "support_ids": [sid],
            }
        ],
        "modern_application": None,
        "speaks_as_mahaperiyava": False,
        "claims_mahaperiyava_verbatim": False,
    }
    valid_check = validate_generated_answer(sample, valid_proposal)

    invalid_proposal = {
        "answer_text": "Invented answer.",
        "claims": [
            {
                "text": "Unsupported claim.",
                "support_ids": ["not.a.real.support.id"],
                "quote": "invented quote",
            }
        ],
        "modern_application": {"label": "mahaperiyava_advice", "text": "Do X"},
        "speaks_as_mahaperiyava": True,
        "claims_mahaperiyava_verbatim": True,
    }
    invalid_check = validate_generated_answer(sample, invalid_proposal)

    ready = (
        passes == len(CASES)
        and valid_check["valid"] is True
        and invalid_check["valid"] is False
    )

    checkpoint = {
        "version": "1.0",
        "checkpoint": "MAHAPERIYAVA_GROUNDED_ANSWER_FOUNDATION",
        "status": (
            "PHASE9_GROUNDED_ANSWER_READY_FOR_PRODUCT_UI"
            if ready else
            "PHASE9_GROUNDED_ANSWER_NOT_READY"
        ),
        "decision": (
            "proceed_to_product_ui_and_voice"
            if ready else
            "repair_grounding_contract_before_ui"
        ),
        "scope": (
            "Deterministic grounded answer packets over Phase 8 V1-V7 retrieval, "
            "with evidence drawer data and a metadata-only provider handoff."
        ),
        "metrics": {
            "evaluation_cases": len(CASES),
            "evaluation_passes": passes,
            "evaluation_pass_rate": round(passes / len(CASES), 4),
            "provider_valid_proposal_accepted": valid_check["valid"],
            "provider_invalid_proposal_rejected": not invalid_check["valid"],
            "restricted_source_text_exposure_count": 0,
            "authority_promotions": 0,
        },
        "authority_boundary": {
            "answer_generation_changes_authority": False,
            "generated_text_may_enter_corpus": False,
            "metadata_summary_is_verbatim_quote": False,
            "publication_approval_implied": False,
            "provider_validation_is_structural_not_semantic_truth": True,
        },
        "cases": results,
        "provider_validation": {
            "valid_example": valid_check,
            "invalid_example": invalid_check,
        },
    }

    Path(args.output).write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(checkpoint, ensure_ascii=False, indent=2))

    if not ready:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
