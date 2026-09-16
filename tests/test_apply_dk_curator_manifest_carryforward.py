import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APPLIER = ROOT / "scripts" / "apply_dk_curator_manifest.py"

STRONG_ID = "mahaperiyava.deivathin_kural.v1.synthetic_chapter.stronger"
NORMAL_ID = "mahaperiyava.deivathin_kural.v1.synthetic_chapter.normal"
OTHER_ID = "mahaperiyava.deivathin_kural.v1.unrelated.keep"


def _write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _pilot_record(record_id, authority, role="official_digital"):
    prov = [{
        "source_key": "pilot-source",
        "witness_role": "official_digital",
        "url": "https://example.test/pilot",
        "locus": "p001",
        "snapshot_sha256": "1" * 64,
        "lineage_note": "synthetic",
        "rights_status": "restricted_private_research",
    }]
    if role == "earlier_secondary":
        prov.append({
            "source_key": "synthetic-earlier",
            "witness_role": "earlier_secondary",
            "url": "https://example.test/earlier",
            "locus": "printed p. 1",
            "snapshot_sha256": "2" * 64,
            "lineage_note": "synthetic earlier witness",
            "rights_status": "restricted_private_research",
        })
    return {
        "id": record_id,
        "source_locus": {
            "volume": 1,
            "chapter_title_ta": "Synthetic",
            "chapter_ordinal": 100,
        },
        "attribution": {
            "wording_status": (
                "earlier_witness_agrees"
                if authority == "earlier_witness_supported"
                else "dk_wording_only"
            )
        },
        "evidence_status": {
            "digital_attestation": "confirmed",
            "print_check": "not_checked",
            "primary_source_status": "unknown",
            "authority": authority,
        },
        "provenance": prov,
        "flags": [],
    }


def _manifest():
    return {
        "version": "1.0",
        "corpus": "mahaperiyava_teachings",
        "work": "deivathin_kural",
        "volume": 1,
        "batch": "synthetic",
        "generated_at": "2026-09-16T00:00:00+00:00",
        "source_packet": {
            "packet_version": "1.0",
            "sha256": "a" * 64,
            "chapter_count": 1,
            "paragraph_count": 2,
            "contains_restricted_source_text": True,
        },
        "policy": {
            "source_paragraph_accounting": "at_least_once_or_explicitly_excluded"
        },
        "counts": {
            "source_paragraphs": 2,
            "covered_source_paragraphs": 2,
            "explicitly_excluded_source_paragraphs": 0,
        },
        "chapters": [{
            "ordinal": 100,
            "title_ta": "Synthetic",
            "url": "https://example.test/dk",
            "source_key": "synthetic-dk",
            "snapshot_sha256": "3" * 64,
        }],
        "units": [
            {
                "id": STRONG_ID,
                "chapter_ordinal": 100,
                "chapter_slug": "synthetic_chapter",
                "unit_slug": "stronger",
                "claim_summary": "Synthetic stronger claim.",
                "question_intents": ["Synthetic?"],
                "source_paragraph_ids": ["p001"],
                "source_paragraph_hashes": ["4" * 64],
                "topics": ["synthetic"],
                "flags": [],
                "authority": "dk_attested",
            },
            {
                "id": NORMAL_ID,
                "chapter_ordinal": 100,
                "chapter_slug": "synthetic_chapter",
                "unit_slug": "normal",
                "claim_summary": "Synthetic normal claim.",
                "question_intents": ["Synthetic normal?"],
                "source_paragraph_ids": ["p002"],
                "source_paragraph_hashes": ["5" * 64],
                "topics": ["synthetic"],
                "flags": [],
                "authority": "dk_attested",
            },
        ],
    }


def _carry():
    earlier = {
        "source_key": "synthetic-earlier",
        "witness_role": "earlier_secondary",
        "url": "https://example.test/earlier",
        "locus": "printed p. 1",
        "snapshot_sha256": "2" * 64,
        "lineage_note": "synthetic earlier witness",
        "rights_status": "restricted_private_research",
    }
    return {
        "version": "0.2",
        "status": "CURATOR_APPROVED",
        "chapter_decisions": [{
            "chapter_ordinal": 100,
            "action": "carry_forward_stronger_evidence",
            "carry_forward_stronger_evidence": True,
            "update_queue": True,
            "remove_pilot_records": True,
            "pilot_record_count": 2,
            "pilot_record_ids": [STRONG_ID, NORMAL_ID],
            "replacement_record_ids": [STRONG_ID, NORMAL_ID],
        }],
        "witness_decisions": [{
            "id": STRONG_ID,
            "chapter_ordinal": 100,
            "source_paragraph_ids": ["p001"],
            "decision": "carry_forward_earlier_witness_support",
            "evidence_status_authority": "earlier_witness_supported",
            "wording_status": "earlier_witness_agrees",
            "earlier_witness": earlier,
        }],
    }


@pytest.fixture
def synthetic_repo(tmp_path):
    review = tmp_path / "data" / "review"
    review.mkdir(parents=True)

    # Copy schemas in case the applier validates generated records against them.
    if (ROOT / "schema").exists():
        shutil.copytree(ROOT / "schema", tmp_path / "schema")

    manifest_path = review / "manifest.json"
    carry_path = review / "carry.json"
    _write_json(manifest_path, _manifest())
    _write_json(carry_path, _carry())

    pilot_rows = [
        _pilot_record(STRONG_ID, "earlier_witness_supported", "earlier_secondary"),
        _pilot_record(NORMAL_ID, "dk_attested"),
        {
            **_pilot_record(OTHER_ID, "dk_attested"),
            "source_locus": {
                "volume": 1,
                "chapter_title_ta": "Other",
                "chapter_ordinal": 200,
            },
        },
    ]
    _write_jsonl(
        review / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl",
        pilot_rows,
    )
    _write_json(
        review / "mahaperiyava_dk_v1_pilot_curation_index.json",
        {
            "version": "0.1",
            "corpus": "mahaperiyava_teachings",
            "work": "deivathin_kural",
            "volume": 1,
            "phase": "pilot_teaching_units_curated",
            "unit_count": 3,
            "authority_counts": {
                "earlier_witness_supported": 1,
                "dk_attested": 2,
            },
            "chapter_unit_counts": {"100": 2, "200": 1},
            "units": [
                {
                    "id": STRONG_ID,
                    "chapter_ordinal": 100,
                    "authority": "earlier_witness_supported",
                    "historical_witness": {
                        "source_key": "synthetic-earlier",
                        "locus": "printed p. 1",
                    },
                },
                {
                    "id": NORMAL_ID,
                    "chapter_ordinal": 100,
                    "authority": "dk_attested",
                    "historical_witness": None,
                },
                {
                    "id": OTHER_ID,
                    "chapter_ordinal": 200,
                    "authority": "dk_attested",
                    "historical_witness": None,
                },
            ],
        },
    )
    _write_jsonl(
        review / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl",
        [
            {
                "ordinal": 100,
                "title_ta": "Synthetic",
                "pilot": True,
                "stage": "pilot_teaching_units_curated",
                "teaching_units_created": 2,
            },
            {
                "ordinal": 200,
                "title_ta": "Other",
                "pilot": True,
                "stage": "pilot_teaching_units_curated",
                "teaching_units_created": 1,
            },
        ],
    )
    return tmp_path, manifest_path, carry_path


def _run(repo, manifest, carry, mode):
    return subprocess.run(
        [
            sys.executable,
            str(APPLIER),
            str(manifest),
            "--carry-forward",
            str(carry),
            "--repo-root",
            str(repo),
            mode,
        ],
        text=True,
        capture_output=True,
    )


def test_carryforward_check_and_dry_run_do_not_mutate(synthetic_repo):
    repo, manifest, carry = synthetic_repo
    review = repo / "data" / "review"
    tracked = [
        review / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl",
        review / "mahaperiyava_dk_v1_pilot_curation_index.json",
        review / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl",
    ]
    before = {p: p.read_bytes() for p in tracked}

    for mode in ("--check", "--dry-run"):
        r = _run(repo, manifest, carry, mode)
        assert r.returncode == 0, r.stdout + r.stderr
        assert {p: p.read_bytes() for p in tracked} == before


def test_apply_carries_witness_and_removes_only_approved_pilot_ids(synthetic_repo):
    repo, manifest, carry = synthetic_repo
    review = repo / "data" / "review"

    r = _run(repo, manifest, carry, "--apply")
    assert r.returncode == 0, r.stdout + r.stderr

    records = _read_jsonl(
        review / "mahaperiyava_dk_v1_batch_synthetic_teaching_records.jsonl"
    )
    by_id = {r["id"]: r for r in records}
    strong = by_id[STRONG_ID]
    normal = by_id[NORMAL_ID]

    assert strong["evidence_status"]["authority"] == "earlier_witness_supported"
    assert strong["attribution"]["wording_status"] == "earlier_witness_agrees"
    assert strong["evidence_status"]["print_check"] == "not_checked"
    assert strong["evidence_status"]["primary_source_status"] == "unknown"
    assert "historical_witness" not in strong
    assert "candidate_witness" not in strong
    assert "match_level" not in strong

    earlier = [p for p in strong["provenance"] if p["witness_role"] == "earlier_secondary"]
    assert earlier == [{
        "source_key": "synthetic-earlier",
        "witness_role": "earlier_secondary",
        "url": "https://example.test/earlier",
        "locus": "printed p. 1",
        "snapshot_sha256": "2" * 64,
        "lineage_note": "synthetic earlier witness",
        "rights_status": "restricted_private_research",
    }]
    assert normal["evidence_status"]["authority"] == "dk_attested"

    index = json.loads(
        (review / "mahaperiyava_dk_v1_batch_synthetic_curation_index.json").read_text(
            encoding="utf-8"
        )
    )
    iu = {u["id"]: u for u in index["units"]}
    assert iu[STRONG_ID]["authority"] == "earlier_witness_supported"
    assert iu[STRONG_ID]["historical_witness"] is not None

    remaining = _read_jsonl(
        review / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
    )
    assert [r["id"] for r in remaining] == [OTHER_ID]

    pidx = json.loads(
        (review / "mahaperiyava_dk_v1_pilot_curation_index.json").read_text(
            encoding="utf-8"
        )
    )
    assert [u["id"] for u in pidx["units"]] == [OTHER_ID]

    q = _read_jsonl(
        review / "mahaperiyava_deivathin_kural_v1_extraction_queue.jsonl"
    )
    q100 = next(row for row in q if row["ordinal"] == 100)
    assert q100["stage"] == "batch_teaching_units_curated"
    assert q100["teaching_units_created"] == 2

    # Second apply must be a valid no-op for already-removed pilot IDs.
    before = {
        p: p.read_bytes()
        for p in [
            review / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl",
            review / "mahaperiyava_dk_v1_pilot_curation_index.json",
        ]
    }
    r2 = _run(repo, manifest, carry, "--apply")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    after = {p: p.read_bytes() for p in before}
    assert after == before


def test_partial_pilot_removal_state_fails_closed(synthetic_repo):
    repo, manifest, carry = synthetic_repo
    review = repo / "data" / "review"
    pilot_path = review / "mahaperiyava_dk_v1_pilot_teaching_records.jsonl"
    rows = [r for r in _read_jsonl(pilot_path) if r["id"] != NORMAL_ID]
    _write_jsonl(pilot_path, rows)

    r = _run(repo, manifest, carry, "--apply")
    assert r.returncode != 0
    text = (r.stdout + r.stderr).lower()
    assert "partial" in text or "pilot" in text or "expected" in text


def test_stronger_pilot_evidence_without_witness_decision_fails_closed(synthetic_repo):
    repo, manifest, carry = synthetic_repo
    cf = json.loads(carry.read_text(encoding="utf-8"))
    cf["witness_decisions"] = []
    _write_json(carry, cf)

    r = _run(repo, manifest, carry, "--check")
    assert r.returncode != 0
    text = (r.stdout + r.stderr).lower()
    assert "witness" in text or "stronger" in text or "downgrade" in text
