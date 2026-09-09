#!/usr/bin/env python3
import json,re,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
eps=json.loads((ROOT/'schema/episode_catalog.json').read_text())['episodes']
allowed={'locus_verified','chapter_range_verified','exact_locus_verified','needs_locus_verification'}
seen=set(); exact=0
for e in eps:
    k=e['key']; assert k not in seen, f'duplicate episode {k}'; seen.add(k)
    assert e['status'] in allowed,(k,e['status'])
    if e['status']!='needs_locus_verification':
        assert e.get('start_locus') and e.get('end_locus'),k
    if e['status']=='exact_locus_verified':
        exact+=1
        if e['parent_work']=='bhagavata_purana':
            pat=r'^BhP_\d{2}\.\d{2}\.\d{3}\*?$'
            assert re.match(pat,e['start_locus']), (k,e['start_locus'])
            assert re.match(pat,e['end_locus']), (k,e['end_locus'])
print(f'episode catalog: {len(eps)} episodes; exact={exact}; unresolved={sum(e["status"]=="needs_locus_verification" for e in eps)}')
