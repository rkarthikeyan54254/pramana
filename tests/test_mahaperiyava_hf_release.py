from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_mahaperiyava_hf_release import build
from scripts.check_mahaperiyava_hf_release import validate_release


def test_metadata_only_huggingface_bundle_builds_and_validates():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "hf"
        built = build(out)
        result = validate_release(out)

        assert result["status"] == "HUGGINGFACE_METADATA_RELEASE_CANDIDATE_GREEN"
        assert result["record_count"] == 3368
        assert result["source_text_included"] is False
        assert result["publication_approval"] is False

        info = json.loads((out / "dataset_info.json").read_text(encoding="utf-8"))
        assert info["authority_counts"] == {
            "dk_attested": 3331,
            "earlier_witness_supported": 37,
        }

        rows = [
            json.loads(line)
            for line in (out / "records.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(rows) == 3368
        assert all(row["rights"]["public_export"] == "metadata_only" for row in rows)
        assert all("curator_notes" not in row for row in rows)
        assert all("digital_anchor" not in row.get("source", {}) for row in rows)


def test_release_records_do_not_contain_private_review_markers():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "hf"
        build(out)
        blob = (out / "records.jsonl").read_text(encoding="utf-8").casefold()
        for marker in (
            "private_curation_blocks:",
            "private batch review packet",
            "paragraph_sha256=",
            "source_packet_sha256=",
            "exact_text_restricted",
        ):
            assert marker.casefold() not in blob
