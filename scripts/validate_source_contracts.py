#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

contracts = json.loads(
    (ROOT / "schema/source_contracts.json").read_text(encoding="utf-8")
)["contracts"]

episodes = json.loads(
    (ROOT / "schema/episode_catalog.json").read_text(encoding="utf-8")
)["episodes"]

allowed_statuses = {
    "source_pinned_structure_verified",
    "source_pinned",
    "pilot_contract_defined",
}

keys = set()

for c in contracts:
    key = c["key"]

    assert key not in keys, f"duplicate contract {key}"
    keys.add(key)

    assert c["status"] in allowed_statuses, (
        f"{key}: unexpected status {c['status']!r}"
    )

    # Validate direct URL-bearing contracts.
    for field in ("url", "primary_url", "secondary_url"):
        value = c.get(field)
        if value is not None:
            assert isinstance(value, str) and value.startswith("https://"), (
                f"{key}: invalid {field}: {value!r}"
            )

    template = c.get("secondary_source_url_template")
    if template is not None:
        assert template.startswith("https://"), (
            f"{key}: invalid secondary_source_url_template"
        )

    for url in c.get("secondary_source_chapters", []):
        assert url.startswith("https://"), (
            f"{key}: invalid secondary source chapter URL: {url!r}"
        )

    # A source contract must provide either a direct source URL or a structural
    # source-key model. Deivathin Kural intentionally uses per-volume official
    # index source keys rather than one synthetic top-level URL.
    has_direct_url = any(
        c.get(field)
        for field in ("url", "primary_url", "secondary_url")
    )

    official_index_keys = (
        c.get("structure", {}).get("official_index_source_keys", [])
    )

    assert has_direct_url or official_index_keys, (
        f"{key}: contract has neither a source URL nor official index source keys"
    )

    if official_index_keys:
        assert isinstance(official_index_keys, list)
        assert len(official_index_keys) == len(set(official_index_keys))
        assert all(
            isinstance(x, str) and x.strip()
            for x in official_index_keys
        ), f"{key}: invalid official_index_source_keys"

for e in episodes:
    assert e["status"] in {
        "locus_verified",
        "chapter_range_verified",
        "exact_locus_verified",
        "needs_locus_verification",
    }

    if e["status"] in {
        "locus_verified",
        "chapter_range_verified",
        "exact_locus_verified",
    }:
        assert e.get("start_locus") and e.get("end_locus"), e["key"]

print(
    f"source contracts: {len(contracts)}; "
    f"episodes: {len(episodes)}; "
    f"locus-verified: "
    f"{sum(e['status'] == 'locus_verified' for e in episodes)}; "
    f"chapter-range-verified: "
    f"{sum(e['status'] == 'chapter_range_verified' for e in episodes)}"
)
