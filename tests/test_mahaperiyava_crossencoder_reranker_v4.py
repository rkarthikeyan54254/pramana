from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mahaperiyava_candidate_reranker_v3 import CandidateReranker
from mahaperiyava_crossencoder_reranker_v4 import (
    CrossEncoderCandidateReranker,
    FakeCrossEncoderScorer,
    detect_language_v4,
    public_safe_passage,
)
from mahaperiyava_hybrid_retrieval_v2 import HashFieldEmbedder

CP = ROOT / "data/review/mahaperiyava_crossencoder_reranker_checkpoint_v4.json"


def build_offline():
    phase14 = CandidateReranker(embedder=HashFieldEmbedder())
    return CrossEncoderCandidateReranker(
        phase14=phase14,
        scorer=FakeCrossEncoderScorer(),
    )


def test_language_detection_is_not_confused_by_generic_english_role_words():
    assert detect_language_v4("What is the difference between a teacher role and a guru role?") == "en"
    assert detect_language_v4("Padippai affect pannama students sevai eppadi seyyanum?") == "roman_ta"
    assert detect_language_v4("படிப்பையும் பாதிக்காமல் சேவை செய்வது எப்படி?") == "ta"


def test_public_safe_passage_excludes_urls_hashes_and_provenance():
    r = build_offline()
    row = r.records[0]
    text = public_safe_passage(row)
    assert row["claim_summary"] in text
    assert "http://" not in text
    assert "https://" not in text
    assert "snapshot_sha256" not in text
    assert "provenance" not in text
    assert "earlier_secondary" not in text


def test_crossencoder_preserves_exact_title_and_authority():
    r = build_offline()
    assert r.authority_counts() == {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }
    out = r.retrieve("வேதாந்த மதங்களும் மீமாம்ஸையும்")
    assert out["status"] == "retrieved_evidence"
    assert out["retrieval_mode"] == "exact_title"
    assert out["crossencoder_used"] is False
    assert out["hits"][0]["source"]["volume"] == 2
    assert out["hits"][0]["source"]["chapter_ordinal"] == 113


def test_crossencoder_cannot_override_fail_closed_negative():
    r = build_offline()
    for q in (
        "What did Mahaperiyava say about smartphone push notifications?",
        "Did Mahaperiyava discuss Kubernetes service-mesh routing?",
        "செயற்கை நுண்ணறிவு சாட்பாட் பற்றி மஹாபெரியவா என்ன சொன்னார்?",
    ):
        out = r.retrieve(q)
        assert out["status"] == "insufficient_evidence"
        assert out["answerable"] is False
        assert out["hits"] == []
        assert out["crossencoder_used"] is False


def test_checkpoint_contract_when_present():
    if not CP.exists():
        return
    cp = json.loads(CP.read_text(encoding="utf-8"))
    assert cp["benchmark"]["cases"] == 154
    assert cp["model"]["restricted_source_text_embedded_or_reranked"] is False
    assert cp["model"]["model_weights_committed"] is False
    assert cp["model"]["score_cache_committed"] is False
    assert cp["authority_boundary"]["authority_promotions"] == 0
    assert cp["authority_boundary"]["product_retriever_switched"] is False
    assert cp["authority_boundary"]["authority_counts"] == {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }
    assert cp["metrics"]["test"]["abstention"] == 1.0
