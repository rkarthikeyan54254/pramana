#!/usr/bin/env python3
import json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
contracts=json.loads((ROOT/'schema/source_contracts.json').read_text())['contracts']
episodes=json.loads((ROOT/'schema/episode_catalog.json').read_text())['episodes']
keys=set()
for c in contracts:
    assert c['key'] not in keys, f"duplicate contract {c['key']}"
    keys.add(c['key'])
    assert c['url'].startswith('https://')
    assert c['status'] in {'source_pinned_structure_verified','source_pinned'}
for e in episodes:
    assert e['status'] in {'locus_verified','chapter_range_verified','exact_locus_verified','needs_locus_verification'}
    if e['status'] in {'locus_verified','chapter_range_verified','exact_locus_verified'}:
        assert e.get('start_locus') and e.get('end_locus'), e['key']
print(f"source contracts: {len(contracts)}; episodes: {len(episodes)}; locus-verified: {sum(e['status']=='locus_verified' for e in episodes)}; chapter-range-verified: {sum(e['status']=='chapter_range_verified' for e in episodes)}")
