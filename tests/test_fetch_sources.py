from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(
    0,
    str(ROOT / "scripts"),
)

from fetch_sources import enforce_expected_snapshot


class FetchSourceSnapshotContractTests(
    unittest.TestCase
):
    def test_matching_snapshot_contract(self):
        data = b"pramana-witness"
        import hashlib

        sha = hashlib.sha256(data).hexdigest()

        actual = enforce_expected_snapshot(
            {
                "key": "fixture",
                "expected_sha256": sha,
                "expected_bytes": len(data),
            },
            data,
        )

        self.assertEqual(actual, sha)

    def test_hash_change_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "source hash mismatch",
        ):
            enforce_expected_snapshot(
                {
                    "key": "fixture",
                    "expected_sha256": "0" * 64,
                },
                b"changed",
            )

    def test_byte_length_change_fails_closed(self):
        with self.assertRaisesRegex(
            ValueError,
            "source byte-length mismatch",
        ):
            enforce_expected_snapshot(
                {
                    "key": "fixture",
                    "expected_bytes": 999,
                },
                b"changed",
            )


if __name__ == "__main__":
    unittest.main()
