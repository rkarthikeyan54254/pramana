#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rag'))
from verified_store import load_jsonl
from cross_text_compare import build_comparison
rows=load_jsonl([str(ROOT/'tests/rag/cross_text_fixture.jsonl')])
spec=json.loads((ROOT/'tests/rag/cross_text_spec.json').read_text(encoding='utf-8'))
out=build_comparison(rows,spec)
assert {c['id'] for c in out['claims']} == {'c1','c2'}
assert any(c['id']=='c3' and c['reason']=='support_not_verified_or_missing' for c in out['rejected_claims'])
assert any(g['source_key']=='alwar' and g['dimension']=='episode_presence' for g in out['gaps'])
assert any(s['source_key']=='alwar' and s['status']=='no_verified_evidence' for s in out['sources'])
assert out['policy']['silent_reconciliation'] is False
print('cross-text comparison: PASS')
