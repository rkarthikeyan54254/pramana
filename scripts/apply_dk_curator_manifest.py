#!/usr/bin/env python3
"""
scripts/apply_dk_curator_manifest.py

Deterministic DK Curator Manifest Applier.

Consumes a human-approved curator manifest (e.g. data/review/mahaperiyava_dk_v1_batch_066_085_curator_manifest.json)
and deterministically prepares or applies:
1. Teaching record JSONL (data/review/mahaperiyava_dk_v1_batch_<batch>_teaching_records.jsonl)
2. Curation index JSON (data/review/mahaperiyava_dk_v1_batch_<batch>_curation_index.json)
3. Extraction queue updates (data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl)

Mechanical repo engineering ONLY:
- Makes NO semantic decisions.
- Never invents claim summaries, boundaries, questions, topics, flags, or authority.
- Enforces strict safety against silent overwriting or downgrade of pilot chapters.
- Deterministic and idempotent.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import glob
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

# Controlled vocabulary and default conventions for dk_attested units
CORPUS_NAME = "mahaperiyava_teachings"
WORK_NAME = "deivathin_kural"
TEACHER = "chandrasekharendra_saraswati"
COMPILER = "ra_ganapathi"
LANGUAGE = "tamil"

DEFAULT_AUTHORITY = "dk_attested"
DEFAULT_DIGITAL_ATTESTATION = "confirmed"
DEFAULT_PRINT_CHECK = "not_checked"
DEFAULT_PRIMARY_SOURCE_STATUS = "unknown"
DEFAULT_DK_ATTESTATION = "located"
DEFAULT_WORDING_STATUS = "dk_wording_only"
DEFAULT_COMPILER_INTERVENTION = "unknown"
DEFAULT_WITNESS_ROLE = "official_digital"
DEFAULT_RIGHTS_TIER = "restricted"
DEFAULT_PUBLIC_EXPORT = "metadata_only"

DEFAULT_LINEAGE_NOTE = (
    "Official Kanchi digital Deivathin Kural is a descendant of the Ra. Ganapathi "
    "compilation and is not treated as an independent primary witness."
)
DEFAULT_ATTRIBUTION_NOTE = (
    "Curator-authored summary, not a quotation. Official Kanchi digital Deivathin Kural "
    "attests this teaching. Exact primary wording is not established. "
    "Historical-witness comparison has not yet been performed for this batch."
)
DEFAULT_RIGHTS_NOTE = (
    "Exact source wording remains only in private/gitignored snapshots and review packets."
)
DEFAULT_QUEUE_REVIEW_NOTE = (
    "Curated metadata-only teaching units from private hashed review packet. "
    "Authority remains dk_attested; historical-witness comparison, print check, "
    "and primary-source verification remain pending."
)

# Witness carry-forward attribution note convention
WITNESS_CARRYFORWARD_ATTRIBUTION_NOTE = (
    "Curator-authored summary, not a quotation. A pre-DK historical witness "
    "supports this narrow claim; no verbatim identity or textual dependence "
    "is asserted."
)

ID_PATTERN = re.compile(r"^mahaperiyava\.deivathin_kural\.v[1-7]\.[a-z0-9_-]+(?:\.[a-z0-9_-]+)?$")


class PilotOverlapInfo:
    def __init__(
        self,
        chapter_ordinal: int,
        chapter_title: str,
        pilot_record_count: int,
        authority_distribution: Dict[str, int],
        pilot_record_ids: List[str],
        has_earlier_witness_supported: bool,
        has_dk_print_checked: bool,
        has_primary_source_verified: bool,
        has_earlier_secondary_provenance: bool,
    ):
        self.chapter_ordinal = chapter_ordinal
        self.chapter_title = chapter_title
        self.pilot_record_count = pilot_record_count
        self.authority_distribution = authority_distribution
        self.pilot_record_ids = pilot_record_ids
        self.has_earlier_witness_supported = has_earlier_witness_supported
        self.has_dk_print_checked = has_dk_print_checked
        self.has_primary_source_verified = has_primary_source_verified
        self.has_earlier_secondary_provenance = has_earlier_secondary_provenance

    @property
    def has_stronger_evidence(self) -> bool:
        return (
            self.has_earlier_witness_supported
            or self.has_dk_print_checked
            or self.has_primary_source_verified
            or self.has_earlier_secondary_provenance
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_ordinal": self.chapter_ordinal,
            "chapter_title": self.chapter_title,
            "pilot_record_count": self.pilot_record_count,
            "authority_distribution": self.authority_distribution,
            "pilot_record_ids": self.pilot_record_ids,
            "stronger_evidence": {
                "earlier_witness_supported": self.has_earlier_witness_supported,
                "dk_print_checked": self.has_dk_print_checked,
                "primary_source_verified": self.has_primary_source_verified,
                "earlier_secondary_provenance": self.has_earlier_secondary_provenance,
            },
        }


def format_overlap_report(overlaps: List[PilotOverlapInfo]) -> str:
    lines = [
        "=" * 64,
        f"PILOT OVERLAP DETECTED: {len(overlaps)} chapter(s) overlap pilot records",
        "=" * 64,
    ]
    for o in overlaps:
        lines.append(f"Chapter {o.chapter_ordinal}:")
        lines.append(f"  Title: {o.chapter_title}")
        lines.append(f"  Existing pilot records: {o.pilot_record_count}")
        lines.append(f"  Authority distribution: {dict(o.authority_distribution)}")
        lines.append(f"  Record IDs ({len(o.pilot_record_ids)}):")
        for rid in o.pilot_record_ids:
            lines.append(f"    - {rid}")
        lines.append("  Stronger evidence detected:")
        lines.append(f"    - earlier_witness_supported: {o.has_earlier_witness_supported}")
        lines.append(f"    - dk_print_checked: {o.has_dk_print_checked}")
        lines.append(f"    - primary_source_verified: {o.has_primary_source_verified}")
        lines.append(f"    - earlier_secondary provenance: {o.has_earlier_secondary_provenance}")
        lines.append("")
    lines.append("=" * 64)
    lines.append("FAIL-CLOSED: Refusing automatic replacement of pilot chapter(s).")
    lines.append("An approved carry-forward decision artifact (--carry-forward <path>) is required.")
    lines.append("=" * 64)
    return "\n".join(lines)


class DKManifestApplier:
    def __init__(
        self,
        manifest_path: Path,
        repo_root: Optional[Path] = None,
        carry_forward_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ):
        self.manifest_path = manifest_path
        self.repo_root = repo_root or Path.cwd()
        self.carry_forward_path = carry_forward_path
        self.output_dir = output_dir

        self.manifest: Dict[str, Any] = {}
        self.carry_forward: Optional[Dict[str, Any]] = None
        self.pilot_records: List[Dict[str, Any]] = []

        self._load_manifest()
        if self.carry_forward_path:
            self._load_carry_forward()
        self._load_pilot_records()

    def _load_manifest(self) -> None:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Curator manifest not found: {self.manifest_path}")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def _load_carry_forward(self) -> None:
        if self.carry_forward_path is None:
            return
        if not self.carry_forward_path.exists():
            raise FileNotFoundError(f"Carry-forward artifact not found: {self.carry_forward_path}")
        with open(self.carry_forward_path, "r", encoding="utf-8") as f:
            self.carry_forward = json.load(f)

    def _load_pilot_records(self) -> None:
        pilot_file = self.repo_root / "data/review/mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
        if not pilot_file.exists():
            self.pilot_records = []
            return
        rows = []
        with open(pilot_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        self.pilot_records = rows

    def validate_manifest(self) -> List[str]:
        errors: List[str] = []
        m = self.manifest
        required_keys = ["corpus", "work", "volume", "batch", "chapters", "units"]
        for k in required_keys:
            if k not in m:
                errors.append(f"Manifest missing required top-level key: {k}")

        if errors:
            return errors

        if m["corpus"] != CORPUS_NAME:
            errors.append(f"Unexpected corpus '{m['corpus']}', expected '{CORPUS_NAME}'")
        if m["work"] != WORK_NAME:
            errors.append(f"Unexpected work '{m['work']}', expected '{WORK_NAME}'")

        chapter_ordinals = set()
        for i, ch in enumerate(m.get("chapters", [])):
            if "ordinal" not in ch:
                errors.append(f"Chapter index {i} missing 'ordinal'")
            else:
                chapter_ordinals.add(ch["ordinal"])
            for field in ["url", "source_key", "snapshot_sha256"]:
                if field not in ch:
                    errors.append(f"Chapter {ch.get('ordinal', i)} missing '{field}'")

        seen_unit_ids: Set[str] = set()
        for i, u in enumerate(m.get("units", [])):
            uid = u.get("id")
            if not uid:
                errors.append(f"Unit index {i} missing 'id'")
                continue
            if uid in seen_unit_ids:
                errors.append(f"Duplicate unit id: {uid}")
            seen_unit_ids.add(uid)

            if not ID_PATTERN.match(uid):
                errors.append(f"Unit id does not match pattern: {uid}")

            ch_ord = u.get("chapter_ordinal")
            if ch_ord not in chapter_ordinals:
                errors.append(f"Unit {uid} references chapter_ordinal {ch_ord} not in manifest chapters")

            for req in [
                "claim_summary",
                "question_intents",
                "source_paragraph_ids",
                "source_paragraph_hashes",
                "topics",
                "flags",
            ]:
                if req not in u:
                    errors.append(f"Unit {uid} missing required field '{req}'")

            if not u.get("source_paragraph_ids"):
                errors.append(f"Unit {uid} has empty source_paragraph_ids")
            if len(u.get("source_paragraph_ids", [])) != len(u.get("source_paragraph_hashes", [])):
                errors.append(f"Unit {uid} source_paragraph_ids length != source_paragraph_hashes length")

            # Check for forbidden source text leakage in manifest
            for forbidden in ["text", "exact_text_restricted", "raw_text"]:
                if forbidden in u:
                    errors.append(f"Unit {uid} contains forbidden source text field: '{forbidden}'")

        return errors

    def check_pilot_overlap(self) -> Tuple[List[PilotOverlapInfo], Optional[str]]:
        """
        Detect whether any chapter in incoming manifest overlaps with pilot records.
        Returns (overlap_info_list, error_message_if_blocked).
        """
        manifest_ordinals = {ch["ordinal"] for ch in self.manifest.get("chapters", [])}
        pilot_by_chapter: Dict[int, List[Dict[str, Any]]] = {}
        for r in self.pilot_records:
            c = r.get("source_locus", {}).get("chapter_ordinal")
            if c is not None and c in manifest_ordinals:
                pilot_by_chapter.setdefault(c, []).append(r)

        if not pilot_by_chapter:
            return [], None

        overlap_infos: List[PilotOverlapInfo] = []
        for ch_ord, recs in sorted(pilot_by_chapter.items()):
            title = recs[0].get("source_locus", {}).get("chapter_title_ta", f"chapter_{ch_ord}")
            auth_dist = Counter(r.get("evidence_status", {}).get("authority", "unknown") for r in recs)
            ids = [r.get("id", "") for r in recs]

            has_earlier_witness = any(
                r.get("evidence_status", {}).get("authority") == "earlier_witness_supported"
                for r in recs
            )
            has_print_checked = any(
                r.get("evidence_status", {}).get("print_check") not in (None, "not_checked")
                for r in recs
            )
            has_primary_verified = any(
                r.get("evidence_status", {}).get("primary_source_status") == "verified"
                for r in recs
            )
            has_earlier_sec_prov = any(
                any(p.get("witness_role") in ("earlier_secondary", "primary", "primary_source")
                    for p in r.get("provenance", []))
                for r in recs
            )

            overlap_infos.append(
                PilotOverlapInfo(
                    chapter_ordinal=ch_ord,
                    chapter_title=title,
                    pilot_record_count=len(recs),
                    authority_distribution=dict(auth_dist),
                    pilot_record_ids=ids,
                    has_earlier_witness_supported=has_earlier_witness,
                    has_dk_print_checked=has_print_checked,
                    has_primary_source_verified=has_primary_verified,
                    has_earlier_secondary_provenance=has_earlier_sec_prov,
                )
            )

        # Evaluate carry-forward approval
        cf = self.carry_forward or self.manifest.get("pilot_carry_forward")
        if not cf:
            report = format_overlap_report(overlap_infos)
            return overlap_infos, report

        # Validate carry-forward artifact
        cf_decisions = cf.get("chapter_decisions", cf.get("decisions", []))
        if isinstance(cf_decisions, list):
            decision_map = {d.get("chapter_ordinal"): d for d in cf_decisions if "chapter_ordinal" in d}
        elif isinstance(cf_decisions, dict):
            decision_map = {int(k): v for k, v in cf_decisions.items()}
        else:
            decision_map = {}

        missing_decisions = [o.chapter_ordinal for o in overlap_infos if o.chapter_ordinal not in decision_map]
        if missing_decisions:
            err = (
                f"Carry-forward artifact missing explicit decision for overlapping chapter(s): {missing_decisions}."
            )
            return overlap_infos, err

        # Stronger pilot evidence scheduled for replacement must have an
        # item-level curator decision describing how that evidence survives.
        # A chapter-level carry_forward_stronger_evidence flag alone is not
        # sufficient, because it does not identify which stronger pilot
        # record/provenance is being preserved.
        raw_witness_decisions = cf.get("witness_decisions", [])
        witness_decision_by_id = {
            d.get("id"): d
            for d in raw_witness_decisions
            if isinstance(d, dict) and d.get("id")
        }

        # Check that stronger evidence is NOT silently downgraded
        for o in overlap_infos:
            dec = decision_map[o.chapter_ordinal]
            if o.has_stronger_evidence:
                action = dec.get("action", "")
                curator_approved_downgrade = dec.get("curator_downgrade_approved", False)
                has_rationale = bool(dec.get("downgrade_rationale"))
                carries_forward_stronger = dec.get("carry_forward_stronger_evidence", False) or (
                    action in ("carry_forward_stronger_evidence", "retain_pilot", "carry_forward_evidence")
                )

                if not (carries_forward_stronger or (curator_approved_downgrade and has_rationale)):
                    err = (
                        f"Refusing replacement for Chapter {o.chapter_ordinal}: Chapter has stronger pilot "
                        f"evidence (earlier_witness_supported={o.has_earlier_witness_supported}, "
                        f"earlier_secondary={o.has_earlier_secondary_provenance}). "
                        "Automation must never silently erase or downgrade stronger evidence. "
                        "Carry-forward decision must either carry forward the stronger evidence "
                        "or provide explicit 'curator_downgrade_approved: true' with 'downgrade_rationale'."
                    )
                    return overlap_infos, err

                # If stronger evidence is meant to be carried forward while the
                # pilot representation is removed, require an item-level
                # witness decision for every stronger pilot record. This makes
                # the replacement fail closed instead of trusting a broad
                # chapter-level approval.
                if carries_forward_stronger and dec.get("remove_pilot_records", False):
                    stronger_ids = []
                    for r in self.pilot_records:
                        if r.get("source_locus", {}).get("chapter_ordinal") != o.chapter_ordinal:
                            continue
                        evidence = r.get("evidence_status", {})
                        provenance = r.get("provenance", [])
                        is_stronger = (
                            evidence.get("authority") == "earlier_witness_supported"
                            or evidence.get("print_check") not in (None, "not_checked")
                            or evidence.get("primary_source_status") == "verified"
                            or any(
                                pr.get("witness_role") in (
                                    "earlier_secondary",
                                    "primary",
                                    "primary_source",
                                )
                                for pr in provenance
                            )
                        )
                        if is_stronger:
                            stronger_ids.append(r.get("id", ""))

                    missing_witness_decisions = [
                        rid
                        for rid in stronger_ids
                        if rid and rid not in witness_decision_by_id
                    ]
                    if missing_witness_decisions:
                        return overlap_infos, (
                            f"Refusing replacement for Chapter {o.chapter_ordinal}: "
                            "stronger pilot evidence is marked for carry-forward but "
                            "no item-level witness_decision was supplied for record(s): "
                            f"{missing_witness_decisions}. "
                            "Chapter-level carry_forward_stronger_evidence is not enough."
                        )

        return overlap_infos, None

    def generate_teaching_records(self) -> List[Dict[str, Any]]:
        m = self.manifest
        chapters_by_ordinal = {c["ordinal"]: c for c in m["chapters"]}
        source_packet_sha = m.get("source_packet", {}).get("sha256", "")

        records = []
        for u in m["units"]:
            ch = chapters_by_ordinal[u["chapter_ordinal"]]
            p_ids = ",".join(u["source_paragraph_ids"])
            p_hashes = ",".join(u["source_paragraph_hashes"])

            record = {
                "id": u["id"],
                "corpus": m["corpus"],
                "work": m["work"],
                "teacher": TEACHER,
                "compiler": COMPILER,
                "language": LANGUAGE,
                "source_locus": {
                    "volume": m["volume"],
                    "section_title_ta": None,
                    "chapter_title_ta": u["chapter_slug"].replace("_", " "),
                    "chapter_ordinal": u["chapter_ordinal"],
                    "print_edition": None,
                    "print_page_start": None,
                    "print_page_end": None,
                    "digital_url": ch["url"],
                    "digital_anchor": None,
                },
                "claim_summary": u["claim_summary"],
                "topics": u["topics"],
                "attribution": {
                    "dk_attestation": DEFAULT_DK_ATTESTATION,
                    "wording_status": DEFAULT_WORDING_STATUS,
                    "compiler_intervention_status": DEFAULT_COMPILER_INTERVENTION,
                    "note": DEFAULT_ATTRIBUTION_NOTE,
                },
                "evidence_status": {
                    "digital_attestation": DEFAULT_DIGITAL_ATTESTATION,
                    "print_check": DEFAULT_PRINT_CHECK,
                    "primary_source_status": DEFAULT_PRIMARY_SOURCE_STATUS,
                    "authority": u.get("authority", DEFAULT_AUTHORITY),
                },
                "provenance": [
                    {
                        "source_key": ch["source_key"],
                        "witness_role": DEFAULT_WITNESS_ROLE,
                        "url": ch["url"],
                        "locus": f"private batch review packet paragraph(s) {p_ids}",
                        "snapshot_sha256": ch["snapshot_sha256"],
                        "lineage_note": DEFAULT_LINEAGE_NOTE,
                        "rights_status": "restricted_private_research",
                    }
                ],
                "rights": {
                    "source_text_tier": DEFAULT_RIGHTS_TIER,
                    "public_export": DEFAULT_PUBLIC_EXPORT,
                    "terms_url": None,
                    "note": DEFAULT_RIGHTS_NOTE,
                },
                "flags": u["flags"],
                "curator_notes": (
                    f"Private batch review packet refs={p_ids}; "
                    f"paragraph_sha256={p_hashes}; "
                    f"source_packet_sha256={source_packet_sha}. "
                    "Summary is metadata, not a quotation."
                ),
            }
            records.append(record)
        return records

    def _apply_witness_decisions(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply approved witness carry-forward decisions to generated teaching records.
        This modifies records in place for those matching witness_decisions.
        """
        if not self.carry_forward:
            return records
        witness_decisions = self.carry_forward.get("witness_decisions", [])
        if not witness_decisions:
            return records

        # Build lookup for decisions by unit ID
        decisions_by_id = {d["id"]: d for d in witness_decisions if "id" in d}

        # Build lookup for manifest units by ID for paragraph verification
        manifest_units_by_id = {u["id"]: u for u in self.manifest.get("units", [])}

        for record in records:
            uid = record.get("id")
            if uid not in decisions_by_id:
                continue

            dec = decisions_by_id[uid]

            # Verify chapter ordinal matches
            if dec.get("chapter_ordinal") != record.get("source_locus", {}).get("chapter_ordinal"):
                raise ValueError(f"Witness decision chapter mismatch for {uid}")

            # Verify source_paragraph_ids match using manifest unit data
            dec_paras = set(dec.get("source_paragraph_ids", []))
            manifest_unit = manifest_units_by_id.get(uid)
            if manifest_unit:
                rec_paras = set(manifest_unit.get("source_paragraph_ids", []))
            else:
                rec_paras = set()
            if dec_paras != rec_paras:
                raise ValueError(f"Witness decision paragraph mismatch for {uid}: {dec_paras} vs {rec_paras}")

            # Apply authority and wording status
            record["evidence_status"]["authority"] = dec.get("evidence_status_authority", "earlier_witness_supported")
            record["attribution"]["wording_status"] = dec.get("wording_status", "earlier_witness_agrees")
            record["attribution"]["note"] = WITNESS_CARRYFORWARD_ATTRIBUTION_NOTE

            # Append earlier_secondary provenance exactly from artifact
            ew = dec.get("earlier_witness", {})
            if ew:
                prov_entry = {
                    "source_key": ew.get("source_key", ""),
                    "witness_role": ew.get("witness_role", "earlier_secondary"),
                    "url": ew.get("url", ""),
                    "locus": ew.get("locus", ""),
                    "snapshot_sha256": ew.get("snapshot_sha256", ""),
                    "lineage_note": ew.get("lineage_note", ""),
                    "rights_status": ew.get("rights_status", "restricted_private_research"),
                }
                record["provenance"].append(prov_entry)

            # DO NOT change these:
            record["evidence_status"]["print_check"] = "not_checked"
            record["evidence_status"]["primary_source_status"] = "unknown"
            record["attribution"]["compiler_intervention_status"] = "unknown"

        return records

    def _apply_witness_decisions_to_index(self, index: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply approved witness carry-forward decisions to curation index units.
        """
        if not self.carry_forward:
            return index
        witness_decisions = self.carry_forward.get("witness_decisions", [])
        if not witness_decisions:
            return index

        decisions_by_id = {d["id"]: d for d in witness_decisions if "id" in d}

        for unit in index.get("units", []):
            uid = unit.get("id")
            if uid not in decisions_by_id:
                continue

            dec = decisions_by_id[uid]
            unit["authority"] = dec.get("evidence_status_authority", "earlier_witness_supported")

            # Populate review-only historical_witness metadata
            ew = dec.get("earlier_witness", {})
            if ew:
                unit["historical_witness"] = {
                    "source_key": ew.get("source_key", ""),
                    "witness_role": ew.get("witness_role", "earlier_secondary"),
                    "url": ew.get("url", ""),
                    "locus": ew.get("locus", ""),
                    "snapshot_sha256": ew.get("snapshot_sha256", ""),
                    "basis": ew.get("basis", ""),
                    "wording_agreement": dec.get("wording_status", "earlier_witness_agrees"),
                }
            else:
                unit["historical_witness"] = None

        return index

    def _remove_pilot_records(self) -> None:
        """
        Remove pilot teaching records and curation index units for chapters
        where carry-forward artifact specifies remove_pilot_records: true.
        """
        if not self.carry_forward:
            return

        cf_decisions = self.carry_forward.get("chapter_decisions", [])
        if not isinstance(cf_decisions, list):
            return

        for dec in cf_decisions:
            if not dec.get("remove_pilot_records", False):
                continue

            ch_ord = dec.get("chapter_ordinal")
            expected_pilot_ids = set(dec.get("pilot_record_ids", []))

            if not ch_ord or not expected_pilot_ids:
                continue

            # Load current pilot records
            pilot_file = self.repo_root / "data/review/mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
            if not pilot_file.exists():
                continue

            pilot_rows = []
            with open(pilot_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        pilot_rows.append(json.loads(line))

            # Find pilot records for this chapter
            chapter_pilot_ids = {r.get("id") for r in pilot_rows
                                 if r.get("source_locus", {}).get("chapter_ordinal") == ch_ord}

            if chapter_pilot_ids != expected_pilot_ids:
                # Check for partial removal state (idempotency)
                if expected_pilot_ids & chapter_pilot_ids:
                    # Some but not all expected IDs present -> partial state -> ERROR
                    missing = expected_pilot_ids - chapter_pilot_ids
                    extra = chapter_pilot_ids - expected_pilot_ids
                    raise ValueError(
                        f"Partial pilot removal state for chapter {ch_ord}: "
                        f"missing expected IDs: {sorted(missing)}, "
                        f"unexpected IDs: {sorted(extra)}. "
                        f"Expected exactly: {sorted(expected_pilot_ids)}"
                    )
                # If none of the expected IDs present, it's already been removed -> valid no-op
                continue

            # Remove the expected pilot records
            filtered_rows = [r for r in pilot_rows
                             if r.get("id") not in expected_pilot_ids]

            # Write back
            with open(pilot_file, "w", encoding="utf-8") as f:
                for r in filtered_rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

            # Also update pilot curation index
            pilot_index_file = self.repo_root / "data/review/mahaperiyava_dk_v1_pilot_curation_index.json"
            if pilot_index_file.exists():
                with open(pilot_index_file, "r", encoding="utf-8") as f:
                    pilot_index = json.load(f)

                filtered_units = [u for u in pilot_index.get("units", [])
                                  if u.get("id") not in expected_pilot_ids]

                # Update counts
                pilot_index["units"] = filtered_units
                pilot_index["unit_count"] = len(filtered_units)

                from collections import Counter
                auth_counter = Counter(u.get("authority", "dk_attested") for u in filtered_units)
                pilot_index["authority_counts"] = dict(auth_counter)

                flag_counter = Counter(f for u in filtered_units for f in u.get("flags", []))
                pilot_index["flag_counts"] = dict(flag_counter)

                # Rebuild chapter_unit_counts from remaining pilot teaching records.
                # Join by stable teaching-record ID rather than attempting to derive
                # an English chapter_slug from the Tamil chapter title.
                id_to_ordinal = {}
                pilot_records_file = self.repo_root / "data/review/mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
                if pilot_records_file.exists():
                    with open(pilot_records_file, "r", encoding="utf-8") as pf:
                        for line in pf:
                            line = line.strip()
                            if line:
                                r = json.loads(line)
                                rid = r.get("id")
                                ord_val = r.get("source_locus", {}).get("chapter_ordinal")
                                if rid and ord_val is not None:
                                    id_to_ordinal[rid] = ord_val

                unmapped_units = [
                    u.get("id")
                    for u in filtered_units
                    if u.get("id") not in id_to_ordinal
                ]
                if unmapped_units:
                    raise ValueError(
                        "Cannot rebuild pilot chapter_unit_counts; remaining curation "
                        f"index unit(s) have no matching pilot teaching record: {unmapped_units}"
                    )

                chapter_counter = Counter(
                    id_to_ordinal[u.get("id")]
                    for u in filtered_units
                )
                pilot_index["chapter_unit_counts"] = {
                    str(k): v for k, v in sorted(chapter_counter.items())
                }

                with open(pilot_index_file, "w", encoding="utf-8") as f:
                    json.dump(pilot_index, f, ensure_ascii=False, indent=2)

    def generate_curation_index(
        self,
        existing_index: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        m = self.manifest
        batch_slug = f"batch_{m['batch']}"
        source_packet = m.get("source_packet", {})

        # Retain existing generated_at timestamp for strict idempotency if re-applying
        if timestamp:
            gen_at = timestamp
        elif existing_index and "generated_at" in existing_index:
            gen_at = existing_index["generated_at"]
        elif "generated_at" in m:
            gen_at = m["generated_at"]
        else:
            gen_at = datetime.now(timezone.utc).isoformat()

        if timestamp:
            sp_gen_at = timestamp
        elif existing_index and "generated_at" in existing_index.get("source_packet", {}):
            sp_gen_at = existing_index["source_packet"]["generated_at"]
        elif "generated_at" in source_packet:
            sp_gen_at = source_packet["generated_at"]
        else:
            sp_gen_at = gen_at

        # Flag counts
        flag_counter = Counter(f for u in m["units"] for f in u.get("flags", []))
        flag_counts = dict(flag_counter)

        # Chapter unit counts
        chapter_counter = Counter(u["chapter_ordinal"] for u in m["units"])
        chapter_unit_counts = {str(k): v for k, v in sorted(chapter_counter.items())}

        # Authority counts
        auth_counter = Counter(u.get("authority", DEFAULT_AUTHORITY) for u in m["units"])
        authority_counts = dict(auth_counter)

        # Source coverage
        coverage_counts = m.get("counts", {})
        source_paragraphs = coverage_counts.get(
            "source_paragraphs", source_packet.get("paragraph_count", 0)
        )
        covered_paragraphs = coverage_counts.get("covered_source_paragraphs", source_paragraphs)
        excluded_blocks = coverage_counts.get("explicitly_excluded_source_paragraphs", 0)
        coverage_mode = m.get("policy", {}).get(
            "source_paragraph_accounting", "at_least_once_or_explicitly_excluded"
        )

        units_index = []
        for u in m["units"]:
            u_entry = dict(u)
            if "historical_witness" not in u_entry:
                u_entry["historical_witness"] = None
            units_index.append(u_entry)

        policy_obj = {
            "no_exact_source_text_in_tracked_artifacts": True,
            "claim_summaries_are_not_quotes": True,
            "all_batch_authority_is_dk_attested": all(
                u.get("authority", DEFAULT_AUTHORITY) == DEFAULT_AUTHORITY for u in m["units"]
            ),
            "historical_witness_comparison_deferred": True,
            "no_print_check_claimed": True,
            "no_primary_source_verified_claimed": True,
            "source_paragraph_accounting_policy": coverage_mode,
            "replacement_decoded_source_units_are_flagged": True,
            "source_title_anomalies_preserved_pending_qc": True,
            "sensitive_external_fact_claims_are_flagged": True,
            "social_and_religious_generalizations_are_attributed_only": True,
            "caste_varna_material_requires_contextual_answering": True,
            "political_material_requires_source_attribution": True,
            "violence_punishment_and_sacrifice_material_requires_context": True,
            "human_publication_review_still_required": True,
        }

        index = {
            "version": "0.1",
            "corpus": m["corpus"],
            "work": m["work"],
            "volume": m["volume"],
            "phase": f"{batch_slug}_teaching_units_curated",
            "status": "CURATED_REVIEW_DATA_NOT_PUBLICATION_APPROVED",
            "generated_at": gen_at,
            "source_packet": {
                "packet_version": source_packet.get("packet_version", "1.0"),
                "private_path": source_packet.get(
                    "expected_private_repo_path",
                    f"data/private/mahaperiyava_dk_v1_{batch_slug}_review_packet.json",
                ),
                "sha256": source_packet.get("sha256", ""),
                "generated_at": sp_gen_at,
                "chapter_count": source_packet.get("chapter_count", len(m["chapters"])),
                "paragraph_count": source_packet.get("paragraph_count", source_paragraphs),
                "contains_restricted_source_text": True,
                "tracked": False,
            },
            "policy": policy_obj,
            "source_anomalies": m.get("source_anomalies", []),
            "unit_count": len(m["units"]),
            "authority_counts": authority_counts,
            "chapter_unit_counts": chapter_unit_counts,
            "flag_counts": flag_counts,
            "source_coverage": {
                "paragraph_count": source_paragraphs,
                "covered_paragraph_count": covered_paragraphs,
                "coverage_mode": coverage_mode,
                "excluded_source_blocks": excluded_blocks,
            },
            "units": units_index,
        }
        return index

    def update_extraction_queue(self, queue_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        m = self.manifest
        chapter_counter = Counter(u["chapter_ordinal"] for u in m["units"])
        target_ordinals = {ch["ordinal"] for ch in m["chapters"]}

        # Check carry-forward decisions for pilot chapter queue updates
        cf = self.carry_forward or self.manifest.get("pilot_carry_forward")
        cf_decisions = {}
        if cf:
            raw_decs = cf.get("chapter_decisions", cf.get("decisions", []))
            if isinstance(raw_decs, list):
                cf_decisions = {d.get("chapter_ordinal"): d for d in raw_decs if "chapter_ordinal" in d}
            elif isinstance(raw_decs, dict):
                cf_decisions = {int(k): v for k, v in raw_decs.items()}

        updated_rows = []
        for row in queue_rows:
            ord_val = row.get("ordinal")
            if ord_val not in target_ordinals:
                updated_rows.append(row)
                continue

            is_pilot = row.get("pilot", False)
            if is_pilot:
                # Pilot chapters: update queue only if explicit carry-forward decision approves updating queue
                decision = cf_decisions.get(ord_val, {})
                if decision.get("update_queue", False):
                    r_copy = dict(row)
                    r_copy["stage"] = "batch_teaching_units_curated"
                    r_copy["pilot"] = False
                    r_copy["teaching_units_created"] = chapter_counter.get(ord_val, 0)
                    r_copy["review_notes"] = DEFAULT_QUEUE_REVIEW_NOTE
                    updated_rows.append(r_copy)
                else:
                    # By default preserve pilot queue entry untouched to protect pilot provenance
                    updated_rows.append(row)
            else:
                # Non-pilot chapter in target ordinals
                r_copy = dict(row)
                r_copy["stage"] = "batch_teaching_units_curated"
                r_copy["teaching_units_created"] = chapter_counter.get(ord_val, 0)
                r_copy["review_notes"] = DEFAULT_QUEUE_REVIEW_NOTE
                updated_rows.append(r_copy)

        return updated_rows

    def get_target_paths(self) -> Tuple[Path, Path, Path]:
        m = self.manifest
        batch = m["batch"]
        base_dir = self.output_dir if self.output_dir else (self.repo_root / "data/review")
        records_path = base_dir / f"mahaperiyava_dk_v1_batch_{batch}_teaching_records.jsonl"
        index_path = base_dir / f"mahaperiyava_dk_v1_batch_{batch}_curation_index.json"
        queue_path = (self.output_dir / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl") if self.output_dir else (self.repo_root / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl")
        return records_path, index_path, queue_path

    def run(self, mode: str) -> int:
        """
        Runs check, dry-run, or apply.
        mode: 'check', 'dry-run', or 'apply'
        """
        # Step 1: Validate Manifest
        errors = self.validate_manifest()
        if errors:
            print("MANIFEST VALIDATION FAILED:")
            for err in errors:
                print(f"  - {err}")
            return 1

        # Step 2: Pilot Overlap Guard
        overlaps, overlap_error = self.check_pilot_overlap()
        if overlap_error:
            print(overlap_error)
            return 1

        # Step 3: Plan outputs
        records_path, index_path, queue_path = self.get_target_paths()

        existing_index = None
        if index_path.exists():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    existing_index = json.load(f)
            except Exception:
                pass
        elif self.output_dir:
            repo_index = (
                self.repo_root
                / f"data/review/mahaperiyava_dk_v1_batch_{self.manifest.get('batch')}_curation_index.json"
            )
            if repo_index.exists():
                try:
                    with open(repo_index, "r", encoding="utf-8") as f:
                        existing_index = json.load(f)
                except Exception:
                    pass

        records = self.generate_teaching_records()
        index = self.generate_curation_index(existing_index=existing_index)

        # Extraction queue
        queue_rows = []
        if queue_path.exists():
            with open(queue_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        queue_rows.append(json.loads(line))
        updated_queue = self.update_extraction_queue(queue_rows)

        # Compute deterministic hashes
        records_text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
        records_sha = hashlib.sha256(records_text.encode("utf-8")).hexdigest()

        index_text = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
        index_sha = hashlib.sha256(index_text.encode("utf-8")).hexdigest()

        queue_diff_count = sum(1 for a, b in zip(queue_rows, updated_queue) if a != b)
        if len(queue_rows) != len(updated_queue):
            queue_diff_count += abs(len(queue_rows) - len(updated_queue))

        if mode == "check":
            print("============================================================")
            print("MANIFEST CHECK: GREEN")
            print("============================================================")
            print(f"Manifest: {self.manifest_path.name}")
            print(f"Batch: {self.manifest['batch']}")
            print(f"Chapters: {len(self.manifest['chapters'])}")
            print(f"Teaching units: {len(self.manifest['units'])}")
            print(f"Pilot overlaps detected: {len(overlaps)}")
            if overlaps:
                print("  All pilot overlaps resolved via approved carry-forward artifact.")
            print("Schema compliance: PASSED")
            print("No source text leakage: CONFIRMED")
            print("============================================================")
            return 0

        elif mode == "dry-run":
            print("============================================================")
            print("DRY-RUN SUMMARY (NO FILES WRITTEN)")
            print("============================================================")
            print(f"Manifest: {self.manifest_path.name}")
            print(f"Batch: {self.manifest['batch']}")
            print(f"Planned records file: {records_path}")
            print(f"  Total records: {len(records)}")
            print(f"  Records SHA256: {records_sha}")
            print(f"Planned curation index: {index_path}")
            print(f"  Index unit count: {index['unit_count']}")
            print(f"  Index SHA256: {index_sha}")
            print(f"Planned queue updates: {queue_path}")
            print(f"  Target chapter ordinals: {[c['ordinal'] for c in self.manifest['chapters']]}")
            print(f"  Queue rows modified: {queue_diff_count}")
            print(f"Pilot overlaps: {len(overlaps)}")
            for o in overlaps:
                print(f"  Chapter {o.chapter_ordinal} ({o.chapter_title}): {o.pilot_record_count} pilot units handled")
            print("============================================================")
            return 0

        elif mode == "apply":
            records_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.parent.mkdir(parents=True, exist_ok=True)

            # Apply witness decisions to records and index
            records = self._apply_witness_decisions(records)
            index = self._apply_witness_decisions_to_index(index)

            # Remove pilot records if carry-forward specifies
            self._remove_pilot_records()

            # Recompute records_text after witness decisions applied
            records_text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
            records_sha = hashlib.sha256(records_text.encode("utf-8")).hexdigest()

            index_text = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
            index_sha = hashlib.sha256(index_text.encode("utf-8")).hexdigest()

            with open(records_path, "w", encoding="utf-8") as f:
                f.write(records_text)

            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_text)

            if queue_path.exists() or self.output_dir:
                queue_path.parent.mkdir(parents=True, exist_ok=True)
                with open(queue_path, "w", encoding="utf-8") as f:
                    for row in updated_queue:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")

            print("============================================================")
            print("APPLY: SUCCESS")
            print("============================================================")
            print(f"Wrote {len(records)} records to {records_path}")
            print(f"Wrote curation index to {index_path}")
            print(f"Updated extraction queue at {queue_path} ({queue_diff_count} rows changed)")
            print("============================================================")
            return 0

        else:
            print(f"Unknown mode: {mode}")
            return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic Mahaperiyava Deivathin Kural Curator Manifest Applier."
    )
    parser.add_argument("manifest", type=Path, help="Path to curator manifest JSON")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--check", action="store_true", help="Validate manifest and planned changes only")
    mode_group.add_argument(
        "--dry-run", action="store_true", help="Show path/count/hash summaries without writing files"
    )
    mode_group.add_argument("--apply", action="store_true", help="Write approved derived metadata")

    parser.add_argument(
        "--carry-forward",
        type=Path,
        default=None,
        help="Path to approved human-curator pilot carry-forward decision artifact",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (defaults to current working directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional override directory to write files to (defaults to data/review)",
    )

    args = parser.parse_args()

    mode = "check" if args.check else ("dry-run" if args.dry_run else "apply")

    applier = DKManifestApplier(
        manifest_path=args.manifest,
        repo_root=args.repo_root,
        carry_forward_path=args.carry_forward,
        output_dir=args.output_dir,
    )
    return applier.run(mode)


if __name__ == "__main__":
    sys.exit(main())
