from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def test_evidence_depth_triage_is_bounded_and_non_promoting():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "triage.json"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/triage_mahaperiyava_evidence_depth.py"),
                "--output",
                str(out),
            ],
            check=True,
        )
        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["input_count"] == 30
        assert report["output_count"] == 30
        assert report["authority_promotions"] == 0
        assert report["source_text_included"] is False
        assert {item["volume"] for item in report["items"]} == {1,2,3,4,5,6,7}
        assert all(item["authority_changed"] is False for item in report["items"])
        assert all(item["current_authority"] == "dk_attested" for item in report["items"])
        assert sum(report["tier_counts"].values()) == 30
