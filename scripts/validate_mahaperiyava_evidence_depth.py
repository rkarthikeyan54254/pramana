#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter
import hashlib, json, re
from pathlib import Path
import jsonschema

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"data/review"

def J(p): return json.loads(p.read_text(encoding="utf-8"))
def JL(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def H(o): return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def records():
    files=sorted(R.glob("mahaperiyava_dk_v1_*_teaching_records.jsonl"))
    files += [R/f"mahaperiyava_deivathin_kural_v{v}_teaching_records.jsonl" for v in range(2,8)]
    rows=[]
    for p in files: rows += JL(p)
    by={x["id"]:x for x in rows}
    assert len(by)==len(rows)
    return rows,by

def validate_review_item(item,schema=None):
    schema=schema or J(ROOT/"schema/mahaperiyava_evidence_depth_review.schema.json")
    jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(item)
    st,dec,bef,aft=item["review_stage"],item["decision"],item["authority_before"],item["authority_after"]
    ev=item["evidence"]
    if aft!=bef: assert dec=="supported"
    if aft=="dk_print_checked":
        assert st=="dk_print_check"
        assert any(e["witness_role"]=="print_reference" and e["match_level"] in {"exact_wording","close_paraphrase","same_claim"} for e in ev)
    if aft=="earlier_witness_supported":
        assert st=="earlier_witness_check"
        assert any(e["witness_role"]=="earlier_secondary" and e["relation_to_dk"] in {"earlier_attestation","possible_ancestor","dependency_unknown"} and e["match_level"] in {"exact_wording","close_paraphrase","same_claim"} for e in ev)
    if aft=="primary_source_verified":
        assert st=="primary_source_check"
        assert any(e["witness_role"]=="primary" and e["relation_to_dk"]=="independent_primary" and e["match_level"] in {"exact_wording","close_paraphrase","same_claim"} for e in ev)
    if dec!="supported": assert aft==bef
    return True

def main():
    policy=J(R/"mahaperiyava_evidence_depth_policy.json")
    baseline=J(R/"mahaperiyava_evidence_depth_baseline.json")
    queue=J(R/"mahaperiyava_evidence_depth_pilot_queue.json")
    audit=J(R/"mahaperiyava_evidence_depth_foundation_audit.json")
    manifest=J(ROOT/"sources/manifest.json")
    ts=J(ROOT/"schema/teaching_record.schema.json")

    p=policy["principles"]
    assert p["item_level_review_required"] and p["machine_similarity_never_grants_authority"] and p["majority_vote_never_grants_authority"]
    assert p["print_check_is_not_primary_source_verification"] and p["no_transitive_authority_promotion"]

    rows,by=records()
    assert len(rows)==3368
    c=Counter(x["evidence_status"]["authority"] for x in rows)
    assert c["dk_attested"]==3335 and c["earlier_witness_supported"]==33
    assert c["dk_print_checked"]==0 and c["primary_source_verified"]==0

    v=jsonschema.Draft202012Validator(ts,format_checker=jsonschema.FormatChecker())
    for row in rows: v.validate(row)

    mb={x["key"]:x for x in manifest["sources"]}
    sup=[x for x in rows if x["evidence_status"]["authority"]=="earlier_witness_supported"]
    for row in sup:
        witnesses=[p for p in row["provenance"] if p["witness_role"]=="earlier_secondary" and isinstance(p.get("snapshot_sha256"),str) and re.fullmatch(r"[0-9a-f]{64}",p["snapshot_sha256"]) and (p.get("locus") or "").strip()]
        assert witnesses, row["id"]
        for w in witnesses:
            src=mb.get(w["source_key"])
            if src and src.get("expected_sha256"): assert w["snapshot_sha256"]==src["expected_sha256"], row["id"]

    assert baseline["teaching_record_count"]==3368 and baseline["publication_approved"] is False
    assert queue["count"]==30 and len(queue["items"])==30
    assert {x["volume"] for x in queue["items"]}==set(range(1,8))
    assert dict(Counter(x["volume"] for x in queue["items"]))=={1:6,2:4,3:4,4:4,5:4,6:4,7:4}
    for x in queue["items"]:
        r=by[x["teaching_id"]]
        assert r["evidence_status"]["authority"]=="dk_attested"
        assert x["record_metadata_sha256"]==H(r)
        s=r.get("claim_summary") or ""
        assert x["claim_summary_sha256"]==hashlib.sha256(s.encode()).hexdigest()
        assert x["source_text_included"] is False and "exact_text_restricted" not in x

    a=audit["checks"]
    assert audit["foundation_result"]=="PASS"
    assert a["legacy_placeholder_hash_repairs"]==9
    assert a["legacy_missing_provenance_url_repairs"]==2
    assert len(audit["provenance_url_repairs"])==2
    assert all(x["authority_changed"] is False for x in audit["provenance_url_repairs"])
    assert a["earlier_witness_supported_with_pinned_item_level_evidence_after_repair"]==33
    assert a["known_partial_match_negative_controls"]==4 and a["negative_controls_still_dk_attested"] is True
    assert a["new_authority_promotions"]==0 and a["restricted_source_text_embedded"] is False and a["publication_approved"] is False
    print("Mahaperiyava evidence-depth gate: GREEN (3368 records; 33/33 earlier-witness promotions pinned; 9 legacy hashes repaired; 4 negative controls unpromoted; 30 forward candidates; 0 new promotions)")

if __name__=="__main__": main()
