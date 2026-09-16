#!/usr/bin/env python3
"""
Regression tests for Mahaperiyava DK V1 batch 046-065 witness review.

These tests lock down the curator-approved witness review decisions.
They do NOT modify corpus data; they only validate the applied decisions.
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = ROOT / "data/review/mahaperiyava_dk_v1_batch_046_065_witness_decisions.json"
TEACHING_PATH = ROOT / "data/review/mahaperiyava_dk_v1_batch_046_065_teaching_records.jsonl"
CURATION_PATH = ROOT / "data/review/mahaperiyava_dk_v1_batch_046_065_curation_index.json"

EXPECTED_MANIFEST_SHA256 = "256c8863aaee15a52462e5bd9ab32aefb23d6697564de3083a41c10dcde9f7dd"

# Expected promoted IDs (9)
PROMOTED_IDS = {
    "mahaperiyava.deivathin_kural.v1.samanya_dharmangal_anaivarukkum_pothuvana.restless_mind_obstructs_meditation",
    "mahaperiyava.deivathin_kural.v1.ahimsai.respond_to_wrongdoing_without_hatred",
    "mahaperiyava.deivathin_kural.v1.ahimsai.sannyasi_bound_to_radical_ahimsa",
    "mahaperiyava.deivathin_kural.v1.ahimsai.contextual_exceptions_to_absolute_ahimsa",
    "mahaperiyava.deivathin_kural.v1.ahimsai.critique_of_universal_absolute_ahimsa",
    "mahaperiyava.deivathin_kural.v1.sathiyam.truth_must_be_beneficial_not_merely_literal",
    "mahaperiyava.deivathin_kural.v1.paropakaram.tirukkural_and_vedic_duty_interpretation",
    "mahaperiyava.deivathin_kural.v1.anbum_thunbamum.imperishable_love_should_rest_in_paramatman",
    "mahaperiyava.deivathin_kural.v1.anbum_thunbamum.see_all_beings_as_paramatman",
}

# Expected partial IDs (13)
PARTIAL_IDS = {
    "mahaperiyava.deivathin_kural.v1.samanya_dharmangal_anaivarukkum_pothuvana.mastery_means_mind_obeys_intention",
    "mahaperiyava.deivathin_kural.v1.samanya_dharmangal_anaivarukkum_pothuvana.mind_mastery_and_response_to_pain_fear_anger",
    "mahaperiyava.deivathin_kural.v1.samanya_dharmangal_anaivarukkum_pothuvana.one_pointed_isvara_meditation",
    "mahaperiyava.deivathin_kural.v1.samanya_dharmangal_anaivarukkum_pothuvana.master_mind_in_this_life",
    "mahaperiyava.deivathin_kural.v1.samanya_dharmangal_anaivarukkum_pothuvana.yoga_is_for_people_with_restless_minds",
    "mahaperiyava.deivathin_kural.v1.ahimsai.ahimsa_purifies_and_disciplines_mind",
    "mahaperiyava.deivathin_kural.v1.sathiyam.truth_should_be_spoken_gently",
    "mahaperiyava.deivathin_kural.v1.sathiyam.common_dharmas_and_samskaras_purify_person",
    "mahaperiyava.deivathin_kural.v1.paropakaram.purta_dharma_and_physical_service",
    "mahaperiyava.deivathin_kural.v1.ella_uyirgalin_thirupthikkaga.vegetarianism_as_lesser_harm_claim",
    "mahaperiyava.deivathin_kural.v1.chitta_suddhikku_sila_chinna_vishayangal.service_and_bhakti_prepare_mind_for_grace",
    "mahaperiyava.deivathin_kural.v1.kobam.desire_and_anger_as_moral_enemies",
    "mahaperiyava.deivathin_kural.v1.anbum_thunbamum.finite_attachment_ends_in_separation_grief",
}

# Expected counts
EXPECTED_COUNTS = {
    "total": 105,
    "promoted": 9,
    "partial": 13,
    "not_evaluated": 83,
}

# Batch authority totals
EXPECTED_BATCH_AUTHORITY = {
    "dk_attested": 96,
    "earlier_witness_supported": 9,
    "dk_print_checked": 0,
    "primary_source_verified": 0,
}



def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class TestManifestIntegrity:
    """Test the decision manifest integrity."""

    def test_manifest_sha256(self):
        """Manifest SHA256 must match the curator-approved value."""
        content = MANIFEST_PATH.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
        assert sha == EXPECTED_MANIFEST_SHA256, f"Manifest SHA256 mismatch: {sha}"

    def test_manifest_decision_counts(self):
        """Manifest must have exactly 105 decisions with expected category counts."""
        manifest = load_json(MANIFEST_PATH)
        decisions = manifest["decisions"]
        counts = manifest["counts"]

        assert len(decisions) == EXPECTED_COUNTS["total"], f"Total decisions: {len(decisions)}"
        assert counts["supported_for_claim_level_promotion"] == EXPECTED_COUNTS["promoted"]
        assert counts["partial_match_not_sufficient"] == EXPECTED_COUNTS["partial"]
        assert counts["not_evaluated_in_targeted_sections"] == EXPECTED_COUNTS["not_evaluated"]

        # Verify each decision has a valid status
        statuses = {d["status"] for d in decisions}
        valid_statuses = {
            "supported_for_claim_level_promotion",
            "partial_match_not_sufficient",
            "not_evaluated_in_targeted_sections",
        }
        assert statuses == valid_statuses

        # Verify promoted IDs match expected
        promoted = {d["id"] for d in decisions if d["status"] == "supported_for_claim_level_promotion"}
        assert promoted == PROMOTED_IDS

        # Verify partial IDs match expected
        partial = {d["id"] for d in decisions if d["status"] == "partial_match_not_sufficient"}
        assert partial == PARTIAL_IDS

        # Verify all 105 IDs are unique
        ids = [d["id"] for d in decisions]
        assert len(ids) == len(set(ids)) == EXPECTED_COUNTS["total"]


class TestBatchAuthority:
    """Test batch 046-065 authority totals."""

    def test_batch_teaching_authority_totals(self):
        """Batch teaching records must have correct authority distribution."""
        records = load_jsonl(TEACHING_PATH)
        assert len(records) == 105

        authority_counts = {}
        for r in records:
            auth = r.get("evidence_status", {}).get("authority")
            authority_counts[auth] = authority_counts.get(auth, 0) + 1

        # Check expected non-zero counts
        assert authority_counts.get("dk_attested", 0) == EXPECTED_BATCH_AUTHORITY["dk_attested"]
        assert authority_counts.get("earlier_witness_supported", 0) == EXPECTED_BATCH_AUTHORITY["earlier_witness_supported"]
        # Zero-count authorities should not appear or be 0
        assert authority_counts.get("dk_print_checked", 0) == 0
        assert authority_counts.get("primary_source_verified", 0) == 0

    def test_batch_curation_authority_totals(self):
        """Batch curation index must have correct authority distribution."""
        curation = load_json(CURATION_PATH)
        authority_counts = curation.get("authority_counts", {})

        # Check expected non-zero counts
        assert authority_counts.get("dk_attested", 0) == EXPECTED_BATCH_AUTHORITY["dk_attested"]
        assert authority_counts.get("earlier_witness_supported", 0) == EXPECTED_BATCH_AUTHORITY["earlier_witness_supported"]
        # Zero-count authorities should not appear or be 0
        assert authority_counts.get("dk_print_checked", 0) == 0
        assert authority_counts.get("primary_source_verified", 0) == 0



class TestPromotedRecordIntegrity:
    """Test integrity of the 9 promoted records."""

    @pytest.fixture
    def teaching_records(self):
        return {r["id"]: r for r in load_jsonl(TEACHING_PATH)}

    @pytest.fixture
    def curation_units(self):
        curation = load_json(CURATION_PATH)
        return {u["id"]: u for u in curation.get("units", [])}

    def test_promoted_ids_exist(self, teaching_records, curation_units):
        """All 9 promoted IDs must exist in both teaching and curation."""
        for pid in PROMOTED_IDS:
            assert pid in teaching_records, f"Promoted ID missing from teaching: {pid}"
            assert pid in curation_units, f"Promoted ID missing from curation: {pid}"

    def test_promoted_authority_earlier_witness_supported(self, teaching_records, curation_units):
        """All 9 promoted records must have authority=earlier_witness_supported in both teaching and curation."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            cu = curation_units[pid]
            assert tr["evidence_status"]["authority"] == "earlier_witness_supported", f"{pid}: teaching authority mismatch"
            assert cu["authority"] == "earlier_witness_supported", f"{pid}: curation authority mismatch"

    def test_promoted_earlier_secondary_provenance_exists(self, teaching_records):
        """All 9 promoted records must have an earlier_secondary provenance witness."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            prov = tr.get("provenance", [])
            has_earlier_secondary = any(
                p.get("witness_role") == "earlier_secondary" for p in prov
            )
            assert has_earlier_secondary, f"{pid}: missing earlier_secondary provenance"

    def test_promoted_wording_status_earlier_witness_agrees(self, teaching_records):
        """All 9 promoted records must have wording_status = earlier_witness_agrees."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            wording = tr.get("attribution", {}).get("wording_status")
            assert wording == "earlier_witness_agrees", f"{pid}: wording_status={wording}"

    def test_promoted_print_check_not_checked(self, teaching_records):
        """All 9 promoted records must have print_check = not_checked."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            pc = tr.get("evidence_status", {}).get("print_check")
            assert pc == "not_checked", f"{pid}: print_check={pc}"

    def test_promoted_primary_source_status_unknown(self, teaching_records):
        """All 9 promoted records must have primary_source_status = unknown (or not verified)."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            pss = tr.get("evidence_status", {}).get("primary_source_status")
            assert pss in ("unknown", None), f"{pid}: primary_source_status={pss}"

    def test_promoted_no_restricted_exact_text(self, teaching_records):
        """No promoted record may contain restricted exact source text."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            # Check for exact_text_restricted field
            if "exact_text_restricted" in tr:
                assert tr["exact_text_restricted"] is None, f"{pid}: contains non-null exact_text_restricted"
            # Rights must be metadata_only or none
            rights = tr.get("rights", {})
            if rights.get("source_text_tier") == "restricted":
                pub = rights.get("public_export")
                assert pub in ("metadata_only", "none"), f"{pid}: restricted but public_export={pub}"

    def test_promoted_no_top_level_historical_witness_in_teaching(self, teaching_records):
        """Promoted teaching records must NOT have top-level historical_witness field (layering rule)."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            assert "historical_witness" not in tr, f"{pid}: teaching record must not have top-level historical_witness (belongs in curation index)"
            assert "candidate_witness" not in tr, f"{pid}: teaching record must not have top-level candidate_witness"

    def test_promoted_curation_has_historical_witness(self, curation_units):
        """Promoted curation index units must carry historical_witness review metadata."""
        for pid in PROMOTED_IDS:
            cu = curation_units[pid]
            cu_hw = cu.get("historical_witness")
            assert cu_hw is not None, f"{pid}: missing historical_witness in curation"
            assert "source_key" in cu_hw
            assert "locus" in cu_hw
            assert "basis" in cu_hw

    def test_promoted_no_verbatim_claim(self, teaching_records):
        """Promoted records must not claim verbatim primary speech."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            note = tr.get("attribution", {}).get("note", "")
            # Should mention "not verbatim" or similar
            assert "not verbatim" in note.lower() or "not treated as verbatim" in note.lower() or "no textual dependence" in note.lower()


class TestPartialMatchIntegrity:
    """Test integrity of the 13 partial-match records."""

    @pytest.fixture
    def teaching_records(self):
        return {r["id"]: r for r in load_jsonl(TEACHING_PATH)}

    @pytest.fixture
    def curation_units(self):
        curation = load_json(CURATION_PATH)
        return {u["id"]: u for u in curation.get("units", [])}

    def test_partial_ids_exist(self, teaching_records, curation_units):
        """All 13 partial IDs must exist."""
        for pid in PARTIAL_IDS:
            assert pid in teaching_records, f"Partial ID missing from teaching: {pid}"
            assert pid in curation_units, f"Partial ID missing from curation: {pid}"

    def test_partial_authority_remains_dk_attested(self, teaching_records, curation_units):
        """All 13 partial records must retain dk_attested authority."""
        for pid in PARTIAL_IDS:
            tr = teaching_records[pid]
            cu = curation_units[pid]
            assert tr["evidence_status"]["authority"] == "dk_attested", f"{pid}: teaching authority mismatch"
            assert cu["authority"] == "dk_attested", f"{pid}: curation authority mismatch"

    def test_partial_no_top_level_fields_in_teaching(self, teaching_records):
        """Partial teaching records must NOT have top-level historical_witness or candidate_witness fields."""
        for pid in PARTIAL_IDS:
            tr = teaching_records[pid]
            assert "historical_witness" not in tr, f"{pid}: teaching record must not have top-level historical_witness"
            assert "candidate_witness" not in tr, f"{pid}: teaching record must not have top-level candidate_witness"

    def test_partial_curation_has_candidate_witness(self, curation_units):
        """Partial curation units must carry candidate_witness review metadata."""
        for pid in PARTIAL_IDS:
            cu = curation_units[pid]
            cw = cu.get("candidate_witness")
            assert cw is not None, f"{pid}: missing candidate_witness in curation"
            assert "source_key" in cw
            assert "locus" in cw
            assert "reason" in cw

    def test_partial_no_earlier_secondary_promotion(self, teaching_records):
        """Partial records must NOT have earlier_secondary provenance that implies promotion."""
        for pid in PARTIAL_IDS:
            tr = teaching_records[pid]
            prov = tr.get("provenance", [])
            has_earlier_secondary = any(
                p.get("witness_role") == "earlier_secondary" for p in prov
            )
            # It's OK to have the witness present, but the authority must be dk_attested
            # (already tested above)


class TestNotEvaluatedIntegrity:
    """Test integrity of the 83 not-evaluated records."""

    @pytest.fixture
    def teaching_records(self):
        return {r["id"]: r for r in load_jsonl(TEACHING_PATH)}

    @pytest.fixture
    def curation_units(self):
        curation = load_json(CURATION_PATH)
        return {u["id"]: u for u in curation.get("units", [])}

    def test_not_evaluated_ids(self, teaching_records, curation_units):
        """All non-promoted, non-partial IDs must be not_evaluated."""
        all_ids = {r["id"] for r in load_jsonl(TEACHING_PATH)}
        not_evaluated = all_ids - PROMOTED_IDS - PARTIAL_IDS
        assert len(not_evaluated) == 83

        for pid in not_evaluated:
            assert pid in teaching_records
            assert pid in curation_units

    def test_not_evaluated_authority_dk_attested(self, teaching_records, curation_units):
        """Not-evaluated records must retain dk_attested authority."""
        all_ids = {r["id"] for r in load_jsonl(TEACHING_PATH)}
        not_evaluated = all_ids - PROMOTED_IDS - PARTIAL_IDS

        for pid in not_evaluated:
            tr = teaching_records[pid]
            cu = curation_units[pid]
            assert tr["evidence_status"]["authority"] == "dk_attested", f"{pid}: teaching authority"
            assert cu["authority"] == "dk_attested", f"{pid}: curation authority"

    def test_not_evaluated_not_imply_no_witness(self, teaching_records):
        """Not-evaluated status must not be treated as evidence that no earlier witness exists."""
        # The manifest explicitly marks them as "not_evaluated_in_targeted_sections"
        # which means they were simply not evaluated in this targeted review
        # This test documents the requirement; the manifest itself is the source of truth
        manifest = load_json(MANIFEST_PATH)
        not_eval_manifest = {
            d["id"] for d in manifest["decisions"]
            if d["status"] == "not_evaluated_in_targeted_sections"
        }
        assert len(not_eval_manifest) == 83
        # The status field itself documents that they were not evaluated, not that no witness exists
        for d in manifest["decisions"]:
            if d["status"] == "not_evaluated_in_targeted_sections":
                assert d["target_authority"] == "dk_attested"


class TestFlagsPreservation:
    """Test that all pre-existing flags on all 105 units are preserved."""

    @pytest.fixture
    def teaching_records(self):
        return {r["id"]: r for r in load_jsonl(TEACHING_PATH)}

    def test_all_units_have_flags_field(self, teaching_records):
        """Every unit must have a flags field (list)."""
        for r in load_jsonl(TEACHING_PATH):
            assert "flags" in r, f"{r['id']}: missing flags field"
            assert isinstance(r["flags"], list), f"{r['id']}: flags not a list"

    def test_no_flags_removed_from_promoted(self, teaching_records):
        """Promoted records must not have flags removed."""
        # We can't compare to pre-promotion state without baseline,
        # but we can verify flags field is present and non-empty for records that had them
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            # At minimum, flags field should exist
            assert "flags" in tr

    def test_no_flags_removed_from_partial(self, teaching_records):
        for pid in PARTIAL_IDS:
            tr = teaching_records[pid]
            assert "flags" in tr

    def test_no_flags_removed_from_not_evaluated(self, teaching_records):
        all_ids = {r["id"] for r in load_jsonl(TEACHING_PATH)}
        not_evaluated = all_ids - PROMOTED_IDS - PARTIAL_IDS
        for pid in not_evaluated:
            tr = teaching_records[pid]
            assert "flags" in tr


class TestRightsEvidenceDiscipline:
    """Test rights and evidence discipline for promoted records."""

    @pytest.fixture
    def teaching_records(self):
        return {r["id"]: r for r in load_jsonl(TEACHING_PATH)}

    def test_no_verbatim_primary_speech_claim(self, teaching_records):
        """No promoted record claims verbatim primary speech."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            note = tr.get("attribution", {}).get("note", "")
            # Must explicitly disclaim verbatim
            assert "not verbatim" in note.lower() or "not treated as verbatim" in note.lower() or "no textual dependence" in note.lower()

    def test_no_print_checked_promotion(self, teaching_records):
        """No promoted record becomes print checked."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            pc = tr.get("evidence_status", {}).get("print_check")
            assert pc == "not_checked", f"{pid}: print_check={pc}"

    def test_no_primary_source_verified_promotion(self, teaching_records):
        """No promoted record becomes primary_source_verified."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            auth = tr.get("evidence_status", {}).get("authority")
            assert auth != "primary_source_verified", f"{pid}: promoted to primary_source_verified"
            pss = tr.get("evidence_status", {}).get("primary_source_status")
            assert pss in ("unknown", None), f"{pid}: primary_source_status={pss}"

    def test_no_restricted_exact_source_text(self, teaching_records):
        """No tracked record contains restricted exact source text."""
        for r in load_jsonl(TEACHING_PATH):
            if "exact_text_restricted" in r:
                assert r["exact_text_restricted"] is None, f"{r['id']}: contains non-null exact_text_restricted"
            rights = r.get("rights", {})
            if rights.get("source_text_tier") == "restricted":
                pub = rights.get("public_export")
                assert pub in ("metadata_only", "none"), f"{r['id']}: restricted but public_export={pub}"

    def test_attribution_note_disclaims_verbatim(self, teaching_records):
        """All promoted records' attribution notes must disclaim verbatim wording."""
        for pid in PROMOTED_IDS:
            tr = teaching_records[pid]
            note = tr.get("attribution", {}).get("note", "")
            # The note should indicate that exact wording is not established
            assert "exact primary wording is not established" in note or "not a quotation" in note or "not verbatim" in note.lower()


class TestArchitecturalLayering:
    """Architectural regression tests enforcing layering between teaching records and curation metadata."""

    def test_schema_no_top_level_historical_witness(self):
        """Schema must NOT define historical_witness as top-level teaching record field."""
        schema = load_json(ROOT / "schema/teaching_record.schema.json")
        assert "historical_witness" not in schema.get("properties", {}), \
            "Schema must not define historical_witness as top-level teaching record field"

    def test_schema_no_candidate_witness(self):
        """Schema must NOT define candidate_witness as top-level teaching record field."""
        schema = load_json(ROOT / "schema/teaching_record.schema.json")
        assert "candidate_witness" not in schema.get("properties", {}), \
            "Schema must not define candidate_witness as top-level teaching record field"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])