import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ask_mahaperiyava_v1.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("ask_v1", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_retriever_loads_frozen_v1_corpus():
    mod = _load_module()
    r = mod.V1Retriever()
    assert len(r.records) == 927


def test_retriever_finds_unique_curated_concept_anchors():
    mod = _load_module()
    r = mod.V1Retriever()
    cases = [
        ("nonduality_of_brahman", 4),
        ("karma_and_phaladata", 108),
        ("shiva_vishnu_essential_unity", 136),
        ("kamakshiyin_kangal", 162),
    ]
    for query, chapter in cases:
        result = r.retrieve(query, top_k=5)
        assert result["status"] == "retrieved_evidence"
        assert chapter in [h["chapter_ordinal"] for h in result["hits"]], query


def test_retriever_basic_tamil_alias_path_works_for_siva_vishnu():
    mod = _load_module()
    r = mod.V1Retriever()
    result = r.retrieve("சிவனும் விஷ்ணுவும் ஒன்றா?", top_k=5)
    assert result["status"] == "retrieved_evidence"
    assert 136 in [h["chapter_ordinal"] for h in result["hits"]]


def test_retriever_abstains_when_v1_has_no_meaningful_match():
    mod = _load_module()
    r = mod.V1Retriever()
    result = r.retrieve("What did Mahaperiyava say about smartphones?", top_k=5)
    assert result["status"] == "insufficient_evidence"
    assert result["hits"] == []


def test_retrieval_output_is_provenance_forward_not_quote_claim():
    mod = _load_module()
    r = mod.V1Retriever()
    result = r.retrieve("shiva_vishnu_essential_unity", top_k=3)
    assert "not verbatim quotations" in result["note"]
    for hit in result["hits"]:
        assert hit["digital_url"]
        assert hit["authority"] in {"dk_attested", "earlier_witness_supported"}
        assert "claim_summary" in hit
        assert "quote" not in hit
