from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/"data"/"review"
SCHEMA=ROOT/"schema"/"teaching_record.schema.json"
CATALOG=REVIEW/"mahaperiyava_deivathin_kural_v4_catalog.json"
MANIFEST=REVIEW/"mahaperiyava_deivathin_kural_v4_curator_manifest.json"
INDEX=REVIEW/"mahaperiyava_deivathin_kural_v4_curation_index.json"
RECORDS=REVIEW/"mahaperiyava_deivathin_kural_v4_teaching_records.jsonl"
AUDIT=REVIEW/"mahaperiyava_deivathin_kural_v4_semantic_completion_audit.json"

def _json(p): return json.loads(p.read_text(encoding="utf-8"))
def _jsonl(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

def test_v4_shape_authority_and_frontier():
    rows=_jsonl(RECORDS)
    assert len(rows)==487
    assert len({r["id"] for r in rows})==487
    assert {r["source_locus"]["chapter_ordinal"] for r in rows}==set(range(1,451))
    assert Counter(r["evidence_status"]["authority"] for r in rows)==Counter({"dk_attested":487})
    assert all(r["evidence_status"]["digital_attestation"]=="confirmed" for r in rows)
    assert all(r["evidence_status"]["print_check"]=="not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"]=="unknown" for r in rows)

def test_v4_schema_shape_rights_and_nonquotation():
    schema=_json(SCHEMA); rows=_jsonl(RECORDS); allowed=set(schema["properties"]); required=set(schema["required"]); id_re=re.compile(schema["properties"]["id"]["pattern"])
    for r in rows:
        assert not (required-set(r)), r["id"]
        assert not (set(r)-allowed), r["id"]
        assert id_re.fullmatch(r["id"]), r["id"]
        assert "exact_text_restricted" not in r and "text" not in r
        assert r["rights"]["source_text_tier"]=="restricted" and r["rights"]["public_export"]=="metadata_only"
        assert r["attribution"]["dk_attestation"]=="located" and r["attribution"]["wording_status"]=="dk_wording_only"
        assert r["claim_summary"] and isinstance(r["topics"],list) and isinstance(r["flags"],list)
        assert re.fullmatch(r"[0-9a-f]{64}",r["provenance"][0]["snapshot_sha256"])

def test_v4_paragraph_accounting_complete():
    i=_json(INDEX); cov=i["source_coverage"]
    assert cov["full_extracted_paragraph_count"]==52254
    assert cov["mechanically_excluded_chrome_paragraph_count"]==49046
    assert cov["curation_paragraph_count"]==3208
    assert cov["covered_curation_paragraph_count"]==3208
    assert cov["explicitly_excluded_curation_paragraphs"]==0
    assert cov["unaccounted_curation_paragraphs"]==0
    assert cov["intentional_overlap_paragraphs"]==0
    assert cov["all_curation_paragraphs_accounted_for"] is True
    assert len(i["units"])==487
    assert all(u["historical_witness"] is None for u in i["units"])

def test_v4_manifest_and_source_baseline():
    m=_json(MANIFEST); rows=_jsonl(RECORDS)
    assert m["counts"]["chapters"]==450 and m["counts"]["teaching_units"]==487
    assert m["counts"]["curation_source_paragraphs"]==3208 and m["counts"]["covered_curation_paragraphs"]==3208
    assert m["counts"]["mechanically_excluded_raw_paragraphs"]==49046
    assert {u["id"] for u in m["units"]}=={r["id"] for r in rows}
    assert all(u["historical_witness"] is None for u in m["units"])
    assert m["source_packet"]["snapshot_count_after_volume_4"]==1219
    assert m["source_packet"]["live_official_page_count"]==450 and m["source_packet"]["archive_recovery_count"]==0

def test_v4_catalog_preserves_special_24b_and_live_sources():
    c=_json(CATALOG); assert c["chapter_count"]==450 and len(c["chapters"])==450
    assert [x["ordinal"] for x in c["chapters"]]==list(range(1,451))
    special=[x for x in c["chapters"] if x["legacy_file_id"]=="24b"]
    assert len(special)==1
    assert special[0]["url"]=="https://www.kamakoti.org/tamil/part4kural24b.html"
    assert all(x["source_availability"]["retrieval_mode"]=="live_official" for x in c["chapters"])

def test_v4_sensitive_context_flags_exist():
    rows=_jsonl(RECORDS); flags={f for r in rows for f in r.get("flags",[])}
    required={"caste_varna_normative_claim","gender_discriminatory_norm_requires_context","self_harm_or_suicide_historical_material","explicit_nonendorsement_required","violence_requires_context","scientific_claim_requires_external_verification","religious_comparison_attributed_only"}
    assert required<=flags

def test_v4_public_artifacts_do_not_embed_source_text():
    rows=_jsonl(RECORDS); i=_json(INDEX); m=_json(MANIFEST)
    assert all("text" not in r and "exact_text_restricted" not in r for r in rows)
    assert all("text" not in u and "exact_text_restricted" not in u for u in i["units"])
    assert all("text" not in u and "exact_text_restricted" not in u for u in m["units"])

def test_v4_completion_audit_passes():
    a=_json(AUDIT); assert a["result"]=="PASS"
    assert a["checks"]["chapter_count"]==450 and a["checks"]["teaching_record_count"]==487
    assert a["checks"]["unaccounted_curation_paragraph_count"]==0
    assert a["checks"]["all_historical_witness_null"] is True
    assert a["checks"]["source_text_embedded_in_public_artifacts"] is False
    assert a["checks"]["snapshot_count_after_volume_4"]==1219
    assert a["checks"]["special_legacy_file_24b_preserved"] is True
