import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts/audit_mahaperiyava_v1_release.py"
REPORT = ROOT / "data/review/mahaperiyava_dk_v1_release_checkpoint.json"
RETRIEVAL = ROOT / "data/review/mahaperiyava_dk_v1_retrieval_checkpoint.json"


def test_v1_release_audit_passes():
    r = subprocess.run(
        [sys.executable, str(AUDIT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_release_checkpoint_records_frozen_semantic_frontier():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["counts"] == {
        "teaching_records": 927,
        "chapters": 175,
        "dk_attested": 894,
        "earlier_witness_supported": 33,
        "pilot_records": 28,
        "print_checked": 0,
        "primary_source_verified": 0,
    }


def test_retrieval_checkpoint_records_quality_without_faking_readiness():
    report = json.loads(RETRIEVAL.read_text(encoding="utf-8"))
    assert report["checkpoint"] == "THIN_V1_RETRIEVAL_BASELINE"
    assert report["metrics"]["supported_cases"] == 7
    assert report["metrics"]["unsupported_cases"] == 1
    assert 0.0 <= report["metrics"]["top1_accuracy"] <= 1.0
    assert 0.0 <= report["metrics"]["top5_recall"] <= 1.0
    assert report["metrics"]["abstention_accuracy"] == 1.0
    if report["metrics"]["top5_recall"] < report["quality_target"]["top5_recall"]:
        assert report["status"] == "BASELINE_RECORDED_RETRIEVAL_NOT_READY"
        assert report["decision"] == "do_not_use_as_production_answerer"
        assert report["failed_case_ids"]
