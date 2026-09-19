from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mahaperiyava_candidate_reranker_v3 import (
    CandidateReranker,
    PROFILES,
    concept_query,
    detect_language,
)
from mahaperiyava_hybrid_retrieval_v2 import HashFieldEmbedder

CP = ROOT / "data/review/mahaperiyava_candidate_reranker_checkpoint_v3.json"


def test_language_detection_and_concept_views():
    assert detect_language("படிப்பையும் பாதிக்காமல் சேவை") == "ta"
    assert detect_language("Padippai affect pannama students sevai") == "roman_ta"
    assert detect_language("How should students balance service and study?") == "en"

    q = concept_query("பொருள் செல்வத்தை விட அறியாமை நீங்கி மோக்ஷம் பெறுவது ஏன்?")
    assert "wealth" in q or "prosperity" in q
    assert "ignorance" in q
    assert "moksha" in q or "liberation" in q

    q2 = concept_query("Padippai affect pannama students sevai eppadi seyyanum?")
    assert "study" in q2 or "education" in q2
    assert "service" in q2


def test_profiles_are_explicit_and_finite():
    assert {"lexical_guarded", "balanced", "concept_heavy", "tamil_concept_title"} <= set(PROFILES)
    for p in PROFILES.values():
        assert p.rrf_k > 0


def test_offline_plumbing_preserves_authority_and_exact_title():
    r = CandidateReranker(embedder=HashFieldEmbedder())
    assert r.authority_counts() == {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }

    out = r.retrieve("வேதாந்த மதங்களும் மீமாம்ஸையும்", profile="balanced")
    assert out["status"] == "retrieved_evidence"
    assert out["retrieval_mode"] == "exact_title"
    assert out["hits"][0]["source"]["volume"] == 2
    assert out["hits"][0]["source"]["chapter_ordinal"] == 113


def test_modern_queries_remain_fail_closed():
    r = CandidateReranker(embedder=HashFieldEmbedder())
    for q in (
        "What did Mahaperiyava say about smartphone push notifications?",
        "Did Mahaperiyava discuss Kubernetes service-mesh routing?",
        "செயற்கை நுண்ணறிவு சாட்பாட் பற்றி மஹாபெரியவா என்ன சொன்னார்?",
    ):
        out = r.retrieve(q, profile="balanced")
        assert out["status"] == "insufficient_evidence"
        assert out["answerable"] is False
        assert out["hits"] == []


def test_real_checkpoint_contract_when_present():
    if not CP.exists():
        return
    cp = json.loads(CP.read_text(encoding="utf-8"))
    assert cp["benchmark"]["cases"] == 154
    assert cp["architecture"]["restricted_source_text_embedded"] is False
    assert cp["architecture"]["embedding_vectors_committed"] is False
    assert cp["architecture"]["product_retriever_switched"] is False
    assert cp["authority_boundary"]["authority_promotions"] == 0
    assert cp["authority_boundary"]["authority_counts"] == {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }
    assert cp["metrics"]["test"]["abstention"] == 1.0
