from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "data/review"

SOURCE_KEY = (
    "illustrated-weekly-as-raman-interview-1963-scan"
)

TARGETS = {
    "mahaperiyava.deivathin_kural.v1.advaitamum_anu_vignaanamum.science_matter_energy_unity_as_analogy":
        "mahaperiyava_dk_v1_batch_001_022_curation_index.json",

    "mahaperiyava.deivathin_kural.v1.sadangugal.ritual_cultivates_concentration_and_discipline":
        "mahaperiyava_dk_v1_batch_086_105_curation_index.json",

    "mahaperiyava.deivathin_kural.v2.c206.knowledge_is_to_be_grounded_in_character_and_religious_discipline_before_broad_intellectual_exploration":
        "mahaperiyava_deivathin_kural_v2_curation_index.json",

    "mahaperiyava.deivathin_kural.v3.c110.ritual_observances_shared_across_different_doctrines_preparatory":
        "mahaperiyava_deivathin_kural_v3_curation_index.json",
}


def load_json(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def test_four_promotions_are_synced_into_curation_indexes():
    for rid, filename in TARGETS.items():
        d = load_json(R / filename)

        matches = [
            u for u in d["units"]
            if u["id"] == rid
        ]

        assert len(matches) == 1

        unit = matches[0]

        assert (
            unit["authority"]
            == "earlier_witness_supported"
        )

        witness = unit["historical_witness"]

        assert witness is not None
        assert witness["source_key"] == SOURCE_KEY
        assert witness["witness_role"] == "earlier_secondary"
        assert witness["match_level"] == "same_claim"
        assert len(witness["snapshot_sha256"]) == 64


def test_curation_index_authority_counts_match_units():
    files = {
        filename
        for filename in TARGETS.values()
    }

    for filename in files:
        d = load_json(R / filename)

        actual = Counter(
            u["authority"]
            for u in d["units"]
        )

        if "authority_counts" in d:
            assert d["authority_counts"] == dict(actual)


def test_only_four_raman_curation_units_are_promoted_by_this_source():
    found = set()

    for path in R.glob(
        "mahaperiyava*curation_index.json"
    ):
        d = load_json(path)

        for unit in d.get("units", []):
            witness = unit.get("historical_witness")

            if not isinstance(witness, dict):
                continue

            if witness.get("source_key") != SOURCE_KEY:
                continue

            assert (
                unit["authority"]
                == "earlier_witness_supported"
            )

            found.add(unit["id"])

    assert found == set(TARGETS)
