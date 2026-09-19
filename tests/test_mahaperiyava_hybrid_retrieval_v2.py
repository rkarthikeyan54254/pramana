from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ask_mahaperiyava import load_corpus
from mahaperiyava_hybrid_retrieval_v2 import (
    FieldedHybridRetriever,
    HashFieldEmbedder,
    _public_claim,
    _public_title_topic,
)

BENCHMARK = ROOT / "data/review/mahaperiyava_retrieval_benchmark_v3.json"
CHECKPOINT = ROOT / "data/review/mahaperiyava_hybrid_retrieval_checkpoint_v2.json"


def test_v3_benchmark_shape_and_multilingual_negatives():
    d = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    cases = d["cases"]
    assert len(cases) == 154
    assert len({x["id"] for x in cases}) == 154
    groups = Counter(x["group"] for x in cases)
    assert groups["natural_supported"] == 80
    assert groups["exact_title_lookup"] == 14
    assert groups["phase13_supported"] == 24
    assert groups["hard_negative"] == 36
    negatives = [x for x in cases if x["group"] == "hard_negative"]
    langs = Counter(x["language"] for x in negatives)
    assert langs["en"] >= 32
    assert langs["ta"] >= 2
    assert langs["roman_ta"] >= 2


def test_field_documents_are_public_safe_metadata_only():
    for row in load_corpus()[:100]:
        for text in (_public_claim(row), _public_title_topic(row)):
            assert "http://" not in text
            assert "https://" not in text
            assert "snapshot_sha256" not in text
            assert "provenance" not in text
            assert "earlier_secondary" not in text


def test_fielded_retriever_keeps_authority_and_exact_title_boundary():
    r = FieldedHybridRetriever(HashFieldEmbedder())
    assert r.authority_counts() == {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }
    out = r.retrieve("வேதாந்த மதங்களும் மீமாம்ஸையும்", top_k=5)
    assert out["status"] == "retrieved_evidence"
    assert out["retrieval_mode"] == "exact_title"
    assert out["hits"][0]["source"]["volume"] == 2
    assert out["hits"][0]["source"]["chapter_ordinal"] == 113


def test_multilingual_modern_subjects_fail_closed():
    r = FieldedHybridRetriever(HashFieldEmbedder())
    queries = (
        "Did Mahaperiyava discuss retrieval-augmented generation and vector databases?",
        "மஹாபெரியவா செயற்கை நுண்ணறிவு சாட்பாட்கள் பற்றி என்ன சொன்னார்?",
        "Mahaperiyava cryptocurrency staking pathi enna sonnaar?",
        "மஹாபெரியவா ஸ்மார்ட்போன் அறிவிப்புகள் பற்றி என்ன சொன்னார்?",
        "Mahaperiyava UPI transaction security pathi enna advise panninaar?",
    )
    for q in queries:
        out = r.retrieve(q, top_k=5)
        assert out["status"] == "insufficient_evidence", (q, out)
        assert out["answerable"] is False
        assert out["hits"] == []


def test_real_checkpoint_keeps_trust_boundary_when_present():
    if not CHECKPOINT.exists():
        return
    cp = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    assert cp["benchmark"]["cases"] == 154
    assert cp["selection"]["restricted_source_text_embedded"] is False
    assert cp["selection"]["embedding_vectors_committed"] is False
    assert cp["authority_boundary"]["authority_promotions"] == 0
    assert cp["authority_boundary"]["authority_counts"] == {
        "dk_attested": 3329,
        "earlier_witness_supported": 39,
    }
    assert cp["metrics"]["tuned_test"]["abstention"] == 1.0
