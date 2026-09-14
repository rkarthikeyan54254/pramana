#!/usr/bin/env python3
# Apply the targeted historical-witness review to Mahaperiyava DK Volume 1
# batch ordinals 001..022.
#
# Run from the pramana repo root on:
#     mahaperiyava-dk-v1-corpus
#
# Recommended:
#     python ~/Downloads/apply_mahaperiyava_dk_v1_batch_001_022_witness_review.py --commit --push
#
# This milestone records a 102-row TARGETED historical-witness review matrix
# and promotes exactly 13 narrow claims to earlier_witness_supported.
# It does NOT claim print-checking, primary-source verification, verbatim
# oral wording, or exhaustive witness coverage.

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

RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_curation_index.json"
REVIEW = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_historical_witness_review.json"
RESEARCH = ROOT / "data/research/mahaperiyava_dk_v1_batch_001_022_teaching_units.md"
REVIEW_RESEARCH = ROOT / "data/research/mahaperiyava_dk_v1_batch_001_022_historical_witness_review.md"
TEST = ROOT / "tests/test_mahaperiyava_dk_v1_batch_001_022_teaching_records.py"
REVIEW_TEST = ROOT / "tests/test_mahaperiyava_dk_v1_batch_001_022_historical_witness_review.py"
REPO_SCRIPT = ROOT / "scripts/apply_mahaperiyava_dk_v1_batch_001_022_witness_review.py"

PART1 = {
    "source_key": "acharya-upanyasangal-part1-1957-58-scan",
    "title": "Acharya Swamigalin Upanyasangal — Part 1",
    "url": "https://mahaperiyavaa.blog/wp-content/uploads/2023/04/Acharyaswamigal-Upanyasangal-Part-1.pdf",
    "snapshot_sha256": "ace3c1cca4c3077d9e15080365741f541d471274c28d11e07d85f2b372901f7e",
    "rights_status": "restricted_private_research",
}

PART2 = {
    "source_key": "acharya-upanyasangal-part2-1957-58-scan",
    "title": "Acharya Swamigalin Upanyasangal — Part 2",
    "url": "https://mahaperiyavaa.blog/wp-content/uploads/2023/04/Acharyaswamigal-Upanyasangal-Part-2.pdf",
    "snapshot_sha256": "eaf06d8936fb3b160a279b388ec0e2ef408be49c416618bf8bfb9d038f4a31e1",
    "rights_status": "restricted_private_research",
}

LINEAGE_NOTE = (
    "1957–58 witness from the Acharya Swamigalin Upanyasangal publication "
    "family. The collection was produced through shorthand capture, typed "
    "copies, and editorial arrangement. Claim-level agreement therefore "
    "supports earlier attestation of the teaching, but printed wording is "
    "not treated as verbatim primary speech and textual dependence on "
    "Deivathin Kural is not asserted."
)

SUPPORTED: dict[str, dict[str, Any]] = {
    "mahaperiyava.deivathin_kural.v1.vinayagar.avvaiyar_worship_as_kailasa": {
        "witness": PART2,
        "locus": "Part 2, விக்னேசுவரர், printed pp. 43–51 (PDF pp. 54–62)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness contains the Avvaiyar/Vinayaka/Kailasa narrative used for the same devotional teaching.",
    },
    "mahaperiyava.deivathin_kural.v1.vinayagar.ganesha_grace_elevates_devotee": {
        "witness": PART2,
        "locus": "Part 2, விக்னேசுவரர், printed pp. 43–51 (PDF pp. 54–62)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness preserves the same Avvaiyar narrative in which Vinayaka's grace elevates the devotee to Kailasa.",
    },
    "mahaperiyava.deivathin_kural.v1.tattuva_mayamana_vinayagar.coconut_as_highest_offering": {
        "witness": PART2,
        "locus": "Part 2, விக்னேசுவரர், printed pp. 43–51 (PDF pp. 54–62)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness gives the same interpretive use of coconut offering in Vinayaka worship.",
    },
    "mahaperiyava.deivathin_kural.v1.tattuva_mayamana_vinayagar.large_form_small_vehicle_symbolism": {
        "witness": PART2,
        "locus": "Part 2, விக்னேசுவரர், printed pp. 43–51 (PDF pp. 54–62)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness supports the large-form/small-vehicle symbolic teaching at claim level.",
    },
    "mahaperiyava.deivathin_kural.v1.tattuva_mayamana_vinayagar.broken_tusk_sacrifice_for_dharma": {
        "witness": PART2,
        "locus": "Part 2, விக்னேசுவரர், printed pp. 43–51 (PDF pp. 54–62)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness supports the broken-tusk interpretation as self-sacrifice in sacred/dharmic work.",
    },
    "mahaperiyava.deivathin_kural.v1.tattuva_mayamana_vinayagar.elephant_form_as_joy_symbol": {
        "witness": PART2,
        "locus": "Part 2, விக்னேசுவரர், printed pp. 43–51 (PDF pp. 54–62)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness supports the interpretive link between Vinayaka's form and joy/ananda.",
    },
    "mahaperiyava.deivathin_kural.v1.tattuva_mayamana_vinayagar.thoppukaranam_story_and_etymology": {
        "witness": PART2,
        "locus": "Part 2, விக்னேசுவரர், printed pp. 43–51 (PDF pp. 54–62)",
        "match_level": "same_traditional_explanation",
        "note": "Earlier witness attests the same traditional thoppukaranam explanation. This upgrades attribution of the teaching only; the etymology remains externally unverified.",
    },
    "mahaperiyava.deivathin_kural.v1.swami_naama_illai_endral.bhakti_needed_before_direct_nonduality": {
        "witness": PART2,
        "locus": "Part 2, எல்லாம் தழுவும் அத்வைதம், printed p. 29 (PDF p. 40)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness explicitly presents saguna bhakti/upasana as the practical route for approaching the Advaitic state.",
    },
    "mahaperiyava.deivathin_kural.v1.swami_naama_illai_endral.all_beings_as_forms_of_one_reality": {
        "witness": PART2,
        "locus": "Part 2, எல்லாம் தழுவும் அத்வைதம், printed pp. 29–30 (PDF pp. 40–41)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness supports the move from apparent multiplicity toward a single underlying Advaitic reality.",
    },
    "mahaperiyava.deivathin_kural.v1.swami_etharku_advaitam_amaithikke.meditation_on_isvara_shapes_mind_toward_peace": {
        "witness": PART2,
        "locus": "Part 2, பக்தியும் கர்மமும், printed pp. 24–27 (PDF pp. 35–38)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness supports devotional/upasana practice as a means of shaping and purifying the mind toward spiritual steadiness.",
    },
    "mahaperiyava.deivathin_kural.v1.swami_etharku_advaitam_amaithikke.saguna_worship_practical_for_restless_mind": {
        "witness": PART2,
        "locus": "Part 2, எல்லாம் தழுவும் அத்வைதம், printed p. 29 (PDF p. 40)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness explicitly treats saguna bhakti as a practical preparatory means before Advaitic realization.",
    },
    "mahaperiyava.deivathin_kural.v1.kandamum_akandamum.tat_tvam_asi_identity": {
        "witness": PART2,
        "locus": "Part 2, முடிவான நிலை, printed p. 94 (PDF p. 105)",
        "match_level": "close_paraphrase",
        "note": "Earlier witness explicitly states the Tat–Tvam identity teaching at the same doctrinal level.",
    },
    "mahaperiyava.deivathin_kural.v1.kandamum_akandamum.saguna_meditation_toward_nirguna": {
        "witness": PART2,
        "locus": "Part 2, முடிவான நிலை, printed pp. 94–96 (PDF pp. 105–107)",
        "match_level": "same_doctrinal_claim",
        "note": "Earlier witness supports progression from conditioned/saguna contemplation toward higher nondual/nirguna realization.",
    },
}

PARTIAL: dict[str, dict[str, Any]] = {
    "mahaperiyava.deivathin_kural.v1.vinayagar.ganesha_as_pranava_form": {
        "witness": PART2,
        "locus": "Part 2, விக்னேசுவரர், printed pp. 43–51 (PDF pp. 54–62)",
        "match_level": "partial_match_not_sufficient",
        "note": "Earlier witness supports Vinayaka/Pranava identification, but the DK unit also bundles a broader cosmic-origin interpretation. No authority upgrade for the compound claim.",
    },
    "mahaperiyava.deivathin_kural.v1.tattuva_mayamana_vinayagar.ganesha_invoked_before_all_worship": {
        "witness": PART2,
        "locus": "Part 2, விக்னேசுவரர், printed pp. 43–51 (PDF pp. 54–62)",
        "match_level": "partial_match_not_sufficient",
        "note": "Earlier material supports Vinayaka's vighna-related role, but the DK unit also bundles first-worship and Ganapatya claims.",
    },
    "mahaperiyava.deivathin_kural.v1.swami_etharku_advaitam_amaithikke.karma_and_bhakti_as_mind_purification": {
        "witness": PART2,
        "locus": "Part 2, பக்தியும் கர்மமும், printed pp. 24–27 (PDF pp. 35–38)",
        "match_level": "partial_match_not_sufficient",
        "note": "Earlier witness agrees with the preparatory role of karma/bhakti, but the DK unit is broader than the reviewed passage.",
    },
    "mahaperiyava.deivathin_kural.v1.swami_etharku_advaitam_amaithikke.selfless_duty_purifies_chitta": {
        "witness": PART2,
        "locus": "Part 2, பக்தியும் கர்மமும், printed pp. 24–27 (PDF pp. 35–38)",
        "match_level": "partial_match_not_sufficient",
        "note": "The witness supports karma as preparation/purification, but the specific DK formulation about selfless social duty is broader.",
    },
}

EXPECTED_SUPPORTED = set(SUPPORTED)
EXPECTED_UNIT_COUNT = 102

MANAGED = [
    RECORDS,
    INDEX,
    REVIEW,
    RESEARCH,
    REVIEW_RESEARCH,
    TEST,
    REVIEW_TEST,
    REPO_SCRIPT,
]


def die(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def sh(cmd: list[str], *, capture: bool = False, check: bool = True):
    print("+", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=check,
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    if not path.exists():
        die(f"Missing expected file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        die(f"Missing expected file: {path.relative_to(ROOT)}")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def ensure_repo_state() -> None:
    if not (ROOT / ".git").exists():
        die("Run from the pramana repo root.")

    branch = sh(["git", "branch", "--show-current"], capture=True).stdout.strip()
    if branch != EXPECTED_BRANCH:
        die(f"Expected {EXPECTED_BRANCH!r}; found {branch!r}")

    dirty = sh(["git", "status", "--porcelain"], capture=True).stdout.strip()
    if dirty:
        die("Working tree must be clean before witness promotion.\n" + dirty)

    for path in (RECORDS, INDEX, RESEARCH, TEST):
        if not path.exists():
            die(f"Missing required input: {path.relative_to(ROOT)}")

    if REVIEW.exists():
        die(
            "Historical witness review file already exists. "
            "This script is intentionally one-shot."
        )


def validate_baseline(
    rows: list[dict[str, Any]],
    index: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    if len(rows) != EXPECTED_UNIT_COUNT:
        die(f"Expected 102 batch records; found {len(rows)}")

    by_id = {row["id"]: row for row in rows}
    if len(by_id) != EXPECTED_UNIT_COUNT:
        die("Teaching record IDs are not unique.")

    missing_supported = EXPECTED_SUPPORTED - set(by_id)
    if missing_supported:
        die(
            "Expected promotion IDs missing:\n  - "
            + "\n  - ".join(sorted(missing_supported))
        )

    missing_partial = set(PARTIAL) - set(by_id)
    if missing_partial:
        die(
            "Expected partial-match IDs missing:\n  - "
            + "\n  - ".join(sorted(missing_partial))
        )

    counts = Counter(row["evidence_status"]["authority"] for row in rows)
    if counts != Counter({"dk_attested": 102}):
        die(f"Unexpected baseline authority distribution: {counts}")

    for row in rows:
        if row["evidence_status"]["print_check"] != "not_checked":
            die(f"Unexpected print-check state in {row['id']}")
        if row["evidence_status"]["primary_source_status"] != "unknown":
            die(f"Unexpected primary-source state in {row['id']}")
        if row["attribution"]["wording_status"] != "dk_wording_only":
            die(f"Unexpected baseline wording status in {row['id']}")
        roles = [p["witness_role"] for p in row["provenance"]]
        if roles != ["official_digital"]:
            die(f"Unexpected baseline provenance in {row['id']}: {roles}")

    if index.get("unit_count") != 102:
        die("Curation index is not the expected 102-unit batch.")

    index_ids = {u["id"] for u in index["units"]}
    if index_ids != set(by_id):
        die("Curation index IDs do not exactly match teaching-record IDs.")

    return by_id


def make_review_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = []

    for row in rows:
        unit_id = row["id"]

        if unit_id in SUPPORTED:
            evidence = SUPPORTED[unit_id]
            status = "supported_for_claim_level_promotion"
            proposed = "earlier_witness_supported"
            witness = {
                "source_key": evidence["witness"]["source_key"],
                "locus": evidence["locus"],
                "match_level": evidence["match_level"],
                "note": evidence["note"],
            }
        elif unit_id in PARTIAL:
            evidence = PARTIAL[unit_id]
            status = "partial_match_not_sufficient"
            proposed = "dk_attested"
            witness = {
                "source_key": evidence["witness"]["source_key"],
                "locus": evidence["locus"],
                "match_level": evidence["match_level"],
                "note": evidence["note"],
            }
        else:
            status = "not_evaluated_in_targeted_sections"
            proposed = "dk_attested"
            witness = None

        matrix.append(
            {
                "id": unit_id,
                "chapter_ordinal": row["source_locus"]["chapter_ordinal"],
                "chapter_title_ta": row["source_locus"]["chapter_title_ta"],
                "claim_summary": row.get("claim_summary"),
                "review_scope": "targeted_section_level_manual_comparison",
                "review_status": status,
                "authority_before": "dk_attested",
                "authority_after": proposed,
                "historical_witness": witness,
                "guardrails": {
                    "verbatim_wording_claimed": False,
                    "primary_source_verified_claimed": False,
                    "textual_dependency_claimed": False,
                    "external_factual_truth_claimed": False,
                },
            }
        )

    counts = Counter(x["review_status"] for x in matrix)

    return {
        "version": "0.1",
        "generated_at": now_iso(),
        "corpus": "mahaperiyava_teachings",
        "work": "deivathin_kural",
        "volume": 1,
        "batch": "001_022",
        "review_type": "targeted_historical_witness_matching",
        "review_scope": {
            "exhaustive_across_all_102_units": False,
            "description": (
                "Manual comparison of high-yield Ganesha, Advaita, bhakti, "
                "upasana and Tat-Tvam sections against the acquired 1957–58 "
                "Acharya Swamigalin Upanyasangal scans. Rows outside the "
                "targeted sections are explicitly marked not evaluated rather "
                "than treated as negative evidence."
            ),
        },
        "witnesses_consulted": [PART1, PART2],
        "transmission_guardrail": LINEAGE_NOTE,
        "matrix_count": len(matrix),
        "status_counts": dict(sorted(counts.items())),
        "promotion_count": sum(
            1 for x in matrix
            if x["authority_after"] == "earlier_witness_supported"
        ),
        "policy": {
            "claim_level_only": True,
            "no_chapter_wide_promotion": True,
            "no_verbatim_claim": True,
            "no_primary_source_upgrade": True,
            "sensitivity_flags_do_not_change": True,
            "earlier_attestation_is_separate_from_external_factual_truth": True,
        },
        "rows": matrix,
    }


def apply_promotions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    original_flags = {
        row["id"]: list(row.get("flags", []))
        for row in rows
    }

    for row in rows:
        unit_id = row["id"]
        if unit_id not in SUPPORTED:
            continue

        evidence = SUPPORTED[unit_id]
        witness = evidence["witness"]

        row["evidence_status"]["authority"] = "earlier_witness_supported"
        row["attribution"]["wording_status"] = "earlier_witness_agrees"
        row["attribution"]["note"] = (
            "Curator-authored summary, not a quotation. Official Kanchi "
            "digital Deivathin Kural attests this teaching, and a pre-DK "
            "1957–58 Acharya Swamigalin Upanyasangal witness supports this "
            "narrow claim. Printed witness wording is not treated as verbatim "
            "oral wording; no textual dependence is asserted."
        )

        row["provenance"].append(
            {
                "source_key": witness["source_key"],
                "witness_role": "earlier_secondary",
                "url": witness["url"],
                "locus": evidence["locus"],
                "snapshot_sha256": witness["snapshot_sha256"],
                "lineage_note": LINEAGE_NOTE,
                "rights_status": witness["rights_status"],
            }
        )

        row["curator_notes"] = (
            row.get("curator_notes", "")
            + " Historical witness targeted-pass result: "
            + evidence["match_level"]
            + "; "
            + evidence["locus"]
            + ". Earlier attestation supports the narrow teaching only; "
            + "not verbatim and not primary-source verified."
        ).strip()

    for row in rows:
        if row.get("flags", []) != original_flags[row["id"]]:
            die(f"Sensitivity flags changed unexpectedly in {row['id']}")

    return rows


def update_index(
    index: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    by_review = {r["id"]: r for r in review["rows"]}

    for unit in index["units"]:
        r = by_review[unit["id"]]
        unit["authority"] = r["authority_after"]
        if r["authority_after"] == "earlier_witness_supported":
            unit["historical_witness"] = r["historical_witness"]
        else:
            unit["historical_witness"] = None

    counts = Counter(u["authority"] for u in index["units"])
    index["authority_counts"] = dict(sorted(counts.items()))

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
        "exhaustive": False,
    }

    return index


def write_research_review(review: dict[str, Any]) -> None:
    supported = [
        r for r in review["rows"]
        if r["authority_after"] == "earlier_witness_supported"
    ]
    partial = [
        r for r in review["rows"]
        if r["review_status"] == "partial_match_not_sufficient"
    ]

    lines = [
        "# Mahaperiyava DK V1 Batch 001–022 — Historical Witness Review",
        "",
        "## Result",
        "",
        "- Teaching units in batch: **102**",
        "- Promoted to `earlier_witness_supported`: **13**",
        "- Remaining `dk_attested`: **89**",
        "- `dk_print_checked`: **0**",
        "- `primary_source_verified`: **0**",
        "",
        "This was a **targeted**, not exhaustive, historical-witness pass.",
        "It manually compared the highest-yield Ganesha, Advaita, bhakti, "
        "upasana and Tat-Tvam claims with the acquired 1957–58 "
        "*Acharya Swamigalin Upanyasangal* scans.",
        "",
        "Rows outside those targeted sections are recorded as "
        "`not_evaluated_in_targeted_sections`; that status is **not negative evidence**.",
        "",
        "## Transmission guardrail",
        "",
        "The earlier volumes were produced through shorthand capture, typed "
        "copies and editorial arrangement. Therefore an authority upgrade means "
        "the **teaching is supported by an earlier witness**. It does not mean "
        "the printed wording is verbatim oral speech, and it does not establish "
        "a primary source.",
        "",
        "## Promoted narrow claims",
        "",
    ]

    for row in supported:
        w = row["historical_witness"]
        lines.append(
            f"- `{row['id']}` — `{w['match_level']}` — "
            f"{w['source_key']}; {w['locus']}"
        )

    lines += [
        "",
        "## Partial matches deliberately not promoted",
        "",
    ]
    for row in partial:
        w = row["historical_witness"]
        lines.append(f"- `{row['id']}` — {w['note']}")

    lines += [
        "",
        "## Important evidence distinction",
        "",
        "`earlier_witness_supported` concerns **earlier attestation of the "
        "teaching**. It does not independently prove every external historical, "
        "scientific, medical, etymological or hagiographic assertion embedded "
        "inside that teaching. Existing sensitivity flags are therefore retained.",
        "",
        "For example, the thoppukaranam unit can be historically supported as "
        "an earlier-attested Mahaperiyava teaching while still retaining its "
        "`etymology_claim_requires_external_verification` flag.",
        "",
        "## Next gate",
        "",
        "An exhaustive witness search across the remaining 89 units is still "
        "open. No unmatched unit in this targeted pass should be interpreted as "
        "having no historical witness.",
        "",
    ]

    REVIEW_RESEARCH.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_RESEARCH.write_text("\n".join(lines), encoding="utf-8")


def update_existing_research_md() -> None:
    text = RESEARCH.read_text(encoding="utf-8")
    marker = "## Historical witness targeted pass"
    if marker in text:
        die("Existing research markdown already contains witness-pass marker.")

    addition = '''

## Historical witness targeted pass

A targeted manual comparison against the acquired 1957–58
*Acharya Swamigalin Upanyasangal* scans promoted **13** narrow claims to
`earlier_witness_supported`. The batch authority distribution is now:

- `dk_attested`: **89**
- `earlier_witness_supported`: **13**
- `dk_print_checked`: **0**
- `primary_source_verified`: **0**

This is not an exhaustive negative search over all 102 units. Unreviewed rows
remain `dk_attested`. Existing science, health, astrology, mathematical,
etymology, hagiographic and other sensitivity flags remain unchanged.

See:
`data/review/mahaperiyava_dk_v1_batch_001_022_historical_witness_review.json`.
'''
    # Keep exactly one trailing newline and no blank line at EOF so
    # `git diff --check` remains clean.
    RESEARCH.write_text(
        text.rstrip() + "\n\n" + addition.strip() + "\n",
        encoding="utf-8",
    )


def write_tests() -> None:
    TEST.write_text(
        '''from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_teaching_records.jsonl"
INDEX = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_curation_index.json"
QUEUE = ROOT / "data/review/mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"

EXPECTED = {1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,22}


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path):
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def test_batch_shape_and_claim_level_authority():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)

    assert len(rows) == 102
    assert index["unit_count"] == 102
    assert len({r["id"] for r in rows}) == 102
    assert {r["source_locus"]["chapter_ordinal"] for r in rows} == EXPECTED

    assert Counter(
        r["evidence_status"]["authority"] for r in rows
    ) == {
        "dk_attested": 89,
        "earlier_witness_supported": 13,
    }

    assert all(
        r["evidence_status"]["print_check"] == "not_checked"
        for r in rows
    )
    assert all(
        r["evidence_status"]["primary_source_status"] == "unknown"
        for r in rows
    )


def test_earlier_supported_rows_have_independent_witness_edge():
    rows = _jsonl(RECORDS)
    supported = [
        r for r in rows
        if r["evidence_status"]["authority"] == "earlier_witness_supported"
    ]
    assert len(supported) == 13

    for row in supported:
        roles = [p["witness_role"] for p in row["provenance"]]
        assert roles == ["official_digital", "earlier_secondary"]
        assert row["attribution"]["wording_status"] == "earlier_witness_agrees"
        assert "not treated as verbatim" in row["provenance"][1]["lineage_note"]
        assert row["evidence_status"]["primary_source_status"] == "unknown"


def test_dk_only_rows_remain_fail_closed():
    rows = _jsonl(RECORDS)
    dk_only = [
        r for r in rows
        if r["evidence_status"]["authority"] == "dk_attested"
    ]
    assert len(dk_only) == 89
    assert all(
        r["attribution"]["wording_status"] == "dk_wording_only"
        for r in dk_only
    )
    assert all(
        [p["witness_role"] for p in r["provenance"]] == ["official_digital"]
        for r in dk_only
    )


def test_no_restricted_source_text_is_tracked():
    rows = _jsonl(RECORDS)
    index = _json(INDEX)

    assert index["source_packet"]["tracked"] is False
    assert index["policy"]["no_exact_source_text_in_tracked_artifacts"] is True

    for row in rows:
        assert "text" not in row
        assert "exact_text_restricted" not in row
        assert row["rights"]["source_text_tier"] == "restricted"
        assert row["rights"]["public_export"] == "metadata_only"


def test_private_hash_mapping_and_question_intents_exist():
    index = _json(INDEX)
    assert len(index["units"]) == 102

    for unit in index["units"]:
        assert unit["question_intents"]
        assert len(unit["source_paragraph_ids"]) == len(
            unit["source_paragraph_hashes"]
        )
        assert all(
            re.fullmatch(r"[0-9a-f]{64}", h)
            for h in unit["source_paragraph_hashes"]
        )


def test_queue_stays_semantically_curated():
    queue = _jsonl(QUEUE)
    selected = [q for q in queue if q["ordinal"] in EXPECTED]

    assert len(selected) == 20
    assert all(not q["pilot"] for q in selected)
    assert all(
        q["stage"] == "batch_teaching_units_curated"
        for q in selected
    )
    assert all(q["teaching_units_created"] > 0 for q in selected)


def test_sensitive_claims_can_gain_attestation_without_losing_flags():
    rows = _jsonl(RECORDS)
    thoppu = next(
        r for r in rows
        if r["id"].endswith(".thoppukaranam_story_and_etymology")
    )

    assert thoppu["evidence_status"]["authority"] == "earlier_witness_supported"
    assert "etymology_claim_requires_external_verification" in thoppu["flags"]
    assert "hagiographic_tradition" in thoppu["flags"]


def test_index_records_targeted_not_exhaustive_review():
    index = _json(INDEX)
    policy = index["policy"]

    assert policy["targeted_historical_witness_pass_completed"] is True
    assert policy["historical_witness_exhaustive_review_completed"] is False
    assert policy["historical_witness_support_is_claim_level"] is True
    assert policy["no_verbatim_wording_claimed"] is True
    assert policy["no_primary_source_verified_claimed"] is True
''',
        encoding="utf-8",
    )

    REVIEW_TEST.write_text(
        '''from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_historical_witness_review.json"
RECORDS = ROOT / "data/review/mahaperiyava_dk_v1_batch_001_022_teaching_records.jsonl"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path):
    return [
        json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]


def test_witness_review_has_one_row_per_teaching_unit():
    review = _json(REVIEW)
    rows = _jsonl(RECORDS)

    assert review["matrix_count"] == 102
    assert len(review["rows"]) == 102
    assert {r["id"] for r in review["rows"]} == {r["id"] for r in rows}


def test_review_is_explicitly_targeted_not_exhaustive():
    review = _json(REVIEW)

    assert review["review_type"] == "targeted_historical_witness_matching"
    assert review["review_scope"]["exhaustive_across_all_102_units"] is False
    assert review["policy"]["no_chapter_wide_promotion"] is True
    assert review["policy"]["no_verbatim_claim"] is True
    assert review["policy"]["no_primary_source_upgrade"] is True


def test_exactly_13_supported_and_4_partial():
    review = _json(REVIEW)
    counts = Counter(r["review_status"] for r in review["rows"])

    assert counts["supported_for_claim_level_promotion"] == 13
    assert counts["partial_match_not_sufficient"] == 4
    assert counts["not_evaluated_in_targeted_sections"] == 85
    assert review["promotion_count"] == 13


def test_supported_rows_have_locus_and_guardrails():
    review = _json(REVIEW)
    supported = [
        r for r in review["rows"]
        if r["review_status"] == "supported_for_claim_level_promotion"
    ]

    for row in supported:
        witness = row["historical_witness"]
        assert witness["source_key"].startswith("acharya-upanyasangal-")
        assert "printed p" in witness["locus"]
        assert witness["match_level"] in {
            "same_doctrinal_claim",
            "same_traditional_explanation",
            "close_paraphrase",
        }
        assert row["guardrails"]["verbatim_wording_claimed"] is False
        assert row["guardrails"]["primary_source_verified_claimed"] is False
        assert row["guardrails"]["textual_dependency_claimed"] is False


def test_partial_matches_do_not_promote():
    review = _json(REVIEW)
    partial = [
        r for r in review["rows"]
        if r["review_status"] == "partial_match_not_sufficient"
    ]

    assert partial
    assert all(r["authority_after"] == "dk_attested" for r in partial)
''',
        encoding="utf-8",
    )


def install_repo_script() -> None:
    REPO_SCRIPT.parent.mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    if src != REPO_SCRIPT.resolve():
        shutil.copyfile(src, REPO_SCRIPT)
        REPO_SCRIPT.chmod(0o755)


def snapshot_managed() -> dict[Path, bytes | None]:
    return {
        path: path.read_bytes() if path.exists() else None
        for path in MANAGED
    }


def restore_managed(snapshot: dict[Path, bytes | None]) -> None:
    print("\n=== Validation failed: restoring managed files ===")
    sh(["git", "reset"], check=False)

    for path, content in snapshot.items():
        if content is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    sh(["git", "status", "--short"], check=False)


def validate_after(
    rows: list[dict[str, Any]],
    review: dict[str, Any],
) -> None:
    counts = Counter(
        row["evidence_status"]["authority"] for row in rows
    )
    if counts != Counter(
        {"dk_attested": 89, "earlier_witness_supported": 13}
    ):
        die(f"Unexpected post-review authority distribution: {counts}")

    promoted = {
        row["id"]
        for row in rows
        if row["evidence_status"]["authority"]
        == "earlier_witness_supported"
    }
    if promoted != EXPECTED_SUPPORTED:
        die(
            "Promotion set drifted.\nexpected="
            + repr(sorted(EXPECTED_SUPPORTED))
            + "\nactual="
            + repr(sorted(promoted))
        )

    if review["matrix_count"] != 102:
        die("Historical witness matrix must have 102 rows.")
    if review["promotion_count"] != 13:
        die("Historical witness matrix must have 13 promotions.")

    for row in rows:
        if row["evidence_status"]["print_check"] != "not_checked":
            die(f"Print check was accidentally upgraded: {row['id']}")
        if row["evidence_status"]["primary_source_status"] != "unknown":
            die(f"Primary source was accidentally upgraded: {row['id']}")


def run_checks() -> None:
    print("\n=== Repo checks ===")
    sh(["git", "diff", "--check"])
    sh([sys.executable, "-m", "pytest", "-q"])
    sh([sys.executable, "scripts/audit_snapshots.py"])
    sh(["git", "diff", "--stat"])
    sh(["git", "status", "--short"])


def commit_changes() -> None:
    paths = [
        str(path.relative_to(ROOT))
        for path in MANAGED
        if path.exists()
    ]

    sh(["git", "add", "--", *paths])

    unstaged = sh(
        ["git", "diff", "--name-only"],
        capture=True,
    ).stdout.strip()
    if unstaged:
        die(
            "Unexpected unstaged changes remain; refusing to commit.\n"
            + unstaged
        )

    staged = sh(
        ["git", "diff", "--cached", "--name-only"],
        capture=True,
    ).stdout.strip()
    if not staged:
        die("Nothing staged to commit.")

    print("\nStaged files:")
    print(staged)

    sh(
        [
            "git",
            "commit",
            "-m",
            "Promote DK V1 claims with 1957-58 witnesses",
        ]
    )


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
        write_research_review(review)
        update_existing_research_md()
        write_tests()
        install_repo_script()

        validate_after(rows, review)

        print("\n=== Historical witness promotion summary ===")
        print("Teaching units:                 102")
        print("dk_attested:                     89")
        print("earlier_witness_supported:       13")
        print("partial matches not promoted:     4")
        print("not evaluated in targeted pass:  85")
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
    else:
        print("\nChanges validated but not committed.")

    if args.push:
        sh(["git", "push", "origin", EXPECTED_BRANCH])

    print("\n=== Final ===")
    sh(["git", "status", "--short"])
    sh(["git", "log", "-5", "--oneline"])
    print(
        "\nTargeted 1957–58 historical-witness pass complete. "
        "Next gate: either exhaustive witness matching for the remaining "
        "89 units, or return to the next DK semantic batch."
    )


if __name__ == "__main__":
    main()
