from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ask_mahaperiyava import load_corpus
from mahaperiyava_hybrid_retrieval import (
    DeterministicHashEmbedder,
    HybridMahaperiyavaRetriever,
    public_safe_document,
)

BENCHMARK = ROOT / "data/review/mahaperiyava_retrieval_benchmark_v2.json"
CHECKPOINT = ROOT / "data/review/mahaperiyava_hybrid_retrieval_checkpoint_v1.json"


def test_benchmark_v2_is_large_multilingual_and_split():
    d = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    cases = d["cases"]
    assert len(cases) == 124
    assert len({c["id"] for c in cases}) == 124
    assert Counter(c["group"] for c in cases) == Counter({
        "natural_supported": 80,
        "hard_negative": 30,
        "exact_title_lookup": 14,
    })
    languages = Counter(c["language"] for c in cases)
    assert languages["en"] >= 60
    assert languages["ta"] >= 30
    assert languages["roman_ta"] >= 20
    assert {c["split"] for c in cases} == {"dev", "test"}


def test_embedding_document_is_public_safe_metadata_only():
    rows = load_corpus()
    for row in rows[:50]:
        text = public_safe_document(row)
        assert row["claim_summary"] in text
        assert "http://" not in text
        assert "https://" not in text
        assert "snapshot_sha256" not in text
        assert "provenance" not in text
        assert "earlier_secondary" not in text


def test_hybrid_plumbing_does_not_change_authority():
    r = HybridMahaperiyavaRetriever(embedder=DeterministicHashEmbedder())
    assert r.authority_counts() == {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }

    out = r.retrieve("வேதாந்த மதங்களும் மீமாம்ஸையும்", top_k=5)
    assert out["status"] == "retrieved_evidence"
    assert out["retrieval_mode"] == "exact_title"
    assert out["hits"][0]["source"]["volume"] == 2
    assert out["hits"][0]["source"]["chapter_ordinal"] == 113


def test_hybrid_preserves_fail_closed_modern_attribution():
    r = HybridMahaperiyavaRetriever(embedder=DeterministicHashEmbedder())
    for q in (
        "What did Mahaperiyava say about smartphone push notifications?",
        "Did Mahaperiyava discuss Kubernetes service-mesh routing?",
        "What was Mahaperiyava's view on generative-AI copyright licensing?",
    ):
        out = r.retrieve(q, top_k=5)
        assert out["status"] == "insufficient_evidence"
        assert out["answerable"] is False
        assert out["hits"] == []


def test_real_model_checkpoint_keeps_trust_boundary_when_present():
    if not CHECKPOINT.exists():
        return
    cp = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    assert cp["benchmark"]["cases"] == 124
    assert cp["model"]["restricted_source_text_embedded"] is False
    assert cp["model"]["embedding_vectors_committed"] is False
    assert cp["authority_boundary"]["authority_promotions"] == 0
    assert cp["authority_boundary"]["authority_counts"] == {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }
    assert cp["authority_boundary"]["retrieval_score_changes_authority"] is False
    assert cp["metrics"]["hybrid_test"]["abstention"] == 1.0
