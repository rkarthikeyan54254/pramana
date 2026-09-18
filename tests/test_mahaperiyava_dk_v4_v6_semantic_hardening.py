from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data" / "review"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GENERIC = (
    "this teaching centers on",
    "develops a distinct step",
)
EXPECTED = {
    4: {"chapters": 450, "units": 457, "paragraphs": 3208, "covered": 3139, "excluded": 69,
        "bundle_sha": "447ff2dbdf1a8c97ab0c65b36f8ae5cef26fdc0b1d3c85552cd353075cb74e29"},
    5: {"chapters": 298, "units": 345, "paragraphs": 4134, "covered": 3950, "excluded": 184,
        "bundle_sha": "1da25dda072c706402d1978abd6620ab50f3b657e92054935d3f4502cd8389f5"},
    6: {"chapters": 208, "units": 254, "paragraphs": 3160, "covered": 3160, "excluded": 0,
        "bundle_sha": "7eac96834e4b48dc3dd499504d6987b96ff1b305a0f6009e737af7250d796e43"},
}


def _j(v: int, suffix: str):
    return json.loads((REVIEW / f"mahaperiyava_deivathin_kural_v{v}_{suffix}.json").read_text(encoding="utf-8"))


def _rows(v: int):
    p = REVIEW / f"mahaperiyava_deivathin_kural_v{v}_teaching_records.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_v4_v6_hardened_counts_and_authority():
    for v, exp in EXPECTED.items():
        rows = _rows(v)
        assert len(rows) == exp["units"]
        assert len({r["id"] for r in rows}) == len(rows)
        assert {r["source_locus"]["chapter_ordinal"] for r in rows} == set(range(1, exp["chapters"] + 1))
        assert Counter(r["evidence_status"]["authority"] for r in rows) == Counter({"dk_attested": len(rows)})
        assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
        assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)
        assert all(r["attribution"]["wording_status"] == "dk_wording_only" for r in rows)


def test_claim_summaries_are_proposition_specific_not_templates_or_labels():
    for v in EXPECTED:
        rows = _rows(v)
        summaries = []
        for r in rows:
            s = (r.get("claim_summary") or "").strip()
            assert len(s.split()) >= 8, r["id"]
            low = s.lower()
            assert not any(x in low for x in GENERIC), r["id"]
            title = (r["source_locus"].get("chapter_title_ta") or "").strip()
            assert s != title, r["id"]
            assert s not in set(r.get("topics", [])), r["id"]
            summaries.append(s)
        assert len(set(summaries)) == len(summaries)
        prefixes = Counter(" ".join(s.lower().split()[:5]) for s in summaries)
        # Phrase-repetition lint is a warning-style proxy only; it must not become semantic authority.
        assert max(prefixes.values(), default=0) <= 3


def test_exact_paragraph_accounting_and_exclusion_rationales():
    for v, exp in EXPECTED.items():
        index = _j(v, "curation_index")
        cov = index["source_coverage"]
        assert cov["curation_paragraph_count"] == exp["paragraphs"]
        assert cov["covered_curation_paragraph_count"] == exp["covered"]
        assert cov["explicitly_excluded_curation_paragraphs"] == exp["excluded"]
        assert cov["unaccounted_curation_paragraphs"] == 0
        assert cov["covered_curation_paragraph_count"] + cov["explicitly_excluded_curation_paragraphs"] == cov["curation_paragraph_count"]
        assert cov["all_curation_paragraphs_accounted_for"] is True
        exclusions = index.get("explicit_exclusions", [])
        assert len(exclusions) == exp["excluded"]
        for e in exclusions:
            rationale = (e.get("rationale") or e.get("reason") or "").strip()
            assert rationale
            assert SHA256.fullmatch(e["paragraph_sha256"])


def test_paragraph_hashes_provenance_and_historical_witness_policy():
    for v in EXPECTED:
        rows = _rows(v)
        index = _j(v, "curation_index")
        assert len(index["units"]) == len(rows)
        for u in index["units"]:
            assert u["source_paragraph_ids"]
            assert len(u["source_paragraph_ids"]) == len(u["source_paragraph_hashes"])
            assert all(SHA256.fullmatch(h) for h in u["source_paragraph_hashes"])
            assert "historical_witness" in u and u["historical_witness"] is None
        for r in rows:
            assert r["provenance"]
            assert all(SHA256.fullmatch(p["snapshot_sha256"]) for p in r["provenance"] if p.get("snapshot_sha256"))
            assert r["rights"]["source_text_tier"] == "restricted"
            assert r["rights"]["public_export"] == "metadata_only"


def test_semantic_hardening_is_not_publication_approval():
    for v, exp in EXPECTED.items():
        catalog = _j(v, "catalog")
        manifest = _j(v, "curator_manifest")
        audit = _j(v, "semantic_completion_audit")
        spine = _j(v, "semantic_spine")
        assert "hardened" in catalog["semantic_status"]
        assert "not_publication_approved" in catalog["semantic_status"]
        assert manifest["policy"]["human_publication_review_still_required"] is True
        assert manifest["policy"]["historical_witness_comparison_deferred"] is True
        assert manifest["policy"]["no_historical_witness_promotion"] is True
        assert manifest["source_packet"]["source_bundle_sha256"] == exp["bundle_sha"]
        assert manifest["counts"]["teaching_units"] == exp["units"]
        assert audit["result"] == "PASS"
        assert audit["checks"]["generic_template_summary_count"] == 0
        assert audit["checks"]["topic_label_only_summary_count"] == 0
        assert audit["checks"]["exact_restricted_paragraph_leak_count"] == 0
        assert audit["checks"]["paragraph_hash_recomputation_failures"] == 0
        assert audit["checks"]["record_provenance_snapshot_mismatches"] == 0
        assert audit["checks"]["semantic_hardening_complete"] is True
        assert audit["checks"]["publication_approved"] is False
        assert len(spine["units"]) == exp["units"]


def test_public_safe_artifacts_do_not_contain_restricted_text_fields():
    for v in EXPECTED:
        rows = _rows(v)
        index = _j(v, "curation_index")
        manifest = _j(v, "curator_manifest")
        spine = _j(v, "semantic_spine")
        for r in rows:
            assert "text" not in r and "exact_text_restricted" not in r
        for collection in (index["units"], manifest["units"], spine["units"]):
            for u in collection:
                assert "text" not in u and "exact_text_restricted" not in u


def test_sensitive_context_flags_remain_available():
    required = {
        4: {"caste_varna_normative_claim", "gender_discriminatory_norm_requires_context", "historical_claim_requires_external_verification", "political_social_claim_requires_context", "religious_comparison_attributed_only", "scientific_claim_requires_external_verification", "violence_requires_context"},
        5: {"caste_varna_normative_claim", "gender_discriminatory_norm_requires_context", "hagiographic_tradition", "historical_claim_requires_external_verification", "political_social_claim_requires_context", "religious_comparison_attributed_only", "self_harm_or_suicide_historical_material", "violence_requires_context"},
        6: {"caste_varna_normative_claim", "esoteric_practice_requires_qualified_guidance", "gender_discriminatory_norm_requires_context", "hagiographic_tradition", "historical_claim_requires_external_verification", "religious_comparison_attributed_only", "scientific_claim_requires_external_verification", "supernatural_claim_attributed_only", "violence_requires_context"},
    }
    for v in EXPECTED:
        flags = {f for r in _rows(v) for f in r.get("flags", [])}
        assert required[v] <= flags


def test_v4_special_24b_source_is_preserved():
    catalog = _j(4, "catalog")
    special = [
        c for c in catalog["chapters"]
        if c.get("source_key") == "mahaperiyava-deivathin-kural-v4-24b"
        or c.get("url") == "https://www.kamakoti.org/tamil/part4kural24b.html"
    ]
    assert len(special) == 1
    assert special[0]["legacy_file_number"] is None
    assert special[0]["url"] == "https://www.kamakoti.org/tamil/part4kural24b.html"
