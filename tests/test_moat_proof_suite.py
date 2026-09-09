#!/usr/bin/env python3
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from product.verify_claim import run as verify
from product.compare_sources import run as compare
from product.trace_evidence import run as trace

p=verify('नरसिंहः स्तम्भमध्याद् निर्गत्य')
assert p['verified'] and any(x['id']=='purana.narasimha_purana.44.16' for x in p['matches'])
n=verify('Everything happens for a reason')
assert not n['verified'] and n['verdict']=='no_verified_exact_match'
c=compare()
assert len(c['sources'])==3 and not c['rejected_claims']
assert {g['source_key'] for g in c['gaps'] if g['dimension']=='place_association'} >= {'bhagavata','vishnu_purana'}
t=trace('person:prahlada',2)
assert t['edges'] and all(e['evidence_ids'] for e in t['edges'])
s=trace('place:srisaila',2)
assert not any(node['id'].startswith('temple:') for node in s['nodes'])
print('test_moat_proof_suite: PASS')
