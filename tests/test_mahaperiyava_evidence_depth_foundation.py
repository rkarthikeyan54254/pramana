from __future__ import annotations
from collections import Counter
import importlib.util,json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"data/review"
def J(p): return json.loads(p.read_text(encoding="utf-8"))

def mod():
    p=ROOT/"scripts/validate_mahaperiyava_evidence_depth.py"
    s=importlib.util.spec_from_file_location("ed",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def item(stage,before,after,role,rel,match="same_claim"):
    return {"version":"1.0","review_id":"test.review","teaching_id":"mahaperiyava.deivathin_kural.v1.test.unit","review_stage":stage,"authority_before":before,"authority_after":after,"decision":"supported","review_method":"manual_item_level","evidence":[{"source_key":"test","witness_role":role,"locus":"p. 1","snapshot_sha256":"a"*64,"source_date":"1958","relation_to_dk":rel,"match_level":match,"rights_status":"restricted_private_research","note":None}],"guardrails":{"source_text_embedded":False,"verbatim_wording_claimed":False,"primary_source_claimed_without_primary_evidence":False,"external_factual_truth_claimed":False,"machine_similarity_grants_authority":False,"majority_vote_grants_authority":False},"reviewer":"curator","reviewed_at":"2026-09-18T12:00:00Z","notes":None}

def test_supported_stages_validate():
    m=mod(); s=J(ROOT/"schema/mahaperiyava_evidence_depth_review.schema.json")
    assert m.validate_review_item(item("dk_print_check","dk_attested","dk_print_checked","print_reference","same_compilation_print"),s)
    assert m.validate_review_item(item("earlier_witness_check","dk_attested","earlier_witness_supported","earlier_secondary","earlier_attestation"),s)
    assert m.validate_review_item(item("primary_source_check","earlier_witness_supported","primary_source_verified","primary","independent_primary"),s)

def test_authority_inflation_fails_closed():
    m=mod(); s=J(ROOT/"schema/mahaperiyava_evidence_depth_review.schema.json")
    with pytest.raises(AssertionError): m.validate_review_item(item("earlier_witness_check","dk_attested","primary_source_verified","earlier_secondary","earlier_attestation"),s)
    with pytest.raises(AssertionError): m.validate_review_item(item("earlier_witness_check","dk_attested","earlier_witness_supported","earlier_secondary","earlier_attestation","topic_only"),s)

def test_policy_is_fail_closed():
    p=J(R/"mahaperiyava_evidence_depth_policy.json")["principles"]
    for k in ["item_level_review_required","collection_lineage_never_auto_promotes_claims","machine_similarity_never_grants_authority","majority_vote_never_grants_authority","print_check_is_not_primary_source_verification","earlier_witness_support_is_not_verbatim_primary_wording","no_transitive_authority_promotion","publication_approval_is_separate"]:
        assert p[k] is True

def test_foundation_revalidates_without_new_promotion():
    a=J(R/"mahaperiyava_evidence_depth_foundation_audit.json")
    c=a["checks"]
    assert a["foundation_result"]=="PASS"
    assert c["existing_earlier_witness_supported_count"]==33
    assert c["legacy_placeholder_hash_repairs"]==9
    assert c["legacy_missing_provenance_url_repairs"]==2
    assert len(a["provenance_url_repairs"])==2
    assert all(x["authority_changed"] is False for x in a["provenance_url_repairs"])
    assert c["earlier_witness_supported_with_pinned_item_level_evidence_after_repair"]==33
    assert c["known_partial_match_negative_controls"]==4 and c["negative_controls_still_dk_attested"] is True
    assert c["new_authority_promotions"]==0 and c["dk_print_checked_count"]==0 and c["primary_source_verified_count"]==0
    assert c["publication_approved"] is False
    assert all(x["authority_changed"] is False for x in a["provenance_hash_repairs"])

def test_forward_queue_is_bounded_and_cross_volume():
    q=J(R/"mahaperiyava_evidence_depth_pilot_queue.json")
    assert q["count"]==30 and len(q["items"])==30
    assert len({x["teaching_id"] for x in q["items"]})==30
    assert Counter(x["volume"] for x in q["items"])=={1:6,2:4,3:4,4:4,5:4,6:4,7:4}
    assert all(x["current_authority"]=="dk_attested" and x["source_text_included"] is False for x in q["items"])

def test_teaching_schema_has_authority_gates():
    s=J(ROOT/"schema/teaching_record.schema.json")
    c=[x.get("$comment","") for x in s.get("allOf",[])]
    assert any("dk_print_checked requires" in x for x in c)
    assert any("earlier_witness_supported requires" in x for x in c)
    assert any("primary_source_verified requires" in x for x in c)
