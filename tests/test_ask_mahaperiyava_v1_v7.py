from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ask_mahaperiyava import MahaperiyavaRetriever, classify_question

CHECKPOINT = ROOT / "data/review/mahaperiyava_v1_v7_retrieval_checkpoint.json"


def test_loads_exact_v1_v7_public_safe_frontier():
    r = MahaperiyavaRetriever()
    assert len(r.records) == 3368
    counts = {}
    for row in r.records:
        v = row["source_locus"]["volume"]
        counts[v] = counts.get(v, 0) + 1
        assert "exact_text_restricted" not in row
    assert counts == {1:927,2:673,3:370,4:457,5:345,6:254,7:342}


def test_unsupported_modern_query_abstains():
    out = MahaperiyavaRetriever().retrieve("What did Mahaperiyava say about smartphone push notifications?")
    assert out["status"] == "insufficient_evidence"
    assert out["answerable"] is False
    assert out["hits"] == []


def test_weak_single_overlap_abstains():
    out = MahaperiyavaRetriever().retrieve("smartphone push notifications")
    assert out["status"] == "insufficient_evidence"
    assert out["answerable"] is False
    assert out["hits"] == []


def test_tamil_and_all_volume_smokes():
    r = MahaperiyavaRetriever()

    ta = r.retrieve("சிவனும் விஷ்ணுவும் ஒன்றா?", 5)
    assert "mahaperiyava.deivathin_kural.v1.siva_vishnu_abhedam.shiva_vishnu_essential_unity" in {x["support_id"] for x in ta["hits"]}

    v2 = r.retrieve("கிழவியும் குழவியும்", 3)
    assert any(x["source"]["volume"] == 2 and x["source"]["chapter_ordinal"] == 1 for x in v2["hits"])

    v3 = r.retrieve("பிள்ளையார் சுழி", 3)
    assert any(x["source"]["volume"] == 3 and x["source"]["chapter_ordinal"] == 1 for x in v3["hits"])

    fixed = [
        ("What does the Ganesha moon curse story teach about pride and ridicule?", "mahaperiyava.deivathin_kural.v4.c033.chapter_teaching"),
        ("What does the discourse say about uncertain traditions of Pallava origins?", "mahaperiyava.deivathin_kural.v5.c055.chapter_teaching"),
        ("Why invoke Ganesha before beginning an undertaking?", "mahaperiyava.deivathin_kural.v6.c001.obstacle_removal_across_life"),
        ("Should Tamil devotion to Ganesha become sectarian or separatist?", "mahaperiyava.deivathin_kural.v7.c002.chapter_teaching"),
    ]
    for query, expected in fixed:
        out = r.retrieve(query, 5)
        assert expected in {x["support_id"] for x in out["hits"]}, (query, out)


def test_question_type_and_generation_contract():
    assert classify_question("What should I do when I feel angry?") == "personal_guidance"
    assert classify_question("What does Mahaperiyava say about bhakti?") == "broad_question"
    assert classify_question("Which chapter discusses Kamakshi's eyes?") == "source_lookup"

    out = MahaperiyavaRetriever().retrieve("What does Mahaperiyava say about bhakti?", 3)
    c = out["generation_contract"]
    assert c["never_speak_as_mahaperiyava"] is True
    assert c["every_substantive_answer_idea_requires_support_ids"] is True
    assert c["retrieval_score_never_changes_authority"] is True
    assert c["raw_retrieval_is_not_advice"] is True
    assert c["generated_text_may_not_enter_corpus"] is True
    assert c["synthesis_shape"] == "themes_not_single_prescription"


def test_hits_are_metadata_only_and_evidence_aware():
    out = MahaperiyavaRetriever().retrieve("Kamakshi compassion", 5)
    assert out["hits"]
    for hit in out["hits"]:
        assert hit["exact_source_text_exposed"] is False
        assert hit["support_id"]
        assert hit["source"]["work"] == "Deivathin Kural"
        assert hit["evidence_status"]["authority"] in {"dk_attested","dk_print_checked","earlier_witness_supported","primary_source_verified"}
        assert "attested in Deivathin Kural" in hit["safe_attribution"]


def test_checkpoint_is_honest_and_fail_closed():
    cp = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    assert cp["checkpoint"] == "MAHAPERIYAVA_V1_V7_RETRIEVAL_FOUNDATION"
    assert cp["authority_boundary"]["retrieval_score_changes_authority"] is False
    assert cp["authority_boundary"]["answer_generation_changes_authority"] is False
    assert cp["authority_boundary"]["exact_source_text_exposed"] is False
    assert cp["authority_boundary"]["publication_approval_implied"] is False
    assert cp["metrics"]["abstention_accuracy"] == 1.0
    assert cp["metrics"]["supported_cases"] >= 13
    assert cp["metrics"]["distinct_expected_volumes_hit"] == 7
