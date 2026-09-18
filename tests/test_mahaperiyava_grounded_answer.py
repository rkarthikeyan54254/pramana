from __future__ import annotations

import json
from pathlib import Path
import sys

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from product.mahaperiyava_answer import build_answer, validate_generated_answer
from product.service import dispatch

SCHEMA = json.loads(
    (ROOT / "schema/mahaperiyava_answer_packet.schema.json").read_text(encoding="utf-8")
)


def validate(packet):
    jsonschema.Draft202012Validator(SCHEMA).validate(packet)


def test_broad_answer_is_grounded_and_metadata_only():
    packet = build_answer("What does Mahaperiyava say about Kamakshi and compassion?")
    validate(packet)
    assert packet["answerable"] is True
    assert packet["question_type"] == "broad_question"
    assert packet["answer"]["mode"] == "themes"
    assert packet["claims"]
    evidence_ids = {x["support_id"] for x in packet["evidence"]}
    for claim in packet["claims"]:
        assert set(claim["support_ids"]).issubset(evidence_ids)
        assert claim["is_verbatim_quote"] is False
    assert packet["policy"]["exact_source_text_exposed"] is False
    assert packet["generation_request"]["restricted_source_text_included"] is False


def test_unsupported_query_abstains_end_to_end():
    packet = build_answer("What did Mahaperiyava say about smartphone push notifications?")
    validate(packet)
    assert packet["answerable"] is False
    assert packet["status"] == "insufficient_evidence"
    assert packet["answer"] is None
    assert packet["claims"] == []
    assert packet["evidence"] == []
    assert packet["generation_request"] is None


def test_question_types_shape_answer_without_changing_evidence():
    source = build_answer("Which chapter discusses Kamakshi's eyes?")
    assert source["question_type"] == "source_lookup"
    assert source["answer"]["mode"] == "source_lookup"

    guidance = build_answer("What should I do when pride makes me ridicule others?")
    assert guidance["question_type"] == "personal_guidance"
    assert guidance["answerable"] is True
    assert guidance["answer"]["mode"] == "personal_guidance_grounding"
    assert guidance["answer"]["modern_application"] is None
    assert guidance["answer"]["modern_application_status"] == "requires_separate_app_generated_layer"


def test_sensitive_historical_material_surfaces_context():
    packet = build_answer(
        "What does the discourse say about uncertain traditions of Pallava origins?"
    )
    assert packet["answerable"] is True
    assert any(c["context_required"] for c in packet["claims"])


def test_generated_answer_validator_accepts_grounded_structure_and_rejects_boundary_breaks():
    packet = build_answer("Does Mahaperiyava teach the essential unity of Shiva and Vishnu?")
    sid = packet["claims"][0]["support_ids"][0]

    good = {
        "answer_text": "The supplied evidence presents an essential unity.",
        "claims": [{"text": "Essential unity is presented.", "support_ids": [sid]}],
        "modern_application": None,
        "speaks_as_mahaperiyava": False,
        "claims_mahaperiyava_verbatim": False,
    }
    assert validate_generated_answer(packet, good)["valid"] is True

    bad = {
        "answer_text": "Invented.",
        "claims": [{
            "text": "Unsupported.",
            "support_ids": ["fake"],
            "quote": "invented source wording",
        }],
        "modern_application": {"label": "mahaperiyava_advice", "text": "Do this"},
        "speaks_as_mahaperiyava": True,
        "claims_mahaperiyava_verbatim": True,
    }
    result = validate_generated_answer(packet, bad)
    assert result["valid"] is False
    assert "must_not_speak_as_mahaperiyava" in result["errors"]
    assert any("support_not_in_retrieved_evidence" in x for x in result["errors"])
    assert any("quote_not_allowed" in x for x in result["errors"])


def test_service_dispatch_exposes_grounded_answer_operation():
    packet = dispatch(
        "mahaperiyava-answer",
        {"query": "Does Mahaperiyava teach the essential unity of Shiva and Vishnu?"}
    )
    assert packet["answerable"] is True
    assert packet["status"] == "grounded_answer_packet"
    assert packet["claims"]
