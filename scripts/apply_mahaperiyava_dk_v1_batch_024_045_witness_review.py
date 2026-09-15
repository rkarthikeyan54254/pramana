#!/usr/bin/env python3
# Targeted 1957-58 historical-witness review for DK V1 batch 024..045.
# Run from pramana repo root on mahaperiyava-dk-v1-corpus.
# Recommended:
#   python ~/Downloads/apply_mahaperiyava_dk_v1_batch_024_045_witness_review.py --commit --push

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path.cwd()
EXPECTED_BRANCH = "mahaperiyava-dk-v1-corpus"

RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_curation_index.json"
REVIEW = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_historical_witness_review.json"
RESEARCH = ROOT / "data/research/mahaperiyava_dk_v1_batch_024_045_teaching_units.md"
REVIEW_RESEARCH = ROOT / "data/research/mahaperiyava_dk_v1_batch_024_045_historical_witness_review.md"
TEST = ROOT / "tests/test_mahaperiyava_dk_v1_batch_024_045_teaching_records.py"
REVIEW_TEST = ROOT / "tests/test_mahaperiyava_dk_v1_batch_024_045_historical_witness_review.py"
REPO_SCRIPT = ROOT / "scripts/apply_mahaperiyava_dk_v1_batch_024_045_witness_review.py"

PART1 = {
    "source_key": "acharya-upanyasangal-part1-1957-58-scan",
    "title": "Acharya Swamigalin Upanyasangal - Part 1",
    "url": "https://mahaperiyavaa.blog/wp-content/uploads/2023/04/Acharyaswamigal-Upanyasangal-Part-1.pdf",
    "snapshot_sha256": "ace3c1cca4c3077d9e15080365741f541d471274c28d11e07d85f2b372901f7e",
    "rights_status": "restricted_private_research",
}
PART2 = {
    "source_key": "acharya-upanyasangal-part2-1957-58-scan",
    "title": "Acharya Swamigalin Upanyasangal - Part 2",
    "url": "https://mahaperiyavaa.blog/wp-content/uploads/2023/04/Acharyaswamigal-Upanyasangal-Part-2.pdf",
    "snapshot_sha256": "eaf06d8936fb3b160a279b388ec0e2ef408be49c416618bf8bfb9d038f4a31e1",
    "rights_status": "restricted_private_research",
}

LINEAGE_NOTE = (
    "1957-58 witness from the Acharya Swamigalin Upanyasangal publication "
    "family. The collection was produced through shorthand capture, typed "
    "copies, and editorial arrangement. Claim-level agreement therefore "
    "supports earlier attestation of the teaching, but printed wording is "
    "not treated as verbatim primary speech and textual dependence on "
    "Deivathin Kural is not asserted."
)

SUPPORTED: dict[str, dict[str, Any]] = {
    "mahaperiyava.deivathin_kural.v1.nam_mathathin_thani_amsangal.karma_as_moral_cause_and_effect": {
        "witness": PART1,
        "locus": "Part 1, ஈசுவர பக்தி ஏன் செய்யவேண்டும்?, printed pp. 117-120 (PDF pp. 132-135), especially printed p. 118 / PDF p. 133",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness explicitly describes good and bad actions as receiving fitting results and identifies Isvara as giver of karmic fruits. It supports the moral action-result claim, not the DK physics analogy.",
    },
    "mahaperiyava.deivathin_kural.v1.mathangalin_otrumai.hindu_nonexclusive_path_claim": {
        "witness": PART2,
        "locus": "Part 2, எல்லாம் தழுவும் அத்வைதம், printed pp. 28-30 (PDF pp. 39-41), especially printed p. 29",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness names multiple Hindu siddhantas and says Isvara-bhakti and the path prescribed by the respective acharya can lead toward the same Paramatma. It does not establish separate conversion-history claims.",
    },
    "mahaperiyava.deivathin_kural.v1.moolamagiya_vedam.sectarian_diversity_within_hindu_fold": {
        "witness": PART2,
        "locus": "Part 2, எல்லாம் தழுவும் அத்வைதம், printed pp. 28-30 (PDF pp. 39-41)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness explicitly discusses Madhva, Ramanuja, Shaiva and other siddhantas as distinct while sharing devotional orientation and a higher spiritual goal.",
    },
    "mahaperiyava.deivathin_kural.v1.moolamagiya_vedam.many_hindu_deities_as_vedic_branches": {
        "witness": PART2,
        "locus": "Part 2, வேதமும் தர்மமும், printed pp. 148-151 (PDF pp. 159-162)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness describes many Vedic deities, yajnas, upasana paths and teachings while bringing them back to one underlying Vedic purport.",
    },
    "mahaperiyava.deivathin_kural.v1.moolamagiya_vedam.upanishadic_brahman_as_common_divine": {
        "witness": PART2,
        "locus": "Part 2, வேதமும் தர்மமும், printed pp. 149-151 (PDF pp. 160-162)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness says, in an Upanishadic framing, that the many Vedic teachings ultimately indicate one Paramporul / Parama Purusha.",
    },
    "mahaperiyava.deivathin_kural.v1.moolamagiya_vedam.veda_as_common_guide_to_life_and_realization": {
        "witness": PART2,
        "locus": "Part 2, வேதமும் தர்மமும், printed pp. 149-155 (PDF pp. 160-166)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness presents Vedic yajna, upasana, meditation, tapas, karma and discipline as varied means converging on one spiritual purpose and realization.",
    },
}

PARTIAL: dict[str, dict[str, Any]] = {
    "mahaperiyava.deivathin_kural.v1.manithanum_mirugamum.desire_anger_karma_rebirth_chain": {
        "witness": PART2,
        "locus": "Part 2, வேதமும் தர்மமும், printed pp. 152-155 (PDF pp. 163-166)",
        "match_level": "partial_match_not_sufficient",
        "note": "Earlier witness supports desire, mental impurity and suffering and the need to restrain desire, but not the full DK chain through karma to repeated birth.",
    },
    "mahaperiyava.deivathin_kural.v1.mathangalin_otrumai.unity_without_uniformity": {
        "witness": PART2,
        "locus": "Part 2, எல்லாம் தழுவும் அத்வைதம், printed pp. 28-30 (PDF pp. 39-41)",
        "match_level": "partial_match_not_sufficient",
        "note": "Earlier witness supports coexistence of differing Hindu siddhantas, but the DK unit is framed as a broader inter-religious unity principle.",
    },
    "mahaperiyava.deivathin_kural.v1.nam_mathathin_thani_amsangal.one_formless_divine_many_forms_and_murtis": {
        "witness": PART2,
        "locus": "Part 2, வேதமும் தர்மமும், printed pp. 148-151 (PDF pp. 159-162)",
        "match_level": "partial_match_not_sufficient",
        "note": "Earlier witness supports many Vedic deities and practices converging on one ultimate reality, but not the DK unit's specific murti-worship explanation.",
    },
    "mahaperiyava.deivathin_kural.v1.nam_mathathin_thani_amsangal.avatar_as_divine_compassion_and_dharma_restoration": {
        "witness": PART2,
        "locus": "Part 2, வேதமும் தர்மமும், printed pp. 150, 157-161 (PDF pp. 161, 168-172)",
        "match_level": "partial_match_not_sufficient",
        "note": "Earlier witness identifies the Vedic supreme reality with Rama's birth and presents Rama as protector of dharma, but not the full DK compassion/guidance/protection scope.",
    },
    "mahaperiyava.deivathin_kural.v1.nagariga_viyathikku_marundhu.shastra_rooted_in_veda_not_personal_opinion": {
        "witness": PART2,
        "locus": "Part 2, வேதமும் தர்மமும், printed p. 159 (PDF p. 170)",
        "match_level": "partial_match_not_sufficient",
        "note": "Earlier witness explicitly cites Veda as the root of dharma, but not the full DK claims about private rishi opinion and later rewriting for convenience.",
    },
    "mahaperiyava.deivathin_kural.v1.vedathin_moola_vadivam.one_fixed_source_many_interpretations": {
        "witness": PART2,
        "locus": "Part 2, எல்லாம் தழுவும் அத்வைதம் and வேதமும் தர்மமும், printed pp. 28-30 and 149-151 (PDF pp. 39-41 and 160-162)",
        "match_level": "partial_match_not_sufficient",
        "note": "Earlier witness establishes multiple siddhantas and a common ultimate Vedic purport, but not the stronger claim about different acharyas preserving one unchanged textual source.",
    },
}

EXPECTED_SUPPORTED = set(SUPPORTED)
EXPECTED_PARTIAL = set(PARTIAL)
MANAGED = [RECORDS, INDEX, REVIEW, RESEARCH, REVIEW_RESEARCH, TEST, REVIEW_TEST, REPO_SCRIPT]


def die(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def sh(cmd: list[str], *, capture: bool = False, check: bool = True):
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=capture, check=check)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    if not path.exists():
        die(f"Missing expected file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        die(f"Missing expected file: {path.relative_to(ROOT)}")
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def ensure_repo_state() -> None:
    if not (ROOT / ".git").exists():
        die("Run this script from the pramana repo root.")
    branch = sh(["git", "branch", "--show-current"], capture=True).stdout.strip()
    if branch != EXPECTED_BRANCH:
        die(f"Expected {EXPECTED_BRANCH!r}; found {branch!r}")
    dirty = sh(["git", "status", "--porcelain"], capture=True).stdout.strip()
    if dirty:
        die("Working tree must be clean before witness review.\n" + dirty)
    for path in (RECORDS, INDEX, RESEARCH, TEST):
        if not path.exists():
            die("The 024..045 semantic curation baseline is missing: " + str(path.relative_to(ROOT)))
    if REVIEW.exists():
        die("Historical witness review already exists; refusing a second application.")


def validate_baseline(rows: list[dict[str, Any]], index: dict[str, Any]) -> None:
    if len(rows) != 130:
        die(f"Expected 130 records; found {len(rows)}")
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != 130:
        die("Teaching-record IDs are not unique.")
    if EXPECTED_SUPPORTED - set(by_id):
        die("One or more intended promotion IDs are missing.")
    if EXPECTED_PARTIAL - set(by_id):
        die("One or more intended partial-match IDs are missing.")
    counts = Counter(row["evidence_status"]["authority"] for row in rows)
    if counts != Counter({"dk_attested": 130}):
        die(f"Expected untouched semantic baseline; found {counts}")
    for row in rows:
        if row["evidence_status"]["print_check"] != "not_checked":
            die(f"Unexpected print-check state: {row['id']}")
        if row["evidence_status"]["primary_source_status"] != "unknown":
            die(f"Unexpected primary-source state: {row['id']}")
        if row["attribution"]["wording_status"] != "dk_wording_only":
            die(f"Unexpected wording state: {row['id']}")
        if [p["witness_role"] for p in row["provenance"]] != ["official_digital"]:
            die(f"Unexpected baseline provenance: {row['id']}")
    if index.get("unit_count") != 130:
        die("Curation index is not the expected 130-unit batch.")
    if {u["id"] for u in index["units"]} != set(by_id):
        die("Curation-index IDs do not match teaching-record IDs.")


def make_review_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = []
    for row in rows:
        unit_id = row["id"]
        if unit_id in SUPPORTED:
            evidence = SUPPORTED[unit_id]
            status = "supported_for_claim_level_promotion"
            authority_after = "earlier_witness_supported"
        elif unit_id in PARTIAL:
            evidence = PARTIAL[unit_id]
            status = "partial_match_not_sufficient"
            authority_after = "dk_attested"
        else:
            evidence = None
            status = "not_evaluated_in_targeted_sections"
            authority_after = "dk_attested"
        witness = None
        if evidence is not None:
            witness = {
                "source_key": evidence["witness"]["source_key"],
                "locus": evidence["locus"],
                "match_level": evidence["match_level"],
                "note": evidence["note"],
            }
        matrix.append({
            "id": unit_id,
            "chapter_ordinal": row["source_locus"]["chapter_ordinal"],
            "chapter_title_ta": row["source_locus"]["chapter_title_ta"],
            "claim_summary": row.get("claim_summary"),
            "review_scope": "targeted_section_level_manual_comparison",
            "review_status": status,
            "authority_before": "dk_attested",
            "authority_after": authority_after,
            "historical_witness": witness,
            "guardrails": {
                "verbatim_wording_claimed": False,
                "primary_source_verified_claimed": False,
                "textual_dependency_claimed": False,
                "external_factual_truth_claimed": False,
            },
        })
    counts = Counter(r["review_status"] for r in matrix)
    return {
        "version": "0.1",
        "generated_at": now_iso(),
        "corpus": "mahaperiyava_teachings",
        "work": "deivathin_kural",
        "volume": 1,
        "batch": "024_045",
        "review_type": "targeted_historical_witness_matching",
        "review_scope": {
            "exhaustive_across_all_130_units": False,
            "description": "Manual comparison of high-yield karma, Hindu-pluralism, Vedic-unity, dharma and related claims against the acquired 1957-58 Acharya Swamigalin Upanyasangal Part 1 and Part 2 scans. Rows outside targeted sections are not negative evidence.",
        },
        "witnesses_consulted": [PART1, PART2],
        "transmission_guardrail": LINEAGE_NOTE,
        "matrix_count": len(matrix),
        "status_counts": dict(sorted(counts.items())),
        "promotion_count": sum(r["authority_after"] == "earlier_witness_supported" for r in matrix),
        "policy": {
            "claim_level_only": True,
            "no_chapter_wide_promotion": True,
            "no_verbatim_claim": True,
            "no_primary_source_upgrade": True,
            "sensitivity_flags_do_not_change": True,
            "earlier_attestation_is_separate_from_external_factual_truth": True,
            "partial_matches_do_not_promote": True,
        },
        "rows": matrix,
    }


def apply_promotions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    original_flags = {row["id"]: list(row.get("flags", [])) for row in rows}
    for row in rows:
        if row["id"] not in SUPPORTED:
            continue
        evidence = SUPPORTED[row["id"]]
        witness = evidence["witness"]
        row["evidence_status"]["authority"] = "earlier_witness_supported"
        row["attribution"]["wording_status"] = "earlier_witness_agrees"
        row["attribution"]["note"] = (
            "Curator-authored summary, not a quotation. Official Kanchi digital "
            "Deivathin Kural attests this teaching, and a pre-DK 1957-58 Acharya "
            "Swamigalin Upanyasangal witness supports this narrow claim. Printed "
            "witness wording is not treated as verbatim oral wording; no textual "
            "dependence is asserted."
        )
        row["provenance"].append({
            "source_key": witness["source_key"],
            "witness_role": "earlier_secondary",
            "url": witness["url"],
            "locus": evidence["locus"],
            "snapshot_sha256": witness["snapshot_sha256"],
            "lineage_note": LINEAGE_NOTE,
            "rights_status": witness["rights_status"],
        })
        row["curator_notes"] = (
            row.get("curator_notes", "")
            + " Historical witness targeted-pass result: "
            + evidence["match_level"]
            + "; " + evidence["locus"]
            + ". Earlier attestation supports the curated narrow teaching only; "
            + "not verbatim, not primary-source verified, and not independent "
            + "proof of embedded external factual assertions."
        ).strip()
    for row in rows:
        if row.get("flags", []) != original_flags[row["id"]]:
            die(f"Sensitivity flags changed unexpectedly in {row['id']}")
    return rows


def update_index(index: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    by_review = {r["id"]: r for r in review["rows"]}
    for unit in index["units"]:
        result = by_review[unit["id"]]
        unit["authority"] = result["authority_after"]
        unit["historical_witness"] = result["historical_witness"] if result["authority_after"] == "earlier_witness_supported" else None
    index["authority_counts"] = dict(sorted(Counter(u["authority"] for u in index["units"]).items()))
    policy = index.setdefault("policy", {})
    policy["all_batch_authority_is_dk_attested"] = False
    policy["historical_witness_comparison_deferred"] = False
    policy["targeted_historical_witness_pass_completed"] = True
    policy["historical_witness_exhaustive_review_completed"] = False
    policy["historical_witness_support_is_claim_level"] = True
    policy["no_verbatim_wording_claimed"] = True
    policy["no_primary_source_verified_claimed"] = True
    policy["sensitivity_flags_preserved_through_authority_promotion"] = True
    policy["external_factual_truth_separate_from_earlier_attestation"] = True
    index["historical_witness_review"] = {
        "path": str(REVIEW.relative_to(ROOT)),
        "review_type": review["review_type"],
        "matrix_count": review["matrix_count"],
        "promotion_count": review["promotion_count"],
        "partial_match_count": 6,
        "exhaustive": False,
    }
    return index


def update_existing_research_md() -> None:
    text = RESEARCH.read_text(encoding="utf-8")
    if "## Historical witness targeted pass" in text:
        die("Existing research markdown already contains witness-pass marker.")
    addition = """## Historical witness targeted pass

A targeted manual comparison against the acquired 1957-58
*Acharya Swamigalin Upanyasangal* Part 1 and Part 2 scans promoted
**6** narrow claims to `earlier_witness_supported`.

The batch authority distribution is now:

- `dk_attested`: **124**
- `earlier_witness_supported`: **6**
- `dk_print_checked`: **0**
- `primary_source_verified`: **0**

This is not an exhaustive negative search across all 130 units.
Six additional inspected units were partial matches and remain `dk_attested`;
the other 118 units were not evaluated in this targeted pass.

Earlier attestation remains distinct from independent factual truth.
All existing sensitivity flags are preserved.

See:
`data/review/mahaperiyava_dk_v1_batch_024_045_historical_witness_review.json`.
"""
    RESEARCH.write_text(text.rstrip() + "\n\n" + addition.strip() + "\n", encoding="utf-8")


def write_review_research(review: dict[str, Any]) -> None:
    supported = [r for r in review["rows"] if r["review_status"] == "supported_for_claim_level_promotion"]
    partial = [r for r in review["rows"] if r["review_status"] == "partial_match_not_sufficient"]
    lines = [
        "# Mahaperiyava DK V1 Batch 024-045 - Historical Witness Review",
        "", "## Result", "",
        "- Teaching units in batch: **130**",
        "- Promoted to `earlier_witness_supported`: **6**",
        "- Remaining `dk_attested`: **124**",
        "- Partial matches deliberately not promoted: **6**",
        "- Not evaluated in this targeted pass: **118**",
        "- `dk_print_checked`: **0**",
        "- `primary_source_verified`: **0**", "",
        "This was a targeted manual comparison, not an exhaustive search.", "",
        "## Promoted narrow claims", "",
    ]
    for row in supported:
        w = row["historical_witness"]
        lines.append(f"- `{row['id']}` - `{w['match_level']}` - {w['source_key']}; {w['locus']}")
    lines += ["", "## Partial matches deliberately not promoted", ""]
    for row in partial:
        lines.append(f"- `{row['id']}` - {row['historical_witness']['note']}")
    lines += [
        "", "## Evidence distinction", "",
        "`earlier_witness_supported` means earlier documentary attestation of the curated teaching. It does not independently prove every historical, scientific, linguistic, social, medical, hagiographic, caste/varna, or comparative-religion assertion in the source context.",
        "", "The 1957-58 witness wording is not treated as verbatim oral speech.", "",
    ]
    REVIEW_RESEARCH.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_RESEARCH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_tests() -> None:
    TEST.write_text('''from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_curation_index.json"
def _json(path): return json.loads(path.read_text(encoding="utf-8"))
def _jsonl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def test_batch_authority_after_targeted_witness_pass():
    rows = _jsonl(RECORDS); index = _json(INDEX)
    assert len(rows) == 130 and index["unit_count"] == 130
    assert Counter(r["evidence_status"]["authority"] for r in rows) == {"dk_attested": 124, "earlier_witness_supported": 6}
    assert all(r["evidence_status"]["print_check"] == "not_checked" for r in rows)
    assert all(r["evidence_status"]["primary_source_status"] == "unknown" for r in rows)
def test_supported_rows_have_earlier_secondary_provenance():
    rows = _jsonl(RECORDS); supported = [r for r in rows if r["evidence_status"]["authority"] == "earlier_witness_supported"]
    assert len(supported) == 6
    for row in supported:
        assert [p["witness_role"] for p in row["provenance"]] == ["official_digital", "earlier_secondary"]
        assert row["attribution"]["wording_status"] == "earlier_witness_agrees"
        assert "not treated as verbatim" in row["provenance"][1]["lineage_note"]
def test_dk_only_rows_remain_fail_closed():
    rows = _jsonl(RECORDS); dk_only = [r for r in rows if r["evidence_status"]["authority"] == "dk_attested"]
    assert len(dk_only) == 124
    assert all(r["attribution"]["wording_status"] == "dk_wording_only" for r in dk_only)
def test_context_flags_survive_promotion():
    rows = _jsonl(RECORDS)
    karma = next(r for r in rows if r["id"].endswith(".karma_as_moral_cause_and_effect"))
    assert karma["evidence_status"]["authority"] == "earlier_witness_supported"
    assert "scientific_analogy_not_literal" in karma["flags"]
    paths = next(r for r in rows if r["id"].endswith(".hindu_nonexclusive_path_claim"))
    assert paths["evidence_status"]["authority"] == "earlier_witness_supported"
    assert "historical_claim_requires_external_verification" in paths["flags"]
def test_index_records_targeted_not_exhaustive_review():
    policy = _json(INDEX)["policy"]
    assert policy["targeted_historical_witness_pass_completed"] is True
    assert policy["historical_witness_exhaustive_review_completed"] is False
    assert policy["historical_witness_support_is_claim_level"] is True
    assert policy["no_verbatim_wording_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True
''', encoding="utf-8")

    REVIEW_TEST.write_text('''from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_historical_witness_review.json"
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_024_045_teaching_records.jsonl"
def _json(path): return json.loads(path.read_text(encoding="utf-8"))
def _jsonl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def test_review_has_one_row_per_teaching_unit():
    review = _json(REVIEW); rows = _jsonl(RECORDS)
    assert review["matrix_count"] == 130 and len(review["rows"]) == 130
    assert {r["id"] for r in review["rows"]} == {r["id"] for r in rows}
def test_review_is_targeted_not_exhaustive():
    review = _json(REVIEW)
    assert review["review_type"] == "targeted_historical_witness_matching"
    assert review["review_scope"]["exhaustive_across_all_130_units"] is False
    assert review["policy"]["no_chapter_wide_promotion"] is True
    assert review["policy"]["no_verbatim_claim"] is True
def test_exactly_six_supported_six_partial():
    review = _json(REVIEW); counts = Counter(r["review_status"] for r in review["rows"])
    assert counts["supported_for_claim_level_promotion"] == 6
    assert counts["partial_match_not_sufficient"] == 6
    assert counts["not_evaluated_in_targeted_sections"] == 118
    assert review["promotion_count"] == 6
def test_partial_matches_do_not_promote():
    review = _json(REVIEW); partial = [r for r in review["rows"] if r["review_status"] == "partial_match_not_sufficient"]
    assert len(partial) == 6
    assert all(r["authority_after"] == "dk_attested" for r in partial)
''', encoding="utf-8")


def snapshot_managed() -> dict[Path, bytes | None]:
    return {p: (p.read_bytes() if p.exists() else None) for p in MANAGED}


def restore_managed(snapshot: dict[Path, bytes | None]) -> None:
    print("\n=== Validation failed: restoring managed files ===")
    sh(["git", "reset"], check=False)
    for path, old in snapshot.items():
        if old is None:
            if path.exists(): path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(old)
    sh(["git", "status", "--short"], check=False)


def install_repo_script() -> None:
    REPO_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    if src != REPO_SCRIPT.resolve():
        shutil.copyfile(src, REPO_SCRIPT)
        REPO_SCRIPT.chmod(0o755)


def validate_after(rows: list[dict[str, Any]], review: dict[str, Any]) -> None:
    counts = Counter(r["evidence_status"]["authority"] for r in rows)
    if counts != Counter({"dk_attested": 124, "earlier_witness_supported": 6}):
        die(f"Unexpected post-review authority distribution: {counts}")
    promoted = {r["id"] for r in rows if r["evidence_status"]["authority"] == "earlier_witness_supported"}
    if promoted != EXPECTED_SUPPORTED:
        die("Promotion set drifted.\nexpected=" + repr(sorted(EXPECTED_SUPPORTED)) + "\nactual=" + repr(sorted(promoted)))
    if review["matrix_count"] != 130 or review["promotion_count"] != 6:
        die("Historical witness matrix count/promotion count drifted.")
    for row in rows:
        if row["evidence_status"]["print_check"] != "not_checked":
            die(f"Print check accidentally upgraded: {row['id']}")
        if row["evidence_status"]["primary_source_status"] != "unknown":
            die(f"Primary source accidentally upgraded: {row['id']}")


def run_checks() -> None:
    print("\n=== Repo checks ===")
    sh(["git", "diff", "--check"])
    sh([sys.executable, "-m", "pytest", "-q"])
    sh([sys.executable, "scripts/audit_snapshots.py"])
    sh(["git", "diff", "--stat"])
    sh(["git", "status", "--short"])


def commit_changes() -> None:
    paths = [str(p.relative_to(ROOT)) for p in MANAGED if p.exists()]
    sh(["git", "add", "--", *paths])
    unstaged = sh(["git", "diff", "--name-only"], capture=True).stdout.strip()
    if unstaged:
        die("Unexpected unstaged changes remain; refusing to commit.\n" + unstaged)
    staged = sh(["git", "diff", "--cached", "--name-only"], capture=True).stdout.strip()
    if not staged:
        die("Nothing staged to commit.")
    print("\nStaged files:\n" + staged)
    sh(["git", "commit", "-m", "Promote DK V1 024-045 claims with 1957-58 witnesses"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()
    if args.push and not args.commit:
        die("--push requires --commit")
    ensure_repo_state()
    before = snapshot_managed()
    try:
        rows = load_jsonl(RECORDS)
        index = load_json(INDEX)
        validate_baseline(rows, index)
        review = make_review_matrix(rows)
        rows = apply_promotions(rows)
        index = update_index(index, review)
        write_jsonl(RECORDS, rows)
        write_json(INDEX, index)
        write_json(REVIEW, review)
        update_existing_research_md()
        write_review_research(review)
        write_tests()
        install_repo_script()
        validate_after(rows, review)
        print("\n=== Historical witness review summary ===")
        print("Teaching units:                 130")
        print("dk_attested:                    124")
        print("earlier_witness_supported:        6")
        print("partial matches not promoted:     6")
        print("not evaluated in targeted pass: 118")
        print("dk_print_checked:                 0")
        print("primary_source_verified:          0")
        print("verbatim wording claimed:         0")
        print("sensitivity flags removed:        0")
        print("Tracked exact witness text:       NONE")
        run_checks()
    except Exception:
        restore_managed(before)
        raise
    if args.commit:
        commit_changes()
    if args.push:
        sh(["git", "push", "origin", EXPECTED_BRANCH])
    print("\n=== Final ===")
    sh(["git", "status", "--short"])
    sh(["git", "log", "-5", "--oneline"])


if __name__ == "__main__":
    main()
