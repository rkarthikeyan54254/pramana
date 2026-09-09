#!/usr/bin/env python3
import json
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "schema" / "ithihasa_purana_catalog.json"
data = json.loads(p.read_text(encoding="utf-8"))

anchors = data.get("tier_1_anchor_corpora", [])
assert anchors, "tier_1_anchor_corpora must not be empty"
works = []
for tier in ("tier_1_anchor_corpora", "tier_2_high_value_corpora"):
    for row in data.get(tier, []):
        work = row.get("work")
        assert work, f"missing work in {tier}"
        assert row.get("corpus"), f"missing corpus for {work}"
        assert row.get("priority") in (1, 2), f"invalid priority for {work}"
        assert row.get("primary_source_candidates"), f"no source candidates for {work}"
        works.append(work)
assert len(works) == len(set(works)), "duplicate work across tier 1/2"

# Stable high-value anchors that should not disappear accidentally.
required = {
    "valmiki_ramayana",
    "mahabharata_critical_edition",
    "harivamsa_critical_edition",
    "bhagavata_purana",
    "vishnu_purana",
    "devi_mahatmya",
}
missing = required - set(works)
assert not missing, f"missing required anchor corpora: {sorted(missing)}"

assert data.get("cross_corpus_products"), "cross_corpus_products must not be empty"
print(f"Ithihasa/Purana catalog OK: {len(anchors)} tier-1 anchors, {len(data.get('tier_2_high_value_corpora', []))} tier-2 corpora, {len(data.get('tier_3_breadth', []))} tier-3 candidates")
