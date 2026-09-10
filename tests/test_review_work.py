from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_work import (
    machine_classify,
    safe_norm,
    strip_terminal_unit_marker,
    tamil_ranking_projection,
)


class ReviewWorkV2Tests(unittest.TestCase):
    def test_terminal_marker_removed_only_when_matching(self):
        self.assertEqual(strip_terminal_unit_marker("abc (17)", 17), "abc")
        self.assertEqual(strip_terminal_unit_marker("abc (18)", 17), "abc (18)")

    def test_projection_folds_joining_noise(self):
        self.assertEqual(
            tamil_ranking_projection("நீர் ஆட்டு ஏலோர்"),
            tamil_ranking_projection("நீராட்டேலோர்"),
        )

    def test_projection_does_not_collapse_real_lexical_difference(self):
        self.assertNotEqual(
            tamil_ranking_projection("உகந்து"),
            tamil_ranking_projection("உறங்கேல்"),
        )

    def test_machine_output_never_contains_verified_authority(self):
        r = machine_classify(
            "நீர் ஆட்டு ஏலோர் (20)",
            "நீராட்டேலோர்",
            ["நீராட்டேலோர்"],
            high_similarity=0.945,
            unit_no=20,
        )
        self.assertNotIn("verified", r)

    def test_projected_similarity_is_ranking_only(self):
        r = machine_classify(
            "செப்பு அன்ன மென் முலைச்",
            "செப்பன்ன மென்முலை",
            ["செப்பன்ன மென்முலை"],
            high_similarity=0.945,
            unit_no=20,
        )
        self.assertIn("ranking_projected_similarity", r)
        self.assertIn(
            r["machine_classification"],
            {"high_similarity_review_candidate", "textual_review_required"},
        )


if __name__ == "__main__":
    unittest.main()
